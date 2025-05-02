#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import logging
from typing import Dict, List, Tuple, Union, Optional
from collections import defaultdict

from visual_stock_system import VisualStockSystem
from china_stock_provider import ChinaStockProvider
from lazy_analyzer import LazyStockAnalyzer


class SmartReviewCore:
    """
    智能复盘核心模块
    实现高级股票分析、自适应推荐和历史数据深度学习分析
    """
    
    def __init__(self, token=None, data_dir='./smart_review_data', lazy_mode=True):
        """初始化智能复盘核心
        
        Args:
            token: API令牌
            data_dir: 数据目录
        """
        self.token = token
        self.data_dir = data_dir
        self.review_pool_file = os.path.join(data_dir, 'smart_review_pool.json')
        self.performance_file = os.path.join(data_dir, 'smart_performance.json')
        self.model_dir = os.path.join(data_dir, 'models')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 首先设置日志
        self._setup_logging()
        
        # 初始化系统组件
        self.visual_system = VisualStockSystem(token, headless=True)
        self.data_provider = ChinaStockProvider(token)
        self.lazy_mode = lazy_mode
        # 根据模式选择分析器初始化方式
        if self.lazy_mode:
            # 按需计算模式 - 智能复盘核心只需要这些指标
            required_indicators = ['ma', 'ema', 'macd', 'rsi', 'kdj', 'volume_ratio', 'trend_direction']
            self.analyzer = LazyStockAnalyzer(required_indicators=required_indicators)
            self.logger.info("LazyStockAnalyzer初始化为按需计算模式")
        else:
            # 全量计算模式
            self.analyzer = LazyStockAnalyzer(required_indicators='all')
            self.logger.info("LazyStockAnalyzer初始化为全量计算模式")
        
        # 加载复盘池和绩效数据
        self.review_pool = self._load_review_pool()
        self.performance_data = self._load_performance_data()
        
        self.logger.info("智能复盘核心初始化完成")
    
    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('SmartReviewCore')
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        log_file = os.path.join(self.data_dir, 'smart_review.log')
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
    
    def _load_review_pool(self):
        """加载复盘股票池"""
        if os.path.exists(self.review_pool_file):
            try:
                with open(self.review_pool_file, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
                self.logger.info(f"成功加载复盘股票池，包含 {len(pool.get('stocks', []))} 只股票")
                return pool
            except Exception as e:
                self.logger.error(f"加载复盘股票池失败: {str(e)}")
                return self._create_default_review_pool()
        else:
            self.logger.info("复盘股票池文件不存在，创建新的复盘池")
            return self._create_default_review_pool()
    
    def _create_default_review_pool(self):
        """创建默认复盘池结构"""
        return {
            'stocks': [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '2.0'
        }
    
    def _save_review_pool(self):
        """保存复盘股票池"""
        try:
            # 更新最后更新时间
            self.review_pool['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.review_pool_file, 'w', encoding='utf-8') as f:
                json.dump(self.review_pool, f, ensure_ascii=False, indent=4)
            self.logger.info(f"复盘股票池已保存到 {self.review_pool_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存复盘股票池失败: {str(e)}")
            return False
    
    def _load_performance_data(self):
        """加载绩效数据"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    performance = json.load(f)
                self.logger.info(f"成功加载绩效数据，包含 {len(performance.get('trades', []))} 条交易记录")
                return performance
            except Exception as e:
                self.logger.error(f"加载绩效数据失败: {str(e)}")
                return self._create_default_performance_data()
        else:
            self.logger.info("绩效数据文件不存在，创建新的绩效数据")
            return self._create_default_performance_data()
    
    def _create_default_performance_data(self):
        """创建默认绩效数据结构"""
        return {
            'trades': [],
            'metrics': {
                'total_profit': 0.0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            },
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '2.0'
        }
    
    def _save_performance_data(self):
        """保存绩效数据"""
        try:
            # 更新最后更新时间
            self.performance_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"绩效数据已保存到 {self.performance_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存绩效数据失败: {str(e)}")
            return False
    
    def add_stock_to_review(self, stock_info):
        """添加股票到智能复盘池
        
        Args:
            stock_info: 股票信息字典
            
        Returns:
            是否添加成功
        """
        try:
            # 验证必要字段
            required_fields = ['symbol', 'name']
            for field in required_fields:
                if field not in stock_info:
                    self.logger.error(f"添加股票失败: 缺少必要字段 {field}")
                    return False
            
            # 添加标准化字段
            today = datetime.now().strftime('%Y-%m-%d')
            stock_entry = {
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'date_added': today,
                'status': 'watching',
                'analysis': {},
                'trade_history': [],
                'notes': stock_info.get('notes', ''),
                'tags': stock_info.get('tags', []),
                'importance': stock_info.get('importance', 3),  # 1-5 重要性评级
                'smart_score': self._calculate_smart_score(stock_info),
                'last_analyzed': today,
                'strategies': stock_info.get('strategies', []),
                'price_targets': {
                    'support': stock_info.get('support_price'),
                    'resistance': stock_info.get('resistance_price'),
                    'buy_target': stock_info.get('buy_target'),
                    'sell_target': stock_info.get('sell_target')
                }
            }
            
            # 检查是否已存在
            exists = False
            for i, stock in enumerate(self.review_pool['stocks']):
                if stock['symbol'] == stock_entry['symbol']:
                    # 合并更新现有记录
                    for key, value in stock_entry.items():
                        if key not in ['trade_history', 'notes', 'tags'] and value is not None:
                            stock[key] = value
                    
                    # 特殊处理某些字段
                    if 'notes' in stock_entry and stock_entry['notes']:
                        stock['notes'] += f"\n[{today}] {stock_entry['notes']}"
                    
                    if 'tags' in stock_entry and stock_entry['tags']:
                        stock['tags'] = list(set(stock['tags'] + stock_entry['tags']))
                    
                    self.review_pool['stocks'][i] = stock
                    exists = True
                    self.logger.info(f"更新了股票 {stock_entry['name']}({stock_entry['symbol']}) 的信息")
                    break
            
            # 如果不存在，添加新股票
            if not exists:
                self.review_pool['stocks'].append(stock_entry)
                self.logger.info(f"添加新股票 {stock_entry['name']}({stock_entry['symbol']}) 到复盘池")
            
            # 保存复盘池
            self._save_review_pool()
            return True
            
        except Exception as e:
            self.logger.error(f"添加股票到复盘池时出错: {str(e)}")
            return False
    
    def _calculate_smart_score(self, stock_info):
        """计算智能评分
        
        Args:
            stock_info: 股票信息
            
        Returns:
            0-100的评分
        """
        try:
            # 基础分数
            base_score = 50
            
            # 根据不同因素调整分数
            adjustments = 0
            
            # 技术指标分析
            if 'trend' in stock_info:
                if stock_info['trend'] == 'uptrend':
                    adjustments += 15
                elif stock_info['trend'] == 'downtrend':
                    adjustments -= 15
            
            if 'volume_ratio' in stock_info:
                volume_ratio = stock_info['volume_ratio']
                if volume_ratio > 2.0:
                    adjustments += 10
                elif volume_ratio > 1.5:
                    adjustments += 5
                elif volume_ratio < 0.5:
                    adjustments -= 5
            
            if 'macd_hist' in stock_info:
                if stock_info['macd_hist'] > 0:
                    adjustments += 8
                else:
                    adjustments -= 8
            
            if 'rsi' in stock_info:
                rsi = stock_info['rsi']
                if 40 <= rsi <= 60:
                    adjustments += 5  # 中性区域
                elif 30 <= rsi < 40 or 60 < rsi <= 70:
                    adjustments += 0  # 临界区域
                elif rsi < 30:
                    adjustments += 2  # 超卖区域，可能反弹
                elif rsi > 70:
                    adjustments -= 2  # 超买区域，可能回调
            
            # 根据推荐级别调整
            if 'recommendation' in stock_info:
                if stock_info['recommendation'] == '强烈推荐买入':
                    adjustments += 20
                elif stock_info['recommendation'] == '建议买入':
                    adjustments += 10
                elif stock_info['recommendation'] == '建议卖出':
                    adjustments -= 10
                elif stock_info['recommendation'] == '强烈建议卖出':
                    adjustments -= 20
            
            # 计算最终分数，确保在0-100范围内
            final_score = min(100, max(0, base_score + adjustments))
            return round(final_score, 1)
            
        except Exception as e:
            self.logger.error(f"计算智能评分时出错: {str(e)}")
            return 50  # 出错返回中等分数
    
    def analyze_all_stocks_in_pool(self):
        """分析复盘池中的所有股票
        
        Returns:
            分析结果摘要
        """
        results = {
            'success_count': 0,
            'fail_count': 0,
            'improved_count': 0,
            'declined_count': 0,
            'stocks': []
        }
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        for i, stock in enumerate(self.review_pool['stocks']):
            try:
                symbol = stock['symbol']
                self.logger.info(f"分析股票 {stock['name']}({symbol})")
                
                # 获取股票数据
                df = self.visual_system.get_stock_data(symbol)
                if df is None or len(df) < 20:
                    self.logger.warning(f"无法获取足够的股票数据: {symbol}")
                    results['fail_count'] += 1
                    continue
                
                # 使用LazyStockAnalyzer进行分析
                analysis = self.analyzer.analyze(df)
                
                # 保存前一次的智能评分
                previous_score = stock.get('smart_score', 50)
                
                # 更新股票分析结果
                stock_info = {
                    'symbol': symbol,
                    'name': stock['name'],
                    'trend': 'uptrend' if analysis.get('trend_direction', 0) > 0 else 'downtrend' if analysis.get('trend_direction', 0) < 0 else 'sideways',
                    'volume_ratio': analysis.get('volume_ratio', 1.0),
                    'macd_hist': analysis.get('macd_hist', 0),
                    'rsi': analysis.get('rsi', 50)
                }
                
                # 根据分析结果生成推荐级别
                if stock_info['trend'] == 'uptrend' and stock_info['volume_ratio'] > 1.5 and stock_info['macd_hist'] > 0:
                    stock_info['recommendation'] = '强烈推荐买入'
                elif stock_info['trend'] == 'uptrend' and stock_info['volume_ratio'] > 1.2:
                    stock_info['recommendation'] = '建议买入'
                elif stock_info['trend'] == 'downtrend' and stock_info['volume_ratio'] > 1.5 and stock_info['macd_hist'] < 0:
                    stock_info['recommendation'] = '强烈建议卖出'
                elif stock_info['trend'] == 'downtrend':
                    stock_info['recommendation'] = '建议卖出'
                else:
                    stock_info['recommendation'] = '观望'
                
                # 计算新的智能评分
                new_score = self._calculate_smart_score(stock_info)
                stock_info['smart_score'] = new_score
                
                # 更新分析数据
                self.review_pool['stocks'][i]['analysis'] = {
                    'trend': stock_info['trend'],
                    'volume_ratio': stock_info['volume_ratio'],
                    'macd_hist': stock_info['macd_hist'],
                    'rsi': stock_info['rsi'],
                    'recommendation': stock_info['recommendation'],
                    'last_price': float(df.iloc[-1]['close']) if 'close' in df.columns else None,
                    'last_date': df.index[-1].strftime('%Y-%m-%d') if hasattr(df.index[-1], 'strftime') else str(df.index[-1]),
                    'indicators': {k: v for k, v in analysis.items() if k not in ['date', 'open', 'high', 'low', 'close', 'volume']}
                }
                
                # 更新智能评分和最后分析日期
                self.review_pool['stocks'][i]['smart_score'] = new_score
                self.review_pool['stocks'][i]['last_analyzed'] = today
                
                # 记录分数变化
                if new_score > previous_score:
                    results['improved_count'] += 1
                    self.review_pool['stocks'][i]['score_trend'] = 'up'
                elif new_score < previous_score:
                    results['declined_count'] += 1
                    self.review_pool['stocks'][i]['score_trend'] = 'down'
                else:
                    self.review_pool['stocks'][i]['score_trend'] = 'unchanged'
                
                # 添加到结果
                results['stocks'].append({
                    'symbol': symbol,
                    'name': stock['name'],
                    'recommendation': stock_info['recommendation'],
                    'smart_score': new_score,
                    'score_change': new_score - previous_score
                })
                
                results['success_count'] += 1
                
            except Exception as e:
                self.logger.error(f"分析股票 {stock['symbol']} 时出错: {str(e)}")
                results['fail_count'] += 1
        
        # 保存更新后的复盘池
        self._save_review_pool()
        
        # 对分析结果排序
        results['stocks'] = sorted(results['stocks'], key=lambda x: x['smart_score'], reverse=True)
        
        self.logger.info(f"分析完成，成功: {results['success_count']}，失败: {results['fail_count']}，" +
                        f"上升: {results['improved_count']}，下降: {results['declined_count']}")
        
        return results
    
    def get_stock_from_pool(self, symbol=None, status=None, min_score=None, max_count=None):
        """从复盘池获取股票
        
        Args:
            symbol: 特定股票代码
            status: 过滤状态
            min_score: 最低分数
            max_count: 最大返回数量
            
        Returns:
            符合条件的股票列表
        """
        try:
            # 应用过滤条件
            filtered_stocks = self.review_pool['stocks']
            
            if symbol:
                filtered_stocks = [s for s in filtered_stocks if s['symbol'] == symbol]
            
            if status:
                filtered_stocks = [s for s in filtered_stocks if s['status'] == status]
            
            if min_score is not None:
                filtered_stocks = [s for s in filtered_stocks if s.get('smart_score', 0) >= min_score]
            
            # 按分数排序
            filtered_stocks = sorted(filtered_stocks, key=lambda x: x.get('smart_score', 0), reverse=True)
            
            # 限制返回数量
            if max_count is not None:
                filtered_stocks = filtered_stocks[:max_count]
            
            return filtered_stocks
            
        except Exception as e:
            self.logger.error(f"从复盘池获取股票时出错: {str(e)}")
            return []
    
    def update_stock_status(self, symbol, status, price=None, date=None, notes=None):
        """更新股票状态
        
        Args:
            symbol: 股票代码
            status: 新状态 (watching, bought, half_bought, half_sold, sold)
            price: 交易价格
            date: 交易日期，默认为今天
            notes: 备注信息
            
        Returns:
            更新是否成功
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            updated = False
            for i, stock in enumerate(self.review_pool['stocks']):
                if stock['symbol'] == symbol:
                    old_status = stock['status']
                    stock['status'] = status
                    
                    # 创建交易记录
                    trade_record = {
                        'date': date,
                        'price': price,
                        'status_from': old_status,
                        'status_to': status,
                        'notes': notes or ""
                    }
                    
                    # 添加到交易历史
                    if 'trade_history' not in stock:
                        stock['trade_history'] = []
                    stock['trade_history'].append(trade_record)
                    
                    # 特殊处理买入和卖出
                    if status == 'bought' or status == 'half_bought':
                        stock['buy_price'] = price
                        stock['buy_date'] = date
                    elif (status == 'sold' or status == 'half_sold') and stock.get('buy_price'):
                        stock['sell_price'] = price
                        stock['sell_date'] = date
                        
                        # 完全卖出才计算盈利
                        if status == 'sold' and stock.get('buy_price'):
                            # 计算收益率和持有天数
                            profit_percent = round((price - stock['buy_price']) / stock['buy_price'] * 100, 2)
                            stock['profit_percent'] = profit_percent
                            
                            try:
                                buy_date_obj = datetime.strptime(stock['buy_date'], '%Y-%m-%d')
                                sell_date_obj = datetime.strptime(date, '%Y-%m-%d')
                                stock['holding_days'] = (sell_date_obj - buy_date_obj).days
                            except:
                                stock['holding_days'] = None
                            
                            # 添加到绩效数据
                            self._add_trade_performance(stock)
                    
                    # 更新备注
                    if notes:
                        if 'notes' not in stock or not stock['notes']:
                            stock['notes'] = f"[{date}] {notes}"
                        else:
                            stock['notes'] += f"\n[{date}] {notes}"
                    
                    self.review_pool['stocks'][i] = stock
                    updated = True
                    self.logger.info(f"已更新股票 {symbol} 的状态为 {status}")
                    break
            
            if updated:
                self._save_review_pool()
                return True
            else:
                self.logger.warning(f"未找到股票 {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新股票状态时出错: {str(e)}")
            return False
    
    def _add_trade_performance(self, stock):
        """添加交易绩效数据
        
        Args:
            stock: 股票信息
        """
        try:
            trade = {
                'symbol': stock['symbol'],
                'name': stock['name'],
                'buy_date': stock['buy_date'],
                'buy_price': stock['buy_price'],
                'sell_date': stock['sell_date'],
                'sell_price': stock['sell_price'],
                'profit_percent': stock['profit_percent'],
                'holding_days': stock['holding_days'],
                'notes': stock.get('notes', ''),
                'tags': stock.get('tags', []),
                'smart_score_at_buy': stock.get('smart_score_at_buy', stock.get('smart_score', 50)),
                'strategy': stock.get('active_strategy', 'default')
            }
            
            # 添加交易记录
            self.performance_data['trades'].append(trade)
            
            # 更新性能指标
            self._update_performance_metrics()
            
            # 保存绩效数据
            self._save_performance_data()
            
            self.logger.info(f"已添加交易绩效记录: {stock['symbol']}, 盈利率: {stock['profit_percent']}%")
            
        except Exception as e:
            self.logger.error(f"添加交易绩效数据时出错: {str(e)}")
    
    def _update_performance_metrics(self):
        """更新绩效指标"""
        try:
            trades = self.performance_data['trades']
            if not trades:
                return
            
            # 计算基本指标
            profits = [t['profit_percent'] for t in trades]
            win_trades = len([p for p in profits if p > 0])
            total_trades = len(profits)
            
            metrics = {
                'total_profit': round(sum(profits), 2),
                'win_rate': round(win_trades / total_trades * 100, 2) if total_trades > 0 else 0,
                'avg_profit': round(sum(profits) / len(profits), 2) if profits else 0,
                'max_profit': round(max(profits), 2) if profits else 0,
                'min_profit': round(min(profits), 2) if profits else 0,
                'trade_count': total_trades,
                'win_count': win_trades,
                'loss_count': total_trades - win_trades
            }
            
            # 计算最大回撤
            # 累计收益按交易日期排序
            sorted_trades = sorted(trades, key=lambda x: x['sell_date'])
            cumulative_returns = np.cumsum([t['profit_percent'] for t in sorted_trades])
            
            max_dd = 0
            peak = float('-inf')
            for ret in cumulative_returns:
                if ret > peak:
                    peak = ret
                dd = (peak - ret) / (100 + peak) * 100 if peak > 0 else 0
                max_dd = max(max_dd, dd)
            
            metrics['max_drawdown'] = round(max_dd, 2)
            
            # 计算夏普比率 (简化版本)
            if len(profits) > 1:
                avg_return = np.mean(profits)
                std_return = np.std(profits)
                sharpe = avg_return / std_return if std_return > 0 else 0
                metrics['sharpe_ratio'] = round(sharpe, 2)
            else:
                metrics['sharpe_ratio'] = 0
            
            # 更新性能指标
            self.performance_data['metrics'] = metrics
            
            self.logger.info(f"已更新绩效指标, 总盈利: {metrics['total_profit']}%, 胜率: {metrics['win_rate']}%")
            
        except Exception as e:
            self.logger.error(f"更新绩效指标时出错: {str(e)}")
    
    def get_performance_metrics(self):
        """获取绩效指标
        
        Returns:
            绩效指标字典
        """
        return self.performance_data['metrics']
    
    def get_trade_history(self, symbol=None):
        """获取交易历史
        
        Args:
            symbol: 可选的股票代码过滤器
            
        Returns:
            交易历史列表
        """
        trades = self.performance_data['trades']
        
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]
        
        return sorted(trades, key=lambda x: x['sell_date'], reverse=True)
    
    def get_top_recommendations(self, count=10, min_score=70):
        """获取顶级推荐股票
        
        Args:
            count: 返回数量
            min_score: 最低分数要求
            
        Returns:
            推荐股票列表
        """
        try:
            # 分析所有股票
            self.analyze_all_stocks_in_pool()
            
            # 获取观察中的股票
            watching_stocks = [s for s in self.review_pool['stocks'] if s['status'] == 'watching']
            
            # 按智能评分排序
            sorted_stocks = sorted(watching_stocks, key=lambda x: x.get('smart_score', 0), reverse=True)
            
            # 过滤掉低于最低分数的股票
            filtered_stocks = [s for s in sorted_stocks if s.get('smart_score', 0) >= min_score]
            
            # 限制返回数量
            top_stocks = filtered_stocks[:count]
            
            return [
                {
                    'symbol': s['symbol'],
                    'name': s['name'],
                    'smart_score': s.get('smart_score', 0),
                    'recommendation': s.get('analysis', {}).get('recommendation', '观望'),
                    'last_price': s.get('analysis', {}).get('last_price'),
                    'trend': s.get('analysis', {}).get('trend'),
                    'volume_ratio': s.get('analysis', {}).get('volume_ratio')
                }
                for s in top_stocks
            ]
            
        except Exception as e:
            self.logger.error(f"获取顶级推荐股票时出错: {str(e)}")
            return []

    def smart_filter_stocks(self, criteria=None):
        """智能过滤符合特定条件的股票
        
        Args:
            criteria: 过滤条件字典
            
        Returns:
            过滤后的股票列表
        """
        if criteria is None:
            criteria = {}
        
        try:
            # 应用过滤条件
            stocks = self.review_pool['stocks']
            
            # 状态过滤
            if 'status' in criteria:
                stocks = [s for s in stocks if s['status'] == criteria['status']]
            
            # 分数范围过滤
            if 'min_score' in criteria:
                stocks = [s for s in stocks if s.get('smart_score', 0) >= criteria['min_score']]
            if 'max_score' in criteria:
                stocks = [s for s in stocks if s.get('smart_score', 0) <= criteria['max_score']]
            
            # 趋势过滤
            if 'trend' in criteria:
                stocks = [s for s in stocks if s.get('analysis', {}).get('trend') == criteria['trend']]
            
            # 技术指标过滤
            if 'min_rsi' in criteria:
                stocks = [s for s in stocks if s.get('analysis', {}).get('rsi', 0) >= criteria['min_rsi']]
            if 'max_rsi' in criteria:
                stocks = [s for s in stocks if s.get('analysis', {}).get('rsi', 100) <= criteria['max_rsi']]
            
            if 'macd_positive' in criteria and criteria['macd_positive']:
                stocks = [s for s in stocks if s.get('analysis', {}).get('macd_hist', 0) > 0]
            elif 'macd_positive' in criteria and not criteria['macd_positive']:
                stocks = [s for s in stocks if s.get('analysis', {}).get('macd_hist', 0) <= 0]
            
            # 成交量比率过滤
            if 'min_volume_ratio' in criteria:
                stocks = [s for s in stocks if s.get('analysis', {}).get('volume_ratio', 0) >= criteria['min_volume_ratio']]
            
            # 标签过滤
            if 'tags' in criteria:
                stocks = [s for s in stocks if any(tag in s.get('tags', []) for tag in criteria['tags'])]
            
            # 推荐级别过滤
            if 'recommendation' in criteria:
                stocks = [s for s in stocks if s.get('analysis', {}).get('recommendation') == criteria['recommendation']]
            
            # 添加日期过滤
            if 'added_after' in criteria:
                stocks = [s for s in stocks if s.get('date_added', '') >= criteria['added_after']]
            
            if 'added_before' in criteria:
                stocks = [s for s in stocks if s.get('date_added', '') <= criteria['added_before']]
            
            # 按智能评分排序
            return sorted(stocks, key=lambda x: x.get('smart_score', 0), reverse=True)
            
        except Exception as e:
            self.logger.error(f"智能过滤股票时出错: {str(e)}")
            return []


# 测试函数
def test_smart_review_core():
    """测试智能复盘核心功能"""
    # 创建实例
    core = SmartReviewCore(token='0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10')
    
    # 添加测试股票
    test_stock = {
        'symbol': '000001.SZ',
        'name': '平安银行',
        'trend': 'uptrend',
        'volume_ratio': 1.8,
        'macd_hist': 0.15,
        'rsi': 55,
        'recommendation': '强烈推荐买入',
        'notes': '测试添加股票',
        'tags': ['金融', '银行', '蓝筹']
    }
    
    print("添加测试股票...")
    core.add_stock_to_review(test_stock)
    
    # 分析股票
    print("\n分析复盘池中的股票...")
    results = core.analyze_all_stocks_in_pool()
    print(f"分析结果: 成功 {results['success_count']} 只，失败 {results['fail_count']} 只")
    
    # 获取顶级推荐
    print("\n获取顶级推荐...")
    top_recommendations = core.get_top_recommendations(count=5)
    for i, rec in enumerate(top_recommendations, 1):
        print(f"{i}. {rec['name']}({rec['symbol']}) - 评分: {rec['smart_score']}, 推荐: {rec['recommendation']}")
    
    # 更新股票状态
    print("\n更新股票状态...")
    core.update_stock_status('000001.SZ', 'bought', price=18.5, notes='测试买入')
    
    # 获取股票信息
    print("\n获取股票信息...")
    stock = core.get_stock_from_pool(symbol='000001.SZ')
    if stock:
        stock = stock[0]
        print(f"股票: {stock['name']}({stock['symbol']})")
        print(f"状态: {stock['status']}")
        print(f"智能评分: {stock.get('smart_score')}")
        print(f"推荐: {stock.get('analysis', {}).get('recommendation')}")
    
    print("\n测试完成!")


# 如果直接运行此文件，执行测试
if __name__ == '__main__':
    test_smart_review_core() 