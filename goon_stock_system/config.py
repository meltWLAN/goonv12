#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tushare Pro API配置
TUSHARE_TOKEN = "0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10"

# 数据存储路径
DATA_PATH = "./data"

# 打榜系统配置
# 涨幅阈值(%)，超过该值视为暴涨股票
SURGE_THRESHOLD = 5.0  

# 监控的股票类型
STOCK_TYPE = {
    "A股": True,
    "科创板": True,
    "创业板": True,
    "北交所": True
}

# 回测时间范围(默认值)
DEFAULT_START_DATE = "20230101"
DEFAULT_END_DATE = "20231231" 