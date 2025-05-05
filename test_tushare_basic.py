#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Tushare API基本连接
"""

import tushare as ts
import time
import pandas as pd

# 测试Tushare连接
print(f"Tushare版本: {ts.__version__}")

# 设置token
token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
ts.set_token(token)
pro = ts.pro_api()
print("成功设置Tushare token")

# 测试1：获取交易日历
print("\n测试1: 获取交易日历")
try:
    start_time = time.time()
    trade_cal = pro.trade_cal(exchange='SSE', start_date='20230101', end_date='20230110')
    end_time = time.time()
    
    if trade_cal is None or trade_cal.empty:
        print("❌ 获取交易日历失败: 返回空数据")
    else:
        print(f"✅ 成功获取交易日历数据，共 {len(trade_cal)} 条记录")
        print(f"请求耗时: {end_time - start_time:.2f} 秒")
        print(trade_cal.head())
except Exception as e:
    print(f"❌ 获取交易日历失败: {str(e)}")

# 测试2：获取股票列表
print("\n测试2: 获取股票列表")
try:
    start_time = time.time()
    stock_list = pro.stock_basic(exchange='', list_status='L')
    end_time = time.time()
    
    if stock_list is None or stock_list.empty:
        print("❌ 获取股票列表失败: 返回空数据")
    else:
        print(f"✅ 成功获取股票列表，共 {len(stock_list)} 只股票")
        print(f"请求耗时: {end_time - start_time:.2f} 秒")
        print(stock_list.head())
except Exception as e:
    print(f"❌ 获取股票列表失败: {str(e)}")

# 测试3：获取单只股票历史数据
print("\n测试3: 获取单只股票历史数据")
try:
    # 尝试获取贵州茅台数据
    stock_code = '600519.SH'
    start_time = time.time()
    stock_data = pro.daily(ts_code=stock_code, start_date='20230101', end_date='20230131')
    end_time = time.time()
    
    if stock_data is None or stock_data.empty:
        print(f"❌ 获取{stock_code}历史数据失败: 返回空数据")
    else:
        print(f"✅ 成功获取{stock_code}历史数据，共 {len(stock_data)} 条记录")
        print(f"请求耗时: {end_time - start_time:.2f} 秒")
        print(stock_data.head())
except Exception as e:
    print(f"❌ 获取{stock_code}历史数据失败: {str(e)}")

# 测试4：获取指数数据
print("\n测试4: 获取指数数据")
try:
    # 尝试获取上证指数
    index_code = '000001.SH'
    start_time = time.time()
    index_data = pro.index_daily(ts_code=index_code, start_date='20230101', end_date='20230131')
    end_time = time.time()
    
    if index_data is None or index_data.empty:
        print(f"❌ 获取{index_code}指数数据失败: 返回空数据")
    else:
        print(f"✅ 成功获取{index_code}指数数据，共 {len(index_data)} 条记录")
        print(f"请求耗时: {end_time - start_time:.2f} 秒")
        print(index_data.head())
except Exception as e:
    print(f"❌ 获取{index_code}指数数据失败: {str(e)}")

# 打印token使用情况
print("\n查询剩余积分:")
try:
    start_time = time.time()
    # 使用动态获取可以查询的积分情况API
    user_info = pro.query('tmt_tus', fields='', cb='')
    end_time = time.time()
    
    print(f"请求耗时: {end_time - start_time:.2f} 秒")
    print("账户信息:", user_info)
except Exception as e:
    print(f"❌ 查询账户信息失败: {str(e)}")

print("\n总结:")
print("如果以上测试都成功，则Tushare API配置正确并且能够正常使用")
print("如果出现错误，请检查token是否有效，网络连接是否正常，以及是否超出API调用限制") 