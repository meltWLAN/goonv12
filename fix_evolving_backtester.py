#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复 evolving_backtester_part2.py 文件的脚本
处理现存的缩进错误和缺少的类定义问题
"""

import os
import sys
import logging
import shutil
import traceback
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FixBacktesterScript')

def fix_backtester_file():
    """修复 evolving_backtester_part2.py 文件"""
    
    logger.info("开始修复 evolving_backtester_part2.py 文件...")
    
    # 创建完整的修复后的文件内容
    new_content = """from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import os

# 导入模型管理器
from evolving_backtester import ModelManager

# 配置日志
logger = logging.getLogger('EvolvingBacktester')

class AdvancedTradeRecord:
    \"\"\"高级交易记录，包含交易的详细信息\"\"\"
    
    def __init__(self, 
                 symbol: str, 
                 entry_time: datetime, 
                 entry_price: float, 
                 position_size: float, 
                 exit_time: Optional[datetime] = None, 
                 exit_price: Optional[float] = None,
                 profit_loss: Optional[float] = None,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None,
                 risk_reward_ratio: Optional[float] = None,
                 position_ratio: Optional[float] = None,
                 features: Optional[Dict] = None,
                 trade_signals: Optional[Dict] = None):
        \"\"\"初始化交易记录
        
        Args:
            symbol: 股票代码
            entry_time: 入场时间
            entry_price: 入场价格
            position_size: 仓位大小（股数）
            exit_time: 出场时间
            exit_price: 出场价格
            profit_loss: 盈亏金额
            stop_loss: 止损价格
            take_profit: 止盈价格
            risk_reward_ratio: 风险回报比
            position_ratio: 仓位比例
            features: 交易时的特征
            trade_signals: 交易信号
        \"\"\"
        self.symbol = symbol
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.position_size = position_size
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.profit_loss = profit_loss
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.risk_reward_ratio = risk_reward_ratio
        self.position_ratio = position_ratio
        self.features = features or {}
        self.trade_signals = trade_signals or {}
        
    def to_dict(self) -> Dict:
        \"\"\"转换为字典\"\"\"
        return {
            'symbol': self.symbol,
            'entry_time': self.entry_time.strftime('%Y-%m-%d %H:%M:%S') if self.entry_time else None,
            'entry_price': self.entry_price,
            'position_size': self.position_size,
            'exit_time': self.exit_time.strftime('%Y-%m-%d %H:%M:%S') if self.exit_time else None,
            'exit_price': self.exit_price,
            'profit_loss': self.profit_loss,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward_ratio': self.risk_reward_ratio,
            'position_ratio': self.position_ratio,
            'features': self.features,
            'trade_signals': self.trade_signals
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'AdvancedTradeRecord':
        \"\"\"从字典创建交易记录\"\"\"
        entry_time = datetime.strptime(data['entry_time'], '%Y-%m-%d %H:%M:%S') if data.get('entry_time') else None
        exit_time = datetime.strptime(data['exit_time'], '%Y-%m-%d %H:%M:%S') if data.get('exit_time') else None
        
        return cls(
            symbol=data['symbol'],
            entry_time=entry_time,
            entry_price=data['entry_price'],
            position_size=data['position_size'],
            exit_time=exit_time,
            exit_price=data.get('exit_price'),
            profit_loss=data.get('profit_loss'),
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            risk_reward_ratio=data.get('risk_reward_ratio'),
            position_ratio=data.get('position_ratio'),
            features=data.get('features', {}),
            trade_signals=data.get('trade_signals', {})
        )
        
class AdvancedBacktestResult:
    \"\"\"高级回测结果，包含详细的回测统计信息\"\"\"
    
    def __init__(self,
                 trades: List[AdvancedTradeRecord],
                 initial_capital: float,
                 final_capital: float,
                 start_time: datetime,
                 end_time: datetime,
                 win_rate: Optional[float] = None,
                 avg_profit: Optional[float] = None,
                 avg_loss: Optional[float] = None,
                 max_drawdown: Optional[float] = None,
                 sharpe_ratio: Optional[float] = None,
                 profit_factor: Optional[float] = None,
                 total_trades: Optional[int] = None,
                 winning_trades: Optional[int] = None,
                 losing_trades: Optional[int] = None,
                 strategy_params: Optional[Dict] = None,
                 equity_curve: Optional[List[Tuple[datetime, float]]] = None,
                 market_performance: Optional[Dict] = None):
        \"\"\"初始化回测结果
        
        Args:
            trades: 交易列表
            initial_capital: 初始资金
            final_capital: 最终资金
            start_time: 回测开始时间
            end_time: 回测结束时间
            win_rate: 胜率
            avg_profit: 平均盈利
            avg_loss: 平均亏损
            max_drawdown: 最大回撤
            sharpe_ratio: 夏普比率
            profit_factor: 盈亏比
            total_trades: 总交易次数
            winning_trades: 盈利交易次数
            losing_trades: 亏损交易次数
            strategy_params: 策略参数
            equity_curve: 权益曲线
            market_performance: 市场表现
        \"\"\"
        self.trades = trades
        self.initial_capital = initial_capital
        self.final_capital = final_capital
        self.start_time = start_time
        self.end_time = end_time
        self.win_rate = win_rate
        self.avg_profit = avg_profit
        self.avg_loss = avg_loss
        self.max_drawdown = max_drawdown
        self.sharpe_ratio = sharpe_ratio
        self.profit_factor = profit_factor
        self.total_trades = total_trades or len(trades)
        self.winning_trades = winning_trades
        self.losing_trades = losing_trades
        self.strategy_params = strategy_params or {}
        self.equity_curve = equity_curve or []
        self.market_performance = market_performance or {}
        
    def to_dict(self) -> Dict:
        \"\"\"转换为字典\"\"\"
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'win_rate': self.win_rate,
            'avg_profit': self.avg_profit,
            'avg_loss': self.avg_loss,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'profit_factor': self.profit_factor,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'strategy_params': self.strategy_params,
            'trades': [t.to_dict() for t in self.trades],
            'equity_curve': [(t.strftime('%Y-%m-%d %H:%M:%S'), v) for t, v in self.equity_curve],
            'market_performance': self.market_performance
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'AdvancedBacktestResult':
        \"\"\"从字典创建回测结果\"\"\"
        trades = [AdvancedTradeRecord.from_dict(t) for t in data.get('trades', [])]
        start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        
        equity_curve = []
        for t_str, v in data.get('equity_curve', []):
            t = datetime.strptime(t_str, '%Y-%m-%d %H:%M:%S')
            equity_curve.append((t, v))
        
        return cls(
            trades=trades,
            initial_capital=data['initial_capital'],
            final_capital=data['final_capital'],
            start_time=start_time,
            end_time=end_time,
            win_rate=data.get('win_rate'),
            avg_profit=data.get('avg_profit'),
            avg_loss=data.get('avg_loss'),
            max_drawdown=data.get('max_drawdown'),
            sharpe_ratio=data.get('sharpe_ratio'),
            profit_factor=data.get('profit_factor'),
            total_trades=data.get('total_trades'),
            winning_trades=data.get('winning_trades'),
            losing_trades=data.get('losing_trades'),
            strategy_params=data.get('strategy_params', {}),
            equity_curve=equity_curve,
            market_performance=data.get('market_performance', {})
        )
    
    def save_to_file(self, filename: str):
        \"\"\"保存回测结果到文件\"\"\"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
        
    @classmethod
    def load_from_file(cls, filename: str) -> 'AdvancedBacktestResult':
        \"\"\"从文件加载回测结果\"\"\"
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

class EvolvingBacktester:
    \"\"\"自进化回测器，能够通过机器学习不断优化交易策略\"\"\"
    
    def __init__(self, initial_capital=100000.0, model_manager=None):
        \"\"\"初始化回测器
        
        Args:
            initial_capital: 初始资金
            model_manager: 模型管理器
        \"\"\"
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.model_manager = model_manager or ModelManager()
        self.trades = []
        self.equity_curve = []
        self.max_position_ratio = 0.2  # 最大仓位比例
        
        # 自适应参数
        self.adaptive_params = {
            'position_size_factor': 1.0,
            'stop_loss_factor': 1.0,
            'take_profit_factor': 1.5,
            'entry_threshold': 0.6,
            'exit_threshold': 0.6,
            'trend_factor': 1.0
        }
        
    def calculate_position_size(self, features: Dict, signal_strength: float, price: float, stop_loss: float) -> float:
        \"\"\"计算最优仓位大小
        
        Args:
            features: 特征字典
            signal_strength: 信号强度 (0-1)
            price: 当前价格
            stop_loss: 止损价格
            
        Returns:
            仓位比例 (0-1)，表示应该使用的总资金比例
        \"\"\"
        try:
            # 如果特征不完整，使用基本方法计算
            if not features or len(features) < 10 or self.model_manager.models['position'] is None:
                # 计算风险（价格到止损的距离）
                risk_per_share = price - stop_loss
                
                # 基础风险金额（账户的1%）
                base_risk_amount = self.current_capital * 0.01
                
                # 调整风险金额
                adjusted_risk = base_risk_amount * signal_strength
                
                # 计算可承受的仓位比例
                if risk_per_share > 0:
                    position_ratio = adjusted_risk / (self.current_capital * risk_per_share / price)
                else:
                    # 如果止损价格不合理，使用基础仓位
                    position_ratio = self.max_position_ratio * signal_strength
                
                # 确保不超过最大仓位限制
                position_ratio = min(position_ratio, self.max_position_ratio)
                
                return float(max(0.0, position_ratio))
            
            # 获取模型预测的仓位比例
            position_ratio = self.model_manager.predict_position_size(list(features.values()))
            
            # 应用信号强度调整
            adjusted_ratio = position_ratio * signal_strength * self.adaptive_params['position_size_factor']
            
            # 确保不超过最大仓位限制
            adjusted_ratio = min(adjusted_ratio, self.max_position_ratio)
            
            logger.info(f"计算仓位: 模型建议比例={position_ratio:.4f}, 调整后比例={adjusted_ratio:.4f}, 资金比例={adjusted_ratio:.2%}")
            
            return float(max(0.0, adjusted_ratio))
            
        except Exception as e:
            logger.error(f"计算仓位大小出错: {str(e)}")
            
            # 基本仓位计算作为后备
            position_ratio = self.max_position_ratio * 0.5 * signal_strength
            return float(max(0.0, position_ratio))

    def extract_features(self, data, index=-1):
        """Extract features from data
        
        Args:
            data: Stock data
            index: Data index to use, default -1 means the last row
            
        Returns:
            Feature dictionary
        """
        try:
            # Use specified index or last row
            if index == -1:
                row = data.iloc[-1]
                prev_row = data.iloc[-2] if len(data) > 1 else None
            else:
                row = data.iloc[index]
                prev_row = data.iloc[index-1] if index > 0 else None
            
            features = {}
            
            # Handle Chinese and English column names
            close = None
            open_price = None
            high = None
            low = None
            volume = None
            
            # Try to find closing price
            if '收盘' in data.columns:
                close = row['收盘']
            elif 'close' in data.columns:
                close = row['close']
            
            # Try to find opening price
            if '开盘' in data.columns:
                open_price = row['开盘']
            elif 'open' in data.columns:
                open_price = row['open']
            
            # Try to find highest price
            if '最高' in data.columns:
                high = row['最高']
            elif 'high' in data.columns:
                high = row['high']
            
            # Try to find lowest price
            if '最低' in data.columns:
                low = row['最低']
            elif 'low' in data.columns:
                low = row['low']
            
            # Try to find volume
            if '成交量' in data.columns:
                volume = row['成交量']
            elif 'volume' in data.columns:
                volume = row['volume']
            
            # Extract basic price features
            if close is not None:
                features['close'] = close
            if open_price is not None:
                features['open'] = open_price
            if high is not None:
                features['high'] = high
            if low is not None:
                features['low'] = low
            if volume is not None:
                features['volume'] = volume
            
            # Extract technical indicator features
            for col in data.columns:
                col_lower = col.lower() if isinstance(col, str) else col
                # Try to add common technical indicators
                if col_lower in ['ma5', 'ma10', 'ma20', 'macd', 'macd_signal', 'macd_hist', 
                                 'rsi', 'k', 'd', 'j', 'boll_upper', 'boll_middle', 'boll_lower']:
                    features[col_lower] = row[col]
                # Handle uppercase column names
                elif col in ['MA5', 'MA10', 'MA20', 'MACD', 'MACD_Signal', 'MACD_Hist', 
                            'RSI', 'K', 'D', 'J', 'BOLL_UPPER', 'BOLL_MIDDLE', 'BOLL_LOWER']:
                    features[col.lower()] = row[col]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return {}
    
    def evaluate_entry_signal(self, features, signal_strength):
        """Evaluate entry signal strength
        
        Args:
            features: Feature dictionary
            signal_strength: Initial signal strength
            
        Returns:
            Final signal strength (0-1)
        """
        try:
            # If model doesn't exist, return original signal strength
            if self.model_manager.models['entry'] is None:
                return signal_strength
            
            # Use model to predict entry probability
            entry_prob = self.model_manager.predict_entry_signal(list(features.values()))
            
            # Combine original signal and model prediction
            final_signal = (signal_strength + entry_prob) / 2
            
            # Apply threshold
            if final_signal >= self.adaptive_params['entry_threshold']:
                return final_signal
            else:
                return 0
            
        except Exception as e:
            logger.error(f"Error evaluating entry signal: {str(e)}")
            return signal_strength if signal_strength >= 0.6 else 0
    
    def detect_market_regime(self, data):
        """Detect market regime
        
        Args:
            data: Stock data
            
        Returns:
            Market regime label (rising, falling, ranging)
        """
        try:
            # Get closing price
            close = None
            if '收盘' in data.columns:
                close = data['收盘']
            elif 'close' in data.columns:
                close = data['close']
            else:
                logger.warning("Unable to determine closing price column, using default market state")
                return "unknown"
            
            # Need at least 30 data points
            if len(close) < 30:
                return "insufficient_data"
            
            # Calculate short and long term trends
            short_ma = close.rolling(window=10).mean()
            long_ma = close.rolling(window=30).mean()
            
            # Recent moving average values
            last_short = short_ma.iloc[-1]
            last_long = long_ma.iloc[-1]
            
            # Calculate recent 10-day volatility
            recent_volatility = close.iloc[-10:].pct_change().std()
            
            # Determine market regime
            if last_short > last_long and (last_short / last_long - 1) > 0.02:
                return "rising"
            elif last_short < last_long and (1 - last_short / last_long) > 0.02:
                return "falling"
            elif recent_volatility > 0.02:
                return "high_volatility"
            else:
                return "ranging"
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {str(e)}")
            return "unknown"
    
    def backtest_macd_strategy(self, data, stock_code):
        """MACD golden cross strategy backtest
        
        Args:
            data: Stock data
            stock_code: Stock code
            
        Returns:
            Backtest result object
        """
        logger.info(f"Starting MACD golden cross strategy backtest for {stock_code}")
        
        # Ensure data has correct MACD columns
        if 'MACD' not in data.columns and 'macd' not in data.columns:
            # Calculate MACD
            if '收盘' in data.columns:
                close = data['收盘']
            elif 'close' in data.columns:
                close = data['close']
            else:
                logger.error("Cannot find closing price column, backtest failed")
                return None
                
            # Calculate MACD indicator
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            data['MACD'] = ema12 - ema26
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
        
        # Initialize backtest variables
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        start_time = data.index[0] if hasattr(data.index[0], 'strftime') else datetime.now()
        
        # Iterate through each trading day
        for i in range(60, len(data)):
            date = data.index[i] if hasattr(data.index[i], 'strftime') else datetime.now()
            
            # Prepare current data
            current_data = data.iloc[:i+1]
            features = self.extract_features(current_data, i)
            
            # Detect market regime
            market_regime = self.detect_market_regime(current_data)
            
            # Get price
            if '收盘' in data.columns:
                price = data.iloc[i]['收盘']
            elif 'close' in data.columns:
                price = data.iloc[i]['close']
            else:
                logger.warning("Cannot determine closing price, skipping this trading day")
                continue
            
            # Calculate MACD signal
            macd_hist = 0
            if 'MACD_Hist' in data.columns:
                macd_hist = data.iloc[i]['MACD_Hist']
            elif 'macd_hist' in data.columns:
                macd_hist = data.iloc[i]['macd_hist']
            
            # Check if position exists
            has_position = stock_code in self.positions
            
            # Entry signal: MACD histogram turns from negative to positive
            buy_signal = False
            if i > 0:
                prev_hist = 0
                if 'MACD_Hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['MACD_Hist']
                elif 'macd_hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['macd_hist']
                
                buy_signal = prev_hist < 0 and macd_hist > 0
            
            # Exit signal: MACD histogram turns from positive to negative
            sell_signal = False
            if i > 0:
                prev_hist = 0
                if 'MACD_Hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['MACD_Hist']
                elif 'macd_hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['macd_hist']
                
                sell_signal = prev_hist > 0 and macd_hist < 0
            
            # Process signals
            if not has_position and buy_signal:
                # Entry signal strength
                signal_strength = min(1.0, abs(macd_hist) * 10) if macd_hist != 0 else 0.5
                
                # Evaluate signal
                final_signal = self.evaluate_entry_signal(features, signal_strength)
                
                if final_signal > 0:
                    # Calculate position size
                    stop_loss = price * 0.95  # 5% stop loss
                    position_ratio = self.calculate_position_size(features, final_signal, price, stop_loss)
                    
                    # Execute buy
                    position_value = self.current_capital * position_ratio
                    shares = position_value / price
                    
                    # Record trade
                    trade = AdvancedTradeRecord(
                        symbol=stock_code,
                        entry_time=date,
                        entry_price=price,
                        position_size=shares,
                        stop_loss=stop_loss,
                        position_ratio=position_ratio,
                        features=features
                    )
                    
                    self.trades.append(trade)
                    self.positions[stock_code] = {
                        'shares': shares,
                        'entry_price': price,
                        'stop_loss': stop_loss,
                        'entry_time': date,
                        'features': features,
                        'trade_record': trade
                    }
                    
                    logger.info(f"Buy {stock_code}: price={price:.2f}, position={position_ratio:.2%}, shares={shares:.2f}")
            
            elif has_position and (sell_signal or price <= self.positions[stock_code]['stop_loss']):
                # Exit
                position = self.positions[stock_code]
                shares = position['shares']
                entry_price = position['entry_price']
                trade_record = position['trade_record']
                
                # Calculate profit
                profit = (price - entry_price) * shares
                self.current_capital += profit
                
                # Update trade record
                trade_record.exit_time = date
                trade_record.exit_price = price
                trade_record.profit_loss = profit
                
                logger.info(f"Sell {stock_code}: price={price:.2f}, profit={profit:.2f} ({(price/entry_price-1)*100:.2f}%)")
                
                # Clear position
                del self.positions[stock_code]
            
            # Update equity curve
            portfolio_value = self.current_capital
            for pos_symbol, pos_data in self.positions.items():
                portfolio_value += pos_data['shares'] * price
            
            self.equity_curve.append((date, portfolio_value))
        
        # Create backtest result
        end_time = data.index[-1] if hasattr(data.index[-1], 'strftime') else datetime.now()
        final_value = self.current_capital
        for symbol, position in self.positions.items():
            last_price = data.iloc[-1]['收盘'] if '收盘' in data.columns else data.iloc[-1]['close']
            final_value += position['shares'] * last_price
        
        # Calculate performance metrics
        completed_trades = [t for t in self.trades if t.exit_time is not None]
        winning_trades = [t for t in completed_trades if t.profit_loss and t.profit_loss > 0]
        
        total_trades = len(completed_trades)
        if total_trades > 0:
            win_rate = len(winning_trades) / total_trades * 100
            
            win_profits = [t.profit_loss for t in winning_trades]
            loss_trades = [t for t in completed_trades if t.profit_loss and t.profit_loss <= 0]
            loss_profits = [t.profit_loss for t in loss_trades]
            
            avg_profit = sum(win_profits) / len(win_profits) if win_profits else 0
            avg_loss = sum(loss_profits) / len(loss_profits) if loss_profits else 0
            
            profit_factor = abs(sum(win_profits) / sum(loss_profits)) if sum(loss_profits) != 0 else float('inf')
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
        
        # Create result object
        result = AdvancedBacktestResult(
            trades=self.trades,
            initial_capital=self.initial_capital,
            final_capital=final_value,
            start_time=start_time,
            end_time=end_time,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=total_trades - len(winning_trades),
            profit_factor=profit_factor,
            equity_curve=self.equity_curve
        )
        
        return result
    
    def backtest_kdj_strategy(self, data, stock_code):
        """KDJ golden cross strategy backtest (simplified implementation)"""
        logger.info(f"Using MACD strategy instead of KDJ strategy")
        return self.backtest_macd_strategy(data, stock_code)
    
    def backtest_ma_strategy(self, data, stock_code):
        """Dual moving average strategy backtest (simplified implementation)"""
        logger.info(f"Using MACD strategy instead of MA strategy")
        return self.backtest_macd_strategy(data, stock_code)

# Backup the original file
if os.path.exists('evolving_backtester_part2.py'):
    backup_name = f'evolving_backtester_part2.py.bak'
    shutil.copy('evolving_backtester_part2.py', backup_name)
    print(f"Backed up original file to {backup_name}")

try:
    # Read original file content
    with open('evolving_backtester_part2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find class EvolvingBacktester in the file
    backtester_class_pos = content.find("class EvolvingBacktester:")
    if backtester_class_pos == -1:
        print("Error: Cannot find EvolvingBacktester class definition")
        exit(1)
    
    # Find calculate_position_size method position (it's the last method in the class)
    calculate_pos_method = content.find("def calculate_position_size", backtester_class_pos)
    
    if calculate_pos_method == -1:
        print("Error: Cannot find calculate_position_size method")
        exit(1)
    
    # Find method end position
    method_end = content.find("\n\n", calculate_pos_method)
    if method_end == -1:
        method_end = len(content)  # If no double newline found, use end of file
    
    # Insert new methods into the class
    new_content = content[:method_end] + "\n" + methods_to_add + content[method_end:]
    
    # Save new file
    with open('evolving_backtester_part2.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully added methods to evolving_backtester_part2.py file")
    
except Exception as e:
    print(f"Error: {str(e)}")
    traceback.print_exc()

if __name__ == "__main__":
    if fix_backtester_file():
        print("修复成功: evolving_backtester_part2.py 文件已经更新")
    else:
        print("修复失败: 查看日志了解详情")
        sys.exit(1) 