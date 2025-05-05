# 行业分析模块 (SectorAnalyzer) 文档

## 概述

行业分析模块 (SectorAnalyzer) 是一个用于分析股票市场行业板块热度和趋势的组件。该模块使用 Tushare API 作为数据源，获取行业板块的实时和历史数据，进行技术分析和趋势预测。

## 数据源

该模块目前使用 Tushare API 作为唯一的数据源。原先的 AKShare 依赖已完全移除。

### Tushare API 和 Token

Tushare API 需要有效的 token 才能访问数据。当前使用的默认 token 是:

```
0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10
```

您可以通过以下方式设置自己的 token:

1. 环境变量: `TUSHARE_TOKEN`
2. 配置文件: 在 `config/api_keys.txt` 添加 `TUSHARE_TOKEN=your_token`

### Tushare API 访问级别

Tushare API 有不同的访问级别和数据权限。根据您的 token 权限，某些 API 功能可能不可用。当前模块使用的主要 API 功能:

| API 功能 | 说明 | 权限要求 |
|---------|------|---------|
| trade_cal | 交易日历 | 基础权限 |
| index_classify | 行业分类 | 高级权限 |
| index_daily | 行业指数日线 | 高级权限 |
| index_member | 行业成分股 | 高级权限 |
| concept | 概念板块列表 | 基础权限 |
| concept_detail | 概念板块成分股 | 基础权限 |
| daily | 股票日线 | 基础权限 |
| moneyflow_hsgt | 北向资金流入 | 高级权限 |

## 主要功能

SectorAnalyzer 提供以下主要功能:

1. `get_sector_list()`: 获取所有行业板块列表
2. `analyze_hot_sectors()`: 分析当前热门行业
3. `predict_next_hot_sectors()`: 预测未来可能的热门行业
4. `generate_sector_report()`: 生成行业分析报告

## 数据获取流程

为确保数据可靠性，该模块采用多级数据获取机制:

1. **缓存层**: 首先检查内存缓存和磁盘缓存
2. **主数据源**: 使用 Tushare API 尝试直接获取行业数据
3. **备用方案**: 如果无法直接获取行业数据，则通过行业成分股数据计算
4. **备份数据**: 如果无法获取实时数据，使用之前保存的备份数据
5. **模拟数据**: 当所有数据源都失败时，生成模拟数据（标记为模拟，仅供参考）

## 模拟数据机制

当无法获取任何真实数据时，模块会生成模拟数据保持系统运行。需要注意:

- 模拟数据会被明确标记 (`是模拟数据=True`)
- 基于模拟数据的分析结果会有降低的权重
- 系统会发出明确警告
- 建议在网络连接恢复后重新运行分析

## 使用示例

```python
from sector_analyzer import SectorAnalyzer

# 创建分析器实例
analyzer = SectorAnalyzer(top_n=10)

# 获取行业列表
sectors = analyzer.get_sector_list()
print(f"共获取到 {len(sectors)} 个行业板块")

# 分析热门行业
hot_sectors = analyzer.analyze_hot_sectors()
if hot_sectors['status'] == 'success':
    for sector in hot_sectors['data']['hot_sectors']:
        print(f"{sector['name']}: 热度得分 {sector['hot_score']:.2f}")
        print(f"  分析: {sector['analysis_reason']}")
```

## 测试脚本

该模块提供多个测试脚本:

- `test_ts_simple.py`: 简单 Tushare API 连接测试
- `test_tushare_basic.py`: 基本 Tushare API 功能测试
- `test_tushare_sector_data.py`: 行业数据特定 API 测试
- `test_sector_analyzer_tushare.py`: SectorAnalyzer 类集成测试

## 故障排除

如果遇到"返回空数据"错误，可能是由于以下原因:

1. Token 权限不足，无法访问某些 API
2. 网络连接问题
3. Tushare API 限流或服务问题

解决方案:

- 检查 Token 权限级别
- 确认网络连接
- 添加适当的请求延迟避免限流
- 使用更高级别的 Token