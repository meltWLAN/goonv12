#!/bin/bash

# 股票分析系统 GitHub 备份脚本
# 创建一个新的备份版本和回滚点

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始备份股票分析系统到GitHub...${NC}"

# 检查 Git 配置
if [ -z "$(git config --get user.name)" ] || [ -z "$(git config --get user.email)" ]; then
    echo -e "${YELLOW}设置 Git 用户信息...${NC}"
    read -p "输入 Git 用户名: " git_user
    read -p "输入 Git 邮箱: " git_email
    
    git config --global user.name "$git_user"
    git config --global user.email "$git_email"
    echo -e "${GREEN}Git 用户信息已设置${NC}"
fi

# 检查是否是Git仓库
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}初始化Git仓库...${NC}"
    git init
    echo -e "${GREEN}Git仓库已初始化${NC}"
fi

# 创建 .gitignore 文件（如果不存在）
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}创建 .gitignore 文件...${NC}"
    cat > .gitignore << EOL
# 临时文件
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
venv/
.venv/
ENV/

# 日志和缓存
*.log
cache/
data_cache/
*.cache

# 系统文件
.DS_Store
.idea/
.vscode/
*.swp
*.swo
EOL
    echo -e "${GREEN}.gitignore 文件已创建${NC}"
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

# 设置GitHub仓库
echo -e "${YELLOW}设置GitHub仓库...${NC}"
read -p "输入GitHub仓库URL (如: https://github.com/username/repo.git): " github_url

if [ -z "$github_url" ]; then
    echo -e "${RED}未提供GitHub仓库URL，跳过推送步骤${NC}"
else
    # 添加远程仓库
    if git remote | grep -q origin; then
        git remote set-url origin "$github_url"
    else
        git remote add origin "$github_url"
    fi
    
    # 推送到GitHub
    echo -e "${YELLOW}推送到GitHub...${NC}"
    git push -u origin main
    git push --tags
    
    echo -e "${GREEN}备份已成功推送到 $github_url${NC}"
fi

echo -e "${GREEN}备份完成!${NC}"
echo -e "备份标签: ${YELLOW}$BACKUP_TAG${NC}"
echo -e "提交信息: ${YELLOW}$BACKUP_MESSAGE${NC}"
echo -e "${YELLOW}如需回滚，使用命令: git checkout $BACKUP_TAG${NC}" 