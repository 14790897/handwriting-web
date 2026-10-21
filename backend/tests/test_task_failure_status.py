"""业务错误必须把任务标成 failed，并带上可以直接展示的错误信息。

回归 #70：generate_handwriting_impl 对「缺背景图」「CPU 过高」「非法图片」这类业务
错误返回的是 JSONResponse（400/429），并不是抛异常。run_generation_task 以前不看
状态码就写 completed，前端把它当成功、再去拉 result 只拿到笼统失败，用户看不到
真实原因。结果接口本来就有 failed 分支，所以这里只要把状态标对即可。
"""

import asyncio
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.responses import JSONResponse

import app as app_module


def _run_generation(response, task_id):
    """跑完一次 run_generation_task，generate_handwriting_impl 换成返回给定响应。"""

    async def fake_impl(**_kwargs):
        return response

    async def push_noop(*_args, **_kwargs):
        return None

    async def runner():
        # 每次新建信号量：asyncio.Semaphore 在 3.10+ 会绑定到首次使用的 loop，复用
        # 模块级那个会在第二个用例里报 "attached to a different loop"。
        with patch.object(
            app_module, "_generation_semaphore", asyncio.Semaphore(1)
        ), patch.object(app_module, "generate_handwriting_impl", fake_impl), patch.object(
            app_module, "push_task_status_update", push_noop
        ):
            await app_module.run_generation_task(task_id, "http://test/", {})

    asyncio.run(runner())


class GenerationTaskFailureStatusTests(unittest.TestCase):
    def setUp(self):
        self.task_id = uuid4().hex

    def tearDown(self):
        # pop 同时清掉结果目录，避免测试往 backend/temp 里留东西
        app_module.pop_generation_task(self.task_id)

    def test_business_error_marks_task_failed(self):
        """缺背景图这类 400 必须变成 failed，而不是 completed。"""
        _run_generation(
            JSONResponse(
                {"status": "error", "message": "Missing required field: background_image"},
                status_code=400,
            ),
            self.task_id,
        )

        task = app_module.get_generation_task(self.task_id)
        self.assertEqual(task["status"], "failed")
        self.assertEqual(
            task["error_message"], "Missing required field: background_image"
        )
        self.assertEqual(task["response_status_code"], 400)
        # 失败时不该落结果文件：结果接口的 failed 分支只读 error_message
        self.assertIsNone(task["result_file_path"])

    def test_rate_limited_response_marks_task_failed(self):
        """429 也走失败路径，前端要能看到提示而不是「任务处理完成」。"""
        _run_generation(
            JSONResponse(
                {
                    "status": "error",
                    "message": "CPU usage is too high. Please wait and try again.",
                },
                status_code=429,
            ),
            self.task_id,
        )

        task = app_module.get_generation_task(self.task_id)
        self.assertEqual(task["status"], "failed")
        self.assertEqual(
            task["error_message"], "CPU usage is too high. Please wait and try again."
        )

    def test_unparsable_error_body_still_fails(self):
        """响应体不是 JSON 时不能把 error_message 写空，要有兜底文案。"""
        _run_generation(
            JSONResponse({"unexpected": True}, status_code=500), self.task_id
        )

        task = app_module.get_generation_task(self.task_id)
        self.assertEqual(task["status"], "failed")
        self.assertTrue(task["error_message"])
        self.assertIn("500", task["error_message"])

    def test_successful_response_still_completes(self):
        """正常返回不受影响。"""
        _run_generation(JSONResponse({"ok": True}, status_code=200), self.task_id)

        task = app_module.get_generation_task(self.task_id)
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["response_status_code"], 200)


if __name__ == "__main__":
    unittest.main()
