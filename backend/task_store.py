"""
SQLite 任务存储层：跨进程/worker 安全的任务状态管理。

元数据存 SQLite，response_body（图片/PDF 等大文件）存磁盘，避免 DB 膨胀。
"""

import json
import os
import logging
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from task_types import GenerationTask

logger = logging.getLogger(__name__)

# ── 配置 ────────────────────────────────────────────────────────────

_DB_PATH = Path(__file__).resolve().parent / "tasks.db"
_RESULT_DIR = Path(__file__).resolve().parent / "temp" / "task_results"
_DB_TIMEOUT = 10  # 秒
_TTL_SECONDS = 60 * 30  # 30 分钟

_write_lock = Lock()

# DB 列定义，顺序即 INSERT 顺序
_COLUMNS = [
    "task_id", "status", "stage", "message", "progress",
    "created_at", "updated_at",
    "response_status_code", "response_content_type", "response_headers",
    "result_file_path", "error_message",
]

_CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS generation_tasks (
    task_id             TEXT PRIMARY KEY,
    status              TEXT NOT NULL DEFAULT 'pending',
    stage               TEXT DEFAULT '',
    message             TEXT DEFAULT '',
    progress            INTEGER DEFAULT 0,
    created_at          REAL,
    updated_at          REAL,
    response_status_code INTEGER,
    response_content_type TEXT,
    response_headers    TEXT,
    result_file_path    TEXT,
    error_message       TEXT DEFAULT ''
)
"""

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON generation_tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON generation_tasks(updated_at)",
]


# ── 连接管理 ────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), timeout=_DB_TIMEOUT)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


# ── 初始化 ──────────────────────────────────────────────────────────

def init():
    """应用启动时调用，确保表和目录存在。"""
    _RESULT_DIR.mkdir(parents=True, exist_ok=True)
    conn = _connect()
    try:
        conn.execute(_CREATE_TABLE_SQL)
        for sql in _CREATE_INDEXES_SQL:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


init()


# ── 行 ↔ dict 转换 ────────────────────────────────────────────────

def _row_to_task(row: sqlite3.Row | None) -> Optional[GenerationTask]:
    if row is None:
        return None
    headers_raw = row["response_headers"]
    headers = json.loads(headers_raw) if isinstance(headers_raw, str) else (headers_raw or {})
    return {
        "status": row["status"],
        "stage": row["stage"],
        "message": row["message"],
        "progress": row["progress"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "response_status_code": row["response_status_code"],
        "response_content_type": row["response_content_type"],
        "response_headers": headers,
        "result_file_path": row["result_file_path"],
        "error_message": row["error_message"],
    }


def _serialize_updates(updates: dict[str, Any]) -> dict[str, Any]:
    """将 Python 对象转为 DB 可存值。"""
    if "response_headers" in updates and isinstance(updates["response_headers"], dict):
        updates["response_headers"] = json.dumps(updates["response_headers"])
    return updates


# ── 磁盘文件操作 ────────────────────────────────────────────────────

def _write_result_file(task_id: str, data: bytes) -> str:
    """将 response_body 写入磁盘，返回文件绝对路径。"""
    task_dir = _RESULT_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    path = task_dir / "result.bin"
    path.write_bytes(data)
    return str(path)


def _read_result_file(file_path: str) -> bytes | None:
    """从磁盘读取结果文件，失败静默返回 None。"""
    try:
        if not os.path.exists(file_path):
            return None
        return Path(file_path).read_bytes()
    except Exception as e:
        logger.warning("Failed to read result file %s: %s", file_path, e)
        return None


def _remove_result_dir(task_id: str):
    """删除任务的结果目录（整个 task_id 子目录）。"""
    task_dir = _RESULT_DIR / task_id
    if task_dir.exists():
        try:
            import shutil
            shutil.rmtree(task_dir, ignore_errors=True)
        except Exception as e:
            logger.warning("Failed to remove result dir %s: %s", task_dir, e)


# ── 公开 API ────────────────────────────────────────────────────────

def set_task(task_id: str, **updates: Any) -> GenerationTask:
    """写入/更新任务。若传入 response_body（bytes），自动存磁盘。"""
    # response_body → 磁盘文件
    response_body = updates.pop("response_body", None)
    if isinstance(response_body, (bytes, bytearray)):
        updates["result_file_path"] = _write_result_file(task_id, response_body)

    updates["updated_at"] = updates.pop("updated_at", None) or time.time()
    _serialize_updates(updates)

    with _write_lock:
        conn = _connect()
        try:
            # INSERT OR REPLACE — 一条 SQL 搞定 upsert
            row = conn.execute(
                "SELECT task_id FROM generation_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()

            if row is not None:
                # UPDATE：只更新传入的字段
                set_clause = ", ".join(f"{k} = :{k}" for k in updates)
                params = {"task_id": task_id, **updates}
                conn.execute(
                    f"UPDATE generation_tasks SET {set_clause} WHERE task_id = :task_id",
                    params,
                )
            else:
                # INSERT：补齐所有列的默认值
                defaults: dict[str, Any] = {
                    "task_id": task_id,
                    "status": "pending", "stage": "", "message": "",
                    "progress": 0, "created_at": updates["updated_at"],
                    "updated_at": updates["updated_at"],
                    "response_status_code": None, "response_content_type": None,
                    "response_headers": "{}", "result_file_path": None,
                    "error_message": "",
                }
                defaults.update(updates)
                placeholders = ", ".join(f":{c}" for c in _COLUMNS)
                conn.execute(
                    f"INSERT INTO generation_tasks ({', '.join(_COLUMNS)}) VALUES ({placeholders})",
                    defaults,
                )
            conn.commit()

            return _row_to_task(
                conn.execute(
                    "SELECT * FROM generation_tasks WHERE task_id = ?", (task_id,)
                ).fetchone()
            )
        finally:
            conn.close()


def get_task(task_id: str) -> Optional[GenerationTask]:
    """读取任务（纯读操作，不需要写锁）。"""
    conn = _connect()
    try:
        return _row_to_task(
            conn.execute(
                "SELECT * FROM generation_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
        )
    finally:
        conn.close()


def pop_task(task_id: str) -> Optional[GenerationTask]:
    """读取并删除任务，同时清理磁盘文件。"""
    with _write_lock:
        conn = _connect()
        try:
            task = _row_to_task(
                conn.execute(
                    "SELECT * FROM generation_tasks WHERE task_id = ?", (task_id,)
                ).fetchone()
            )
            if task is not None:
                conn.execute("DELETE FROM generation_tasks WHERE task_id = ?", (task_id,))
                conn.commit()
                _remove_result_dir(task_id)
            return task
        finally:
            conn.close()


def cleanup_expired():
    """清理过期任务（TTL）及其磁盘文件。"""
    cutoff = time.time() - _TTL_SECONDS
    with _write_lock:
        conn = _connect()
        try:
            expired = conn.execute(
                "SELECT task_id FROM generation_tasks WHERE updated_at < ?",
                (cutoff,),
            ).fetchall()
            for row in expired:
                _remove_result_dir(row["task_id"])
            conn.execute(
                "DELETE FROM generation_tasks WHERE updated_at < ?", (cutoff,)
            )
            conn.commit()
        finally:
            conn.close()


def get_queue_metrics(task_id: str) -> dict[str, int]:
    """获取排队位置信息。"""
    conn = _connect()
    try:
        task = conn.execute(
            "SELECT status, created_at FROM generation_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if task is None:
            return {"queue_pending_count": 0, "queue_ahead_count": 0,
                    "processing_count": 0, "active_task_count": 0}

        pending = conn.execute(
            "SELECT COUNT(*) FROM generation_tasks WHERE status = 'pending'"
        ).fetchone()[0]
        processing = conn.execute(
            "SELECT COUNT(*) FROM generation_tasks WHERE status = 'processing'"
        ).fetchone()[0]
        ahead = 0
        if task["status"] == "pending":
            created = task["created_at"] or 0
            ahead = conn.execute(
                """SELECT COUNT(*) FROM generation_tasks
                   WHERE status = 'pending'
                   AND (created_at < ? OR (created_at = ? AND task_id < ?))""",
                (created, created, task_id),
            ).fetchone()[0]
        return {
            "queue_pending_count": pending,
            "queue_ahead_count": ahead,
            "processing_count": processing,
            "active_task_count": pending + processing,
        }
    finally:
        conn.close()


def read_result_file(file_path: str) -> bytes | None:
    """供路由层调用的磁盘读取接口。"""
    return _read_result_file(file_path)


# 导出别名，供外部使用
generation_task_ttl_seconds = _TTL_SECONDS
