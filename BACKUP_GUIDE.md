# 系统备份指南

## 备份概述

本系统使用Git进行版本控制和备份。每个备份都使用日期时间标记，格式为 `YYYYMMDD_HHMMSS`，便于轻松识别和恢复。

## 已创建的备份

以下是系统的备份历史：

- backup_20250503_234711 (分支)
- backup_20250503_234745 (标签)

## 如何创建新备份

要创建新的系统备份，只需运行以下命令：

```bash
./backup_system.sh
```

该脚本将：
1. 创建一个新的日期时间标记的分支
2. 添加所有文件更改
3. 提交更改
4. 推送分支到GitHub
5. 创建一个带有相同日期标记的标签
6. 将标签推送到GitHub

## 如何恢复备份

要恢复到特定备份，可以使用以下方法之一：

### 使用分支恢复

```bash
# 查看可用的备份分支
git branch -r | grep backup

# 恢复到特定分支
git checkout backup_YYYYMMDD_HHMMSS
```

### 使用标签恢复

```bash
# 查看可用的备份标签
git tag | grep backup

# 恢复到特定标签
git checkout backup_YYYYMMDD_HHMMSS
```

## 备份策略建议

1. 在进行重大更改前创建备份
2. 每周至少创建一次系统完整备份
3. 在解决复杂问题后创建备份
4. 在添加新模块或功能后创建备份

## 备份内容

备份包含系统的所有内容，包括：
- 源代码文件
- 配置文件
- 文档
- 测试文件和数据
- 依赖项列表
- 模型和缓存数据（如果未被忽略）

## Rollback Procedure

If you need to completely roll back to a previous version:

```bash
# First checkout the backup branch or tag
git checkout backup_YYYYMMDD_HHMMSS

# Create a new branch (optional)
git checkout -b rollback_YYYYMMDD

# Push the rollback branch to GitHub
git push origin rollback_YYYYMMDD

# If you want to make this the new main branch
# (CAUTION: this overwrites main)
git branch -D main
git checkout -b main
git push -f origin main
```

## Backup History

Each backup can be viewed on GitHub in the branches and tags sections. The date-based naming makes it easy to identify when each backup was created and track the evolution of the codebase over time. 