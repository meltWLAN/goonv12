# Enhanced Stock Analysis System

A comprehensive stock analysis toolkit for Chinese markets with TuShare API integration. This project provides various tools for technical analysis, visualization, and trading signals based on historical stock data.

## 使用入口

系统现在使用统一的入口点 `app.py`。请使用以下命令启动系统：

```bash
python app.py
```

这将启动完整的股票分析系统GUI界面。

## 主要功能更新

### 全面集成Tushare数据接口

系统现已完全集成Tushare全部数据接口，包括：

- **基础数据**：股票列表、交易日历、公司信息等
- **行情数据**：日线、周线、月线、分钟线、复权数据等
- **财务数据**：资产负债表、利润表、现金流量表、财务指标等
- **市场参考**：沪深股通、港股通、每日指标等

### 增强功能

- **多级缓存系统**：内存缓存和磁盘缓存，减少API调用次数
- **智能数据分析**：股票画像、行业分析、市场概览一应俱全
- **技术指标计算**：MA、MACD、RSI、KDJ、布林带等全自动计算
- **数据导出**：支持将数据导出为CSV文件供外部分析使用

## Features

- **Reliable Data Access**: Multi-source data retrieval with TuShare and AKShare integration
- **Technical Indicators**: MACD, RSI, KDJ, Bollinger Bands and more
- **Advanced Caching**: Memory and disk-based caching for improved performance
- **Beautiful Visualizations**: Candlestick charts with technical indicators
- **Trading Signals**: Automated analysis and trading recommendations
- **Comprehensive Reports**: Detailed technical analysis reports
- **Complete Tushare Integration**: Access to all Tushare data interfaces

## Getting Started

### Prerequisites

- Python 3.8+
- TuShare API token (register at https://tushare.pro/)
- Required Python packages (see below)

### Installation

1. Clone this repository
2. Install required packages:

```bash
pip install pandas numpy matplotlib mplfinance tushare akshare
```

3. Set your TuShare API token:

```bash
export TUSHARE_TOKEN=your_token_here
```

Or provide it directly when running the scripts.

## 新增组件

### TushareDataCenter

全面的Tushare数据中心，整合所有Tushare接口，提供统一的数据访问方式：

```python
from tushare_data_center import TushareDataCenter

# 初始化数据中心
data_center = TushareDataCenter(token='YOUR_TUSHARE_TOKEN')

# 获取股票列表
stock_list = data_center.get_stock_list()

# 获取日线数据
daily_data = data_center.get_daily_data('000001.SZ', start_date='20230101')

# 获取财务数据
income = data_center.get_income('000001.SZ')
```

### EnhancedDataProvider

增强版数据提供器，基于TushareDataCenter，提供更智能的数据获取和分析功能：

```python
from enhanced_data_provider import EnhancedDataProvider

# 初始化数据提供器
provider = EnhancedDataProvider(token='YOUR_TUSHARE_TOKEN')

# 获取带技术指标的股票数据
stock_data = provider.get_stock_data('000001.SZ', limit=30)

# 获取股票画像
profile = provider.get_stock_profile('000001.SZ')

# 获取行业表现
industry_perf = provider.get_industry_performance('银行', days=30)

# 获取市场概览
overview = provider.get_market_overview()
```

## 使用示例

### 测试数据集成

运行集成测试脚本来验证系统功能：

```bash
python tushare_integration.py --token YOUR_TUSHARE_TOKEN --ts_code 000001.SZ
```

导出数据到CSV文件：

```bash
python tushare_integration.py --token YOUR_TUSHARE_TOKEN --export --export_dir ./my_data
```

### Usage

#### Simple Stock Provider

For basic stock data retrieval:

```bash
python simple_stock_provider.py --token YOUR_TUSHARE_TOKEN --symbol 000001.SZ
```

#### Technical Analysis

For comprehensive technical analysis and reports:

```bash
python technical_analyzer.py --token YOUR_TUSHARE_TOKEN --symbol 600519.SH --days 90
```

#### Visualize Stock Data

For beautiful stock charts with technical indicators:

```bash
python visualize_stock_data.py --token YOUR_TUSHARE_TOKEN --ts_code 000001.SZ --days 60 --output chart.png
```

## Components

- **tushare_data_center.py**: Complete Tushare data interface integration
- **enhanced_data_provider.py**: Advanced data provider with analysis capabilities
- **tushare_integration.py**: Integration testing and data export utilities
- **simple_stock_provider.py**: Simple data provider with TuShare integration
- **technical_analyzer.py**: Comprehensive technical analysis tool
- **visualize_stock_data.py**: Stock data visualization with technical indicators
- **tushare_api_manager.py**: Enhanced TuShare API manager with caching and error handling

## Examples

### Generate Trading Signals

```python
from technical_analyzer import TechnicalAnalyzer

analyzer = TechnicalAnalyzer(token="YOUR_TUSHARE_TOKEN")
report = analyzer.generate_report("000001.SZ", days=60)
print(report)
```

### Visualize Multiple Stocks

```python
import os
from visualize_stock_data import main as visualize

os.environ["TUSHARE_TOKEN"] = "YOUR_TUSHARE_TOKEN"

# Visualize multiple stocks
symbols = ["000001.SZ", "600519.SH", "601318.SH"]
for symbol in symbols:
    visualize(["--ts_code", symbol, "--output", f"{symbol}_chart.png"])
```

### Stock Screening

```python
from enhanced_data_provider import EnhancedDataProvider

provider = EnhancedDataProvider(token="YOUR_TUSHARE_TOKEN")

# 筛选低PE高ROE的股票
criteria = {
    'min_pe': 5,
    'max_pe': 15,
    'min_roe': 15,
    'industry': '银行'
}
stocks = provider.screen_stocks(criteria)
print(stocks[['ts_code', 'name', 'pe', 'pb']])
```

## 增强型行业分析器 V2.0

最新版本的行业分析功能，提供更强大的行业热点分析和预测能力。

### 主要特性

- **多数据源集成**: 支持东方财富、新浪财经、腾讯财经等多数据源，并具备数据源失败自动切换能力
- **增强容错机制**: 使用指数退避策略进行API调用重试，提高数据获取稳定性
- **热度算法优化**: 集成多种技术指标计算和自适应权重模型，提升热点行业识别准确性
- **多线程并行处理**: 使用线程池技术并行获取数据，提高处理速度

### 使用示例

```python
from enhanced_sector_analyzer_v2 import EnhancedSectorAnalyzerV2

# 初始化分析器
analyzer = EnhancedSectorAnalyzerV2(
    top_n=10,                    # 返回前10个热门行业
    enable_multithreading=True,  # 启用多线程
    max_workers=5                # 最大线程数
)

# 获取热门行业
result = analyzer.analyze_hot_sectors()

# 显示结果
if result['status'] == 'success':
    hot_sectors = result['data']['hot_sectors']
    for sector in hot_sectors:
        print(f"{sector['name']} - 热度: {sector['hot_score']:.2f} - {sector['hot_level']}")
        print(f"  分析: {sector['analysis_reason']}")
```

查看更多详情，请参考 [V2_ENHANCEMENT_SUMMARY.md](V2_ENHANCEMENT_SUMMARY.md) 或运行 `demo_enhanced_sector_v2.py` 演示脚本。

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [TuShare](https://tushare.pro/) for providing financial data API
- [AKShare](https://github.com/akfamily/akshare) for alternative data sources
- [MPLFinance](https://github.com/matplotlib/mplfinance) for financial visualization
- [Pandas](https://pandas.pydata.org/) for data manipulation