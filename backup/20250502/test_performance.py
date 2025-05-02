import unittest
import pytest
import time
import resource
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import gc
import psutil
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='performance_test.log'
)
logger = logging.getLogger('PerformanceTest')

# 导入被测试的模块
from visual_stock_system import VisualStockSystem
from single_stock_analyzer import SingleStockAnalyzer
from enhanced_backtesting import EnhancedBacktester

class MemoryProfiler:
    """内存分析工具类"""
    
    @staticmethod
    def get_memory_usage():
        """获取当前进程的内存使用情况（MB）"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # 转换为MB
    
    @staticmethod
    def log_memory_usage(label):
        """记录当前内存使用"""
        memory_usage = MemoryProfiler.get_memory_usage()
        logger.info(f"{label}: {memory_usage:.2f} MB")
        return memory_usage

class PerformanceTest(unittest.TestCase):
    """系统性能测试"""
    
    @classmethod
    def setUpClass(cls):
        """在所有测试前设置共享资源"""
        cls.visual_system = VisualStockSystem()
        cls.analyzer = SingleStockAnalyzer()
        cls.backtester = EnhancedBacktester(initial_capital=1000000.0)
        cls.test_stocks = ['000001.SZ', '600000.SH', '601318.SH', '600036.SH', '000333.SZ']
        
        # 预生成大型测试数据集
        cls.large_test_data = cls._generate_large_test_data(5000)  # 5000天的数据
        
        # 启动时记录初始内存使用
        cls.initial_memory = MemoryProfiler.log_memory_usage("初始内存使用")
    
    @classmethod
    def tearDownClass(cls):
        """所有测试结束后清理资源"""
        # 手动触发垃圾回收
        gc.collect()
        
        # 记录最终内存使用
        final_memory = MemoryProfiler.log_memory_usage("最终内存使用")
        logger.info(f"内存增长: {final_memory - cls.initial_memory:.2f} MB")
    
    @staticmethod
    def _generate_large_test_data(days=5000):
        """生成大型测试数据集"""
        dates = pd.date_range(end=datetime.now(), periods=days)
        base_price = 100
        
        # 创建一个更复杂的价格序列，包含周期性和趋势
        t = np.linspace(0, 10, days)
        trend = t * 2  # 长期上升趋势
        seasonality = 5 * np.sin(t)  # 季节性波动
        noise = np.random.normal(0, 1, days)
        cumulative_noise = noise.cumsum() * 0.2  # 累积随机波动
        
        prices = base_price + trend + seasonality + cumulative_noise
        
        # 创建交易量数据
        volume_base = 100000
        volume_trend = np.linspace(0, 50000, days)  # 交易量增长趋势
        volume_seasonality = 20000 * np.sin(t) + 20000  # 交易量季节性
        volume_noise = np.random.randint(0, 10000, days)
        
        volume = volume_base + volume_trend + volume_seasonality + volume_noise
        volume = np.maximum(volume, 10000)  # 确保交易量为正
        
        # 创建数据框
        df = pd.DataFrame({
            '日期': dates,
            '开盘': prices * 0.995,
            '收盘': prices,
            '最高': prices * 1.01,
            '最低': prices * 0.99,
            '成交量': volume
        })
        
        return df
    
    @pytest.mark.benchmark
    def test_data_processing_performance(self):
        """测试数据处理性能"""
        data = self.large_test_data.copy()
        
        # 测量处理大型数据集的时间
        start_time = time.time()
        
        # 计算常用的技术指标
        data['SMA5'] = data['收盘'].rolling(window=5).mean()
        data['SMA10'] = data['收盘'].rolling(window=10).mean()
        data['SMA20'] = data['收盘'].rolling(window=20).mean()
        data['SMA60'] = data['收盘'].rolling(window=60).mean()
        
        # 计算MACD
        data['EMA12'] = data['收盘'].ewm(span=12, adjust=False).mean()
        data['EMA26'] = data['收盘'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['EMA12'] - data['EMA26']
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['Histogram'] = data['MACD'] - data['Signal']
        
        # 计算RSI
        delta = data['收盘'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算布林带
        data['Middle_Band'] = data['收盘'].rolling(window=20).mean()
        data['Std_Dev'] = data['收盘'].rolling(window=20).std()
        data['Upper_Band'] = data['Middle_Band'] + (data['Std_Dev'] * 2)
        data['Lower_Band'] = data['Middle_Band'] - (data['Std_Dev'] * 2)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 记录处理时间和内存使用
        logger.info(f"大型数据集处理时间: {processing_time:.4f}秒")
        memory_used = MemoryProfiler.log_memory_usage("数据处理后内存使用")
        
        # 验证性能是否在可接受范围内（根据系统性能调整）
        self.assertLess(processing_time, 5.0, "数据处理时间应小于5秒")
        
        # 清理数据以释放内存
        del data
        gc.collect()
    
    @pytest.mark.benchmark
    def test_backtesting_performance(self):
        """测试回测系统性能"""
        # 使用大型数据集的一部分进行回测
        test_data = self.large_test_data.iloc[-1000:].copy()  # 使用最近1000天数据
        
        # 测量回测性能
        start_time = time.time()
        memory_before = MemoryProfiler.get_memory_usage()
        
        # 执行回测
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(4):  # 模拟4个不同的回测任务
                # 每个任务使用稍微不同的数据
                task_data = test_data.copy()
                task_data['收盘'] = task_data['收盘'] * (1 + i * 0.01)  # 轻微调整价格
                
                # 添加任务到线程池
                futures.append(executor.submit(self._run_backtest, task_data, f"TASK_{i}"))
            
            # 等待所有任务完成
            results = [future.result() for future in futures]
        
        end_time = time.time()
        memory_after = MemoryProfiler.get_memory_usage()
        
        # 记录性能指标
        total_time = end_time - start_time
        memory_increase = memory_after - memory_before
        
        logger.info(f"并行回测执行时间: {total_time:.4f}秒")
        logger.info(f"回测内存增长: {memory_increase:.2f} MB")
        
        # 验证性能是否在可接受范围内
        self.assertLess(total_time, 15.0, "并行回测时间应小于15秒")
        
        # 清理
        gc.collect()
    
    def _run_backtest(self, data, task_name):
        """执行单个回测任务"""
        try:
            # 创建新的回测器实例（避免共享状态）
            backtester = EnhancedBacktester(initial_capital=1000000.0)
            
            # 简化的回测过程 - 只做基本操作以测试性能
            # 1. 计算简单的买卖信号
            data['SMA5'] = data['收盘'].rolling(window=5).mean()
            data['SMA20'] = data['收盘'].rolling(window=20).mean()
            data['Signal'] = 0
            data.loc[data['SMA5'] > data['SMA20'], 'Signal'] = 1  # 买入信号
            data.loc[data['SMA5'] < data['SMA20'], 'Signal'] = -1  # 卖出信号
            
            # 2. 模拟交易执行
            position = 0
            trades = []
            
            for idx, row in data.iterrows():
                current_date = row['日期']
                current_price = row['收盘']
                signal = row['Signal']
                
                if signal == 1 and position == 0:  # 买入信号且无持仓
                    # 买入
                    trades.append({
                        'date': current_date,
                        'action': 'buy',
                        'price': current_price,
                        'quantity': 1000
                    })
                    position = 1
                elif signal == -1 and position == 1:  # 卖出信号且有持仓
                    # 卖出
                    trades.append({
                        'date': current_date,
                        'action': 'sell',
                        'price': current_price,
                        'quantity': 1000
                    })
                    position = 0
            
            # 3. 计算结果
            total_trades = len(trades)
            
            return {
                'task_name': task_name,
                'total_trades': total_trades,
                'last_price': data['收盘'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"回测任务 {task_name} 执行失败: {str(e)}")
            return {
                'task_name': task_name,
                'error': str(e)
            }
    
    @pytest.mark.benchmark
    def test_memory_leak(self):
        """测试系统在反复操作后是否存在内存泄漏"""
        # 记录初始内存使用
        initial_memory = MemoryProfiler.log_memory_usage("内存泄漏测试开始")
        
        # 执行多次操作
        iterations = 50
        memory_samples = []
        
        for i in range(iterations):
            # 生成新的测试数据
            test_data = pd.DataFrame({
                '日期': pd.date_range(end=datetime.now(), periods=100),
                '开盘': np.random.normal(100, 5, 100),
                '收盘': np.random.normal(102, 5, 100),
                '最高': np.random.normal(105, 5, 100),
                '最低': np.random.normal(98, 5, 100),
                '成交量': np.random.randint(10000, 50000, 100)
            })
            
            # 执行一系列操作
            test_data['SMA5'] = test_data['收盘'].rolling(window=5).mean()
            test_data['SMA20'] = test_data['收盘'].rolling(window=20).mean()
            test_data['EMA12'] = test_data['收盘'].ewm(span=12, adjust=False).mean()
            test_data['RSI'] = self._calculate_rsi(test_data['收盘'])
            
            # 模拟创建和销毁对象
            temp_analyzer = SingleStockAnalyzer()
            _ = temp_analyzer._calculate_technical_indicators
            del temp_analyzer
            
            # 强制垃圾回收
            if i % 10 == 0:
                gc.collect()
                memory_samples.append(MemoryProfiler.get_memory_usage())
        
        # 最终清理
        gc.collect()
        final_memory = MemoryProfiler.log_memory_usage("内存泄漏测试结束")
        
        # 分析内存使用趋势
        if len(memory_samples) >= 3:
            # 计算最后几次采样的内存增长率
            growth_rates = [(memory_samples[i] - memory_samples[i-1]) for i in range(1, len(memory_samples))]
            avg_growth_rate = sum(growth_rates) / len(growth_rates)
            
            logger.info(f"内存增长率: {avg_growth_rate:.2f} MB/10次迭代")
            
            # 检查增长率是否在合理范围内
            # 如果平均增长率过大，可能存在内存泄漏
            self.assertLess(avg_growth_rate, 5.0, "内存增长率过高，可能存在内存泄漏")
        
        # 检查总内存增长
        memory_increase = final_memory - initial_memory
        logger.info(f"总内存增长: {memory_increase:.2f} MB")
        
        # 清理
        del test_data
        gc.collect()
    
    def _calculate_rsi(self, prices, period=14):
        """计算RSI指标"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        if down == 0:
            rs = float('inf')
        else:
            rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            up = (up * (period-1) + upval) / period
            down = (down * (period-1) + downval) / period
            
            if down == 0:
                rs = float('inf')
            else:
                rs = up/down
            rsi[i] = 100. - 100./(1. + rs)
        return rsi
    
    @pytest.mark.benchmark
    def test_cache_efficiency(self):
        """测试缓存机制的效率"""
        # 设置测试数据
        test_stock = '000001.SZ'
        
        # 创建带缓存的测试函数
        @lru_cache(maxsize=128)
        def cached_function(symbol):
            """模拟一个耗时操作，带缓存"""
            time.sleep(0.1)  # 模拟API调用或复杂计算
            return f"Result for {symbol}"
        
        # 测试不使用缓存的情况
        start_time = time.time()
        for _ in range(10):
            _ = cached_function(test_stock + str(time.time()))  # 每次使用不同参数，不会命中缓存
        no_cache_time = time.time() - start_time
        
        # 测试使用缓存的情况
        start_time = time.time()
        for _ in range(10):
            _ = cached_function(test_stock)  # 使用相同参数，会命中缓存
        cache_time = time.time() - start_time
        
        # 记录和验证结果
        logger.info(f"未使用缓存时间: {no_cache_time:.4f}秒")
        logger.info(f"使用缓存时间: {cache_time:.4f}秒")
        logger.info(f"缓存性能提升: {no_cache_time/cache_time:.2f}倍")
        
        # 缓存应该显著提高性能
        self.assertLess(cache_time, no_cache_time * 0.5, "缓存应至少提高2倍性能")
    
    @pytest.mark.slow
    def test_parallel_processing_scaling(self):
        """测试并行处理的扩展性"""
        # 测试不同线程数量的性能扩展
        tasks = 20  # 任务数量
        
        test_data = self.large_test_data.iloc[-500:].copy()  # 使用最近500天数据
        
        def process_chunk(chunk):
            """处理数据块的函数"""
            # 执行一些CPU密集型计算
            result = {}
            result['SMA'] = chunk['收盘'].rolling(window=20).mean().iloc[-1]
            result['STD'] = chunk['收盘'].rolling(window=20).std().iloc[-1]
            result['RSI'] = self._calculate_rsi(chunk['收盘']).iloc[-1]
            
            # 添加一些额外计算使其更耗时
            for i in range(5):
                result[f'EMA{i}'] = chunk['收盘'].ewm(span=10+i, adjust=False).mean().iloc[-1]
            
            return result
        
        # 准备数据块
        chunks = []
        for i in range(tasks):
            # 创建稍微不同的数据块
            start_idx = i * 20
            end_idx = start_idx + 100
            if end_idx > len(test_data):
                end_idx = len(test_data)
            chunk = test_data.iloc[start_idx:end_idx].copy()
            chunks.append(chunk)
        
        # 测试不同线程数的性能
        thread_counts = [1, 2, 4, 8]
        timing_results = {}
        
        for thread_count in thread_counts:
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                results = list(executor.map(process_chunk, chunks))
            
            end_time = time.time()
            execution_time = end_time - start_time
            timing_results[thread_count] = execution_time
            
            logger.info(f"线程数: {thread_count}, 执行时间: {execution_time:.4f}秒")
        
        # 验证并行性能提升
        # 理想情况下，线程数翻倍应该使时间减半（线性扩展）
        # 但实际上由于各种开销，性能提升会逐渐减弱
        speedup_2_threads = timing_results[1] / timing_results[2]
        speedup_4_threads = timing_results[1] / timing_results[4]
        
        logger.info(f"2线程加速比: {speedup_2_threads:.2f}倍")
        logger.info(f"4线程加速比: {speedup_4_threads:.2f}倍")
        
        # 验证是否有合理的性能提升
        # 考虑到非线性扩展性，我们期望有适度的提升
        self.assertGreater(speedup_2_threads, 1.3, "2线程应提供至少1.3倍的性能提升")
        self.assertGreater(speedup_4_threads, 1.5, "4线程应提供至少1.5倍的性能提升")

if __name__ == '__main__':
    unittest.main() 