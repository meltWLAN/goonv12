# 增强版行业分析器

## 简介
增强版行业分析器是一个强大的工具，它提供全面的行业分析功能，专为交易决策而设计。相比简化版分析器，增强版提供了更多的功能和更深入的分析。

## 主要功能

### 1. 热门行业分析
* 对各行业进行热度评分
* 提供详细的行业趋势分析
* 显示行业当前状态（上升期、震荡期、下降期等）
* 提供交易信号和建议

### 2. 行业技术分析
* 全面的技术指标分析（MACD、KDJ、RSI、均线、布林带等）
* 趋势强度评估
* 支撑位和阻力位分析
* 综合技术评分（0-100分）
* 详细的交易建议

### 3. 行业成分股分析
* 提供行业成分股列表
* 支持成分股筛选和排序
* 显示股票基本信息和入选日期

### 4. 投资报告生成
* 生成专业的行业投资分析报告
* 包含市场概况和热门行业分析
* 提供具体的投资建议和风险提示
* 详细的行业评级（★-★★★★★）

## 使用方法

### 基本使用
```python
# 导入增强版行业分析器集成模块
from integrate_sector_analyzer import SectorAnalyzerIntegrator

# 创建集成器（默认优先使用增强版）
integrator = SectorAnalyzerIntegrator(prefer_enhanced=True)

# 获取热门行业
hot_sectors = integrator.get_hot_sectors()
if hot_sectors['status'] == 'success':
    sectors = hot_sectors['data']['hot_sectors']
    for sector in sectors:
        print(f"{sector['name']} - 热度: {sector['hot_score']}, 信号: {sector['trade_signal']}")
        
# 获取某个行业的技术分析
tech_analysis = integrator.get_sector_technical_analysis("电子")
if tech_analysis['status'] == 'success':
    data = tech_analysis['data']
    print(f"技术评分: {data['tech_score']}")
    print(f"趋势: {data['trend_analysis']['trend']}")
    print(f"交易信号: {data['trade_signal']['signal']}")
    
# 生成投资报告
report = integrator.generate_investment_report()
if report['status'] == 'success':
    recommendations = report['data']['recommendations']
    for rec in recommendations:
        print(f"{rec['rating']} {rec['sector']}: {rec['investment_advice']}")
```

### 直接使用增强版分析器
```python
from enhanced_sector_analyzer import EnhancedSectorAnalyzer
from sector_technical_analysis import SectorTechnicalAnalyzer

# 创建分析器
analyzer = EnhancedSectorAnalyzer()
tech_analyzer = SectorTechnicalAnalyzer()

# 获取热门行业
hot_sectors = analyzer.get_hot_sectors(top_n=20)

# 获取行业成分股
stocks = analyzer.get_sector_stocks("电子")

# 获取行业技术分析
tech_analysis = tech_analyzer.analyze_sector("801080.SI", "电子")
```

## 输出示例

### 热门行业分析
```json
{
  "status": "success",
  "data": {
    "hot_sectors": [
      {
        "name": "电子",
        "code": "801080.SI",
        "hot_score": 85.7,
        "hot_level": "极热",
        "trade_signal": "强势买入",
        "industry_status": "快速上涨期",
        "change_pct": 2.8,
        "analysis": "电子行业极度活跃，资金流入强劲，短期有望持续上涨"
      },
      ...
    ],
    "market_trend": "bull",
    "market_chg_pct": 0.8,
    "update_time": "2025-05-02 14:31:03",
    "source": "enhanced"
  }
}
```

### 技术分析
```json
{
  "status": "success",
  "data": {
    "sector": "电子",
    "code": "801080.SI",
    "tech_score": 78,
    "trend_analysis": {
      "trend": "上升",
      "strength": 8.2,
      "support": 3250.5,
      "resistance": 3450.8,
      "analysis": "电子行业处于上升趋势，支撑位于3250.5，阻力位于3450.8"
    },
    "indicators": {
      "macd": {"signal": "买入"},
      "kdj": {"signal": "买入"},
      "rsi": {"signal": "偏多"},
      "ma": {"signal": "多头排列"},
      "boll": {"signal": "上轨压力"}
    },
    "trade_signal": {
      "signal": "买入",
      "description": "技术指标偏多，可以考虑买入",
      "action": "关注电子行业绩优股"
    }
  }
}
```

## 与简化版的区别
增强版行业分析器在以下方面优于简化版：

1. **更全面的数据分析**：使用多种数据源，提供更准确的行业热度评估
2. **高级技术分析**：提供全面的技术指标和详细的技术图表分析
3. **交易指导**：给出明确的交易信号和行动建议
4. **投资报告**：可生成专业的行业投资分析报告
5. **行业成分股**：提供行业成分股详细信息，帮助选股

## 注意事项
* 增强版分析器要求以下额外依赖：pandas, numpy, matplotlib, tushare
* 如果增强版分析器不可用，系统会自动降级到简化版
* 技术分析结果仅供参考，实际交易请结合市场情况和个人风险偏好 