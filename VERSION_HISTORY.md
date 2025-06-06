# 系统版本历史

本文档记录了系统的备份和版本历史，提供了恢复点和主要更新的概览。

## 最新版本

- **删除股票复盘模块** (2025年5月5日)
  - 主要内容: 删除旧的股票复盘模块，保留智能推荐系统
  - 修改功能: 移除股票复盘相关界面和功能，将其替换为智能推荐系统界面
  - 版本号: v1.4

- **集成智能推荐系统** (2025年5月4日)
  - 主要内容: 将备份分支中的智能推荐系统合并到主分支
  - 新增功能: 股票智能推荐系统UI、自动添加推荐股票到智能系统
  - 版本号: v1.3

- **backup_20250503_234745** (2025年5月3日 23:47:45)
  - 主要内容: 修复了自进化回测模块和智能推荐系统
  - 备份分支: `backup_20250503_234711`
  - 备份标签: `backup_20250503_234745`
  - 备份脚本: `backup_system.sh`

## 回滚指令

要回滚到特定版本，可以使用以下Git命令：

```bash
# 使用分支回滚
git checkout backup_20250503_234711

# 或使用标签回滚
git checkout backup_20250503_234745
```

## 完整版本历史

### 2025年5月

- **v1.4** (2025年5月5日)
  - 删除旧的股票复盘模块
  - 清理系统，移除不再需要的复盘相关文件
  - 确保智能推荐系统可以单独运行

- **v1.3** (2025年5月4日)
  - 将智能推荐系统从备份分支合并到主分支
  - 在主系统中集成了智能推荐功能
  - 实现了市场强推荐股票自动添加到智能推荐系统功能

- **backup_20250503_234745** (2025年5月3日)
  - 修复了自进化回测模块的MACD金叉策略
  - 实现了智能股票推荐系统
  - 解决了UI组件中的递归错误
  - 添加了将市场强推荐股票自动添加到智能推荐系统的功能

## 恢复指南

详细的备份和恢复指南请参见 [BACKUP_GUIDE.md](BACKUP_GUIDE.md) 文件。 