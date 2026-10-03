module.exports = {
  branches: ["main"], // 指定要发布的分支 (通常是 main 或 master)
  plugins: [
    "@semantic-release/commit-analyzer", // 分析提交信息，确定版本更新类型（major/minor/patch）
    "@semantic-release/release-notes-generator", // 根据提交生成 changelog
    "@semantic-release/changelog", // 更新 CHANGELOG.md
    // 不配 assets：原先写的 dist/**/*.{js,css} 在仓库根根本不存在那个目录
    // （前端产物在 frontend/dist 且被 .gitignore 忽略），从来没匹配到东西；
    // 而 docs/**/* 只会把仓库里的截图挂上去，属于噪音。
    // 桌面版的安装包/便携版由 .github/workflows/desktop_release.yml 单独上传。
    "@semantic-release/github", // 发布到 GitHub，生成 Release
    [
      "@semantic-release/exec", // 把发版号同步到 desktop/package.json、desktop/package-lock.json、backend/VERSION
      {
        prepareCmd: "node scripts/sync-version.js ${nextRelease.version}",
      },
    ],
    [
      "@semantic-release/git", // 推送更新后的版本和 changelog 文件
      {
        assets: [
          "CHANGELOG.md",
          "package.json",
          "desktop/package.json",
          "desktop/package-lock.json",
          "backend/VERSION",
        ],
        message: "chore(release): ${nextRelease.version} [skip ci]",
      },
    ],
  ],
};
