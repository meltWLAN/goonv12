#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 SectorAnalyzer 类中的 Tushare 集成
"""

import sys
import time
from datetime import datetime
import pandas as pd
import os

# 测试SectorAnalyzer类
def test_sector_analyzer():
    try:
        print("正在测试 SectorAnalyzer 类的 Tushare 集成...")
        
        # 导入 SectorAnalyzer 类
        try:
            from sector_analyzer import SectorAnalyzer
            print("成功导入 SectorAnalyzer 类")
        except ImportError as e:
            print(f"错误: 导入 SectorAnalyzer 类失败: {str(e)}")
            return False
        
        # 创建 SectorAnalyzer 实例
        try:
            analyzer = SectorAnalyzer(top_n=5)
            print("成功创建 SectorAnalyzer 实例")
        except Exception as e:
            print(f"错误: 创建 SectorAnalyzer 实例失败: {str(e)}")
            return False
        
        # 测试 Tushare API 是否正确初始化
        if not analyzer.tushare_available:
            print("错误: Tushare API 初始化失败，未能正确设置")
            return False
        else:
            print("Tushare API 初始化成功")
            print(f"使用的 Token: {analyzer.token[:4]}{'*' * (len(analyzer.token) - 8)}{analyzer.token[-4:]}")
        
        # 测试获取行业列表
        print("\n正在测试获取行业列表...")
        try:
            start_time = time.time()
            sectors = analyzer.get_sector_list()
            end_time = time.time()
            
            if sectors:
                print(f"成功获取行业列表，共 {len(sectors)} 个行业")
                print(f"请求耗时: {end_time - start_time:.2f} 秒")
                print("\n前3个行业:")
                for i, sector in enumerate(sectors[:3]):
                    print(f"{i+1}. {sector['name']} (代码: {sector['code']})")
            else:
                print("错误: 获取行业列表失败，返回空数据")
                return False
        except Exception as e:
            print(f"错误: 获取行业列表时发生异常: {str(e)}")
            return False
        
        # 测试获取行业历史数据
        print("\n正在测试获取行业历史数据...")
        if sectors:
            # 选择第一个行业进行测试
            test_sector = sectors[0]
            sector_name = test_sector['name']
            sector_code = test_sector['code']
            
            try:
                print(f"正在获取行业 '{sector_name}' 的历史数据...")
                start_time = time.time()
                hist_data = analyzer._get_sector_history(sector_name, sector_code)
                end_time = time.time()
                
                if hist_data is not None and not hist_data.empty:
                    print(f"成功获取行业历史数据，共 {len(hist_data)} 条记录")
                    print(f"请求耗时: {end_time - start_time:.2f} 秒")
                    print("\n数据包含以下列:")
                    for col in hist_data.columns:
                        print(f"- {col}")
                    
                    print("\n前3条历史数据:")
                    print(hist_data.head(3))
                    
                    # 检查是否为模拟数据
                    if '是模拟数据' in hist_data.columns and hist_data['是模拟数据'].any():
                        print("\n⚠️ 警告: 返回的是模拟数据，而非真实数据")
                    else:
                        print("\n✅ 成功获取真实历史数据")
                else:
                    print("错误: 获取行业历史数据返回空数据")
                    return False
            except Exception as e:
                print(f"错误: 获取行业历史数据时发生异常: {str(e)}")
                return False
        
        # 测试热门行业分析
        print("\n正在测试热门行业分析...")
        try:
            start_time = time.time()
            hot_sectors = analyzer.analyze_hot_sectors()
            end_time = time.time()
            
            if hot_sectors and hot_sectors['status'] == 'success':
                print(f"成功分析热门行业，耗时: {end_time - start_time:.2f} 秒")
                top_sectors = hot_sectors['data']['hot_sectors']
                print(f"\n热门行业排名:")
                for i, sector in enumerate(top_sectors):
                    print(f"{i+1}. {sector['name']} (热度得分: {sector['hot_score']:.2f})")
                    print(f"   分析: {sector['analysis_reason']}")
            else:
                print(f"错误: 热门行业分析失败: {hot_sectors.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"错误: 热门行业分析时发生异常: {str(e)}")
            return False
        
        # 检查缓存
        print("\n正在检查数据缓存...")
        cache_file = 'data_cache/sector_analyzer_cache.pkl'
        if os.path.exists(cache_file):
            print(f"缓存文件已创建: {cache_file}")
            print(f"缓存文件大小: {os.path.getsize(cache_file)/1024:.2f} KB")
        else:
            print(f"警告: 未找到缓存文件 {cache_file}")
        
        return True
        
    except Exception as e:
        print(f"测试过程中出现未预期的异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("====== 测试 SectorAnalyzer 类的 Tushare 集成 ======\n")
    
    success = test_sector_analyzer()
    
    print("\n====== 测试结果 ======")
    if success:
        print("✅ 测试通过! SectorAnalyzer 类的 Tushare 集成正常工作")
    else:
        print("❌ 测试失败! 请检查错误信息并解决问题")
    
    sys.exit(0 if success else 1) 