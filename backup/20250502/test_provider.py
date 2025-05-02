#!/usr/bin/env python
# -*- coding: utf-8 -*-

from china_stock_provider import ChinaStockProvider
import time

def test_stock_data():
    print("="*50)
    print("测试股票历史数据获取...")
    provider = ChinaStockProvider()
    print(f"当前数据源: {provider.current_source}")
    
    try:
        # 尝试获取平安银行(000001.SZ)的数据
        df = provider.get_data(
            data_type='stock', 
            symbol='000001.SZ', 
            start_date='20230101', 
            end_date='20230201'
        )
        
        print(f"获取到数据: {not df.empty}")
        if not df.empty:
            print(f"数据行数: {len(df)}")
            print("数据前5行:")
            print(df.head())
        else:
            print("没有获取到数据")
            
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

def test_realtime_data():
    print("="*50)
    print("测试实时数据获取...")
    provider = ChinaStockProvider()
    
    try:
        # 测试实时行情
        print("获取实时行情数据...")
        df = provider.get_realtime_daily(ts_code='000001.SZ')
        print(f"获取到数据: {not df.empty}")
        if not df.empty:
            print(df.head())
        else:
            print("没有获取到实时行情数据")
        
    except Exception as e:
        print(f"实时数据错误: {str(e)}")
        import traceback
        traceback.print_exc()

def test_fundamental_data():
    print("="*50)
    print("测试基本面数据获取...")
    provider = ChinaStockProvider()
    
    try:
        # 获取股票信息
        print("获取股票基本信息...")
        df = provider.get_stock_info(symbol='000001.SZ')
        print(f"获取到数据: {not df.empty}")
        if not df.empty:
            print(df.head())
        else:
            print("没有获取到股票基本信息")
            
    except Exception as e:
        print(f"基本面数据错误: {str(e)}")
        import traceback
        traceback.print_exc()

def test_error_handling():
    print("="*50)
    print("测试错误处理...")
    provider = ChinaStockProvider()
    
    try:
        # 测试无效股票代码
        print("测试无效股票代码...")
        df = provider.get_data(data_type='stock', symbol='INVALID', start_date='20230101', end_date='20230201')
        print(f"错误处理结果: {df.empty}")
        
    except Exception as e:
        print(f"错误处理异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stock_data()
    time.sleep(1)
    test_realtime_data()
    time.sleep(1)
    test_fundamental_data()
    time.sleep(1)
    test_error_handling() 