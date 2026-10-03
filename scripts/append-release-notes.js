#!/usr/bin/env node
/**
 * 往 GitHub Release 正文末尾追加「哪个机器该下哪个包」的说明。
 *
 * 为什么不写成 release-notes-generator 的输出：那段说明只对 Release 页面有意义，
 * 挂在 notes 上会跟着 @semantic-release/changelog 一起写进 CHANGELOG.md，于是每次
 * 发版的历史记录里都重复一遍装包指南。
 *
 * 由 release.config.js 里 @semantic-release/exec 的 successCmd 调用 —— 用 success
 * 而不是 publish，是因为 success 阶段跑在所有 publish 之后，这时
 * @semantic-release/github 一定已经把 Release 建好了，不必依赖插件数组的顺序。
 *
 * 用法：node scripts/append-release-notes.js v1.33.0
 */
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

// 幂等标记：补跑或手动重跑时靠它判断正文里是否已经有这段说明
const MARKER = "<!-- download-guide -->";

const tag = process.argv[2];
if (!tag) {
  console.error("用法: node scripts/append-release-notes.js <gitTag>，例如 v1.33.0");
  process.exit(1);
}
const version = tag.replace(/^v/, "");

function gh(args) {
  return execFileSync("gh", args, { encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
}

const section = `${MARKER}
## 下载哪个包

安装包在本页下方的 Assets 里，按你的机器选：

| 你的机器 | 下载这个 | 说明 |
| --- | --- | --- |
| Windows | \`HandwritingWeb-Setup-${version}.exe\` | **推荐**。安装版，可选安装位置，装完有桌面与开始菜单快捷方式 |
| Windows | \`HandwritingWeb-portable-${version}.exe\` | 免安装便携版，双击直接运行 |
| Mac（Apple 芯片，M1 及以后） | \`HandwritingWeb-${version}-arm64.dmg\` | 挂载后把 \`HandwritingWeb.app\` 拖进「应用程序」 |
| Mac（Apple 芯片，M1 及以后） | \`HandwritingWeb-${version}-arm64.zip\` | 同一个 App 的压缩包，DMG 打不开时用这个 |

**Intel 芯片的 Mac 暂时没有包。** 桌面版后端不能交叉编译，目前只发 arm64。
不确定自己是哪种芯片：苹果菜单 →「关于本机」，看「芯片」那一行。

### macOS 首次打开会被拦下（正常现象）

这个包没有 Apple 开发者签名，也没有公证，所以 macOS 会拦。macOS 15 起提示的是
「已损坏，无法打开」—— 那不是真的损坏，是下载时被系统加上的 quarantine 属性。
照上面的方式装好后执行一次，之后就不会再拦：

\`\`\`bash
xattr -dr com.apple.quarantine /Applications/HandwritingWeb.app
\`\`\`

不想用命令行也行：被拦一次之后去「系统设置 → 隐私与安全性」，在下方的提示里点「仍要打开」。
`;

function main() {
  const raw = gh(["release", "view", tag, "--json", "body", "--jq", ".body"]);
  // 正文为空时 --jq .body 会给一个字符串 "null"
  const body = raw.trim() === "null" ? "" : raw;
  if (body.includes(MARKER)) {
    console.log(`${tag} 的正文里已经有下载说明，跳过`);
    return;
  }

  // gh release edit 没有 --notes-append，只能把拼好的整段正文写回去
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "release-notes-"));
  const file = path.join(dir, "body.md");
  fs.writeFileSync(file, `${body.trimEnd()}\n\n${section}`, "utf8");
  try {
    gh(["release", "edit", tag, "--notes-file", file]);
    console.log(`已把「下载哪个包」追加到 ${tag}`);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

try {
  main();
} catch (error) {
  // 故意只告警、不退出非零：这纯粹是展示文案，失败不该让发版变红。而且
  // desktop_release.yml 的预检要求 semantic-release 的 conclusion == 'success'，
  // 在这里失败会连带把 Windows / macOS 桌面包一起跳过，代价远大于少一段说明。
  console.error(`!! 追加下载说明失败（不影响发版与桌面包上传）：${error.message}`);
}
