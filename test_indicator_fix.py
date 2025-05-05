#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify the fix for NaN warnings in technical indicators
"""

import sys
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QApplication
from visual_stock_system import VisualStockSystem
import traceback

# 配置
TOKEN = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
TEST_STOCK = '000001.SZ'  # 平安银行

def test_technical_indicators(visual_system):
    """测试技术指标计算，确认不再有NaN警告"""
    print("开始测试技术指标计算...")
    
    # 获取股票数据
    print(f"正在获取{TEST_STOCK}的股票数据...")
    df = visual_system.get_stock_data(TEST_STOCK)
    
    if df is None or df.empty:
        print(f"获取{TEST_STOCK}数据失败")
        return False
    
    print(f"成功获取数据: {len(df)}行")
    
    # 检查数据
    print("股票数据样本:")
    print(df.head(3))
    
    # 记录原始stdout以捕获输出
    original_stdout = sys.stdout
    nan_warnings = []
    
    try:
        # 重定向stdout到字符串，捕获所有打印输出
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # 执行技术指标计算
        result_df = visual_system.analyze_momentum(df)
        
        # 恢复stdout
        sys.stdout = original_stdout
        
        # 检查是否有NaN相关警告
        output = captured_output.getvalue()
        for line in output.split('\n'):
            if '含有NaN值' in line:
                nan_warnings.append(line)
    
    except Exception as e:
        # 恢复stdout
        sys.stdout = original_stdout
        print(f"测试过程中出现错误: {str(e)}")
        return False
    finally:
        # 确保stdout被恢复
        sys.stdout = original_stdout
    
    # 检查结果
    if result_df is None:
        print("分析失败，返回None")
        return False
    
    print("\n技术指标计算结果:")
    for indicator in ['EMA21', 'MACD', 'MACD_Signal', 'MACD_Hist']:
        if indicator in result_df.columns:
            has_nan = result_df[indicator].isnull().any()
            print(f"  {indicator}: {'包含NaN值' if has_nan else '无NaN值'}")
    
    print("\nNaN警告数量:", len(nan_warnings))
    if nan_warnings:
        print("NaN警告:")
        for warning in nan_warnings:
            print(f"  {warning}")
        print("警告修复失败")
        return False
    else:
        print("没有NaN警告，修复成功!")
        return True

def test_volume_price(visual_system):
    """测试量价分析功能"""
    print("\n开始测试量价分析...")
    
    # 获取股票数据
    print(f"正在获取{TEST_STOCK}的股票数据...")
    df = visual_system.get_stock_data(TEST_STOCK)
    
    if df is None or len(df) == 0:
        print(f"获取{TEST_STOCK}数据失败")
        return False
    
    print(f"成功获取数据: {len(df)}行")
    
    # 记录原始stdout以捕获输出
    original_stdout = sys.stdout
    nan_warnings = []
    
    try:
        # 重定向stdout到字符串
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # 执行量价分析
        result_df = visual_system.analyze_volume_price(df)
        
        # 恢复stdout
        sys.stdout = original_stdout
        
        # 检查是否有NaN相关警告
        output = captured_output.getvalue()
        for line in output.split('\n'):
            if '含有NaN值' in line or 'NaN' in line:
                nan_warnings.append(line)
        
        # 检查结果
        if result_df is None:
            print("量价分析失败，返回None")
            return False
        
        # 确保有正确的维度和数据
        if len(result_df) != len(df):
            print(f"数据长度不匹配: 结果={len(result_df)}, 输入={len(df)}")
            return False
            
        # 检查关键指标是否存在
        key_indicators = ['Volume_Ratio', 'ATR', 'Trend_Strength', 'Volatility', 'Channel_Width']
        missing_indicators = [ind for ind in key_indicators if ind not in result_df.columns]
        if missing_indicators:
            print(f"缺少关键指标: {', '.join(missing_indicators)}")
            return False
        
        print("\n量价分析结果计算成功")
        print(f"输出数据形状: {result_df.shape}")
        print("主要指标样本:")
        for indicator in key_indicators:
            if indicator in result_df.columns:
                print(f"  * {indicator}: {result_df[indicator].iloc[-1]}")
        
        print("\nNaN警告数量:", len(nan_warnings))
        if nan_warnings:
            print("NaN警告:")
            for warning in nan_warnings:
                print(f"  {warning}")
            return False
        else:
            print("没有NaN警告，量价分析修复成功!")
            return True
    
    except Exception as e:
        # 恢复stdout
        sys.stdout = original_stdout
        print(f"测试过程中出现错误: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # 确保stdout被恢复
        sys.stdout = original_stdout

if __name__ == "__main__":
    print("===== 技术指标NaN警告修复测试 =====")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 初始化系统
    try:
        visual_system = VisualStockSystem(TOKEN, headless=True)
        print("成功初始化数据系统")
        
        # 测试技术指标
        indicators_success = test_technical_indicators(visual_system)
        
        # 测试量价分析
        volume_price_success = test_volume_price(visual_system)
        
        # 总结
        print("\n===== 测试结果 =====")
        print(f"技术指标测试: {'成功' if indicators_success else '失败'}")
        print(f"量价分析测试: {'成功' if volume_price_success else '失败'}")
        
        if indicators_success and volume_price_success:
            print("\n所有测试通过！技术指标NaN警告已成功修复。")
            print("系统现在可以使用真实数据提供准确的技术分析，不再产生NaN警告。")
        else:
            print("\n测试失败，需要进一步排查问题。")
        
        sys.exit(0 if indicators_success and volume_price_success else 1)
    except Exception as e:
        print(f"系统初始化失败: {str(e)}")
        sys.exit(1) 