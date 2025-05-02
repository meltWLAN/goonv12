import unittest
import time
import pytest
import pandas as pd
from datetime import datetime, timedelta
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import sys
from unittest.mock import patch, MagicMock

# 添加当前目录到Python路径
sys.path.insert(0, '.')

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='api_stability_test.log')
logger = logging.getLogger('APIStabilityTest')

# 导入被测试模块
from visual_stock_system import VisualStockSystem
from single_stock_analyzer import SingleStockAnalyzer

class APIStabilityTest(unittest.TestCase):
    """测试股票API调用的稳定性和性能"""
    
    @classmethod
    def setUpClass(cls):
        """在所有测试前设置共享资源"""
        cls.system = VisualStockSystem()
        cls.analyzer = SingleStockAnalyzer()
        cls.test_stocks = ['000001.SZ', '600000.SH', '300750.SZ', '002415.SZ', '601318.SH']
        cls.time_metrics = {'get_stock_data': [], 'get_stock_name': [], 'analyze_stock': []}
        cls.api_failures = {'get_stock_data': 0, 'get_stock_name': 0, 'analyze_stock': 0}
        cls.lock = threading.Lock()
        
    def test_api_success_rate(self):
        """测试API调用成功率"""
        total_calls = 0
        successful_calls = 0
        
        # 测试获取股票名称
        for stock in self.test_stocks:
            try:
                total_calls += 1
                name = self.system.get_stock_name(stock)
                if name and name != stock:
                    successful_calls += 1
                else:
                    logger.warning(f"获取股票名称失败: {stock}")
            except Exception as e:
                logger.error(f"获取股票名称异常: {stock} - {str(e)}")
                
        # 测试获取股票数据
        for stock in self.test_stocks:
            try:
                total_calls += 1
                data = self.system.get_stock_data(stock, limit=30)
                if data is not None and not data.empty:
                    successful_calls += 1
                else:
                    logger.warning(f"获取股票数据失败: {stock}")
            except Exception as e:
                logger.error(f"获取股票数据异常: {stock} - {str(e)}")
                
        # 计算成功率
        success_rate = (successful_calls / total_calls) * 100 if total_calls > 0 else 0
        logger.info(f"API调用成功率: {success_rate:.2f}%")
        
        # 成功率应该大于80%
        self.assertGreaterEqual(success_rate, 80, "API调用成功率应大于80%")
                
    @pytest.mark.benchmark
    def test_api_response_time(self):
        """测试API响应时间"""
        response_times = []
        
        for stock in self.test_stocks:
            # 测试股票数据获取响应时间
            start_time = time.time()
            try:
                self.system.get_stock_data(stock, limit=30)
            except Exception:
                pass  # 忽略异常，仅测试响应时间
            end_time = time.time()
            elapsed = end_time - start_time
            response_times.append(elapsed)
            time.sleep(0.5)  # 避免请求过于频繁
            
        # 计算平均响应时间
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        logger.info(f"API平均响应时间: {avg_response_time:.2f}秒")
        
        # 响应时间应该在合理范围内
        self.assertLessEqual(avg_response_time, 2.0, "平均响应时间应该在2秒以内")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        # 对同一股票连续请求多次，检查数据是否一致
        stock = '600000.SH'
        results = []
        
        for _ in range(3):
            try:
                data = self.system.get_stock_data(stock, limit=30)
                if data is not None and not data.empty:
                    # 只保留收盘价的最后5个值用于比较
                    last_prices = data['close'].tail(5).tolist()
                    results.append(last_prices)
                time.sleep(1)  # 避免请求过于频繁
            except Exception as e:
                logger.error(f"数据一致性测试异常: {str(e)}")
                
        # 验证数据一致性
        if len(results) >= 2:
            for i in range(1, len(results)):
                pd.testing.assert_almost_equal(
                    results[0], results[i], 
                    decimal=2,  # 允许有小数点后两位的误差
                    err_msg="数据一致性检查失败"
                )
    
    def test_parallel_api_calls(self):
        """测试并行API调用的稳定性"""
        # 使用线程池并行调用API
        results = {'success': 0, 'failure': 0}
        
        def fetch_data(stock):
            try:
                data = self.system.get_stock_data(stock)
                if data is not None and not data.empty:
                    with self.lock:
                        results['success'] += 1
                else:
                    with self.lock:
                        results['failure'] += 1
            except Exception:
                with self.lock:
                    results['failure'] += 1
        
        # 准备更多的测试股票
        test_stocks = self.test_stocks * 2
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(fetch_data, test_stocks)
            
        # 检查成功率
        total = results['success'] + results['failure']
        success_rate = (results['success'] / total) * 100 if total > 0 else 0
        logger.info(f"并行API调用成功率: {success_rate:.2f}%")
        
        # 成功率应该在可接受范围内
        self.assertGreaterEqual(success_rate, 70, "并行API调用成功率应大于70%")
    
    def test_error_handling(self):
        """测试错误处理机制"""
        # 测试无效股票代码
        try:
            data = self.system.get_stock_data('INVALID')
            self.assertIsNone(data, "对于无效股票代码应该返回None")
        except ValueError as e:
            # 应该抛出值错误异常
            self.assertIn("股票代码格式错误", str(e))
        
        # 测试日期格式错误
        try:
            data = self.system.get_stock_data('000001.SZ', start_date='INVALID')
            self.assertIsNone(data, "对于无效日期应该返回None")
        except ValueError as e:
            # 应该抛出值错误异常
            self.assertIn("日期格式错误", str(e))
    
    @patch('akshare.stock_zh_a_hist')
    def test_retry_mechanism(self, mock_api):
        """测试重试机制"""
        # 模拟API失败后再成功的情况
        mock_api.side_effect = [
            Exception("API Error"),  # 第一次调用失败
            pd.DataFrame({  # 第二次调用成功
                '日期': pd.date_range(end=datetime.now(), periods=5),
                '开盘': [10.0] * 5,
                '收盘': [10.5] * 5,
                '最高': [11.0] * 5,
                '最低': [9.5] * 5,
                '成交量': [10000] * 5
            })
        ]
        
        # 尝试获取数据
        data = self.system.get_stock_data('000001.SZ')
        
        # 验证数据获取成功及API被调用次数
        self.assertIsNotNone(data)
        self.assertGreaterEqual(mock_api.call_count, 2)
    
    @pytest.mark.slow
    def test_long_running_api_stability(self):
        """测试长时间运行的API稳定性"""
        success_count = 0
        attempts = 10
        
        for i in range(attempts):
            try:
                # 轮流测试不同的股票
                stock = self.test_stocks[i % len(self.test_stocks)]
                data = self.system.get_stock_data(stock)
                if data is not None and not data.empty:
                    success_count += 1
                time.sleep(2)  # 每次请求间隔2秒
            except Exception as e:
                logger.error(f"长时间运行测试异常 ({i+1}/{attempts}): {str(e)}")
        
        # 计算成功率
        success_rate = (success_count / attempts) * 100
        logger.info(f"长时间运行API成功率: {success_rate:.2f}%")
        
        # 成功率应该大于80%
        self.assertGreaterEqual(success_rate, 80, "长时间运行API成功率应大于80%")

if __name__ == '__main__':
    unittest.main() 