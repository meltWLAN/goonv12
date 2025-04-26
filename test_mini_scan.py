#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from visual_stock_system import VisualStockSystem

def main():
    print("开始小样本扫描测试...")
    
    # 创建系统实例
    system = VisualStockSystem(headless=True)
    
    # 创建小样本股票列表
    test_stocks = pd.DataFrame({
        'symbol': ['000001', '600000', '600036', '000651', '300750'],
        'name': ['平安银行', '浦发银行', '招商银行', '格力电器', '宁德时代'],
        'ts_code': ['000001.SZ', '600000.SH', '600036.SH', '000651.SZ', '300750.SZ']
    })
    
    # 逐只分析
    results = []
    for i, row in test_stocks.iterrows():
        try:
            print(f"\n分析股票: {row['name']} ({row['ts_code']})")
            analysis, _ = system.analyze_stock(row['ts_code'])
            if analysis:
                print(f"分析结果: {analysis['trend']}, 推荐: {analysis.get('recommendation', '无推荐')}")
                # 添加到结果
                analysis['name'] = row['name']
                results.append(analysis)
            else:
                print(f"分析失败")
        except Exception as e:
            print(f"分析出错: {str(e)}")
    
    # 打印汇总结果
    print("\n=== 分析结果汇总 ===")
    if results:
        system.print_recommendations(results)
    else:
        print("没有成功分析的股票")
    
    print("\n测试完成")

if __name__ == "__main__":
    main() 