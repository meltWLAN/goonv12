import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import akshare as ak
from backtesting import Backtester, BacktestResult

class Backtesting:
    """回测系统包装类
    为了兼容stock_review.py中的调用，提供了backtest_portfolio方法
    """
    def __init__(self):
        self.backtester = Backtester()
    
    def backtest_portfolio(self, symbols, start_date, end_date, initial_capital=1000000, 
                          position_size=0.1, stop_loss=0.05, take_profit=0.15):
        """对股票组合进行回测
        
        Args:
            symbols: 股票代码列表
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_capital: 初始资金
            position_size: 每只股票仓位比例
            stop_loss: 止损比例
            take_profit: 止盈比例
            
        Returns:
            回测结果
        """
        print(f"开始回测股票组合，共{len(symbols)}只股票")
        print(f"回测时间范围: {start_date} 至 {end_date}")
        print(f"初始资金: {initial_capital}，单股仓位: {position_size*100}%")
        print(f"止损设置: {stop_loss*100}%，止盈设置: {take_profit*100}%")
        
        # 初始化回测器
        backtester = Backtester(initial_capital=initial_capital)
        result = BacktestResult()
        
        # 获取股票数据并进行回测
        for symbol in symbols:
            try:
                # 使用akshare获取股票历史数据
                stock_data = self._get_stock_data(symbol, start_date, end_date)
                if stock_data is None or len(stock_data) == 0:
                    print(f"无法获取股票 {symbol} 的历史数据，跳过回测")
                    continue
                
                # 执行回测策略
                self._backtest_single_stock(backtester, symbol, stock_data, position_size, stop_loss, take_profit)
                
            except Exception as e:
                print(f"回测股票 {symbol} 时出错: {str(e)}")
        
        # 汇总回测结果
        result.trades = backtester.trades
        result.total_profit = backtester.total_profit
        result.max_drawdown = backtester.max_drawdown
        result.win_rate = backtester.win_rate
        
        # 计算其他指标
        if backtester.trades:
            profit_metrics, risk_metrics, trade_metrics, holding_metrics = backtester._parallel_calculate_metrics(backtester.trades)
            
            result.profit_ratio = profit_metrics.get('profit_ratio', 0.0)
            result.sharpe_ratio = risk_metrics.get('sharpe_ratio', 0.0)
            result.annual_return = risk_metrics.get('annual_return', 0.0)
            result.volatility = risk_metrics.get('volatility', 0.0)
            result.trade_count = len(backtester.trades)
            result.win_count = profit_metrics.get('win_count', 0)
            result.loss_count = profit_metrics.get('loss_count', 0)
            result.avg_holding_period = holding_metrics.get('avg_holding_period', 0.0)
            result.max_consecutive_wins = trade_metrics.get('max_consecutive_wins', 0)
            result.max_consecutive_losses = trade_metrics.get('max_consecutive_losses', 0)
        
        print("回测完成!")
        print(f"总收益: {result.total_profit:.2f}")
        print(f"最大回撤: {result.max_drawdown:.2f}")
        print(f"胜率: {result.win_rate*100:.2f}%")
        
        return result
    
    def _get_stock_data(self, symbol, start_date, end_date):
        """获取股票历史数据"""
        try:
            # 处理股票代码格式
            if symbol.isdigit():
                if symbol.startswith('6'):
                    full_symbol = f"{symbol}.SH"
                else:
                    full_symbol = f"{symbol}.SZ"
            else:
                full_symbol = symbol
                
            # 使用akshare获取股票历史数据
            stock_data = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date.replace('-', ''), 
                                           end_date=end_date.replace('-', ''), adjust="qfq")
            
            # 重命名列以便处理
            stock_data.columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            
            # 转换日期格式
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            
            return stock_data
        except Exception as e:
            print(f"获取股票 {symbol} 数据时出错: {str(e)}")
            return None
    
    def _backtest_single_stock(self, backtester, symbol, stock_data, position_size, stop_loss, take_profit):
        """对单只股票进行回测"""
        # 初始化变量
        in_position = False
        entry_price = 0
        entry_date = None
        position_value = backtester.initial_capital * position_size
        
        # 遍历每一天的数据
        for i, row in stock_data.iterrows():
            date = row['日期']
            close_price = row['收盘']
            
            # 如果没有持仓，考虑买入
            if not in_position:
                # 简单策略：当天收盘价高于5日均线时买入
                if i >= 5:
                    ma5 = stock_data['收盘'].iloc[i-5:i].mean()
                    if close_price > ma5 and backtester.current_capital >= position_value:
                        # 计算可买入数量
                        volume = position_value / close_price
                        
                        # 执行买入
                        trade = backtester.execute_trade(
                            timestamp=date,
                            symbol=symbol,
                            action='buy',
                            price=close_price,
                            volume=volume
                        )
                        
                        if trade:
                            in_position = True
                            entry_price = close_price
                            entry_date = date
            
            # 如果已持仓，考虑卖出
            else:
                # 止损条件
                stop_loss_price = entry_price * (1 - stop_loss)
                # 止盈条件
                take_profit_price = entry_price * (1 + take_profit)
                
                # 检查是否触发止损或止盈
                if close_price <= stop_loss_price or close_price >= take_profit_price:
                    # 获取当前持仓
                    current_position = backtester.positions.get(symbol, 0)
                    
                    if current_position > 0:
                        # 执行卖出
                        trade = backtester.execute_trade(
                            timestamp=date,
                            symbol=symbol,
                            action='sell',
                            price=close_price,
                            volume=current_position
                        )
                        
                        if trade:
                            in_position = False
                            entry_price = 0
                            entry_date = None
        
        # 回测结束后，如果还有持仓，以最后一天的收盘价卖出
        if in_position:
            current_position = backtester.positions.get(symbol, 0)
            if current_position > 0:
                last_date = stock_data['日期'].iloc[-1]
                last_price = stock_data['收盘'].iloc[-1]
                
                backtester.execute_trade(
                    timestamp=last_date,
                    symbol=symbol,
                    action='sell',
                    price=last_price,
                    volume=current_position
                )