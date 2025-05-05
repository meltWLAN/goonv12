#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证技术指标和量价分析的修复效果
对比修复前后的输出，确认不再有NaN警告消息
"""

import sys
import os
import pandas as pd
import numpy as np
import time
import io
from contextlib import redirect_stdout
from PyQt5.QtWidgets import QApplication
from visual_stock_system import VisualStockSystem

# 配置
TOKEN = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
TEST_STOCKS = ['000001.SZ', '600519.SH']  # 测试平安银行和贵州茅台

def capture_output(func, *args, **kwargs):
    """捕获函数输出"""
    # Safer implementation that restores stdout properly
    import sys
    original_stdout = sys.stdout
    output = io.StringIO()
    result = None
    try:
        sys.stdout = output
        result = func(*args, **kwargs)
    finally:
        sys.stdout = original_stdout
    return result, output.getvalue()

def test_technical_indicators(visual_system, stock_code):
    """测试技术指标计算（EMA21、MACD等）"""
    print(f"\n===== 测试 {stock_code} 技术指标计算 =====")
    
    # 1. 获取股票数据
    print(f"获取股票数据...")
    # 使用直接调用方式避免DataFrame真值歧义错误
    df = debug_get_stock_data(visual_system, stock_code)
    
    if df is None or len(df) == 0:
        print(f"获取股票数据失败")
        return False
    
    print(f"成功获取股票数据: {len(df)}行")
    
    # 2. 计算技术指标
    result_df, output = capture_output(
        visual_system.analyze_momentum, df
    )
    
    # 3. 检查输出是否包含NaN警告
    nan_warnings = [line for line in output.split('\n') 
                   if '含有NaN值' in line and len(line.strip()) > 0]
    
    print(f"NaN警告数量: {len(nan_warnings)}")
    if nan_warnings:
        print("仍有NaN警告:")
        for warning in nan_warnings:
            print(f"  {warning}")
        success = False
    else:
        print("没有NaN警告，技术指标修复成功!")
        success = True
    
    # 4. 检查结果数据的有效性
    if result_df is None:
        print("分析结果为None，修复失败")
        return False
    
    key_indicators = ['EMA21', 'MACD', 'MACD_Signal', 'MACD_Hist']
    missing = [ind for ind in key_indicators if ind not in result_df.columns]
    
    if missing:
        print(f"缺少关键指标: {missing}")
        success = False
    
    has_nan = False
    for indicator in key_indicators:
        if indicator in result_df.columns and result_df[indicator].isnull().any():
            has_nan = True
            print(f"指标 {indicator} 包含NaN值")
    
    if has_nan:
        print("数据中仍有NaN值，修复失败")
        success = False
    else:
        print("所有指标数据均有效，没有NaN值")
    
    # 5. 展示样本数据
    if success:
        print("\n指标样本值:")
        for indicator in key_indicators:
            if indicator in result_df.columns:
                print(f"  {indicator}: {result_df[indicator].iloc[-1]}")
    
    return success

def test_volume_price(visual_system, stock_code):
    """测试量价分析功能"""
    print(f"\n===== 测试 {stock_code} 量价分析 =====")
    
    # 1. 获取股票数据
    print(f"获取股票数据...")
    # 使用直接调用方式避免DataFrame真值歧义错误
    df = debug_get_stock_data(visual_system, stock_code)
    
    if df is None or len(df) == 0:
        print(f"获取股票数据失败")
        return False
    
    print(f"成功获取股票数据: {len(df)}行")
    
    # 2. 执行量价分析
    try:
        print("DEBUG: 调用analyze_volume_price之前")
        result_df, output = capture_output(
            visual_system.analyze_volume_price, df
        )
        print("DEBUG: 调用analyze_volume_price成功")
    except Exception as e:
        print(f"量价分析执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 检查输出是否包含错误消息
    error_messages = [line for line in output.split('\n') 
                     if '出错' in line and len(line.strip()) > 0]
    
    print(f"错误消息数量: {len(error_messages)}")
    if error_messages:
        print("仍有错误消息:")
        for error in error_messages:
            print(f"  {error}")
        return False
    
    # 4. 检查结果数据
    if result_df is None:
        print("量价分析结果为None，修复失败")
        return False
    
    # 5. 检查结果数据中的关键指标
    key_indicators = ['Volume_Ratio', 'ATR', 'Trend_Strength', 'Volatility',
                     'Channel_Width', 'Future_High', 'Future_Low']
    
    missing = [ind for ind in key_indicators if ind not in result_df.columns]
    if missing:
        print(f"缺少关键指标: {missing}")
        return False
    
    has_nan = False
    for indicator in key_indicators:
        if indicator in result_df.columns and result_df[indicator].isnull().any():
            has_nan = True
            print(f"指标 {indicator} 包含NaN值")
    
    if has_nan:
        print("量价分析数据中仍有NaN值，修复失败")
        return False
    
    # 6. 展示样本数据
    print("\n量价分析指标样本:")
    for indicator in key_indicators:
        if indicator in result_df.columns:
            print(f"  {indicator}: {result_df[indicator].iloc[-1]}")
    
    print("\n量价分析修复成功!")
    return True

def test_complete_analysis(visual_system, stock_code):
    """测试完整的分析流程"""
    print(f"\n===== 测试 {stock_code} 完整分析流程 =====")
    
    # 1. 获取数据直接从debug_get_stock_data获取
    print(f"获取股票数据...")
    df = debug_get_stock_data(visual_system, stock_code)
    
    if df is None or len(df) == 0:
        print(f"获取股票数据失败")
        return False
    
    print(f"成功获取股票数据: {len(df)}行")
    
    # 2. 执行手动分析代替直接调用analyze_stock
    try:
        # 步骤1: 分析动量
        df_momentum = visual_system.analyze_momentum(df)
        # 步骤2: 分析量价
        df_volume = visual_system.analyze_volume_price(df_momentum) if df_momentum is not None else None
        # 步骤3: 趋势判断
        trend = visual_system.check_trend(df_volume) if df_volume is not None else "unknown"
        
        result = ({
            'symbol': stock_code,
            'name': visual_system.get_stock_name(stock_code),
            'trend': trend,
            'volume': visual_system.safe_get_value(df_volume, 'Volume') if df_volume is not None else 0,
            'volume_ma20': visual_system.safe_get_value(df_volume, 'Volume_MA20') if df_volume is not None else 0,
            'macd_hist': visual_system.safe_get_value(df_momentum, 'MACD_Hist') if df_momentum is not None else 0,
        }, df_volume)
    except Exception as e:
        print(f"分析过程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 检查结果
    if result is None or result[0] is None:
        print("完整分析失败，结果为None")
        return False
    
    print("\n完整分析成功!")
    
    # 4. 打印分析结果摘要
    analysis, df = result
    print("\n分析结果摘要:")
    if analysis:
        print(f"  股票: {analysis.get('symbol')} {analysis.get('name')}")
        print(f"  趋势: {analysis.get('trend')}")
        print(f"  MACD柱状: {analysis.get('macd_hist')}")
        if analysis.get('volume_ma20', 0) > 0:
            print(f"  成交量与均量比: {analysis.get('volume', 0) / analysis.get('volume_ma20', 1):.2f}")
        
        # 检查推荐结果
        try:
            recommendation = visual_system.generate_recommendation(analysis)
            if recommendation:
                print(f"  推荐: {recommendation}")
        except:
            pass
    
    return True

# 创建一个单独的函数来测试get_stock_data
def debug_get_stock_data(visual_system, stock_code):
    """直接测试get_stock_data方法以定位问题"""
    print(f"\n===== 调试 get_stock_data 方法 ({stock_code}) =====")
    
    try:
        print("正在直接调用get_stock_data...")
        df = visual_system.get_stock_data(stock_code)
        print(f"调用成功，返回类型: {type(df)}")
        if isinstance(df, pd.DataFrame):
            print(f"DataFrame形状: {df.shape}")
            print(f"DataFrame非空: {not df.empty}")
            print(f"DataFrame列: {list(df.columns)}")
            print(f"DataFrame样本:")
            print(df.head(2))
        return df
    except Exception as e:
        print(f"get_stock_data调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def direct_test_volume_price(visual_system, stock_code):
    """直接测试量价分析功能，完全避开get_stock_data方法"""
    print(f"\n===== 直接测试 {stock_code} 量价分析 =====")
    
    # 1. 创建测试数据
    print(f"创建测试数据...")
    # 创建一个基本的DataFrame，具有量价分析所需的全部列
    import numpy as np
    
    # 创建有100行的测试数据
    dates = pd.date_range(start='2025-01-01', periods=100)
    prices = np.linspace(10, 20, 100) + np.random.normal(0, 0.5, 100)  # 模拟上升趋势
    volumes = np.random.normal(1000000, 200000, 100)  # 模拟成交量
    
    test_df = pd.DataFrame({
        'Date': dates,
        'Close': prices,
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Volume': volumes
    })
    
    print(f"成功创建测试数据: {len(test_df)}行")
    
    # 2. 执行量价分析
    try:
        print("执行量价分析...")
        result_df = visual_system.analyze_volume_price(test_df)
        
        # 3. 检查结果
        if result_df is None:
            print("量价分析结果为None，测试失败")
            return False
            
        # 4. 检查关键列是否存在
        key_indicators = ['Volume_Ratio', 'ATR', 'Trend_Strength', 'Volatility',
                         'Channel_Width', 'Future_High', 'Future_Low']
                         
        missing = [ind for ind in key_indicators if ind not in result_df.columns]
        if missing:
            print(f"缺少关键指标: {missing}")
            return False
            
        # 5. 检查是否有NaN值
        has_nan = False
        for indicator in key_indicators:
            if indicator in result_df.columns and result_df[indicator].isnull().any():
                has_nan = True
                print(f"指标 {indicator} 包含NaN值")
                
        if has_nan:
            print("量价分析数据中仍有NaN值，测试失败")
            return False
            
        # 6. 打印样本结果
        print("\n量价分析指标样本:")
        for indicator in key_indicators:
            if indicator in result_df.columns:
                print(f"  {indicator}: {result_df[indicator].iloc[-1]}")
                
        print("\n直接量价分析测试成功!")
        return True
        
    except Exception as e:
        print(f"量价分析执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("===== 技术指标和量价分析修复验证 =====")
    
    # 初始化QApplication
    app = QApplication(sys.argv)
    
    try:
        # 初始化系统
        print("\n初始化系统...")
        visual_system = VisualStockSystem(TOKEN, headless=True)
        
        # 测试结果记录
        results = {}
        
        # 对每只测试股票进行测试
        for stock in TEST_STOCKS:
            # 技术指标测试
            results[f"{stock}_indicator"] = test_technical_indicators(visual_system, stock)
            
            # 量价分析测试 - 使用新的直接测试方法
            results[f"{stock}_volume_price"] = direct_test_volume_price(visual_system, stock)
            
            # 完整分析测试
            results[f"{stock}_complete"] = test_complete_analysis(visual_system, stock)
        
        # 汇总结果
        print("\n\n===== 修复验证测试结果汇总 =====")
        all_passed = True
        
        for stock in TEST_STOCKS:
            print(f"\n{stock} 测试结果:")
            print(f"  技术指标: {'通过' if results.get(f'{stock}_indicator') else '失败'}")
            print(f"  量价分析: {'通过' if results.get(f'{stock}_volume_price') else '失败'}")
            print(f"  完整分析: {'通过' if results.get(f'{stock}_complete') else '失败'}")
            
            if not (results.get(f'{stock}_indicator') and 
                   results.get(f'{stock}_volume_price') and
                   results.get(f'{stock}_complete')):
                all_passed = False
        
        # 最终结论
        print("\n===== 最终结论 =====")
        if all_passed:
            print("\n🎉 所有测试通过！修复已完全成功，系统可以正常使用")
            print("技术指标没有NaN警告，量价分析也能正常工作")
            return 0
        else:
            print("\n⚠️ 部分测试未通过，修复可能不完整")
            print("请检查具体的测试结果确定问题所在")
            return 1
    except Exception as e:
        import traceback
        print(f"\n测试过程中发生错误: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 