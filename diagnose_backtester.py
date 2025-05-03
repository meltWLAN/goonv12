import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
import matplotlib.pyplot as plt
import json

# 检查必要的模块是否可用
required_modules = [
    'scikit-learn', 'joblib', 'matplotlib', 'pandas', 'numpy'
]

print("==== 检查依赖模块 ====")
missing_modules = []
for module in required_modules:
    try:
        __import__(module)
        print(f"✓ {module} 已安装")
    except ImportError:
        missing_modules.append(module)
        print(f"✗ {module} 未安装")

if missing_modules:
    print(f"\n需要安装以下模块: {', '.join(missing_modules)}")
    print("请运行: pip install " + " ".join(missing_modules))
else:
    print("所有依赖模块已正确安装")

# 检查文件是否存在
print("\n==== 检查系统文件 ====")
required_files = [
    'evolving_backtester.py',
    'evolving_backtester_part2.py',
    'evolving_backtester_integration.py',
    'enhanced_backtesting.py'
]

for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file} 存在")
    else:
        print(f"✗ {file} 不存在")

# 生成诊断模拟数据
def generate_mock_data(days=100):
    """生成模拟股票数据用于诊断"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # 生成价格
    np.random.seed(42)  # 固定随机种子以便重复
    price = 100
    close_prices = [price]
    for i in range(1, len(date_range)):
        change = np.random.normal(0, 0.01)
        trend = 0.0002 * (1 if i < len(date_range)/2 else -1)
        price = price * (1 + change + trend)
        close_prices.append(price)
    
    # 生成其他数据
    open_prices = [p * (1 + np.random.normal(0, 0.003)) for p in close_prices]
    high_prices = [max(o, c) * (1 + abs(np.random.normal(0, 0.005))) for o, c in zip(open_prices, close_prices)]
    low_prices = [min(o, c) * (1 - abs(np.random.normal(0, 0.005))) for o, c in zip(open_prices, close_prices)]
    volumes = [max(100000 * (1 + np.random.normal(0, 0.2)), 10000) for _ in range(len(date_range))]
    
    # 使用中文列名以匹配原系统
    df = pd.DataFrame({
        '日期': date_range,
        '开盘': open_prices,
        '最高': high_prices,
        '最低': low_prices,
        '收盘': close_prices,
        '成交量': volumes
    })
    
    # 添加技术指标
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    
    # MACD
    ema12 = df['收盘'].ewm(span=12).mean()
    ema26 = df['收盘'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # KDJ
    low_list = df['最低'].rolling(9, min_periods=9).min()
    high_list = df['最高'].rolling(9, min_periods=9).max()
    rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
    df['K'] = pd.DataFrame(rsv).ewm(com=2).mean()
    df['D'] = pd.DataFrame(df['K']).ewm(com=2).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    # 设置索引
    df.set_index('日期', inplace=True)
    return df

print("\n==== 诊断 ModelManager 组件 ====")
try:
    from evolving_backtester import ModelManager
    model_manager = ModelManager(models_dir="./test_models")
    print("✓ ModelManager 初始化成功")
    
    # 简单测试特征缩放器
    X = np.random.rand(10, 5)
    y = np.random.randint(0, 2, 10)
    
    try:
        result = model_manager.train_entry_model(X, y)
        print("✓ 入场模型训练成功")
        print(f"  - 准确率: {result['accuracy']:.4f}")
    except Exception as e:
        print(f"✗ 入场模型训练失败: {str(e)}")
        traceback.print_exc()
    
    # 检查预测功能
    try:
        features = np.random.rand(5)
        prob = model_manager.predict_entry_signal(features)
        print(f"✓ 预测入场信号成功: {prob:.4f}")
    except Exception as e:
        print(f"✗ 预测入场信号失败: {str(e)}")
        traceback.print_exc()
        
except ImportError:
    print("✗ 无法导入 ModelManager")
except Exception as e:
    print(f"✗ ModelManager 测试失败: {str(e)}")
    traceback.print_exc()

print("\n==== 诊断 EvolvingBacktester 组件 ====")
try:
    from evolving_backtester_part2 import EvolvingBacktester
    backtester = EvolvingBacktester(initial_capital=100000.0, learning_mode=True)
    print("✓ EvolvingBacktester 初始化成功")
    
    # 生成测试数据
    test_data = generate_mock_data(days=50)
    print(f"✓ 生成测试数据成功，行数: {len(test_data)}")
    
    # 测试市场状态检测
    try:
        regime = backtester.detect_market_regime(test_data)
        print(f"✓ 市场状态检测成功: {regime}")
    except Exception as e:
        print(f"✗ 市场状态检测失败: {str(e)}")
        traceback.print_exc()
    
    # 测试特征提取
    try:
        mid_index = len(test_data) // 2
        features = backtester.extract_features(test_data, mid_index)
        print(f"✓ 特征提取成功，特征数量: {len(features)}")
        print(f"  - 特征列表: {', '.join(features.keys())}")
    except Exception as e:
        print(f"✗ 特征提取失败: {str(e)}")
        traceback.print_exc()
    
    # 测试信号评估
    if 'features' in locals() and features:
        try:
            entry_signal = backtester.evaluate_entry_signal(features, 0.7)
            exit_signal = backtester.evaluate_exit_signal(features, 0.6)
            print(f"✓ 信号评估成功: 入场={entry_signal:.4f}, 出场={exit_signal:.4f}")
        except Exception as e:
            print(f"✗ 信号评估失败: {str(e)}")
            traceback.print_exc()
    
    # 测试仓位计算
    if 'features' in locals() and features:
        try:
            price = test_data.iloc[mid_index]['收盘']
            stop_loss = price * 0.95
            position = backtester.calculate_position_size(features, 0.8, price, stop_loss)
            print(f"✓ 仓位计算成功: {position}")
            
            # 检查仓位类型
            if not isinstance(position, float):
                print(f"! 警告: 仓位计算返回类型为 {type(position).__name__}，应该为 float")
                print("  - 建议修改 calculate_position_size 方法，确保返回类型为 float")
        except Exception as e:
            print(f"✗ 仓位计算失败: {str(e)}")
            traceback.print_exc()
    
except ImportError:
    print("✗ 无法导入 EvolvingBacktester")
except Exception as e:
    print(f"✗ EvolvingBacktester 测试失败: {str(e)}")
    traceback.print_exc()

print("\n==== 诊断 visualize_backtest_results 功能 ====")
try:
    from evolving_backtester_integration import visualize_backtest_results
    
    # 准备测试数据
    mock_result = {
        'total_return': 15.5,
        'annual_return': 8.2,
        'max_drawdown': 5.3,
        'sharpe_ratio': 1.2,
        'win_rate': 65.0,
        'profit_ratio': 2.1,
        'capital_curve': [100000, 101000, 103000, 102000, 105000, 110000, 115500],
        'ml_metrics': {
            'entry_model_accuracy': 0.72,
            'exit_model_accuracy': 0.68,
            'position_model_rmse': 0.15,
            'market_regimes': {
                'bullish': 45.0,
                'bearish': 15.0,
                'sideways': 30.0,
                'volatile': 10.0
            }
        },
        'strategy_adaptation_score': 7.5
    }
    
    chart_files = visualize_backtest_results(mock_result, "000001.SZ", "MACD金叉策略", save_path="./test_charts")
    print(f"✓ 可视化功能测试成功，生成图表数量: {len(chart_files)}")
    for chart in chart_files:
        print(f"  - {chart}")
    
    # 检查图表是否存在且有效
    for chart in chart_files:
        if os.path.exists(chart):
            if os.path.getsize(chart) > 0:
                print(f"✓ 图表有效: {chart}")
            else:
                print(f"✗ 图表大小为零: {chart}")
        else:
            print(f"✗ 图表不存在: {chart}")
    
except ImportError:
    print("✗ 无法导入 visualize_backtest_results")
except Exception as e:
    print(f"✗ 可视化功能测试失败: {str(e)}")
    traceback.print_exc()

print("\n==== 诊断 run_backtest 功能 ====")
try:
    from evolving_backtester_integration import run_backtest
    
    # 准备测试数据
    test_data = generate_mock_data(days=30)
    
    standard_result = None
    
    try:
        # 测试标准回测
        standard_result = run_backtest(
            stock_code="000001.SZ",
            stock_data=test_data,
            strategy="MACD金叉策略",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            initial_capital=100000.0,
            mode="standard",
            learning_mode=False
        )
        
        if standard_result.get('success', False):
            print("✓ 标准回测成功")
            print(f"  - 总收益率: {standard_result.get('total_return', 0):.2f}%")
            print(f"  - 胜率: {standard_result.get('win_rate', 0):.2f}%")
        else:
            print(f"✗ 标准回测失败: {standard_result.get('error', '未知错误')}")
    except Exception as e:
        print(f"✗ 标准回测出错: {str(e)}")
        traceback.print_exc()
    
    try:
        # 测试自进化回测
        evolving_result = run_backtest(
            stock_code="000001.SZ",
            stock_data=test_data,
            strategy="MACD金叉策略",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            initial_capital=100000.0,
            mode="evolving",
            learning_mode=True
        )
        
        if evolving_result.get('success', False):
            print("✓ 自进化回测成功")
            print(f"  - 总收益率: {evolving_result.get('total_return', 0):.2f}%")
            print(f"  - 胜率: {evolving_result.get('win_rate', 0):.2f}%")
            
            if 'ml_metrics' in evolving_result:
                print("  - ML指标可用")
            
            if 'chart_files' in evolving_result and evolving_result['chart_files']:
                print(f"  - 生成图表数量: {len(evolving_result['chart_files'])}")
        else:
            print(f"✗ 自进化回测失败: {evolving_result.get('error', '未知错误')}")
            # 保存错误信息以便进一步分析
            with open("evolving_backtest_error.json", "w") as f:
                json.dump(evolving_result, f, indent=4)
            print("  - 错误详情已保存至 evolving_backtest_error.json")
    except Exception as e:
        print(f"✗ 自进化回测出错: {str(e)}")
        traceback.print_exc()
    
except ImportError:
    print("✗ 无法导入 run_backtest")
except Exception as e:
    print(f"✗ 回测功能测试失败: {str(e)}")
    traceback.print_exc()

print("\n==== 生成修复建议 ====")
print("根据诊断结果，以下是可能需要修复的问题:")

print("1. 确认自进化回测器中的extract_features方法是否正确处理中文列名")
print("   - 检查代码是否使用'收盘'而非'close'作为列名")
print("   - 建议修改extract_features方法，确保能处理中文列名")

print("2. 确认calculate_position_size方法返回float类型")
print("   - 当前可能返回其他类型数据，需修改为返回float类型")

print("3. 检查run_backtest在evolving模式下的错误")
print("   - 可能是由于EvolvingBacktester类中的方法未正确实现导致")
print("   - 建议检查回测日志和错误堆栈以进一步定位问题")

print("4. 确保模型目录存在并有写入权限")
print("   - 创建ml_models目录并确保有写入权限")

print("\n==== 修复方案 ====")
print("1. 创建所需目录:")
print("   mkdir -p ml_models backtest_charts")

print("2. 检查列名处理:")
print("   - 修改evolving_backtester_part2.py，搜索extract_features方法")
print("   - 确保正确处理中文列名")

print("3. 修复calculate_position_size返回类型:")
print("   - 确保此方法返回float类型的值")

print("4. 检查并修复回测错误:")
print("   - 运行单个功能测试，逐步定位问题") 