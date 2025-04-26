#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from enhanced_backtesting import EnhancedBacktester
from china_stock_provider import ChinaStockProvider

def test_volume_price_strategy():
    """测试量价策略回测"""
    print("开始测试量价策略回测...")
    
    # 获取测试数据
    provider = ChinaStockProvider()
    stock_code = '000001.SZ'  # 平安银行
    
    try:
        # 获取股票数据
        stock_data = provider.get_data('stock', stock_code, 
                                      start_date='20220101', 
                                      end_date='20230101')
        
        if stock_data is None or len(stock_data) == 0:
            print(f"无法获取{stock_code}的股票数据")
            return
            
        print(f"获取到{len(stock_data)}条股票数据")
        
        # 创建回测器
        initial_capital = 100000.0
        backtester = EnhancedBacktester(initial_capital=initial_capital)
        
        # 执行回测
        result = backtester.backtest_volume_price_strategy(stock_data, stock_code)
        
        # 输出回测结果
        print("\n===== 回测结果 =====")
        print(f"初始资金: {initial_capital:,.2f} 元")
        
        if hasattr(result, 'final_capital') and result.final_capital is not None:
            print(f"最终资金: {result.final_capital:,.2f} 元")
            print(f"总收益率: {((result.final_capital/initial_capital)-1)*100:.2f}%")
        else:
            print("最终资金: 未知")
            print("总收益率: 未知")
        
        if hasattr(result, 'trade_count') and result.trade_count is not None:
            print(f"交易次数: {result.trade_count}")
        else:
            print("交易次数: 未知")
            
        if hasattr(result, 'win_rate') and result.win_rate is not None:
            print(f"胜率: {result.win_rate*100:.2f}%")
        else:
            print("胜率: 未知")
        
        print("\n测试完成")
        
    except Exception as e:
        import traceback
        print(f"测试过程中出错: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_volume_price_strategy() 