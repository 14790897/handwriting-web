#!/usr/bin/env node
/**
 * 把 semantic-release 定下来的发版号同步到「不属于发版体系」但需要展示版本号的几处：
 *
 *   desktop/package.json        electron-builder 的产物名（${version}）与 About 对话框
 *   desktop/package-lock.json   npm 会把根包的 version 复制一份到 packages[""]
 *   backend/VERSION             后端 /api/version 的兜底来源（进后端镜像与桌面版包内）
 *
 * 仓库根的 package.json 没有 version 字段，发版号唯一来源就是
 * semantic-release 的 ${nextRelease.version}，所以由 release.config.js 里的
 * @semantic-release/exec 在 prepare 阶段调用本脚本，紧接着 @semantic-release/git
 * 把这几处改动随发版一起提交。
 *
 * 用法：node scripts/sync-version.js 1.31.0
 */
const fs = require("fs");
const path = require("path");

const version = process.argv[2];
if (!version || !/^\d+\.\d+\.\d+/.test(version)) {
  console.error("用法: node scripts/sync-version.js <version>，例如 1.31.0");
  process.exit(1);
}

const root = path.join(__dirname, "..");

function writeJson(file, version) {
  const json = JSON.parse(fs.readFileSync(file, "utf8"));
  const before = json.version;
  json.version = version;
  // lockfile 里 npm 会在 packages[""] 再复制一份根包的 version
  if (json.packages && json.packages[""]) {
    json.packages[""].version = version;
  }
  // JSON.stringify(x, null, 2) 与 npm 的落盘格式一致：lockfile 只会变动 version 那一两行；
  // package.json 是手写的，首次同步会把它规范成同样的格式，之后每次只改 version
  fs.writeFileSync(file, JSON.stringify(json, null, 2) + "\n");
  console.log(`${path.relative(root, file)}: ${before} -> ${version}`);
}

writeJson(path.join(root, "desktop", "package.json"), version);
writeJson(path.join(root, "desktop", "package-lock.json"), version);

const versionFile = path.join(root, "backend", "VERSION");
fs.writeFileSync(versionFile, `${version}\n`);
console.log(`backend/VERSION: ${version}`);
