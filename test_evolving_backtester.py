import unittest
import pandas as pd
import numpy as np
import os
import shutil
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免在无GUI环境下出错
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import logging
import json

# 导入被测试模块
from evolving_backtester import ModelManager
from evolving_backtester_part2 import EvolvingBacktester, AdvancedBacktestResult
from evolving_backtester_integration import run_backtest, visualize_backtest_results, SmartBacktesterFactory

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BacktesterTest')

def generate_mock_data(days=100, volatility=0.01):
    """生成模拟股票数据用于测试"""
    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # 生成价格
    price = 100  # 起始价格
    close_prices = [price]
    for i in range(1, len(date_range)):
        # 添加随机波动
        change = np.random.normal(0, volatility)
        # 添加趋势
        trend = 0.0002 * (1 if i < len(date_range)/2 else -1)  # 先上升后下降
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
    
    # 设置索引
    df.set_index('日期', inplace=True)
    return df

class TestModelManager(unittest.TestCase):
    """测试ModelManager类的功能"""
    
    def setUp(self):
        """准备测试环境"""
        self.test_dir = "./test_models"
        os.makedirs(self.test_dir, exist_ok=True)
        self.model_manager = ModelManager(models_dir=self.test_dir)
        
        # 准备测试数据
        np.random.seed(42)  # 设置随机种子以保证可重复性
        n_samples = 100
        self.X_entry = np.random.rand(n_samples, 5)
        self.y_entry = np.random.randint(0, 2, n_samples)
        self.X_exit = np.random.rand(n_samples, 5)
        self.y_exit = np.random.randint(0, 2, n_samples)
        self.X_position = np.random.rand(n_samples, 5)
        self.y_position = np.random.rand(n_samples)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_train_entry_model(self):
        """测试入场模型训练"""
        result = self.model_manager.train_entry_model(self.X_entry, self.y_entry)
        self.assertIsNotNone(result)
        self.assertIn('accuracy', result)
        self.assertIn('precision', result)
        self.assertIn('recall', result)
        self.assertIn('f1', result)
        self.assertIsNotNone(self.model_manager.models['entry'])
        self.assertIn('entry', self.model_manager.scalers)
    
    def test_train_exit_model(self):
        """测试出场模型训练"""
        result = self.model_manager.train_exit_model(self.X_exit, self.y_exit)
        self.assertIsNotNone(result)
        self.assertIn('accuracy', result)
        self.assertIn('precision', result)
        self.assertIn('recall', result)
        self.assertIn('f1', result)
        self.assertIsNotNone(self.model_manager.models['exit'])
        self.assertIn('exit', self.model_manager.scalers)
    
    def test_train_position_model(self):
        """测试仓位模型训练"""
        result = self.model_manager.train_position_model(self.X_position, self.y_position)
        self.assertIsNotNone(result)
        self.assertIn('rmse', result)
        self.assertIsNotNone(self.model_manager.models['position'])
        self.assertIn('position', self.model_manager.scalers)
    
    def test_save_load_models(self):
        """测试模型保存和加载"""
        # 训练并保存模型
        self.model_manager.train_entry_model(self.X_entry, self.y_entry)
        self.model_manager.save_models()
        
        # 检查文件是否创建
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "entry_model.pkl")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "entry_scaler.pkl")))
        
        # 创建新的ModelManager并加载模型
        new_manager = ModelManager(models_dir=self.test_dir)
        self.assertIsNotNone(new_manager.models['entry'])
        self.assertIn('entry', new_manager.scalers)
    
    def test_prediction_functions(self):
        """测试预测功能"""
        # 先训练模型
        self.model_manager.train_entry_model(self.X_entry, self.y_entry)
        self.model_manager.train_exit_model(self.X_exit, self.y_exit)
        self.model_manager.train_position_model(self.X_position, self.y_position)
        
        # 测试预测
        features = np.random.rand(5)
        entry_prob = self.model_manager.predict_entry_signal(features)
        exit_prob = self.model_manager.predict_exit_signal(features)
        position_size = self.model_manager.predict_position_size(features)
        
        self.assertIsInstance(entry_prob, float)
        self.assertIsInstance(exit_prob, float)
        self.assertIsInstance(position_size, float)
        self.assertTrue(0 <= entry_prob <= 1)
        self.assertTrue(0 <= exit_prob <= 1)
        self.assertTrue(0 <= position_size <= 0.5)

class TestEvolvingBacktester(unittest.TestCase):
    """测试EvolvingBacktester类的功能"""
    
    def setUp(self):
        """准备测试环境"""
        self.test_dir = "./test_backtester"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 创建回测器实例
        self.backtester = EvolvingBacktester(initial_capital=100000.0, learning_mode=True)
        
        # 生成测试数据
        self.stock_data = generate_mock_data(days=100)
        self.stock_code = "000001.SZ"
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_detect_market_regime(self):
        """测试市场状态检测"""
        regime = self.backtester.detect_market_regime(self.stock_data)
        self.assertIsInstance(regime, str)
        self.assertIn(regime, ["bullish", "bearish", "volatile", "sideways", "unknown"])
    
    def test_extract_features(self):
        """测试特征提取"""
        # 获取一个中间索引
        mid_index = len(self.stock_data) // 2
        features = self.backtester.extract_features(self.stock_data, mid_index)
        
        self.assertIsInstance(features, dict)
        # 检查关键特征是否存在
        expected_features = ['close', 'ma5', 'ma20', 'rsi', 'macd', 'volume_ratio']
        for feature in expected_features:
            self.assertIn(feature, features)
    
    def test_evaluate_entry_signal(self):
        """测试入场信号评估"""
        # 提取特征
        mid_index = len(self.stock_data) // 2
        features = self.backtester.extract_features(self.stock_data, mid_index)
        
        # 评估信号
        strategy_signal = 0.7  # 模拟策略给出的信号
        result = self.backtester.evaluate_entry_signal(features, strategy_signal)
        
        self.assertIsInstance(result, float)
        self.assertTrue(0 <= result <= 1)
    
    def test_evaluate_exit_signal(self):
        """测试出场信号评估"""
        # 提取特征
        mid_index = len(self.stock_data) // 2
        features = self.backtester.extract_features(self.stock_data, mid_index)
        
        # 评估信号
        strategy_signal = 0.6  # 模拟策略给出的信号
        result = self.backtester.evaluate_exit_signal(features, strategy_signal)
        
        self.assertIsInstance(result, float)
        self.assertTrue(0 <= result <= 1)
    
    def test_calculate_position_size(self):
        """测试仓位大小计算"""
        # 提取特征
        mid_index = len(self.stock_data) // 2
        features = self.backtester.extract_features(self.stock_data, mid_index)
        
        # 计算仓位
        signal_strength = 0.8
        price = self.stock_data.iloc[mid_index]['收盘']
        stop_loss = price * 0.95
        
        result = self.backtester.calculate_position_size(features, signal_strength, price, stop_loss)
        
        self.assertIsInstance(result, float)
        self.assertTrue(0 <= result <= 1)

class TestIntegration(unittest.TestCase):
    """测试集成功能"""
    
    def setUp(self):
        """准备测试环境"""
        self.test_dir = "./test_integration"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 生成测试数据
        self.stock_data = generate_mock_data(days=100)
        self.stock_code = "000001.SZ"
        self.start_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists("backtest_charts"):
            shutil.rmtree("backtest_charts")
        if os.path.exists("ml_models"):
            shutil.rmtree("ml_models")
    
    def test_factory_create_backtester(self):
        """测试工厂创建回测器"""
        # 测试创建标准回测器
        standard_backtester = SmartBacktesterFactory.create_backtester(mode="standard", initial_capital=100000.0)
        self.assertIsNotNone(standard_backtester)
        
        # 测试创建自进化回测器
        evolving_backtester = SmartBacktesterFactory.create_backtester(mode="evolving", initial_capital=100000.0)
        self.assertIsNotNone(evolving_backtester)
    
    def test_run_backtest(self):
        """测试执行回测"""
        # 测试标准回测
        standard_result = run_backtest(
            stock_code=self.stock_code,
            stock_data=self.stock_data,
            strategy='MACD金叉策略',
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=100000.0,
            mode='standard',
            learning_mode=False
        )
        
        self.assertTrue(standard_result['success'])
        self.assertEqual(standard_result['stock_code'], self.stock_code)
        self.assertIn('total_return', standard_result)
        self.assertIn('win_rate', standard_result)
        
        # 测试自进化回测
        evolving_result = run_backtest(
            stock_code=self.stock_code,
            stock_data=self.stock_data,
            strategy='MACD金叉策略',
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=100000.0,
            mode='evolving',
            learning_mode=True
        )
        
        self.assertTrue(evolving_result['success'])
        self.assertEqual(evolving_result['stock_code'], self.stock_code)
        self.assertIn('total_return', evolving_result)
        self.assertIn('win_rate', evolving_result)
        self.assertIn('ml_metrics', evolving_result)
        
        # 检查是否生成图表
        if 'chart_files' in evolving_result:
            for chart_file in evolving_result['chart_files']:
                self.assertTrue(os.path.exists(chart_file))
    
    def test_visualize_backtest_results(self):
        """测试回测结果可视化"""
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
        
        # 生成图表
        chart_files = visualize_backtest_results(mock_result, self.stock_code, 'MACD金叉策略')
        
        # 检查生成的图表
        self.assertGreaterEqual(len(chart_files), 1)
        for chart_file in chart_files:
            self.assertTrue(os.path.exists(chart_file))
            self.assertTrue(os.path.getsize(chart_file) > 0)

class TestPerformance(unittest.TestCase):
    """测试系统性能"""
    
    def setUp(self):
        """准备测试环境"""
        # 生成较大的测试数据用于性能测试
        self.stock_data = generate_mock_data(days=300)
        self.stock_code = "000001.SZ"
        self.start_date = (datetime.now() - timedelta(days=300)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists("backtest_charts"):
            shutil.rmtree("backtest_charts")
        if os.path.exists("ml_models"):
            shutil.rmtree("ml_models")
    
    def test_performance_standard_backtest(self):
        """测试标准回测性能"""
        start_time = time.time()
        
        result = run_backtest(
            stock_code=self.stock_code,
            stock_data=self.stock_data,
            strategy='MACD金叉策略',
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=100000.0,
            mode='standard',
            learning_mode=False
        )
        
        duration = time.time() - start_time
        logger.info(f"标准回测执行时间: {duration:.2f}秒")
        
        self.assertTrue(result['success'])
        self.assertTrue(duration < 60)  # 确保执行时间在合理范围内
    
    def test_performance_evolving_backtest(self):
        """测试自进化回测性能"""
        start_time = time.time()
        
        result = run_backtest(
            stock_code=self.stock_code,
            stock_data=self.stock_data,
            strategy='MACD金叉策略',
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=100000.0,
            mode='evolving',
            learning_mode=True
        )
        
        duration = time.time() - start_time
        logger.info(f"自进化回测执行时间: {duration:.2f}秒")
        
        self.assertTrue(result['success'])
        self.assertTrue(duration < 120)  # 考虑到机器学习计算，允许更长的时间

class TestMultipleStrategies(unittest.TestCase):
    """测试不同策略的回测功能"""
    
    def setUp(self):
        """准备测试环境"""
        self.stock_data = generate_mock_data(days=100)
        self.stock_code = "000001.SZ"
        self.start_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.strategies = [
            'MACD金叉策略', 
            'KDJ金叉策略', 
            '双均线策略', 
            '布林带策略', 
            '量价策略'
        ]
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists("backtest_charts"):
            shutil.rmtree("backtest_charts")
        if os.path.exists("ml_models"):
            shutil.rmtree("ml_models")
    
    def test_all_strategies(self):
        """测试所有策略"""
        results = {}
        
        for strategy in self.strategies:
            result = run_backtest(
                stock_code=self.stock_code,
                stock_data=self.stock_data,
                strategy=strategy,
                start_date=self.start_date,
                end_date=self.end_date,
                initial_capital=100000.0,
                mode='evolving',
                learning_mode=True
            )
            
            self.assertTrue(result['success'])
            results[strategy] = {
                'total_return': result['total_return'],
                'win_rate': result['win_rate'],
                'sharpe_ratio': result.get('sharpe_ratio', 0)
            }
            
        # 保存策略比较结果
        with open('strategy_comparison.json', 'w') as f:
            json.dump(results, f, indent=4)
            
        logger.info(f"策略比较结果已保存到 strategy_comparison.json")

# 主测试入口
if __name__ == '__main__':
    # 运行所有测试
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite([
        test_loader.loadTestsFromTestCase(TestModelManager),
        test_loader.loadTestsFromTestCase(TestEvolvingBacktester),
        test_loader.loadTestsFromTestCase(TestIntegration),
        test_loader.loadTestsFromTestCase(TestPerformance),
        test_loader.loadTestsFromTestCase(TestMultipleStrategies)
    ])
    
    # 使用TextTestRunner运行测试
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # 输出测试总结
    total_tests = test_result.testsRun
    failures = len(test_result.failures)
    errors = len(test_result.errors)
    passed = total_tests - failures - errors
    
    print("\n=====================")
    print("测试结果总结")
    print("=====================")
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {failures}")
    print(f"错误测试: {errors}")
    print(f"通过率: {(passed/total_tests)*100:.2f}%")
    print("=====================") 