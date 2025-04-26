#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import time
import concurrent.futures
import os
from visual_stock_system import VisualStockSystem

# 创建缓存目录
CACHE_DIR = './data_cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def analyze_stock_with_cache(system, ts_code, name):
    """使用缓存分析单只股票"""
    cache_file = f"{CACHE_DIR}/{ts_code.replace('.', '_')}_analysis.pkl"
    
    # 检查缓存
    if os.path.exists(cache_file):
        try:
            cached_result = pd.read_pickle(cache_file)
            print(f"使用缓存分析: {name} ({ts_code})")
            return cached_result
        except Exception as e:
            print(f"缓存读取失败: {e}")
    
    # 执行分析
    try:
        start_time = time.time()
        print(f"分析股票: {name} ({ts_code})")
        analysis, _ = system.analyze_stock(ts_code)
        elapsed = time.time() - start_time
        
        if analysis:
            # 添加名称和耗时信息
            analysis['name'] = name
            analysis['analysis_time'] = elapsed
            
            # 保存缓存
            try:
                pd.to_pickle(analysis, cache_file)
            except Exception as e:
                print(f"缓存保存失败: {e}")
                
            print(f"分析结果: {analysis['trend']}, 推荐: {analysis.get('recommendation', '无推荐')}, 耗时: {elapsed:.2f}秒")
            return analysis
        else:
            print(f"分析失败")
            return None
    except Exception as e:
        print(f"分析出错: {str(e)}")
        return None

def main():
    start_time = time.time()
    print("开始优化版扫描测试...")
    
    # 创建系统实例
    system = VisualStockSystem(headless=True, cache_dir=CACHE_DIR)
    
    # 创建扩展样本股票列表
    test_stocks = pd.DataFrame({
        'symbol': ['000001', '600000', '600036', '000651', '300750', 
                   '000333', '601318', '600519', '000858', '600276'],
        'name': ['平安银行', '浦发银行', '招商银行', '格力电器', '宁德时代',
                '美的集团', '中国平安', '贵州茅台', '五粮液', '恒瑞医药'],
        'ts_code': ['000001.SZ', '600000.SH', '600036.SH', '000651.SZ', '300750.SZ',
                   '000333.SZ', '601318.SH', '600519.SH', '000858.SZ', '600276.SH']
    })
    
    # 方法1: 串行处理
    print("\n===== 串行处理 =====")
    serial_start = time.time()
    serial_results = []
    for i, row in test_stocks.iterrows():
        result = analyze_stock_with_cache(system, row['ts_code'], row['name'])
        if result:
            serial_results.append(result)
    serial_time = time.time() - serial_start
    print(f"串行处理耗时: {serial_time:.2f}秒")
    
    # 方法2: 并行处理
    print("\n===== 并行处理 =====")
    parallel_start = time.time()
    parallel_results = []
    
    # 创建线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # 提交任务
        futures = []
        for i, row in test_stocks.iterrows():
            future = executor.submit(analyze_stock_with_cache, system, row['ts_code'], row['name'])
            futures.append(future)
            
        # 获取结果
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                parallel_results.append(result)
    
    parallel_time = time.time() - parallel_start
    print(f"并行处理耗时: {parallel_time:.2f}秒")
    
    # 打印汇总结果
    print("\n=== 分析结果汇总 ===")
    if parallel_results:
        system.print_recommendations(parallel_results)
    else:
        print("没有成功分析的股票")
    
    # 输出性能比较
    total_time = time.time() - start_time
    print(f"\n性能比较:")
    print(f"串行处理耗时: {serial_time:.2f}秒")
    print(f"并行处理耗时: {parallel_time:.2f}秒")
    print(f"加速比: {serial_time/parallel_time:.2f}x")
    print(f"总耗时: {total_time:.2f}秒")
    print("\n测试完成")

if __name__ == "__main__":
    main() 