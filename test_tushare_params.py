#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Tushare行业数据接口参数
系统性测试不同参数组合，找出可用的参数配置
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time

# 设置token
TOKEN = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'

def test_api_call(api_func, title, **params):
    """测试API调用并打印结果"""
    print(f"\n----- 测试: {title} -----")
    print(f"参数: {params}")
    
    try:
        result = api_func(**params)
        if result is not None and not result.empty:
            print(f"✓ 成功 | 获取到 {len(result)} 条记录")
            print("数据样例:")
            print(result.head(3).to_string())
            return True, result
        else:
            print("✗ 失败 | 返回空数据")
            return False, None
    except Exception as e:
        print(f"✗ 错误 | {str(e)}")
        return False, None

# 初始化API
print(f"使用Token: {TOKEN[:4]}...{TOKEN[-4:]}")
ts.set_token(TOKEN)
pro = ts.pro_api()

# 获取当前日期和过去日期
today = datetime.now().strftime('%Y%m%d')
last_month = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

# 测试1: 申万行业分类接口不同参数组合
print("\n===== 1. 测试申万行业分类接口 (index_classify) =====")
test_api_call(pro.index_classify, "申万一级行业", level='L1', src='SW')
test_api_call(pro.index_classify, "申万二级行业", level='L2', src='SW')
test_api_call(pro.index_classify, "不指定级别", src='SW')
test_api_call(pro.index_classify, "不指定来源", level='L1')
test_api_call(pro.index_classify, "无参数")

# 测试2: 概念板块接口
print("\n===== 2. 测试概念板块接口 (concept) =====")
success, concept_data = test_api_call(pro.concept, "概念板块 - 无参数")
concept_code = None
if success and concept_data is not None and not concept_data.empty:
    concept_code = concept_data.iloc[0]['code']
    print(f"提取概念代码: {concept_code} 用于后续测试")

# 测试3: 指数日线行情
print("\n===== 3. 测试指数日线行情 (index_daily) =====")
index_codes = ['000001.SH', '399001.SZ', '801010.SI', '801020.SI']
for index_code in index_codes:
    test_api_call(pro.index_daily, f"指数日线 {index_code}", 
                ts_code=index_code, start_date=last_month, end_date=today)
    time.sleep(0.5)  # 避免频繁请求

# 测试4: 概念板块成分
print("\n===== 4. 测试概念板块成分 (concept_detail) =====")
if concept_code:
    test_api_call(pro.concept_detail, f"概念板块成分 {concept_code}", concept_id=concept_code)
test_api_call(pro.concept_detail, "概念板块成分 TS1", concept_id='TS1')

# 测试5: 北向资金
print("\n===== 5. 测试北向资金 (moneyflow_hsgt) =====")
dates_to_try = [
    today,
    (datetime.now() - timedelta(days=1)).strftime('%Y%m%d'),
    (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
]
for date in dates_to_try:
    test_api_call(pro.moneyflow_hsgt, f"北向资金 {date}", trade_date=date)
    time.sleep(0.5)  # 避免频繁请求

# 测试6: 申万行业成分股
print("\n===== 6. 测试申万行业成分股 (index_member) =====")
industry_codes = ['801010.SI', '801020.SI', '801780.SI']
for code in industry_codes:
    test_api_call(pro.index_member, f"行业成分股 {code}", index_code=code)
    time.sleep(0.5)  # 避免频繁请求

print("\n测试完成！") 