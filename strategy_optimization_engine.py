#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union, Optional, Callable
from collections import defaultdict

from visual_stock_system import VisualStockSystem
from china_stock_provider import ChinaStockProvider
from enhanced_backtesting import EnhancedBacktester
from lazy_analyzer import LazyStockAnalyzer
from volume_price_strategy import VolumePriceStrategy

class StrategyOptimizationEngine:
    """
    策略优化引擎
    实现策略回测、参数优化和性能评估功能
    """
    
    def __init__(self, token=None, data_dir='./strategy_data'):
        """初始化策略优化引擎
        
        Args:
            token: API令牌
            data_dir: 数据目录
        """
        self.token = token
        self.data_dir = data_dir
        self.strategies_file = os.path.join(data_dir, 'strategies.json')
        self.optimization_file = os.path.join(data_dir, 'optimization_results.json')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化系统组件
        self.visual_system = VisualStockSystem(token, headless=True)
        self.data_provider = ChinaStockProvider(token)
        self.backtester = EnhancedBacktester(initial_capital=100000.0)
        
        # 初始化LazyStockAnalyzer
        self.lazy_analyzer = LazyStockAnalyzer(required_indicators=[
            'ma', 'ema', 'macd', 'rsi', 'kdj', 'volume_ratio', 'trend_direction'
        ])
        
        # 加载策略配置
        self.strategies = self._load_strategies()
        
        # 设置日志
        self._setup_logging()
        
        self.logger.info("策略优化引擎初始化完成")
    
    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('StrategyOptimizationEngine')
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        log_file = os.path.join(self.data_dir, 'strategy_optimization.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _load_strategies(self):
        """加载策略配置"""
        if os.path.exists(self.strategies_file):
            try:
                with open(self.strategies_file, 'r', encoding='utf-8') as f:
                    strategies = json.load(f)
                self.logger.info(f"成功加载策略配置，包含 {len(strategies)} 个策略")
                return strategies
            except Exception as e:
                self.logger.error(f"加载策略配置失败: {str(e)}")
                return self._create_default_strategies()
        else:
            self.logger.info("策略配置文件不存在，创建默认配置")
            return self._create_default_strategies()
    
    def _create_default_strategies(self):
        """创建默认策略配置"""
        default_strategies = {
            "volume_price": {
                "name": "量价策略",
                "description": "基于量价关系的交易策略",
                "parameters": {
                    "volume_threshold": 1.5,
                    "price_change_threshold": 0.02,
                    "ma_period": 20,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9
                },
                "optimization_ranges": {
                    "volume_threshold": {"min": 1.2, "max": 2.0, "step": 0.1},
                    "price_change_threshold": {"min": 0.01, "max": 0.05, "step": 0.01},
                    "ma_period": {"min": 10, "max": 30, "step": 5}
                },
                "class_name": "VolumePriceStrategy"
            },
            "moving_average_crossover": {
                "name": "均线交叉策略",
                "description": "基于快慢均线交叉的交易策略",
                "parameters": {
                    "fast_period": 5,
                    "slow_period": 20,
                    "signal_period": 9,
                    "stop_loss": 0.05,
                    "take_profit": 0.10
                },
                "optimization_ranges": {
                    "fast_period": {"min": 3, "max": 10, "step": 1},
                    "slow_period": {"min": 15, "max": 30, "step": 5},
                    "signal_period": {"min": 5, "max": 15, "step": 2}
                },
                "class_name": "MovingAverageCrossoverStrategy"
            },
            "rsi_strategy": {
                "name": "RSI策略",
                "description": "基于RSI指标的超买超卖策略",
                "parameters": {
                    "rsi_period": 14,
                    "oversold_threshold": 30,
                    "overbought_threshold": 70,
                    "exit_oversold": 50,
                    "exit_overbought": 50
                },
                "optimization_ranges": {
                    "rsi_period": {"min": 7, "max": 21, "step": 7},
                    "oversold_threshold": {"min": 20, "max": 40, "step": 5},
                    "overbought_threshold": {"min": 60, "max": 80, "step": 5}
                },
                "class_name": "RSIStrategy"
            }
        }
        
        # 保存默认策略
        try:
            with open(self.strategies_file, 'w', encoding='utf-8') as f:
                json.dump(default_strategies, f, ensure_ascii=False, indent=4)
            self.logger.info("已创建并保存默认策略配置")
        except Exception as e:
            self.logger.error(f"保存默认策略配置失败: {str(e)}")
        
        return default_strategies
    
    def _save_strategies(self):
        """保存策略配置"""
        try:
            with open(self.strategies_file, 'w', encoding='utf-8') as f:
                json.dump(self.strategies, f, ensure_ascii=False, indent=4)
            self.logger.info(f"策略配置已保存到 {self.strategies_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存策略配置失败: {str(e)}")
            return False
    
    def get_available_strategies(self):
        """获取可用策略列表
        
        Returns:
            策略信息列表
        """
        return [{
            'id': strategy_id,
            'name': strategy_config['name'],
            'description': strategy_config['description']
        } for strategy_id, strategy_config in self.strategies.items()]
    
    def get_strategy_config(self, strategy_id):
        """获取策略配置
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略配置字典
        """
        if strategy_id in self.strategies:
            return self.strategies[strategy_id]
        else:
            self.logger.warning(f"策略 {strategy_id} 不存在")
            return None
    
    def update_strategy_config(self, strategy_id, new_config):
        """更新策略配置
        
        Args:
            strategy_id: 策略ID
            new_config: 新配置字典
            
        Returns:
            是否更新成功
        """
        try:
            if strategy_id not in self.strategies:
                self.logger.warning(f"策略 {strategy_id} 不存在，将创建新策略")
            
            # 合并新配置
            self.strategies[strategy_id] = new_config
            
            # 保存策略配置
            self._save_strategies()
            
            self.logger.info(f"已更新策略 {strategy_id} 的配置")
            return True
        
        except Exception as e:
            self.logger.error(f"更新策略配置时出错: {str(e)}")
            return False
    
    
    def _get_strategy_required_indicators(self, strategy_id):
        """获取策略所需的技术指标
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            所需指标列表
        """
        if strategy_id == 'volume_price':
            return ['volume_ratio', 'trend_direction', 'macd', 'rsi']
        elif strategy_id == 'moving_average_crossover':
            return ['ma', 'ema']
        elif strategy_id == 'rsi_strategy':
            return ['rsi']
        else:
            return 'all'  # 默认全量计算
    
    def backtest_strategy(self, strategy_id, symbol, start_date=None, end_date=None, parameters=None):
        """回测策略
        
        Args:
            strategy_id: 策略ID
            symbol: 股票代码
            start_date: 回测开始日期 (默认为一年前)
            end_date: 回测结束日期 (默认为今天)
            parameters: 可选的参数覆盖
            
        Returns:
            回测结果字典
        """
        try:
            # 检查策略是否存在
            if strategy_id not in self.strategies:
                self.logger.error(f"策略 {strategy_id} 不存在")
                return {'status': 'error', 'message': f"策略 {strategy_id} 不存在"}
            
            # 获取策略配置
            strategy_config = self.strategies[strategy_id]
            
            # 设置日期范围
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # 获取股票数据
            self.logger.info(f"获取 {symbol} 的历史数据，时间范围: {start_date} - {end_date}")
            df = self.data_provider.get_stock_daily_data(symbol, start_date=start_date, end_date=end_date)
            
            # 使用LazyStockAnalyzer预处理数据
            required_indicators = self._get_strategy_required_indicators(strategy_id)
            analysis_result = self.lazy_analyzer.analyze(df)
            
            # 合并分析结果到原始数据
            for key, value in analysis_result.items():
                if key not in ['date', 'open', 'high', 'low', 'close', 'volume']:
                    df[key] = value
            
            if df is None or len(df) < 30:  # 至少需要30个交易日的数据
                self.logger.error(f"获取 {symbol} 的历史数据失败或数据不足")
                return {'status': 'error', 'message': f"获取 {symbol} 的历史数据失败或数据不足"}
            
            # 合并参数
            strategy_params = strategy_config['parameters'].copy()
            if parameters:
                strategy_params.update(parameters)
            
            # 选择策略类
            strategy_class_name = strategy_config.get('class_name')
            
            # 执行回测
            self.logger.info(f"开始回测 {symbol} 的 {strategy_config['name']} 策略")
            
            # 调用对应的策略回测方法
            if strategy_id == 'volume_price':
                result = self.backtester.backtest_volume_price_strategy(data=df, symbol=symbol)
            elif strategy_id == 'moving_average_crossover':
                result = self.backtester.backtest_ma_crossover_strategy(
                    data=df, 
                    symbol=symbol,
                    fast_period=strategy_params['fast_period'],
                    slow_period=strategy_params['slow_period'],
                    signal_period=strategy_params['signal_period']
                )
            elif strategy_id == 'rsi_strategy':
                result = self.backtester.backtest_rsi_strategy(
                    data=df,
                    symbol=symbol,
                    rsi_period=strategy_params['rsi_period'],
                    oversold=strategy_params['oversold_threshold'],
                    overbought=strategy_params['overbought_threshold']
                )
            else:
                self.logger.error(f"未实现的策略类型: {strategy_id}")
                return {'status': 'error', 'message': f"未实现的策略类型: {strategy_id}"}
            
            # 添加回测元数据
            result.update({
                'strategy_id': strategy_id,
                'strategy_name': strategy_config['name'],
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'parameters': strategy_params,
                'backtest_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            self.logger.info(f"回测完成，总收益率: {result.get('total_return', 0)}%")
            
            # 保存回测结果
            self._save_backtest_result(result)
            
            return {'status': 'success', 'data': result}
            
        except Exception as e:
            self.logger.error(f"回测策略时出错: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _save_backtest_result(self, result):
        """保存回测结果
        
        Args:
            result: 回测结果字典
        """
        try:
            # 创建回测结果目录
            backtest_dir = os.path.join(self.data_dir, 'backtest_results')
            os.makedirs(backtest_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{result['strategy_id']}_{result['symbol']}_{timestamp}.json"
            filepath = os.path.join(backtest_dir, filename)
            
            # 保存结果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"回测结果已保存到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存回测结果时出错: {str(e)}")
    
    def optimize_strategy(self, strategy_id, symbol, start_date=None, end_date=None, param_grid=None):
        """优化策略参数
        
        Args:
            strategy_id: 策略ID
            symbol: 股票代码
            start_date: 回测开始日期
            end_date: 回测结束日期
            param_grid: 参数网格，若为None则使用策略配置中的优化范围
            
        Returns:
            优化结果字典
        """
        try:
            # 检查策略是否存在
            if strategy_id not in self.strategies:
                self.logger.error(f"策略 {strategy_id} 不存在")
                return {'status': 'error', 'message': f"策略 {strategy_id} 不存在"}
            
            # 获取策略配置
            strategy_config = self.strategies[strategy_id]
            
            # 设置日期范围
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # 获取股票数据
            self.logger.info(f"获取 {symbol} 的历史数据，时间范围: {start_date} - {end_date}")
            df = self.data_provider.get_stock_daily_data(symbol, start_date=start_date, end_date=end_date)
            
            if df is None or len(df) < 30:  # 至少需要30个交易日的数据
                self.logger.error(f"获取 {symbol} 的历史数据失败或数据不足")
                return {'status': 'error', 'message': f"获取 {symbol} 的历史数据失败或数据不足"}
            
            # 使用策略配置中的优化范围生成参数网格
            if param_grid is None and 'optimization_ranges' in strategy_config:
                param_grid = self._generate_param_grid(strategy_config['optimization_ranges'])
            
            if not param_grid:
                self.logger.error(f"策略 {strategy_id} 没有定义优化范围")
                return {'status': 'error', 'message': f"策略 {strategy_id} 没有定义优化范围"}
            
            # 进行参数优化
            self.logger.info(f"开始优化 {symbol} 的 {strategy_config['name']} 策略参数")
            self.logger.info(f"参数网格包含 {len(param_grid)} 组参数组合")
            
            # 存储所有回测结果
            all_results = []
            
            # 遍历参数组合进行回测
            for params in param_grid:
                result = self.backtest_strategy(strategy_id, symbol, start_date, end_date, params)
                
                if result['status'] == 'success':
                    # 提取回测性能指标
                    performance = {
                        'parameters': params,
                        'total_return': result['data'].get('total_return', 0),
                        'sharpe_ratio': result['data'].get('sharpe_ratio', 0),
                        'max_drawdown': result['data'].get('max_drawdown', 0),
                        'win_rate': result['data'].get('win_rate', 0),
                        'trade_count': result['data'].get('trade_count', 0)
                    }
                    all_results.append(performance)
            
            # 按总收益率排序
            sorted_results = sorted(all_results, key=lambda x: x['total_return'], reverse=True)
            
            # 创建优化结果
            optimization_result = {
                'strategy_id': strategy_id,
                'strategy_name': strategy_config['name'],
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'optimization_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'best_parameters': sorted_results[0]['parameters'] if sorted_results else None,
                'best_performance': {
                    'total_return': sorted_results[0]['total_return'] if sorted_results else 0,
                    'sharpe_ratio': sorted_results[0]['sharpe_ratio'] if sorted_results else 0,
                    'max_drawdown': sorted_results[0]['max_drawdown'] if sorted_results else 0,
                    'win_rate': sorted_results[0]['win_rate'] if sorted_results else 0,
                    'trade_count': sorted_results[0]['trade_count'] if sorted_results else 0
                },
                'all_results': sorted_results[:10]  # 只保存前10个结果
            }
            
            # 保存优化结果
            self._save_optimization_result(optimization_result)
            
            # 如果有最佳参数，更新策略配置
            if sorted_results:
                self.logger.info(f"找到最佳参数配置，总收益率: {sorted_results[0]['total_return']}%")
                strategy_config['parameters'].update(sorted_results[0]['parameters'])
                self._save_strategies()
            
            return {'status': 'success', 'data': optimization_result}
            
        except Exception as e:
            self.logger.error(f"优化策略参数时出错: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _generate_param_grid(self, optimization_ranges):
        """根据参数优化范围生成参数网格
        
        Args:
            optimization_ranges: 参数优化范围配置
            
        Returns:
            参数组合列表
        """
        param_grid = []
        
        # 生成所有参数的可能取值
        param_values = {}
        for param_name, param_range in optimization_ranges.items():
            min_val = param_range['min']
            max_val = param_range['max']
            step = param_range['step']
            
            if isinstance(min_val, int) and isinstance(max_val, int) and isinstance(step, int):
                # 整数参数
                values = list(range(min_val, max_val + 1, step))
            else:
                # 浮点数参数
                values = []
                val = min_val
                while val <= max_val:
                    values.append(val)
                    val += step
                    val = round(val, 4)  # 避免浮点数精度问题
            
            param_values[param_name] = values
        
        # 生成参数的笛卡尔积
        def generate_combinations(params, current_combo=None, param_names=None):
            if current_combo is None:
                current_combo = {}
                param_names = list(params.keys())
            
            if not param_names:
                param_grid.append(current_combo.copy())
                return
            
            current_param = param_names[0]
            for val in params[current_param]:
                current_combo[current_param] = val
                generate_combinations(params, current_combo, param_names[1:])
        
        generate_combinations(param_values)
        return param_grid
    
    def _save_optimization_result(self, result):
        """保存优化结果
        
        Args:
            result: 优化结果字典
        """
        try:
            # 创建优化结果目录
            optimization_dir = os.path.join(self.data_dir, 'optimization_results')
            os.makedirs(optimization_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{result['strategy_id']}_{result['symbol']}_{timestamp}.json"
            filepath = os.path.join(optimization_dir, filename)
            
            # 保存结果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"优化结果已保存到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存优化结果时出错: {str(e)}")
    
    def batch_backtest(self, strategy_id, symbols, start_date=None, end_date=None):
        """批量回测策略
        
        Args:
            strategy_id: 策略ID
            symbols: 股票代码列表
            start_date: 回测开始日期
            end_date: 回测结束日期
            
        Returns:
            批量回测结果字典
        """
        try:
            if not symbols:
                self.logger.error("股票代码列表为空")
                return {'status': 'error', 'message': "股票代码列表为空"}
            
            self.logger.info(f"开始批量回测 {strategy_id} 策略，共 {len(symbols)} 只股票")
            
            results = []
            for symbol in symbols:
                self.logger.info(f"回测 {symbol}...")
                result = self.backtest_strategy(strategy_id, symbol, start_date, end_date)
                
                if result['status'] == 'success':
                    # 提取回测性能指标
                    performance = {
                        'symbol': symbol,
                        'total_return': result['data'].get('total_return', 0),
                        'sharpe_ratio': result['data'].get('sharpe_ratio', 0),
                        'max_drawdown': result['data'].get('max_drawdown', 0),
                        'win_rate': result['data'].get('win_rate', 0),
                        'trade_count': result['data'].get('trade_count', 0)
                    }
                    results.append(performance)
                else:
                    self.logger.warning(f"回测 {symbol} 失败: {result['message']}")
                    results.append({
                        'symbol': symbol,
                        'status': 'failed',
                        'message': result['message']
                    })
            
            # 按总收益率排序
            sorted_results = sorted([r for r in results if 'total_return' in r], 
                                    key=lambda x: x['total_return'], 
                                    reverse=True)
            
            # 添加失败的结果
            failed_results = [r for r in results if 'total_return' not in r]
            
            # 计算汇总指标
            successful_results = [r for r in results if 'total_return' in r]
            summary = {
                'total_stocks': len(symbols),
                'successful_tests': len(successful_results),
                'failed_tests': len(failed_results),
                'avg_return': np.mean([r['total_return'] for r in successful_results]) if successful_results else 0,
                'avg_sharpe': np.mean([r['sharpe_ratio'] for r in successful_results]) if successful_results else 0,
                'avg_drawdown': np.mean([r['max_drawdown'] for r in successful_results]) if successful_results else 0,
                'avg_win_rate': np.mean([r['win_rate'] for r in successful_results]) if successful_results else 0,
                'best_stock': sorted_results[0]['symbol'] if sorted_results else None,
                'best_return': sorted_results[0]['total_return'] if sorted_results else 0,
                'worst_stock': sorted_results[-1]['symbol'] if sorted_results else None,
                'worst_return': sorted_results[-1]['total_return'] if sorted_results else 0
            }
            
            batch_result = {
                'strategy_id': strategy_id,
                'strategy_name': self.strategies[strategy_id]['name'],
                'start_date': start_date,
                'end_date': end_date,
                'batch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': summary,
                'top_performers': sorted_results[:5] if len(sorted_results) > 5 else sorted_results,
                'bottom_performers': sorted_results[-5:] if len(sorted_results) > 5 else sorted_results,
                'failed_stocks': failed_results
            }
            
            # 保存批量回测结果
            self._save_batch_result(batch_result)
            
            self.logger.info(f"批量回测完成，成功率: {summary['successful_tests']}/{summary['total_stocks']}")
            
            return {'status': 'success', 'data': batch_result}
            
        except Exception as e:
            self.logger.error(f"批量回测时出错: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _save_batch_result(self, result):
        """保存批量回测结果
        
        Args:
            result: 批量回测结果字典
        """
        try:
            # 创建批量回测结果目录
            batch_dir = os.path.join(self.data_dir, 'batch_results')
            os.makedirs(batch_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{result['strategy_id']}_batch_{timestamp}.json"
            filepath = os.path.join(batch_dir, filename)
            
            # 保存结果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"批量回测结果已保存到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存批量回测结果时出错: {str(e)}")


# 测试函数
def test_strategy_optimization_engine():
    """测试策略优化引擎功能"""
    # 创建实例
    engine = StrategyOptimizationEngine(token='0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10')
    
    # 获取可用策略
    print("可用策略:")
    strategies = engine.get_available_strategies()
    for strategy in strategies:
        print(f"- {strategy['name']}: {strategy['description']}")
    
    # 回测单个股票
    print("\n回测单个股票...")
    result = engine.backtest_strategy('volume_price', '000001.SZ')
    if result['status'] == 'success':
        print(f"回测成功，总收益率: {result['data'].get('total_return', 0)}%")
    else:
        print(f"回测失败: {result['message']}")
    
    print("\n测试完成!")


# 如果直接运行此文件，执行测试
if __name__ == '__main__':
    test_strategy_optimization_engine() 