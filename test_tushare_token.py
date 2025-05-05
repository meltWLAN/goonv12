#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Tushare令牌是否可用，验证热门行业分析模块使用真实数据
"""

import os
import sys
import pandas as pd
import time
import tushare as ts

# 导入热门行业分析相关模块
try:
    from sector_analyzer import SectorAnalyzer
    from tushare_sector_provider import TushareSectorProvider, get_sector_provider
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def test_tushare_token():
    """测试Tushare令牌是否可用"""
    print("=" * 50)
    print("测试Tushare令牌")
    print("=" * 50)
    
    # 从配置文件读取令牌
    token = None
    config_file = 'config/tushare_token.txt'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    if key.upper() == 'TUSHARE_TOKEN':
                        token = value.strip()
                        print(f"从配置文件读取到Token: {token[:4]}...{token[-4:]}")
    
    if not token:
        print("未找到Token，使用默认Token")
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    
    # 测试Tushare API是否可用
    try:
        print("尝试连接Tushare API...")
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试获取交易日历
        print("获取交易日历数据...")
        df = pro.trade_cal(exchange='SSE', start_date='20230101', end_date='20230110')
        if df is not None and not df.empty:
            print(f"成功获取交易日历数据，共{len(df)}条记录")
            print(df.head(3))
            print("Tushare API连接成功!")
            return True
        else:
            print("获取数据失败，返回空结果")
            return False
    except Exception as e:
        print(f"Tushare API连接失败: {e}")
        return False

def test_sector_provider():
    """测试行业数据提供器是否使用真实数据"""
    print("\n" + "=" * 50)
    print("测试行业数据提供器")
    print("=" * 50)
    
    try:
        # 初始化行业数据提供器
        print("初始化行业数据提供器...")
        provider = get_sector_provider()
        
        # 测试获取行业列表
        print("获取行业列表...")
        sectors = provider.get_sector_list()
        if sectors and len(sectors) > 0:
            print(f"成功获取行业列表，共{len(sectors)}个行业")
            print("前5个行业:")
            for i, sector in enumerate(sectors[:5]):
                print(f"{i+1}. {sector['name']} ({sector['code']})")
        else:
            print("获取行业列表失败")
            return False
        
        # 测试获取某个行业的历史数据
        if sectors:
            test_sector = sectors[0]
            print(f"\n获取行业 {test_sector['name']} 的历史数据...")
            hist_data = provider.get_sector_history(test_sector['code'], days=30)
            
            if hist_data is not None and not hist_data.empty:
                print(f"成功获取历史数据，共{len(hist_data)}条记录")
                # 检查是否为真实数据
                is_real = True
                if '是模拟数据' in hist_data.columns:
                    is_real = not hist_data['是模拟数据'].any()
                
                print(f"数据类型: {'真实数据' if is_real else '模拟数据'}")
                print("数据前3行:")
                print(hist_data.head(3))
                return is_real
            else:
                print("获取历史数据失败")
                return False
    except Exception as e:
        print(f"测试行业数据提供器失败: {e}")
        return False

def test_hot_sectors_analysis():
    """测试热门行业分析功能"""
    print("\n" + "=" * 50)
    print("测试热门行业分析功能")
    print("=" * 50)
    
    try:
        # 初始化行业分析器
        print("初始化行业分析器...")
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        analyzer = SectorAnalyzer(top_n=10, token=token)
        
        # 分析热门行业
        print("分析热门行业...")
        start_time = time.time()
        result = analyzer.analyze_hot_sectors()
        end_time = time.time()
        
        if result['status'] == 'success':
            print(f"热门行业分析成功，耗时: {end_time - start_time:.2f}秒")
            hot_sectors = result['data']['hot_sectors']
            print(f"获取到{len(hot_sectors)}个热门行业")
            
            # 检查是否有模拟数据
            mock_data_count = sum(1 for s in hot_sectors if s.get('is_mock_data', False))
            real_data_count = len(hot_sectors) - mock_data_count
            
            print(f"真实数据数量: {real_data_count}")
            print(f"模拟数据数量: {mock_data_count}")
            
            # 显示前5个热门行业
            print("\n前5个热门行业:")
            for i, sector in enumerate(hot_sectors[:5]):
                print(f"{i+1}. {sector['name']} - 热度: {sector['hot_score']:.2f} - "
                      f"涨跌幅: {sector['change_pct']:.2f}% - "
                      f"{'模拟数据' if sector.get('is_mock_data', False) else '真实数据'}")
            
            # 判断是否使用真实数据
            is_using_real_data = real_data_count > 0
            if is_using_real_data:
                print("\n✅ 热门行业分析正在使用真实数据")
            else:
                print("\n❌ 热门行业分析仍在使用模拟数据")
            
            return is_using_real_data
        else:
            print(f"热门行业分析失败: {result['message']}")
            return False
    except Exception as e:
        print(f"测试热门行业分析功能失败: {e}")
        return False

if __name__ == "__main__":
    print("开始验证Tushare令牌和热门行业分析...")
    
    # 测试Tushare令牌
    token_result = test_tushare_token()
    
    # 测试行业数据提供器
    provider_result = test_sector_provider()
    
    # 测试热门行业分析
    analysis_result = test_hot_sectors_analysis()
    
    # 输出综合结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    print(f"Tushare API连接: {'✅ 成功' if token_result else '❌ 失败'}")
    print(f"行业数据提供器: {'✅ 使用真实数据' if provider_result else '❌ 使用模拟数据'}")
    print(f"热门行业分析: {'✅ 使用真实数据' if analysis_result else '❌ 使用模拟数据'}")
    
    if token_result and provider_result and analysis_result:
        print("\n✅ 总结: Tushare令牌已成功集成，热门行业分析正在使用真实数据")
    else:
        print("\n❌ 总结: 集成仍有问题，请检查以上详细信息") 