#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试股票分析功能
"""

import sys
from PyQt5.QtWidgets import QApplication

from single_stock_analyzer import SingleStockAnalyzer

def test_stock_analysis():
    app = QApplication(sys.argv)
    print("开始测试股票分析功能...")
    analyzer = SingleStockAnalyzer()
    
    # 测试分析特定股票
    stock_code = '300308.SZ'
    print(f"正在分析股票: {stock_code}")
    
    try:
        result = analyzer.get_detailed_analysis(stock_code)
        print(f"分析结果状态: {result['status']}")
        
        if result['status'] == 'success':
            print("分析成功!")
            data = result['data']
            print(f"股票名称: {data.get('name', '未知')}")
            print(f"股票代码: {data.get('symbol', '未知')}")
            print(f"最新价格: {data.get('last_price', 0):.2f}")
        else:
            print(f"分析失败: {result.get('message', '未知错误')}")
    
    except Exception as e:
        print(f"测试过程中出现异常: {str(e)}")

if __name__ == "__main__":
    test_stock_analysis()