#!/usr/bin/env python3
"""校验 PR 标题和描述是否符合 .github/pull_request_template.md。

由 .github/workflows/pr_template.yml 在 PR 打开 / 编辑 / 推送新提交时调用。
本地自测：

    PR_TITLE="fix: 无横线页面不再 500" PR_BODY="$(cat pr.md)" \
        python3 scripts/check_pr_template.py

规则：
1. 标题符合 Conventional Commits（semantic-release 靠它决定版本号）。
2. 模板里的必填小节都存在，且去掉 HTML 注释后还有实际内容。
   Screenshots / Root cause / Impact / Dependency 是可选的。
3. 模板 Checklist 的每一条都要出现在描述里；是否勾选由作者判断，CI 不强制
   （其中两条是条件性的，不是每个 PR 都适用）。
4. 机器人账号（dependabot 等）开的 PR 跳过。

必填小节和 Checklist 条目都从模板文件里读，改模板时不用同步改这个脚本。
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"

# 模板里允许省略的小节：Screenshots 只有界面改动才需要，其余是「按需保留」
OPTIONAL_SECTIONS = {"screenshots", "root cause", "impact", "dependency"}

# semantic-release 认的提交类型
TITLE_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([^()]+\))?!?: \S.*$"
)

HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
CHECKLIST_PATTERN = re.compile(r"^- \[[ xX]\]\s+(.+?)\s*$", re.MULTILINE)


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def strip_comments(text):
    return HTML_COMMENT_PATTERN.sub("", text)


def read_template():
    # 可选小节（Root cause / Impact / Dependency）写在模板底部的 HTML 注释里，
    # 解析前必须先去注释，否则会被当成必填小节。
    template = strip_comments(TEMPLATE_PATH.read_text(encoding="utf-8"))
    headings = HEADING_PATTERN.findall(template)
    required = [h for h in headings if h.strip().lower() not in OPTIONAL_SECTIONS]
    checklist = [normalize(item) for item in CHECKLIST_PATTERN.findall(template)]
    return required, [item for item in checklist if item]


def split_sections(body):
    """把描述按 `## 标题` 切成 {小标题小写: 内容}。"""
    sections = {}
    matches = list(HEADING_PATTERN.finditer(body))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip().lower()] = body[start:end]
    return sections


def has_content(section_text):
    # 去掉 HTML 注释和只剩占位符（`-` / `*`）的行，再判断是否还有内容
    text = strip_comments(section_text)
    lines = [line.strip() for line in text.splitlines()]
    meaningful = [line for line in lines if line and line not in {"-", "*", "_"}]
    return bool(meaningful)


def check(title, body, author):
    """返回错误列表；空列表表示通过。"""
    if author.endswith("[bot]"):
        return []

    required_sections, checklist_items = read_template()
    errors = []

    if not title:
        errors.append("PR 标题为空")
    elif not TITLE_PATTERN.match(title):
        errors.append(
            "标题不符合 Conventional Commits：需要 `<类型>: <英文动词开头的简短描述>`，"
            "类型可用 feat / fix / docs / chore / test / refactor 等"
        )

    if not body or not body.strip():
        errors.append("PR 描述为空：请按 .github/pull_request_template.md 填写")
        return errors

    sections = split_sections(body)
    for heading in required_sections:
        key = heading.strip().lower()
        if key not in sections:
            errors.append(f"缺少小节：## {heading}")
        elif not has_content(sections[key]):
            errors.append(f"小节没有实际内容：## {heading}")

    cleaned_body = normalize(strip_comments(body))
    for item in checklist_items:
        if normalize(item) not in cleaned_body:
            errors.append(f"Checklist 缺少条目：- [ ] {item}")

    return errors


def report(errors):
    if not errors:
        print("PR 模板检查通过。")
        return 0

    print("PR 不符合 .github/pull_request_template.md：")
    for error in errors:
        print(f"  - {error}")
        # 在 Actions 页面上同时标成错误注解，方便直接看到
        print(f"::error::{error}")
    return 1


def main():
    title = os.getenv("PR_TITLE", "").strip()
    body = os.getenv("PR_BODY", "")
    author = os.getenv("PR_AUTHOR", "")

    if author.endswith("[bot]"):
        print(f"跳过机器人账号 {author} 的 PR。")
        return 0

    return report(check(title, body, author))


if __name__ == "__main__":
    sys.exit(main())
