# 股票暴涨打榜系统

基于Tushare Pro接口的股票暴涨监控与分析系统，用于发现暴涨股票、分析暴涨模式并预测潜在的暴涨机会。

## 功能特点

- **今日暴涨股票查询**: 实时获取当日或指定日期涨幅超过阈值的股票
- **暴涨模式分析**: 分析历史时间段内的暴涨股票特征，包括行业分布、涨幅分布等
- **暴涨后续表现**: 统计分析暴涨股票在第二个交易日的表现
- **潜力股发掘**: 通过量价指标筛选可能在未来出现暴涨的潜力股票
- **价值股分析**: 基于市盈率、市净率、ROE和净利润增长率筛选价值投资标的
- **北向资金分析**: 监控沪深股通资金流入前N的股票
- **分钟线分析**: 分析个股分钟级别交易模式，包括量价特征
- **连续上涨股筛选**: 寻找最近一段时间内连续上涨的强势股
- **结果导出**: 支持将分析结果导出为CSV、Excel或HTML格式

## 系统要求

- Python 3.6+
- pandas
- numpy
- matplotlib
- tushare

## 安装方法

1. 克隆或下载本项目到本地
2. 安装依赖包：

```bash
pip install pandas numpy matplotlib tushare
```

3. 修改配置（可选）：编辑`config.py`文件，设置你的Tushare Token和其他参数

## 使用方法

### 查找今日暴涨股票

```bash
python main.py --mode today
```

### 查找指定日期的暴涨股票

```bash
python main.py --mode today --date 20231120
```

### 分析历史暴涨模式

```bash
python main.py --mode analyze --start 20230101 --end 20231231 --threshold 7 --plot
```

### 寻找潜在的暴涨股票

```bash
python main.py --mode potential
```

### 筛选优质价值股

```bash
python main.py --mode value --pe_max 15 --pb_max 1.5 --roe_min 12 --profit_yoy 10
```

### 分析北向资金流入股票

```bash
python main.py --mode hsgt --days 30 --top 20
```

### 分析个股分钟线交易模式

```bash
python main.py --mode minute --ts_code 000001.SZ --freq 5min --date 20231201
```

### 寻找连续上涨的强势股

```bash
python main.py --mode continuous --days 20 --min_rise_days 3
```

### 导出结果到文件

```bash
python main.py --mode today --output today_surge_stocks.csv
```

## 命令行参数说明

- `--mode`: 运行模式，可选值：today(今日暴涨), analyze(模式分析), potential(潜力股), value(价值股), hsgt(北向资金), minute(分钟分析), continuous(连续上涨股)
- `--date`: 指定查询日期，格式YYYYMMDD，默认为最近交易日
- `--start`: 分析开始日期，格式YYYYMMDD
- `--end`: 分析结束日期，格式YYYYMMDD
- `--threshold`: 涨幅阈值，默认为配置文件中的SURGE_THRESHOLD
- `--plot`: 是否绘制分析图表，仅在analyze模式有效
- `--top`: 显示前N个结果
- `--output`: 结果输出文件路径
- `--ts_code`: 股票代码，用于分钟线分析模式
- `--freq`: 分钟线频率，可选值：1min, 5min, 15min, 30min, 60min
- `--pe_max`: 价值股筛选的最大市盈率
- `--pb_max`: 价值股筛选的最大市净率
- `--roe_min`: 价值股筛选的最小净资产收益率(%)
- `--profit_yoy`: 价值股筛选的最小净利润同比增长率(%)
- `--days`: 分析最近的天数，用于hsgt和continuous模式
- `--min_rise_days`: 最少连续上涨天数，用于continuous模式

## 配置文件说明

系统配置存储在`config.py`文件中：

- `TUSHARE_TOKEN`: Tushare Pro的API令牌
- `DATA_PATH`: 数据存储路径
- `SURGE_THRESHOLD`: 涨幅阈值(%)，超过该值视为暴涨股票
- `STOCK_TYPE`: 监控的股票类型配置
- `DEFAULT_START_DATE`: 默认分析开始日期
- `DEFAULT_END_DATE`: 默认分析结束日期

## 示例输出

### 暴涨股票榜单

```
找到32只符合条件的股票，显示前20只：
================================================================================
      ts_code  trade_date     open     high      low    close  pre_close      change     pct_chg        vol       amount  name industry
0  688120.SH    20231120  114.9000  126.3900  114.9000  126.3900   114.9000  11.4900000  10.0000000   9577127  1148542.219  华海清科    专用设备
1  688256.SH    20231120   54.7200   60.1900   54.7200   60.1900    54.7200   5.4700000  10.0000000   6080088   350792.648  寒武纪    计算机
2  688142.SH    20231120  160.0000  176.0000  160.0000  176.0000   160.0000  16.0000000  10.0000000   3067901   513863.776  航宇科技    国防军工
3  688151.SH    20231120   38.6900   42.5600   38.4100   42.5600    38.6900   3.8700000  10.0000000  14484977   597399.109  同心医疗    医疗器械
4  688171.SH    20231120   59.3100   65.2400   59.3100   65.2400    59.3100   5.9300000  10.0000000   5486906   342257.752  纬德信息    通信设备
================================================================================
```

### 价值股筛选结果

```
找到25只符合条件的股票，显示前10只：
================================================================================
      ts_code     name    industry        pe       pb      roe  profit_yoy  total_mv
0   601988.SH   中国银行        银行    4.32    0.42    15.23       12.52    962.50
1   601398.SH   工商银行        银行    4.56    0.46    14.98       10.87   1623.75
2   601166.SH   兴业银行        银行    4.28    0.57    14.81       13.41    754.34
3   600188.SH   兖矿能源        煤炭    3.86    0.72    21.53       18.74    325.81
4   601288.SH   农业银行        银行    4.12    0.45    13.62        9.58   1087.66
================================================================================
```

### 北向资金分析结果

```
找到30只符合条件的股票，显示前10只：
================================================================================
      ts_code     name    industry  net_inflow  appear_days  positive_days  positive_ratio    price  pct_chg
0   600519.SH   贵州茅台      食品饮料    458732.64          20             15          75.0  1688.01     0.52
1   000858.SZ   五粮液        食品饮料    378512.33          20             14          70.0   158.65     0.83
2   601318.SH   中国平安        保险    352148.58          18             12          66.7    43.25     1.17
3   600036.SH   招商银行        银行    321547.92          18             13          72.2    35.80     0.39
4   601012.SH   隆基绿能    电力设备    278634.56          15             10          66.7    45.23     2.31
================================================================================
```

### 分钟线分析结果

```
分析000001.SZ的5min分钟交易数据...

分析结果：
ts_code: 000001.SZ
trade_date: 20231201
freq: 5min
data_points: 48
open: 11.52
close: 11.65
high: 11.70
low: 11.49
am_vol_ratio: 58.32
pm_vol_ratio: 41.68
total_vol: 253674152
max_vol_time: 2023-12-01 09:35:00
max_vol: 28432156
min_vol_time: 2023-12-01 11:25:00
min_vol: 1356284
daily_close: 11.65
daily_pct_chg: 1.13
```

### 连续上涨股筛选结果

```
找到15只符合条件的股票，显示前10只：
================================================================================
      ts_code     name    industry  rise_days  max_rise_pct  latest_price  latest_pct_chg
0   603290.SH   斯达半导    电子元件         5        12.53        142.65          2.15
1   300661.SZ   圣邦股份    电子元件         5        11.87        224.31          1.83
2   688981.SH   中芯国际    电子元件         4        10.36         64.28          1.52
3   603501.SH   韦尔股份    电子元件         4         9.23        108.42          2.31
4   002371.SZ   北方华创    专用设备         4         8.75        178.53          1.98
================================================================================
```

## 高级使用示例

### 1. 完整的价值股分析流程

首先筛选满足财务条件的价值股：

```bash
python main.py --mode value --pe_max 15 --pb_max 1.2 --roe_min 15 --profit_yoy 10 --output value_stocks.csv
```

然后分析这些价值股中，近期连续上涨的强势股：

```bash
python main.py --mode continuous --days 10 --min_rise_days 3 --output rising_value_stocks.csv
```

### 2. 北向资金加持的技术形态分析

先获取北向资金流入前20的股票：

```bash
python main.py --mode hsgt --days 30 --top 20 --output hsgt_top20.csv
```

对北向资金重点关注的个股进行分钟线分析：

```bash
python main.py --mode minute --ts_code 600519.SH --freq 15min
```

### 3. 暴涨股连续性分析

先找出今日暴涨股票：

```bash
python main.py --mode today --threshold 6 --output today_surge.csv
```

然后分析这些暴涨股的历史连续上涨情况：

```bash
python main.py --mode continuous --days 20 --min_rise_days 2 --output surge_continuity.csv
```

## 注意事项

- 使用前请确保已获取有效的Tushare Pro API Token
- 频繁查询可能触发Tushare的接口限制
- 历史数据分析可能需要较长时间，请耐心等待
- 本系统仅供参考，投资决策请自行判断

## 免责声明

本系统仅为个人学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。 