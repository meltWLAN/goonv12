#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Tushare获取行业数据
检查是否能正确获取申万一级行业、概念板块和行业指数数据
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# 设置token - 使用系统中已有的token
token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'

def test_tushare_sector_data():
    """测试Tushare获取行业数据"""
    print("\n===== 测试Tushare行业数据获取 =====\n")
    
    # 初始化Tushare API
    print(f"使用Token: {token[:4]}...{token[-4:]}")
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 测试1: 获取申万行业分类
    print("\n1. 尝试获取申万行业分类数据...")
    try:
        sw_sectors = pro.index_classify(level='L1', src='SW')
        if sw_sectors is not None and not sw_sectors.empty:
            print(f"✓ 成功获取申万一级行业分类，共 {len(sw_sectors)} 个行业")
            print("前5个行业样例:")
            print(sw_sectors.head(5).to_string())
        else:
            print("✗ 无法获取申万行业分类数据")
    except Exception as e:
        print(f"✗ 获取申万行业分类失败: {str(e)}")
    
    # 测试2: 获取概念板块数据
    print("\n2. 尝试获取概念板块数据...")
    try:
        concept_sectors = pro.concept()
        if concept_sectors is not None and not concept_sectors.empty:
            print(f"✓ 成功获取概念板块，共 {len(concept_sectors)} 个概念")
            print("前5个概念板块样例:")
            print(concept_sectors.head(5).to_string())
        else:
            print("✗ 无法获取概念板块数据")
    except Exception as e:
        print(f"✗ 获取概念板块失败: {str(e)}")
    
    # 测试3: 获取行业指数行情数据
    print("\n3. 尝试获取行业指数行情数据...")
    try:
        # 从申万行业中获取一个指数代码
        index_code = None
        if 'sw_sectors' in locals() and sw_sectors is not None and not sw_sectors.empty:
            index_code = sw_sectors.iloc[0]['index_code']
        
        # 如果没有申万行业数据，尝试使用硬编码的指数代码
        if index_code is None:
            index_code = '801010.SI'  # 申万农林牧渔指数代码
            
        # 获取日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        print(f"获取指数 {index_code} 的行情数据，日期范围: {start_date} 至 {end_date}")
        index_data = pro.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
        
        if index_data is not None and not index_data.empty:
            print(f"✓ 成功获取行业指数数据，共 {len(index_data)} 条记录")
            print("最近5条记录样例:")
            print(index_data.head(5).to_string())
        else:
            print("✗ 无法获取行业指数数据")
            
        # 尝试获取上证指数数据作为对照
        print("\n尝试获取上证指数数据作为对照...")
        sh_index = pro.index_daily(ts_code='000001.SH', start_date=start_date, end_date=end_date)
        if sh_index is not None and not sh_index.empty:
            print(f"✓ 成功获取上证指数数据，共 {len(sh_index)} 条记录")
            print("最近5条记录样例:")
            print(sh_index.head(5).to_string())
        else:
            print("✗ 无法获取上证指数数据")
            
    except Exception as e:
        print(f"✗ 获取行业指数数据失败: {str(e)}")
    
    # 测试4: 获取概念板块成分股
    print("\n4. 尝试获取概念板块成分股...")
    try:
        concept_id = None
        if 'concept_sectors' in locals() and concept_sectors is not None and not concept_sectors.empty:
            concept_id = concept_sectors.iloc[0]['code']
            
        if concept_id is not None:
            print(f"获取概念板块 {concept_id} 的成分股")
            concept_stocks = pro.concept_detail(concept_id=concept_id)
            if concept_stocks is not None and not concept_stocks.empty:
                print(f"✓ 成功获取概念板块成分股，共 {len(concept_stocks)} 个股票")
                print("前5个成分股样例:")
                print(concept_stocks.head(5).to_string())
            else:
                print("✗ 无法获取概念板块成分股")
        else:
            print("✗ 无法获取概念ID，跳过成分股测试")
    except Exception as e:
        print(f"✗ 获取概念板块成分股失败: {str(e)}")
    
    # 测试5: 获取北向资金数据
    print("\n5. 尝试获取北向资金数据...")
    try:
        today = datetime.now().strftime('%Y%m%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        for date in [today, yesterday]:
            print(f"尝试获取 {date} 的北向资金数据")
            north_data = pro.moneyflow_hsgt(trade_date=date)
            if north_data is not None and not north_data.empty:
                print(f"✓ 成功获取 {date} 的北向资金数据")
                print(north_data.to_string())
                
                # 计算北向资金
                north_money = north_data['north_money'].sum() / 100000000  # 转换为亿元
                print(f"北向资金净流入: {north_money:.2f}亿元")
                break
            else:
                print(f"✗ 无法获取 {date} 的北向资金数据，尝试前一天")
    except Exception as e:
        print(f"✗ 获取北向资金数据失败: {str(e)}")
    
    print("\n===== 测试完成 =====")
    print("如果某些测试未能成功，可能是由于以下原因:")
    print("1. API权限不足 - 需要升级Tushare账户或使用高级数据包")
    print("2. API调用次数限制 - 免费账户每分钟限制访问")
    print("3. Token无效或过期")
    print("4. 网络连接问题")
    print("5. 数据源暂时不可用")
    print("\n对于无法获取的数据，可以使用缓存机制和备用数据源解决问题")

if __name__ == "__main__":
    test_tushare_sector_data() 