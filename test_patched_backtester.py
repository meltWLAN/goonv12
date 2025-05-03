#!/usr/bin/env python
"""
自进化回测系统测试脚本
用于验证修复后的回测系统功能是否正常
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import traceback

def generate_test_data(days=100, use_chinese_columns=True):
    """生成测试数据"""
    print("生成测试数据...")
    
    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # 生成价格
    np.random.seed(42)  # 固定随机种子以便结果可复现
    price = 100  # 起始价格
    close_prices = [price]
    for i in range(1, len(date_range)):
        # 添加随机波动
        change = np.random.normal(0, 0.01)
        # 添加趋势
        trend = 0.0002 * (1 if i < len(date_range)/2 else -1)  # 先上升后下降
        price = price * (1 + change + trend)
        close_prices.append(price)
    
    # 生成其他数据
    open_prices = [p * (1 + np.random.normal(0, 0.003)) for p in close_prices]
    high_prices = [max(o, c) * (1 + abs(np.random.normal(0, 0.005))) for o, c in zip(open_prices, close_prices)]
    low_prices = [min(o, c) * (1 - abs(np.random.normal(0, 0.005))) for o, c in zip(open_prices, close_prices)]
    volumes = [max(100000 * (1 + np.random.normal(0, 0.2)), 10000) for _ in range(len(date_range))]
    
    # 使用中文列名或英文列名
    if use_chinese_columns:
        column_names = {'日期': date_range, '开盘': open_prices, '最高': high_prices, 
                        '最低': low_prices, '收盘': close_prices, '成交量': volumes}
    else:
        column_names = {'date': date_range, 'open': open_prices, 'high': high_prices, 
                        'low': low_prices, 'close': close_prices, 'volume': volumes}
    
    df = pd.DataFrame(column_names)
    
    # 设置日期为索引
    if use_chinese_columns:
        df.set_index('日期', inplace=True)
    else:
        df.set_index('date', inplace=True)
    
    # 添加技术指标
    close_col = '收盘' if use_chinese_columns else 'close'
    
    # 移动平均线
    df['MA5'] = df[close_col].rolling(window=5).mean()
    df['MA10'] = df[close_col].rolling(window=10).mean()
    df['MA20'] = df[close_col].rolling(window=20).mean()
    
    # MACD
    ema12 = df[close_col].ewm(span=12).mean()
    ema26 = df[close_col].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df

def test_extract_features():
    """测试特征提取功能"""
    print("\n测试特征提取功能...")
    try:
        from evolving_backtester_part2 import EvolvingBacktester
        
        backtester = EvolvingBacktester()
        
        # 创建中文列名数据
        chinese_data = generate_test_data(use_chinese_columns=True)
        print("中文列名数据示例:")
        print(chinese_data.columns.tolist())
        
        # 测试特征提取
        mid_index = len(chinese_data) // 2
        features = backtester.extract_features(chinese_data, mid_index)
        
        if not features:
            print("❌ 特征提取失败，返回空字典")
            return False
            
        print("✓ 成功从中文列名数据中提取特征")
        print(f"  提取到 {len(features)} 个特征: {', '.join(features.keys())}")
        
        # 创建英文列名数据
        english_data = generate_test_data(use_chinese_columns=False)
        print("\n英文列名数据示例:")
        print(english_data.columns.tolist())
        
        # 测试特征提取
        features = backtester.extract_features(english_data, mid_index)
        
        if not features:
            print("❌ 特征提取失败，返回空字典")
            return False
            
        print("✓ 成功从英文列名数据中提取特征")
        print(f"  提取到 {len(features)} 个特征: {', '.join(features.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试特征提取时出错: {str(e)}")
        traceback.print_exc()
        return False

def test_position_calculation():
    """测试仓位计算功能"""
    print("\n测试仓位计算功能...")
    try:
        from evolving_backtester_part2 import EvolvingBacktester
        
        backtester = EvolvingBacktester()
        
        # 创建测试数据
        data = generate_test_data()
        mid_index = len(data) // 2
        features = backtester.extract_features(data, mid_index)
        
        # 测试仓位计算
        signal_strength = 0.8
        price = 100.0
        stop_loss = 95.0
        
        position = backtester.calculate_position_size(features, signal_strength, price, stop_loss)
        
        if not isinstance(position, float):
            print(f"❌ 仓位计算返回类型不正确: {type(position).__name__}，应该为 float")
            return False
            
        print(f"✓ 仓位计算成功，返回值: {position:.4f} (类型: {type(position).__name__})")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试仓位计算时出错: {str(e)}")
        traceback.print_exc()
        return False

def test_backtest_execution():
    """测试回测执行功能"""
    print("\n测试回测执行功能...")
    try:
        from evolving_backtester_part2 import EvolvingBacktester
        from evolving_backtester_integration import run_backtest
        
        # 创建测试数据
        data = generate_test_data()
        
        # 1. 直接使用EvolvingBacktester
        print("1. 测试EvolvingBacktester.backtest_macd_strategy...")
        backtester = EvolvingBacktester(initial_capital=100000.0, learning_mode=True)
        
        if not hasattr(backtester, 'backtest_macd_strategy'):
            print("❌ EvolvingBacktester 没有 backtest_macd_strategy 方法")
            return False
            
        result = backtester.backtest_macd_strategy(data, "TEST")
        
        if result is None:
            print("❌ 回测执行失败，返回None")
            return False
            
        print(f"✓ 回测执行成功，总收益率: {result.total_profit:.2f}%，交易次数: {result.trade_count}")
        
        # 2. 使用集成函数
        print("\n2. 测试run_backtest集成函数...")
        result_dict = run_backtest(
            stock_code="TEST",
            stock_data=data,
            strategy="MACD金叉策略",
            start_date=(datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            initial_capital=100000.0,
            mode="evolving",
            learning_mode=True
        )
        
        if not result_dict.get('success', False):
            print(f"❌ 集成回测失败: {result_dict.get('error', '未知错误')}")
            return False
            
        print(f"✓ 集成回测执行成功，总收益率: {result_dict.get('total_return', 0):.2f}%")
        
        # 3. 测试图表生成
        if 'chart_files' in result_dict:
            print(f"✓ 生成了 {len(result_dict['chart_files'])} 个图表:")
            for chart in result_dict['chart_files']:
                print(f"  • {chart}")
                # 检查文件是否存在且有效
                if os.path.exists(chart) and os.path.getsize(chart) > 0:
                    print(f"  ✓ 图表有效")
                else:
                    print(f"  ❌ 图表无效或不存在")
        else:
            print("⚠️ 未生成图表")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试回测执行时出错: {str(e)}")
        traceback.print_exc()
        return False

def run_tests():
    """运行所有测试"""
    print("==== 自进化回测系统测试 ====\n")
    
    # 检查必要目录是否存在
    needed_dirs = ['./ml_models', './backtest_charts']
    for directory in needed_dirs:
        if not os.path.exists(directory):
            print(f"创建目录: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    # 运行测试
    tests = [
        ("特征提取测试", test_extract_features),
        ("仓位计算测试", test_position_calculation),
        ("回测执行测试", test_backtest_execution)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n==== 运行 {test_name} ====")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # 输出结果摘要
    print("\n==== 测试结果摘要 ====")
    passed = 0
    for test_name, result in results:
        status = "通过 ✓" if result else "失败 ❌"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("\n所有测试通过！自进化回测系统已修复并正常工作。")
    else:
        print("\n部分测试失败，可能需要更多修复。")
    
if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        traceback.print_exc()
    
    input("\n按回车键退出...") 