#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试行业分析模块是否正确使用真实数据
验证Tushare和AKShare数据源的切换和降级机制
"""

import os
import sys
import time
import pickle
from datetime import datetime, timedelta
from sector_analyzer import SectorAnalyzer

def test_data_sources():
    """测试数据源优先级和回退机制"""
    print("=== 测试数据源优先级和回退机制 ===")
    
    # 初始化分析器
    analyzer = SectorAnalyzer(top_n=5)
    print("√ 分析器初始化完成")
    
    # 获取几个热门行业
    result = analyzer.analyze_hot_sectors()
    if result['status'] != 'success':
        print(f"× 获取热门行业失败: {result['message']}")
        return False
    
    hot_sectors = result['data']['hot_sectors']
    if not hot_sectors:
        print("× 未找到热门行业")
        return False
    
    print(f"√ 成功获取热门行业，共 {len(hot_sectors)} 个")
    
    # 测试第一个热门行业的数据获取
    test_sector = hot_sectors[0]
    sector_name = test_sector['name']
    sector_code = test_sector.get('code', '')
    
    print(f"\n测试获取行业 '{sector_name}' 的历史数据")
    
    # 清除缓存，确保重新获取数据
    if os.path.exists('data_cache'):
        cache_files = [f for f in os.listdir('data_cache') if f.startswith('sector_history_')]
        for file in cache_files:
            try:
                os.remove(f'data_cache/{file}')
                print(f"√ 已清除缓存文件: {file}")
            except:
                print(f"× 无法清除缓存文件: {file}")
    
    # 清除内存缓存
    analyzer._cache = {}
    print("√ 已清除内存缓存")
    
    # 测试获取真实数据
    start_time = time.time()
    hist_data = analyzer._get_sector_history(sector_name, sector_code)
    end_time = time.time()
    
    # 检查获取的数据
    if hist_data is None or hist_data.empty:
        print("× 获取历史数据失败，返回空数据")
        return False
    
    print(f"√ 成功获取历史数据，耗时 {end_time - start_time:.2f} 秒")
    print(f"√ 获取了 {len(hist_data)} 条历史记录")
    
    # 检查是否为模拟数据
    is_mock = False
    if '是模拟数据' in hist_data.columns:
        is_mock = hist_data['是模拟数据'].any()
    
    if is_mock:
        print("× 获取到的是模拟数据，未能获取真实市场数据")
        return False
    else:
        print("√ 获取到的是真实市场数据")
    
    # 检查数据来源
    if analyzer.tushare_available:
        print("√ Tushare API 可用")
    else:
        print("× Tushare API 不可用，使用备用数据源")
    
    # 保存测试数据样本
    sample_file = 'test_data_sample.pkl'
    try:
        with open(sample_file, 'wb') as f:
            pickle.dump({
                'sector': sector_name,
                'data': hist_data.head(10).to_dict(),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_mock': is_mock
            }, f)
        print(f"√ 测试数据样本已保存到 {sample_file}")
    except Exception as e:
        print(f"× 保存测试数据样本失败: {e}")
    
    # 测试备份数据是否已创建
    backup_path = f'data_cache/sector_history_{sector_name.replace(" ", "_")}.pkl'
    if os.path.exists(backup_path):
        print(f"√ 已成功创建备份数据: {backup_path}")
    else:
        print(f"× 未能创建备份数据: {backup_path}")
    
    return not is_mock

def test_api_keys_config():
    """测试API密钥配置"""
    print("\n=== 测试API密钥配置 ===")
    
    # 检查配置文件是否存在
    config_file = 'config/api_keys.txt'
    if not os.path.exists(config_file):
        print(f"× 配置文件不存在: {config_file}")
        return False
    
    # 尝试读取配置
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        if 'TUSHARE_TOKEN' in content:
            print("√ 配置文件中包含 Tushare API token 设置")
        else:
            print("× 配置文件中未找到 Tushare API token 设置")
            return False
    except Exception as e:
        print(f"× 读取配置文件失败: {e}")
        return False
    
    # 测试从配置文件加载token
    analyzer = SectorAnalyzer()
    if analyzer.token:
        print(f"√ 成功从配置加载 Tushare token: {analyzer.token[:5]}...{analyzer.token[-5:]}")
    else:
        print("× 未能加载 Tushare token")
        return False
    
    return True

if __name__ == "__main__":
    print("====== 行业数据真实性测试 ======\n")
    
    # 测试数据源
    data_source_test = test_data_sources()
    
    # 测试API配置
    api_config_test = test_api_keys_config()
    
    # 输出总结
    print("\n====== 测试结果总结 ======")
    print(f"数据源测试: {'通过 ✅' if data_source_test else '失败 ❌'}")
    print(f"API配置测试: {'通过 ✅' if api_config_test else '失败 ❌'}")
    
    if data_source_test and api_config_test:
        print("\n🎉 所有测试通过！系统已配置为优先使用真实市场数据。")
    else:
        print("\n⚠️ 部分测试失败，请检查以上日志并修复问题。")
        
    print("\n提示：在无法获取真实市场数据时，系统会使用之前保存的备份数据。")
    print("      只有在无法获取实时数据且无备份数据时，才会使用模拟数据。") 