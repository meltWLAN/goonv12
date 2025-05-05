#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化测试: 专注于测试Tushare API获取行业数据的功能
"""

import tushare as ts
import pandas as pd
import time
from datetime import datetime, timedelta

def test_tushare_sector_data():
    """测试Tushare获取行业数据的关键功能"""
    
    # 设置token
    token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    ts.set_token(token)
    pro = ts.pro_api()
    print(f"成功设置Tushare token: {token[:4]}{'*' * (len(token) - 8)}{token[-4:]}")
    
    # 测试1: 获取申万行业分类
    print("\n测试1: 获取申万行业分类")
    try:
        start_time = time.time()
        industry_list = pro.index_classify(level='L1', src='SW')
        end_time = time.time()
        
        if industry_list is not None and not industry_list.empty:
            print(f"✅ 成功获取申万行业列表，共 {len(industry_list)} 个行业")
            print(f"请求耗时: {end_time - start_time:.2f} 秒")
            print("\n行业列表前5项:")
            print(industry_list.head())
            
            # 打印所有列名
            print("\n数据包含以下列:")
            for col in industry_list.columns:
                print(f"- {col}")
        else:
            print("❌ 获取申万行业列表失败: 返回空数据")
    except Exception as e:
        print(f"❌ 获取申万行业列表失败: {str(e)}")
    
    # 测试2: 获取行业历史数据
    print("\n测试2: 获取行业历史数据")
    try:
        # 如果前面获取行业列表成功，使用第一个行业的代码
        if 'industry_list' in locals() and not industry_list.empty:
            test_industry = industry_list.iloc[0]
            industry_code = test_industry['index_code']
            industry_name = test_industry['industry_name']
        else:
            # 否则使用默认的行业指数代码（申万银行指数）
            industry_code = '801780.SI'
            industry_name = '银行'
            
        print(f"正在获取行业 '{industry_name}' (代码: {industry_code}) 的历史数据...")
        
        # 设置日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        start_time = time.time()
        industry_data = pro.index_daily(ts_code=industry_code, start_date=start_date, end_date=end_date)
        end_time = time.time()
        
        if industry_data is not None and not industry_data.empty:
            print(f"✅ 成功获取行业历史数据，共 {len(industry_data)} 条记录")
            print(f"请求耗时: {end_time - start_time:.2f} 秒")
            print("\n历史数据前5项:")
            print(industry_data.head())
            
            # 打印所有列名
            print("\n数据包含以下列:")
            for col in industry_data.columns:
                print(f"- {col}")
        else:
            print("❌ 获取行业历史数据失败: 返回空数据")
    except Exception as e:
        print(f"❌ 获取行业历史数据失败: {str(e)}")
    
    # 测试3: 获取行业成分股
    print("\n测试3: 获取行业成分股")
    try:
        if 'industry_code' in locals():
            print(f"正在获取行业 '{industry_name}' 的成分股列表...")
            
            start_time = time.time()
            stocks = pro.index_member(index_code=industry_code)
            end_time = time.time()
            
            if stocks is not None and not stocks.empty:
                print(f"✅ 成功获取行业成分股，共 {len(stocks)} 只股票")
                print(f"请求耗时: {end_time - start_time:.2f} 秒")
                print("\n成分股前5项:")
                print(stocks.head())
                
                # 打印所有列名
                print("\n数据包含以下列:")
                for col in stocks.columns:
                    print(f"- {col}")
            else:
                print("❌ 获取行业成分股失败: 返回空数据")
        else:
            print("❌ 无法获取行业成分股，因为没有有效的行业代码")
    except Exception as e:
        print(f"❌ 获取行业成分股失败: {str(e)}")
    
    # 测试4: 获取概念板块列表
    print("\n测试4: 获取概念板块列表")
    try:
        start_time = time.time()
        concept_list = pro.concept()
        end_time = time.time()
        
        if concept_list is not None and not concept_list.empty:
            print(f"✅ 成功获取概念板块列表，共 {len(concept_list)} 个概念")
            print(f"请求耗时: {end_time - start_time:.2f} 秒")
            print("\n概念板块前5项:")
            print(concept_list.head())
            
            # 打印所有列名
            print("\n数据包含以下列:")
            for col in concept_list.columns:
                print(f"- {col}")
        else:
            print("❌ 获取概念板块列表失败: 返回空数据")
    except Exception as e:
        print(f"❌ 获取概念板块列表失败: {str(e)}")
    
    print("\n总结:")
    print("如果以上测试都成功，则Tushare API可以正常用于获取行业数据")
    print("请检查返回的数据结构，以便在SectorAnalyzer类中正确使用")

if __name__ == "__main__":
    print("====== 测试Tushare获取行业数据 ======\n")
    test_tushare_sector_data()
    print("\n====== 测试完成 ======") 