#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试Tushare API获取行业数据的能力
"""

import tushare as ts
import pandas as pd
import time

# 设置token
TOKEN = "0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10"

def test_basic_connection():
    """测试基本连接"""
    print("=" * 50)
    print("测试Tushare基本连接")
    print("=" * 50)
    
    ts.set_token(TOKEN)
    pro = ts.pro_api()
    
    try:
        # 测试获取交易日历
        print("获取交易日历...")
        df = pro.trade_cal(exchange='SSE', start_date='20230101', end_date='20230110')
        if df is not None and not df.empty:
            print(f"成功获取交易日历，共{len(df)}条记录")
            print(df.head(3))
            return pro
        else:
            print("获取交易日历失败")
            return None
    except Exception as e:
        print(f"连接失败: {e}")
        return None

def test_sw_industry(pro):
    """测试获取申万行业分类"""
    print("\n" + "=" * 50)
    print("测试获取申万行业分类")
    print("=" * 50)
    
    try:
        print("获取申万行业分类...")
        df = pro.index_classify(level='L1', src='SW')
        if df is not None and not df.empty:
            print(f"成功获取申万行业分类，共{len(df)}条记录")
            print(df.head(5))
            return df
        else:
            print("获取申万行业分类失败")
            return None
    except Exception as e:
        print(f"获取申万行业分类失败: {e}")
        return None

def test_industry_index(pro, index_code):
    """测试获取行业指数数据"""
    print("\n" + "=" * 50)
    print(f"测试获取行业指数 {index_code} 数据")
    print("=" * 50)
    
    try:
        print(f"获取行业指数 {index_code} 的日线数据...")
        df = pro.index_daily(ts_code=index_code, start_date='20230101', end_date='20230110')
        if df is not None and not df.empty:
            print(f"成功获取行业指数数据，共{len(df)}条记录")
            print(df.head(3))
            return True
        else:
            print("获取行业指数数据失败")
            return False
    except Exception as e:
        print(f"获取行业指数数据失败: {e}")
        return False

def test_concept_list(pro):
    """测试获取概念板块列表"""
    print("\n" + "=" * 50)
    print("测试获取概念板块列表")
    print("=" * 50)
    
    try:
        print("获取概念板块列表...")
        df = pro.concept()
        if df is not None and not df.empty:
            print(f"成功获取概念板块列表，共{len(df)}条记录")
            print(df.head(5))
            return df
        else:
            print("获取概念板块列表失败")
            return None
    except Exception as e:
        print(f"获取概念板块列表失败: {e}")
        return None

def test_concept_stocks(pro, concept_code):
    """测试获取概念板块成分股"""
    print("\n" + "=" * 50)
    print(f"测试获取概念板块 {concept_code} 成分股")
    print("=" * 50)
    
    try:
        print(f"获取概念板块 {concept_code} 成分股...")
        # 概念板块代码可能需要去掉前缀
        code = concept_code
        if concept_code.startswith('TS'):
            code = concept_code[2:]
            
        df = pro.concept_detail(id=code)
        if df is not None and not df.empty:
            print(f"成功获取概念板块成分股，共{len(df)}条记录")
            print(df.head(5))
            return True
        else:
            print("获取概念板块成分股失败")
            return False
    except Exception as e:
        print(f"获取概念板块成分股失败: {e}")
        return False

def main():
    print(f"使用Token: {TOKEN[:4]}...{TOKEN[-4:]}")
    
    # 测试基本连接
    pro = test_basic_connection()
    if pro is None:
        print("基本连接测试失败，无法继续")
        return
    
    # 测试获取申万行业分类
    sw_industries = test_sw_industry(pro)
    
    # 测试获取行业指数数据
    if sw_industries is not None and not sw_industries.empty:
        # 选择第一个行业测试
        test_industry = sw_industries.iloc[0]
        index_code = test_industry['index_code']
        index_name = test_industry['industry_name']
        print(f"\n选择行业 {index_name} ({index_code}) 进行测试")
        test_industry_index(pro, index_code)
    
    # 测试获取概念板块列表
    concepts = test_concept_list(pro)
    
    # 测试获取概念板块成分股
    if concepts is not None and not concepts.empty:
        # 选择第一个概念测试
        test_concept = concepts.iloc[0]
        concept_code = test_concept['code']
        concept_name = test_concept['name']
        print(f"\n选择概念 {concept_name} ({concept_code}) 进行测试")
        test_concept_stocks(pro, concept_code)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main() 