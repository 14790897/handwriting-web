<!--
PR 标题必须遵循 Conventional Commits（feat: / fix: / chore: / test: ...），semantic-release 靠它决定版本号。
写法：类型: 英文动词开头的简短描述，例如 feat: add one-click Chinese letter formatting
-->

## Problem

<!-- 这个 PR 解决什么问题？为什么需要改？引用相关 issue（如 #46）。 -->

## Solution

<!-- 具体做了什么，逐条列出关键改动；说明取舍、边界情况和被有意排除的范围。 -->

## Screenshots

<!-- 涉及界面或生成结果变化时必填：用表格做前后对比，图片直接拖进文本框上传。纯后端改动 / 重构可删除本节。 -->

| Before | After |
| --- | --- |
|  |  |

## Validation

<!-- 逐条列出你实际跑过的命令和验证步骤，不要只写"测试通过"。 -->

-

## Checklist

- [ ] 标题是 Conventional Commits 格式
- [ ] 新增的用户可见文字已同时提供中英文翻译（`frontend/src/i18n.js`）
- [ ] 需要被 `e2e/` 测试点到的元素已加 `data-testid`
- [ ] 未手动修改 `CHANGELOG.md` 和版本号

<!--
按需保留的可选小节：
## Root cause   —— 修 bug 时说明根因，而不只是现象
## Impact       —— 对 API、配置、用户行为的影响范围
## Dependency   —— 合并顺序，以及依赖的其他 PR
-->
