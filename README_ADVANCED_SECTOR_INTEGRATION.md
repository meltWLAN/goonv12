# 高级行业分析模块使用指南

本文档介绍如何使用高级行业分析模块，该模块已集成到股票分析系统中。

## 安装与配置

已安装的高级行业分析模块包括以下核心文件：

1. `advanced_sector_analyzer.py` - 高级行业分析器核心实现
2. `advanced_sector_integration.py` - 与现有系统的集成接口
3. `setup_advanced_sector.py` - 安装与配置脚本

如果您需要重新安装或更新模块，可以运行：

```bash
python setup_advanced_sector.py
```

## 直接使用高级行业分析器

如果您想直接在代码中使用高级行业分析器，可以这样导入：

```python
from advanced_sector_analyzer import AdvancedSectorAnalyzer

# 创建分析器实例
analyzer = AdvancedSectorAnalyzer()

# 获取热门行业
result = analyzer.analyze_hot_sectors()
if result['status'] == 'success':
    hot_sectors = result['data']['hot_sectors']
    print("热门行业排名:")
    for i, sector in enumerate(hot_sectors, 1):
        print(f"{i}. {sector['name']} (热度: {sector['hot_score']:.2f})")
```

## 通过集成器使用

更推荐使用集成器，它提供了更好的兼容性和容错能力：

```python
from advanced_sector_integration import AdvancedSectorIntegrator

# 创建集成器实例
integrator = AdvancedSectorIntegrator()

# 获取热门行业
result = integrator.get_hot_sectors()
if result['status'] == 'success':
    hot_sectors = result['data']['hot_sectors']
    print("热门行业排名:")
    for i, sector in enumerate(hot_sectors, 1):
        print(f"{i}. {sector['name']} (热度: {sector['hot_score']:.2f})")
```

## 在GUI中使用

高级行业分析模块已集成到股票分析GUI中，您可以直接启动GUI查看：

```bash
python stock_analysis_gui.py
```

在GUI中，您将在选项卡中看到"热门行业"选项卡，点击后可以查看热门行业数据。

## 主要功能

高级行业分析模块提供以下主要功能：

1. **热门行业分析**: 根据多种因素识别热门行业
2. **行业历史数据查询**: 获取行业历史数据
3. **行业报告生成**: 生成全面的行业分析报告
4. **北向资金监控**: 监控北向资金流入行业情况

## 数据来源与质量

此模块优先使用真实数据，但在无法获取时会使用模拟数据（会有明确标记）：

- **数据质量标记**: 每个行业数据都有`is_real_data`标记，指示是否为真实数据
- **数据来源标记**: 结果中会标明数据来源（高级分析器/原始分析器）

## 常见问题解答

**Q: 为什么有些行业显示"使用模拟数据"？**  
A: 当无法从Tushare API获取真实数据时，系统会生成模拟数据以保证功能可用性。这通常是由于网络问题或API限制导致的。

**Q: 如何更新Tushare Token？**  
A: 运行`python setup_advanced_sector.py`，在配置过程中选择更新Token。

**Q: 如何测试模块功能？**  
A: 运行`python test_advanced_sector.py`，选择要测试的功能。

## 开发者信息

如需进一步开发或修改此模块，请参考源代码中的详细注释和文档字符串。核心实现位于`advanced_sector_analyzer.py`中，集成逻辑位于`advanced_sector_integration.py`中。 