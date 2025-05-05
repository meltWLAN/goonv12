#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试使用AKShare获取行业数据的能力
"""

import pandas as pd
import time
import sys

try:
    import akshare as ak
    print("AKShare版本:", ak.__version__)
except ImportError:
    print("AKShare库未安装，正在安装...")
    import os
    os.system("pip install akshare -U")
    print("安装完成，请重新运行本脚本")
    sys.exit(1)

def test_stock_sector_industry():
    """测试获取行业板块数据"""
    print("\n" + "=" * 50)
    print("测试获取行业板块数据")
    print("=" * 50)
    
    try:
        print("获取申万一级行业列表...")
        start_time = time.time()
        # 使用正确的函数名获取申万行业
        sw_index = ak.sw_index_first_info()
        end_time = time.time()
        
        if sw_index is not None and not sw_index.empty:
            print(f"成功获取申万一级行业，共{len(sw_index)}条记录，耗时：{end_time-start_time:.2f}秒")
            print(sw_index.head(5))
            return sw_index
        else:
            print("获取申万一级行业失败")
            return None
    except Exception as e:
        print(f"获取行业板块数据出错: {e}")
        
        # 尝试其他行业分类方法
        try:
            print("\n尝试获取申万行业分类...")
            industry_list = ak.stock_sector_spot(indicator="申万一级")
            if industry_list is not None and not industry_list.empty:
                print(f"成功获取申万行业分类，共{len(industry_list)}条记录")
                print(industry_list.head(5))
                return industry_list
            else:
                print("获取申万行业分类失败")
        except Exception as e2:
            print(f"获取申万行业分类出错: {e2}")
        
        return None

def test_industry_index_hist(industry_code):
    """测试获取行业指数历史数据"""
    print("\n" + "=" * 50)
    print(f"测试获取行业指数 {industry_code} 历史数据")
    print("=" * 50)
    
    try:
        print(f"尝试获取申万行业 {industry_code} 历史行情...")
        start_time = time.time()
        sw_hist = ak.sw_index_daily_indicator(symbol=industry_code)
        end_time = time.time()
        
        if sw_hist is not None and not sw_hist.empty:
            print(f"成功获取申万行业历史数据，共{len(sw_hist)}条记录，耗时：{end_time-start_time:.2f}秒")
            print(sw_hist.head(5))
            return sw_hist
        else:
            print("获取申万行业历史数据失败")
            return None
    except Exception as e:
        print(f"获取行业指数历史数据出错: {e}")
        return None

def test_concept_board():
    """测试获取概念板块数据"""
    print("\n" + "=" * 50)
    print("测试获取概念板块数据")
    print("=" * 50)
    
    try:
        print("获取概念板块列表...")
        start_time = time.time()
        concept_list = ak.stock_board_concept_name_em()
        end_time = time.time()
        
        if concept_list is not None and not concept_list.empty:
            print(f"成功获取概念板块列表，共{len(concept_list)}条记录，耗时：{end_time-start_time:.2f}秒")
            print(concept_list.head(5))
            return concept_list
        else:
            print("获取概念板块列表失败")
            return None
    except Exception as e:
        print(f"获取概念板块数据出错: {e}")
        return None

def test_concept_board_detail(concept_name):
    """测试获取概念板块成分股"""
    print("\n" + "=" * 50)
    print(f"测试获取概念板块 {concept_name} 成分股")
    print("=" * 50)
    
    try:
        print(f"获取概念板块 {concept_name} 成分股...")
        start_time = time.time()
        stocks = ak.stock_board_concept_cons_em(symbol=concept_name)
        end_time = time.time()
        
        if stocks is not None and not stocks.empty:
            print(f"成功获取概念板块成分股，共{len(stocks)}条记录，耗时：{end_time-start_time:.2f}秒")
            print(stocks.head(5))
            return stocks
        else:
            print("获取概念板块成分股失败")
            return None
    except Exception as e:
        print(f"获取概念板块成分股出错: {e}")
        return None

def test_concept_board_hist(concept_name):
    """测试获取概念板块历史数据"""
    print("\n" + "=" * 50)
    print(f"测试获取概念板块 {concept_name} 历史数据")
    print("=" * 50)
    
    try:
        print(f"获取概念板块 {concept_name} 历史行情...")
        start_time = time.time()
        # 修正period参数为"daily"
        hist_data = ak.stock_board_concept_hist_em(symbol=concept_name, start_date="20230101", end_date="20230501", period="daily")
        end_time = time.time()
        
        if hist_data is not None and not hist_data.empty:
            print(f"成功获取概念板块历史数据，共{len(hist_data)}条记录，耗时：{end_time-start_time:.2f}秒")
            print(hist_data.head(5))
            return hist_data
        else:
            print("获取概念板块历史数据失败")
            return None
    except Exception as e:
        print(f"获取概念板块历史数据出错: {e}")
        return None

def main():
    print("开始测试AKShare获取行业数据的能力...")
    
    # 测试获取行业板块数据
    sw_index = test_stock_sector_industry()
    
    # 测试获取行业指数历史数据
    if sw_index is not None and not sw_index.empty:
        # 选择第一个行业测试
        test_industry = sw_index.iloc[0]
        if '指数代码' in sw_index.columns:
            industry_code = test_industry['指数代码']
            industry_name = test_industry['板块名称']
        elif 'index_code' in sw_index.columns:
            industry_code = test_industry['index_code']
            industry_name = test_industry['index_name']
        else:
            # 尝试获取合适的列名
            columns = sw_index.columns.tolist()
            print(f"可用的列名: {columns}")
            # 使用第二列作为代码，第一列作为名称
            industry_code = test_industry[columns[1]]
            industry_name = test_industry[columns[0]]
            
        print(f"\n选择行业 {industry_name} ({industry_code}) 进行测试")
        test_industry_index_hist(industry_code)
    
    # 测试获取概念板块数据
    concept_list = test_concept_board()
    
    # 测试获取概念板块成分股和历史数据
    if concept_list is not None and not concept_list.empty:
        # 选择第一个概念测试
        test_concept = concept_list.iloc[0]
        if '板块名称' in concept_list.columns:
            concept_name = test_concept['板块名称']
        elif 'name' in concept_list.columns:
            concept_name = test_concept['name']
        else:
            # 尝试获取合适的列名
            columns = concept_list.columns.tolist()
            print(f"可用的列名: {columns}")
            # 使用第一列作为名称
            concept_name = test_concept[columns[1]] 
            
        print(f"\n选择概念 {concept_name} 进行测试")
        test_concept_board_detail(concept_name)
        test_concept_board_hist(concept_name)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main() 