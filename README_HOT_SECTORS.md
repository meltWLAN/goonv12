# 优化版热门行业分析模块

本模块提供了基于Tushare API的热门行业分析功能，专注于申万行业分类和概念板块的分析，为交易者提供行业趋势、技术分析和交易信号。

## 主要特点

- **数据真实可靠**：直接使用Tushare API获取申万行业和概念板块真实数据
- **高效缓存机制**：内存和磁盘双层缓存，减少API调用，提高性能
- **多维度分析**：综合趋势评分、成交量评分、技术指标等多维度分析行业热度
- **专业交易信号**：提供具体买入/卖出信号、入场/出场价格区间和仓位建议
- **稳健的容错机制**：对于无法获取的数据采用备选方案和合理的模拟数据

## 模块组成

1. **TushareSectorProvider (tushare_sector_provider.py)**
   - 行业数据提供器，对接Tushare API获取数据
   - 支持申万行业和概念板块
   - 高效的缓存机制
   - 容错处理

2. **OptimizedSectorAnalyzer (optimized_sector_analyzer.py)**
   - 优化版行业分析器
   - 技术指标计算与评分
   - 交易信号生成
   - 热点行业识别与排序

3. **SectorIntegrator (optimized_sector_integration.py)**
   - 行业分析集成器
   - 与原系统兼容
   - 行业预测功能
   - 数据服务接口

4. **命令行工具 (hot_sector_cli.py)**
   - 便捷的命令行界面
   - 多种分析和查询功能
   - 数据导出和可视化

## 如何使用

### 前提条件

本模块依赖以下Python库：

```bash
pip install tushare pandas numpy talib tabulate
```

Tushare API需要Token，可在配置文件中设置或通过环境变量`TUSHARE_TOKEN`指定。

### 基本使用

1. **作为库使用**

```python
# 导入行业分析器
from optimized_sector_analyzer import get_hot_sectors

# 获取热门行业（默认返回前10个）
hot_sectors = get_hot_sectors(top_n=5)

# 使用集成器进行更高级的操作
from optimized_sector_integration import get_sector_integrator

integrator = get_sector_integrator()

# 获取热门行业
hot_result = integrator.get_hot_sectors()

# 行业预测
prediction = integrator.predict_hot_sectors()

# 获取特定行业数据
sector_data = integrator.get_sector_data("计算机")
```

2. **使用命令行工具**

```bash
# 列出所有可用行业
python hot_sector_cli.py list

# 查看热门行业排名（前10名）
python hot_sector_cli.py hot

# 查看热门行业详细分析
python hot_sector_cli.py hot --detail

# 分析特定行业
python hot_sector_cli.py analyze 计算机

# 保存行业数据
python hot_sector_cli.py analyze 计算机 --save

# 行业预测
python hot_sector_cli.py predict

# 导出数据
python hot_sector_cli.py export --name 计算机
python hot_sector_cli.py export --hot
python hot_sector_cli.py export --all
```

## 配置说明

主要配置通过参数传递，主要包括：

1. **TushareSectorProvider配置**
   - token: Tushare API Token
   - cache_dir: 缓存目录，默认为'data_cache/sectors'
   - cache_expiry: 缓存过期时间(秒)，默认1800秒

2. **OptimizedSectorAnalyzer配置**
   - top_n: 返回热门行业数量
   - data_days: 获取历史数据的天数

## 数据流向

数据流向如下：

1. TushareSectorProvider从Tushare API获取原始数据
2. OptimizedSectorAnalyzer处理数据并计算技术指标
3. SectorIntegrator集成结果并提供统一接口
4. 命令行工具或用户代码消费最终结果

## 技术指标说明

本模块使用以下技术指标：

- **RSI (相对强弱指标)**: 评估行业超买/超卖状态
- **MACD (移动平均线收敛发散)**: 分析趋势强度和方向
- **ADX (平均定向指数)**: 评估趋势强度
- **MA (移动平均线)**: 分析多头/空头排列和支撑/压力位
- **布林带**: 评估价格波动性和潜在突破

## 热度评分系统

热度评分由两部分组成：

1. **趋势得分 (60%权重)**
   - 均线关系 (25分)
   - MACD状态 (20分)
   - RSI指标 (15分)
   - ADX趋势强度 (15分)
   - 价格位置 (15分)
   - 短期动量 (10分)

2. **成交量得分 (40%权重)**
   - 成交量变化 (30分)
   - 成交量趋势 (20分)

## 容错机制

1. 当申万行业指数数据无法获取时：
   - 对于概念板块，尝试通过成分股合成指数
   - 当所有方法失败时，生成模拟数据

2. Tushare API访问失败时：
   - 首先尝试使用缓存数据
   - 缓存过期时生成模拟数据

## 适用场景

- 交易者识别热门行业和板块轮动
- 系统化分析行业趋势变化
- 行业趋势与个股选择结合
- 制定基于行业的交易计划

## 注意事项

- Tushare API有访问频率限制，请避免频繁调用
- 首次运行时需要缓存数据，可能较慢
- 通过`热门行业分析 > 行业趋势分析 > 个股选择`的层次分析思路效果最佳

## 后续计划

- 加入热点事件对行业影响的分析
- 优化资金流数据的整合
- 提供Web界面和可视化展示 