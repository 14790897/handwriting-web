@echo off
setlocal enabledelayedexpansion

REM 读取.gitignore文件中的每一行
for /F "delims=" %%i in (.gitignore) do (
    REM 使用git rm --cached命令删除对应的文件或目录
    REM 注意：如果要删除目录，需要添加-r选项
    git rm --cached -r "%%i"
)

REM 提交更改
git commit -m "Removed files specified in .gitignore"

REM 推送更改到远程仓库
git push
