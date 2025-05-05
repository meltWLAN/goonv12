#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专用诊断脚本，用于修复量价分析中的问题
"""

import sys
import os
import pandas as pd
import numpy as np
import traceback
from PyQt5.QtWidgets import QApplication
from visual_stock_system import VisualStockSystem

# 配置
TOKEN = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
TEST_STOCK = '000001.SZ'  # 平安银行

def test_volume_price_step_by_step(visual_system):
    """逐步测试量价分析功能，定位错误"""
    print("\n===== 量价分析逐步诊断 =====")
    
    # 获取股票数据
    print(f"正在获取{TEST_STOCK}的股票数据...")
    try:
        print("DEBUG: 调用get_stock_data之前")
        df = visual_system.get_stock_data(TEST_STOCK)
        print("DEBUG: 调用get_stock_data成功")
    except Exception as e:
        print(f"获取股票数据失败: {str(e)}")
        traceback.print_exc()
        return False
    
    if df is None or df.empty:
        print(f"获取{TEST_STOCK}数据失败")
        return False
    
    # 复制一个数据副本用于测试
    test_df = df.copy()
    
    # 列名映射和验证
    print("\n1. 测试列名映射和标准化...")
    column_mapping = {
        'volume': 'Volume', 'close': 'Close', 'open': 'Open', 
        'high': 'High', 'low': 'Low', 'trade_date': 'Date'
    }
    
    # 1. 列名标准化
    for old_col, new_col in column_mapping.items():
        if old_col in test_df.columns and new_col not in test_df.columns:
            test_df[new_col] = test_df[old_col]
    
    # 检查所需的关键列是否存在
    required_columns = ['Volume', 'Close', 'High', 'Low']
    missing_columns = [col for col in required_columns if col not in test_df.columns]
    if missing_columns:
        print(f"列名错误: 缺少必要列 {', '.join(missing_columns)}")
        return False
    else:
        print("列名检查通过")
    
    # 2. 测试日期索引处理
    print("\n2. 测试日期索引处理...")
    try:
        if 'Date' in test_df.columns:
            test_df.set_index('Date', inplace=True)
        elif 'trade_date' in test_df.columns:
            test_df['Date'] = test_df['trade_date']
            test_df.set_index('Date', inplace=True)
        test_df.index = pd.to_datetime(test_df.index)
        print("日期索引处理成功")
    except Exception as e:
        print(f"日期索引处理失败: {str(e)}")
        traceback.print_exc()
        return False
    
    # 3. 测试初始化指标计算
    print("\n3. 测试初始化指标数据...")
    indicator_columns = [
        'Volume_MA20', 'Volume_MA5', 'Volume_Ratio', 'Price_Change', 'Volume_Change',
        'ATR', 'Volatility', 'PEV', 'PEV_MA20', 'BB_Middle', 'BB_Upper', 'BB_Lower'
    ]
    
    try:
        for col in indicator_columns:
            test_df[col] = np.zeros(len(test_df))
        print("指标初始化成功")
    except Exception as e:
        print(f"指标初始化失败: {str(e)}")
        traceback.print_exc()
        return False
    
    # 4. 测试均量指标计算
    print("\n4. 测试均量指标计算...")
    try:
        test_df['Volume_MA20'] = test_df['Volume'].rolling(window=20, min_periods=1).mean().fillna(test_df['Volume'])
        test_df['Volume_MA5'] = test_df['Volume'].rolling(window=5, min_periods=1).mean().fillna(test_df['Volume'])
        test_df['Volume_Ratio'] = (test_df['Volume'] / test_df['Volume_MA20']).fillna(1.0)
        print("均量指标计算成功")
    except Exception as e:
        print(f"均量指标计算失败: {str(e)}")
        traceback.print_exc()
        return False
    
    # 5. 测试价格变化计算
    print("\n5. 测试价格变化计算...")
    try:
        test_df['Price_Change'] = test_df['Close'].pct_change().fillna(0)
        test_df['Volume_Change'] = test_df['Volume'].pct_change().fillna(0)
        print("价格变化计算成功")
    except Exception as e:
        print(f"价格变化计算失败: {str(e)}")
        traceback.print_exc()
        return False
    
    # 6. 测试ATR指标计算
    print("\n6. 测试ATR指标计算...")
    try:
        import talib as ta
        atr_values = ta.ATR(test_df['High'].values, test_df['Low'].values, test_df['Close'].values, timeperiod=14)
        test_df['ATR'] = np.nan_to_num(atr_values, nan=test_df['Close'].std() * 0.1)
        test_df['Volatility'] = (test_df['ATR'] / test_df['Close'] * 100).fillna(5.0)
        print("ATR指标计算成功")
    except Exception as e:
        print(f"ATR指标计算失败: {str(e)}")
        traceback.print_exc()
        return False
    
    # 7. 测试趋势因子计算（关键部分）
    print("\n7. 测试趋势因子计算...")
    try:
        # 获取最新值
        if len(test_df) > 0:
            last_close = test_df['Close'].iloc[-1]
            last_atr = test_df['ATR'].iloc[-1]
            
            # 计算趋势强度
            trend_values = ta.LINEARREG_SLOPE(test_df['Close'].values, timeperiod=14)
            test_df['Trend_Strength'] = np.nan_to_num(trend_values, nan=0.0)
            last_trend_strength = test_df['Trend_Strength'].iloc[-1]
            
            # 获取成交量比率并保证安全
            last_volume_ratio = test_df['Volume_Ratio'].iloc[-1]
            safe_volume_ratio = max(0.1, last_volume_ratio)  # 避免log(0)或log(负数)
            
            # 计算趋势因子
            trend_factor = last_trend_strength * (1 + np.log(safe_volume_ratio))
            
            # 测试最终的价格区间计算
            test_df['Future_High'] = last_close + (last_atr * 2 * abs(trend_factor))
            test_df['Future_Low'] = last_close - (last_atr * abs(trend_factor))
            
            print("趋势因子计算成功")
            print(f"  * 最新收盘价: {last_close}")
            print(f"  * ATR: {last_atr}")
            print(f"  * 趋势强度: {last_trend_strength}")
            print(f"  * 成交量比率: {last_volume_ratio}")
            print(f"  * 安全成交量比率: {safe_volume_ratio}")
            print(f"  * 趋势因子: {trend_factor}")
            print(f"  * 未来价格上限: {test_df['Future_High'].iloc[-1]}")
            print(f"  * 未来价格下限: {test_df['Future_Low'].iloc[-1]}")
        else:
            print("数据为空，无法计算趋势因子")
    except Exception as e:
        print(f"趋势因子计算失败: {str(e)}")
        traceback.print_exc()
        return False
    
    # 8. 测试完整的量价分析
    print("\n8. 测试完整的量价分析函数...")
    try:
        # 调用原始的量价分析函数
        result_df = visual_system.analyze_volume_price(df)
        if result_df is None:
            print("量价分析返回None")
            return False
        else:
            print("量价分析成功完成")
            print(f"输出数据形状: {result_df.shape}")
            print("主要指标样本:")
            for indicator in ['Volume_Ratio', 'ATR', 'Trend_Strength', 'Volume_Price_Score']:
                if indicator in result_df.columns:
                    print(f"  * {indicator}: {result_df[indicator].iloc[-1]}")
            return True
    except Exception as e:
        print(f"完整量价分析失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("===== 量价分析修复诊断 =====")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 初始化系统
    try:
        visual_system = VisualStockSystem(TOKEN, headless=True)
        print("成功初始化数据系统")
        
        # 检查数据提供者是否正确初始化
        print(f"数据提供者类型: {type(visual_system.data_provider)}")
        
        # 逐步测试量价分析功能
        success = test_volume_price_step_by_step(visual_system)
        
        print("\n===== 诊断结果 =====")
        if success:
            print("量价分析功能正常工作！")
            sys.exit(0)
        else:
            print("量价分析功能存在问题，需要进一步修复")
            sys.exit(1)
    except Exception as e:
        print(f"系统初始化失败: {str(e)}")
        traceback.print_exc()
        sys.exit(1) 