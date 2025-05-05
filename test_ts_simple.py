#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tushare as ts
import sys

print("Python version:", sys.version)
print("Tushare version:", ts.__version__)

# 设置token
token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
print(f"Using token: {token[:4]}...{token[-4:]}")

# 初始化API
ts.set_token(token)
pro = ts.pro_api()

# 测试API连接 - 获取交易日历
print("\nGetting trade calendar...")
try:
    cal = pro.trade_cal(exchange='SSE', start_date='20250401', end_date='20250430')
    print("Success! Found", len(cal), "calendar entries")
    print(cal.head(3))
except Exception as e:
    print("Error getting trade calendar:", e)

# 测试获取股票列表
print("\nGetting stock list...")
try:
    stocks = pro.stock_basic(exchange='', list_status='L')
    print("Success! Found", len(stocks), "stocks")
    print(stocks.head(3))
except Exception as e:
    print("Error getting stock list:", e)

print("\nTest completed.") 