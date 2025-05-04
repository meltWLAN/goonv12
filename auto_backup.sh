#!/bin/bash

# 股票分析系统 GitHub 自动备份脚本
# 自动创建一个新的备份版本和回滚点

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 预设的GitHub仓库URL
GITHUB_URL="https://github.com/meltWLAN/goonv12.git"

echo -e "${YELLOW}开始自动备份股票分析系统到GitHub...${NC}"
echo -e "${YELLOW}目标仓库: ${NC}$GITHUB_URL"

# 检查 Git 配置
if [ -z "$(git config --get user.name)" ] || [ -z "$(git config --get user.email)" ]; then
    echo -e "${RED}Git用户信息未设置. 请先运行 'git config --global user.name \"Your Name\"'${NC}"
    echo -e "${RED}和 'git config --global user.email \"your.email@example.com\"'${NC}"
    exit 1
fi

# 检查是否是Git仓库
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}初始化Git仓库...${NC}"
    git init
    echo -e "${GREEN}Git仓库已初始化${NC}"
fi

# 创建备份信息
echo -e "${YELLOW}创建备份信息...${NC}"
BACKUP_DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_MESSAGE="系统备份 - $BACKUP_DATE"
BACKUP_TAG="backup_v1.0_$BACKUP_DATE"

# 添加文件到Git
echo -e "${YELLOW}添加文件到Git...${NC}"
git add .

# 提交更改
echo -e "${YELLOW}提交更改...${NC}"
git commit -m "$BACKUP_MESSAGE"

# 创建标签
echo -e "${YELLOW}创建标签 $BACKUP_TAG...${NC}"
git tag -a "$BACKUP_TAG" -m "回滚点 - $BACKUP_DATE"

# 添加远程仓库
if git remote | grep -q origin; then
    git remote set-url origin "$GITHUB_URL"
else
    git remote add origin "$GITHUB_URL"
fi

# 推送到GitHub
echo -e "${YELLOW}推送到GitHub...${NC}"
git push -u origin main
git push --tags

echo -e "${GREEN}备份完成!${NC}"
echo -e "备份标签: ${YELLOW}$BACKUP_TAG${NC}"
echo -e "提交信息: ${YELLOW}$BACKUP_MESSAGE${NC}"
echo -e "仓库URL: ${YELLOW}$GITHUB_URL${NC}"
echo -e "${YELLOW}如需回滚，使用命令: git checkout $BACKUP_TAG${NC}" 