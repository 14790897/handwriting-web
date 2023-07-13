#!/bin/bash

# 读取.gitignore文件中的每一行
while IFS= read -r line
do
    # 使用git rm --cached命令删除对应的文件或目录
    # 注意：如果要删除目录，需要添加-r选项
    git rm --cached -r "$line"
done < .gitignore

# 提交更改
git commit -m "Removed files specified in .gitignore"

# 推送更改到远程仓库
git push
