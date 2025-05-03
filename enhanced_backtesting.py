import pandas as pd
import numpy as np
import talib as ta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache
from cachetools import LRUCache
import os
import logging
import threading

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='enhanced_backtesting.log')
logger = logging.getLogger('EnhancedBacktester')

@dataclass
class TradeRecord:
    """增强版交易记录数据结构"""
    timestamp: datetime
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    volume: float
    position: float
    profit: float
    drawdown: float
    entry_price: float = 0.0  # 入场价格
    exit_price: float = 0.0  # 出场价格
    holding_days: int = 0  # 持仓天数
    stop_loss: float = 0.0  # 止损价格
    take_profit: float = 0.0  # 止盈价格
    signal_quality: float = 0.0  # 信号质量
    market_condition: str = ""  # 市场状况
    trade_reason: str = ""  # 交易原因

class BacktestResult:
    """增强版回测结果数据结构"""
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self.total_profit: float = 0.0
        self.max_drawdown: float = 0.0
        self.win_rate: float = 0.0
        self.profit_ratio: float = 0.0  # 盈亏比
        self.sharpe_ratio: float = 0.0
        self.annual_return: float = 0.0
        self.volatility: float = 0.0
        self.trade_count: int = 0
        self.win_count: int = 0
        self.loss_count: int = 0
        self.avg_holding_period: float = 0.0
        self.max_consecutive_wins: int = 0
        self.max_consecutive_losses: int = 0
        self.profit_factor: float = 0.0  # 新增：利润因子
        self.recovery_factor: float = 0.0  # 新增：恢复因子
        self.expectancy: float = 0.0  # 新增：期望值
        self.avg_win: float = 0.0  # 新增：平均盈利
        self.avg_loss: float = 0.0  # 新增：平均亏损
        self.max_win: float = 0.0  # 新增：最大单笔盈利
        self.max_loss: float = 0.0  # 新增：最大单笔亏损
        self.monthly_returns: Dict[str, float] = {}  # 新增：月度收益
        self.drawdown_periods: List[Dict] = []  # 新增：回撤周期记录

class TradeStatus(Enum):
    """交易状态枚举"""
    PENDING = "待执行"
    EXECUTED = "已执行"
    CANCELLED = "已取消"
    PARTIAL = "部分执行"
    REJECTED = "被拒绝"


from lazy_analyzer import LazyStockAnalyzer
class EnhancedBacktester:
    """增强版回测系统，专注于提高盈利能力"""
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Dict[str, Any]] = {}  # 增强版持仓管理
        self.trades: List[TradeRecord] = []
        self.daily_returns: List[float] = []
        self.max_capital = initial_capital
        self.risk_free_rate = 0.03
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.win_rate = 0.0
        # 初始化多进程计算池和缓存系统
        self._process_pool = ProcessPoolExecutor(max_workers=os.cpu_count())
        self._thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)
        self._calculation_cache = LRUCache(maxsize=2048)  # 扩大缓存容量
        self._metric_cache = LRUCache(maxsize=1024)  # 新增指标缓存
        self._data_cache = LRUCache(maxsize=512)  # 新增数据缓存
        
        # 市场环境和风险控制参数
        self.market_volatility_percentile = 0.5  # 市场波动率分位数
        self.market_trend_strength = 0.0  # 市场趋势强度
        self.market_sentiment_score = 0.0  # 市场情绪得分
        
        # 增强版参数 - 优化后的参数配置
        self.max_position_ratio = 0.08  # 大幅降低单个股票最大仓位比例，提高安全性
        self.max_total_position = 0.5  # 降低最大总仓位比例，增加现金缓冲
        self.trailing_stop_pct = 0.05  # 收紧移动止损百分比，加强风险控制
        self.use_dynamic_position_sizing = True  # 启用动态仓位管理
        self.use_trailing_stop = True  # 启用移动止损
        self.use_time_stop = True  # 启用时间止损
        self.max_holding_days = 10  # 进一步缩短最大持仓天数，提高资金灵活性
        self.min_profit_ratio = 3.5  # 提高最小盈亏比要求，增加安全边际
        self.max_drawdown_limit = 0.08  # 显著降低最大回撤限制，加强风险控制
        self.consecutive_loss_limit = 1  # 降低连续亏损限制，更早触发风险控制
        self.market_condition_weight = 0.6  # 提高市场状况权重，更注重市场环境
        self.volatility_adjustment = True  # 启用波动率调整
        self.trade_log_enabled = True  # 启用详细交易日志
        self.position_scaling = True  # 启用仓位动态缩放
        self.use_volume_filter = True  # 启用成交量过滤
        self.min_volume_ratio = 2.0  # 提高最小成交量比率要求，确保充足流动性
        
        # 交易状态跟踪
        self.current_drawdown = 0.0
        self.consecutive_losses = 0
        self.last_trade_result = 0.0
        self.trade_history: Dict[str, List[TradeRecord]] = {}
        self.pending_orders: List[Dict] = []
        self.active_trailing_stops: Dict[str, float] = {}
        self.position_cache = {}
        self.cache_lock = threading.Lock()
        
        # 初始化日志
        logger.info(f"初始化增强版回测系统，初始资金: {initial_capital}")
        
        # 初始化线程锁
        self.cache_lock = threading.Lock()

    
    def _prepare_data_with_indicators(self, data, strategy_type):
        """使用LazyStockAnalyzer高效计算策略所需指标
        
        Args:
            data: 股票数据DataFrame
            strategy_type: 策略类型
            
        Returns:
            处理后的数据
        """
        if strategy_type == 'volume_price':
            required = ['volume_ratio', 'trend_direction', 'macd']
        elif strategy_type == 'ma_crossover':
            required = ['ma', 'ema']
        elif strategy_type == 'rsi_strategy':
            required = ['rsi']
        else:
            required = 'all'  # 默认全量计算
            
        analysis_result = self.lazy_analyzer.analyze(data)
        
        # 合并分析结果到原始数据
        for key, value in analysis_result.items():
            if key not in ['date', 'open', 'high', 'low', 'close', 'volume']:
                if isinstance(value, (int, float)):
                    data[key] = value
                
        return data
        
    def backtest_kdj_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """KDJ金叉策略回测，增强版本包含动态止损和资金管理
        
        Args:
            data: 股票数据
            symbol: 股票代码
            
        Returns:
            回测结果，包含详细的交易记录和风险指标
        """
        # 初始化风险控制参数
        self._init_risk_params(data)
        
        # 计算动态止损位
        data['ATR'] = self._calculate_atr(data)
        data['Dynamic_Stop'] = data['收盘'] - data['ATR'] * 2
        data['Trailing_Stop'] = data.apply(self._calculate_trailing_stop, axis=1)
        
        # 计算动态仓位
        data['Position_Size'] = self._calculate_position_size(data)
        # 计算KDJ指标
        low_list = data['最低'].rolling(9, min_periods=9).min()
        high_list = data['最高'].rolling(9, min_periods=9).max()
        rsv = (data['收盘'] - low_list) / (high_list - low_list) * 100
        k = pd.DataFrame(rsv).ewm(com=2).mean()
        d = pd.DataFrame(k).ewm(com=2).mean()
        j = 3 * k - 2 * d
        
        # 计算其他技术指标
        data['RSI'] = self._calculate_rsi(data['收盘'])
        data['ATR'] = self._calculate_atr(data)
        data['Trend'] = self._calculate_trend_strength(data)
        data['Volume_MA'] = data['成交量'].rolling(20).mean()
        
        # 生成交易信号
        signals = pd.DataFrame(index=data.index)
        signals['action'] = 'hold'
        signals['price'] = data['收盘']
        signals['volume'] = 0.0
        signals['signal_quality'] = 0.0
        signals['market_condition'] = 'normal'
        signals['stop_loss'] = 0.0
        
        # KDJ金叉和死叉
        buy_signals = (k < 20) & (j < 0) & (k > d) & (k.shift(1) <= d.shift(1))
        sell_signals = (k > 80) | (j > 100) | ((k < d) & (k.shift(1) >= d.shift(1)))
        
        # 结合成交量和趋势强度优化信号
        for i in range(len(data)):
            current_price = data['收盘'].iloc[i]
            current_volume = data['成交量'].iloc[i]
            volume_ma = data['Volume_MA'].iloc[i]
            
            if buy_signals.iloc[i] and current_volume > volume_ma * 1.2:
                # 计算信号质量
                trend_score = data['Trend'].iloc[i]
                volume_score = min((current_volume / volume_ma - 1) * 0.5, 1.0)
                rsi_score = 1.0 - abs(50 - data['RSI'].iloc[i]) / 50
                signal_quality = (trend_score + volume_score + rsi_score) / 3
                
                signals.iloc[i, signals.columns.get_loc('action')] = 'buy'
                signals.iloc[i, signals.columns.get_loc('signal_quality')] = signal_quality
                
                # 设置止损价格
                atr = data['ATR'].iloc[i]
                stop_loss = current_price - 2 * atr
                signals.iloc[i, signals.columns.get_loc('stop_loss')] = stop_loss
                
                # 根据趋势判断市场状况
                if trend_score > 0.5 and data['RSI'].iloc[i] > 50:
                    signals.iloc[i, signals.columns.get_loc('market_condition')] = 'bullish'
                
            elif sell_signals.iloc[i]:
                signals.iloc[i, signals.columns.get_loc('action')] = 'sell'
                signals.iloc[i, signals.columns.get_loc('signal_quality')] = 0.8
                if data['Trend'].iloc[i] < -0.3:
                    signals.iloc[i, signals.columns.get_loc('market_condition')] = 'bearish'
        
        # 执行回测
        return self.backtest_strategy(data, lambda x: signals)

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ATR指标"""
        high = data['最高']
        low = data['最低']
        close = data['收盘']
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-c'] = abs(high - close.shift())
        tr['l-c'] = abs(low - close.shift())
        tr['tr'] = tr.max(axis=1)
        return tr['tr'].rolling(period).mean()

    def _calculate_trend_strength(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """计算趋势强度"""
        close = data['收盘']
        ma = close.rolling(period).mean()
        std = close.rolling(period).std()
        z_score = (close - ma) / std
        return z_score.clip(-1, 1)

    def calculate_position_size(self, price: float, signal_quality: float, market_condition: str) -> float:
        """根据信号质量和市场状况动态计算仓位大小"""
        try:
            # 基础仓位
            base_position = self.current_capital * self.position_ratio
            
            # 信号质量调整
            quality_factor = {
                'high': 1.0,
                'medium': 0.7,
                'low': 0.5
            }.get(signal_quality, 0.5)
            
            # 市场状况调整
            market_factor = {
                'bullish': 1.2,
                'neutral': 1.0,
                'bearish': 0.8
            }.get(market_condition, 1.0)
            
            # 计算最终仓位
            adjusted_position = base_position * quality_factor * market_factor
            
            # 确保不超过最大仓位限制
            max_position = self.current_capital * self.max_position_ratio
            final_position = min(adjusted_position, max_position)
            
            # 计算可买入数量
            shares = int(final_position / price)
            
            return shares
            
        except Exception as e:
            self.logger.error(f"计算仓位大小时出错: {str(e)}")
            return 0
    
    def update_stop_loss(self, symbol: str, current_price: float):
        """更新移动止损价格"""
        try:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            entry_price = position['entry_price']
            highest_price = position['highest_price']
            
            # 更新最高价
            if current_price > highest_price:
                position['highest_price'] = current_price
                
                # 计算新的移动止损价格
                profit_ratio = (current_price - entry_price) / entry_price
                if profit_ratio >= 0.1:  # 盈利超过10%时启动移动止损
                    new_stop_loss = current_price * (1 - self.trailing_stop_ratio)
                    position['stop_loss'] = max(new_stop_loss, position['stop_loss'])
                    
            return True
            
        except Exception as e:
            self.logger.error(f"更新移动止损时出错: {str(e)}")
            return False

    def calculate_stop_loss(self, price: float, volatility: float, 
                          trend_strength: float = 0.0, 
                          signal_quality: float = 0.8) -> float:
        """计算智能止损价格
        
        Args:
            price: 当前价格
            volatility: 波动率（如ATR值）
            trend_strength: 趋势强度 (-1到1)
            signal_quality: 信号质量 (0-1)
            
        Returns:
            止损价格
        """
        # 基础ATR倍数
        # 动态ATR倍数基准（根据市场波动率分位数调整）
        volatility_percentile = self._get_volatility_percentile()
        base_atr_multiple = 1.5 + (volatility_percentile * 0.03)
        
        # 根据趋势强度调整ATR倍数
        trend_factor = 1.0 + abs(trend_strength) * 0.5  # 1.0-1.5
        
        # 根据信号质量调整ATR倍数
        quality_factor = 1.0 + (1.0 - signal_quality) * 0.5  # 1.0-1.5 (信号质量越低，止损越宽松)
        
        # 计算最终ATR倍数
        atr_multiple = base_atr_multiple * trend_factor * quality_factor
        
        # 计算止损距离
        stop_distance = volatility * atr_multiple
        
        # 计算止损价格
        stop_loss = price * (1 - stop_distance / price)
        
        logger.info(f"智能止损计算[市场波动分位数:{volatility_percentile:.2f}]: 价格={price:.2f}, 波动率={volatility:.4f}, "
                  f"趋势强度={trend_strength:.2f}, 信号质量={signal_quality:.2f}, "
                  f"止损价格={stop_loss:.2f}")
        
        return stop_loss

    def calculate_take_profit(self, price: float, stop_loss: float, 
                            trend_strength: float = 0.0, 
                            signal_quality: float = 0.8) -> float:
        """计算智能止盈价格
        
        Args:
            price: 当前价格
            stop_loss: 止损价格
            trend_strength: 趋势强度 (-1到1)
            signal_quality: 信号质量 (0-1)
            
        Returns:
            止盈价格
        """
        # 计算风险（价格到止损的距离）
        risk = price - stop_loss
        
        # 基础风险收益比
        base_risk_reward = self.min_profit_ratio
        
        # 根据趋势强度调整风险收益比
        trend_factor = 1.0 + abs(trend_strength) * 1.0  # 1.0-2.0
        
        # 根据信号质量调整风险收益比
        quality_factor = 0.8 + signal_quality * 0.4  # 0.8-1.2
        
        # 计算最终风险收益比
        risk_reward = base_risk_reward * trend_factor * quality_factor
        
        # 计算止盈价格
        take_profit = price + (risk * risk_reward)
        
        logger.info(f"智能止盈计算: 价格={price:.2f}, 止损={stop_loss:.2f}, "
                  f"趋势强度={trend_strength:.2f}, 信号质量={signal_quality:.2f}, "
                  f"风险收益比={risk_reward:.2f}, 止盈价格={take_profit:.2f}")
        
        return take_profit

    def update_trailing_stop(self, symbol: str, current_price: float) -> Optional[float]:
        """更新移动止损
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            新的止损价格，如果触发止损则返回None
        """
        if not self.use_trailing_stop or symbol not in self.positions:
            return None
            
        position = self.positions[symbol]
        entry_price = position.get('entry_price', 0)
        current_stop = position.get('stop_loss', 0)
        
        # 如果没有设置止损，使用入场价格的一定比例作为初始止损
        if current_stop <= 0:
            current_stop = entry_price * (1 - self.trailing_stop_pct)
            position['stop_loss'] = current_stop
            return current_stop
        
        # 计算新的止损价格（只上移不下移）
        if current_price > entry_price:  # 盈利中
            # 计算理论止损价格
            theoretical_stop = current_price * (1 - self.trailing_stop_pct)
            
            # 只有当新止损价格高于当前止损价格时才更新
            if theoretical_stop > current_stop:
                position['stop_loss'] = theoretical_stop
                logger.info(f"更新移动止损: {symbol} 价格={current_price:.2f}, 新止损={theoretical_stop:.2f}")
                return theoretical_stop
        
        # 检查是否触发止损
        if current_price <= current_stop:
            logger.info(f"触发止损: {symbol} 价格={current_price:.2f}, 止损={current_stop:.2f}")
            return None  # 返回None表示触发止损
        
        return current_stop

    def check_time_stop(self, symbol: str, current_date: datetime) -> bool:
        """检查是否触发时间止损
        
        Args:
            symbol: 股票代码
            current_date: 当前日期
            
        Returns:
            是否触发时间止损
        """
        if not self.use_time_stop or symbol not in self.positions:
            return False
            
        position = self.positions[symbol]
        entry_date = position.get('entry_date')
        if not entry_date:
            return False
            
        # 计算持仓天数
        holding_days = (current_date - entry_date).days
        
        # 检查是否超过最大持仓天数
        if holding_days >= self.max_holding_days:
            logger.info(f"触发时间止损: {symbol} 持仓天数={holding_days}, 最大持仓天数={self.max_holding_days}")
            return True
            
        return False

    def execute_trade(self, timestamp: datetime, symbol: str, action: str,
                     price: float, volume: float, signal_quality: float = 0.8,
                     market_condition: str = "normal", trade_reason: str = "") -> Optional[TradeRecord]:
        """执行交易并记录交易明细
        
        Args:
            timestamp: 交易时间
            symbol: 股票代码
            action: 交易动作 ('buy' or 'sell')
            price: 交易价格
            volume: 交易数量
            signal_quality: 信号质量 (0-1)
            market_condition: 市场状况
            trade_reason: 交易原因
            
        Returns:
            交易记录，如果交易失败则返回None
        """
        try:
            # 输入验证
            if price <= 0 or volume <= 0:
                logger.warning(f"无效的交易参数: 价格={price}, 数量={volume}")
                return None
                
            if action not in ['buy', 'sell']:
                logger.warning(f"无效的交易动作: {action}")
                return None
                
            # 清除缓存
            self._calculation_cache.clear()
            self._metric_cache.clear()
            
            # 获取当前持仓
            current_position = self.positions.get(symbol, {})
            current_volume = current_position.get('volume', 0.0)
            
            # 计算交易价值
            trade_value = price * volume
            
            # 应用滑点（买入时价格上浮，卖出时价格下浮）
            slippage = 0.001  # 0.1%的滑点
            effective_price = price * (1 + slippage) if action == 'buy' else price * (1 - slippage)
            effective_value = effective_price * volume
            
            # 初始化利润变量
            profit = 0.0
            
            # 执行交易
            if action == 'buy':
                # 检查资金是否足够
                if effective_value > self.current_capital:
                    logger.warning(f"资金不足: 需要{effective_value:.2f}, 可用{self.current_capital:.2f}")
                    return None
                    
                # 更新资金和持仓
                self.current_capital -= effective_value
                
                # 如果已有持仓，计算平均成本
                if current_volume > 0:
                    # 计算新的平均成本
                    total_cost = current_position.get('cost', 0) + effective_value
                    total_volume = current_volume + volume
                    avg_cost = total_cost / total_volume
                    
                    # 更新持仓信息
                    self.positions[symbol] = {
                        'volume': total_volume,
                        'cost': total_cost,
                        'avg_price': avg_cost,
                        'entry_price': current_position.get('entry_price', effective_price),
                        'entry_date': current_position.get('entry_date', timestamp),
                        'stop_loss': current_position.get('stop_loss', 0),
                        'take_profit': current_position.get('take_profit', 0),
                        'value': total_volume * price
                    }
                else:
                    # 新建持仓
                    self.positions[symbol] = {
                        'volume': volume,
                        'cost': effective_value,
                        'avg_price': effective_price,
                        'entry_price': effective_price,
                        'entry_date': timestamp,
                        'stop_loss': 0,  # 后续会设置
                        'take_profit': 0,  # 后续会设置
                        'value': volume * price
                    }
            else:  # sell
                # 检查持仓是否足够
                if volume > current_volume:
                    logger.warning(f"持仓不足: 需要{volume}, 可用{current_volume}")
                    return None
                    
                # 计算利润
                avg_price = current_position.get('avg_price', price)
                profit = (effective_price - avg_price) * volume
                
                # 更新资金和持仓
                self.current_capital += effective_value
                remaining_volume = current_volume - volume
                
                if remaining_volume > 0:
                    # 更新持仓信息
                    self.positions[symbol]['volume'] = remaining_volume
                    self.positions[symbol]['value'] = remaining_volume * price
                else:
                    # 清空持仓
                    self.positions.pop(symbol, None)
                    
                # 更新交易统计
                self.total_profit += profit
                
                # 更新连续亏损计数
                if profit > 0:
                    self.consecutive_losses = 0
                else:
                    self.consecutive_losses += 1
                    
                # 记录交易历史
                if symbol not in self.trade_history:
                    self.trade_history[symbol] = []
                    
                # 计算持仓天数
                entry_date = current_position.get('entry_date', timestamp)
                holding_days = (timestamp - entry_date).days if entry_date else 0
            
            # 更新最大资金和回撤
            self.max_capital = max(self.max_capital, self.current_capital)
            self.current_drawdown = max(0, self.max_capital - self.current_capital)
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
            
            # 创建交易记录
            trade = TradeRecord(
                timestamp=timestamp,
                symbol=symbol,
                action=action,
                price=price,
                volume=volume,
                position=self.positions.get(symbol, {}).get('volume', 0),
                profit=profit if action == 'sell' else 0.0,
                drawdown=self.current_drawdown,
                entry_price=current_position.get('entry_price', price) if action == 'sell' else price,
                exit_price=price if action == 'sell' else 0.0,
                holding_days=holding_days if action == 'sell' else 0,
                stop_loss=current_position.get('stop_loss', 0),
                take_profit=current_position.get('take_profit', 0),
                signal_quality=signal_quality,
                market_condition=market_condition,
                trade_reason=trade_reason
            )
            
            # 记录交易
            self.trades.append(trade)
            
            # 记录每日收益率
            daily_return = (self.current_capital - self.initial_capital) / self.initial_capital
            self.daily_returns.append(daily_return)
            
            # 记录交易日志
            if self.trade_log_enabled:
                logger.info(f"交易执行: {action} {symbol} {volume}股 价格={price:.2f} 有效价格={effective_price:.2f} "
                          f"价值={effective_value:.2f} 利润={profit if action == 'sell' else 0.0:.2f} "
                          f"资金={self.current_capital:.2f} 回撤={self.current_drawdown:.2f}")
                
            return trade
            
        except Exception as e:
            logger.error(f"交易执行失败: {str(e)}")
            return None

    def calculate_metrics(self) -> BacktestResult:
        """计算回测指标
        
        Returns:
            回测结果
        """
        result = BacktestResult()
        
        # 基本指标
        result.trades = self.trades
        result.total_profit = self.total_profit
        result.max_drawdown = self.max_drawdown
        
        # 交易统计
        sell_trades = [t for t in self.trades if t.action == 'sell']
        result.trade_count = len(sell_trades)
        result.win_count = sum(1 for t in sell_trades if t.profit > 0)
        result.loss_count = sum(1 for t in sell_trades if t.profit <= 0)
        
        # 胜率
        result.win_rate = result.win_count / result.trade_count if result.trade_count > 0 else 0.0
        
        # 盈亏比
        avg_win = np.mean([t.profit for t in sell_trades if t.profit > 0]) if result.win_count > 0 else 0.0
        avg_loss = abs(np.mean([t.profit for t in sell_trades if t.profit < 0])) if result.loss_count > 0 else 1.0
        result.profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0
        
        # 平均持仓周期
        result.avg_holding_period = np.mean([t.holding_days for t in sell_trades]) if sell_trades else 0.0
        
        # 收益率和波动率
        if self.daily_returns:
            result.annual_return = np.mean(self.daily_returns) * 252
            result.volatility = np.std(self.daily_returns) * np.sqrt(252)
            result.sharpe_ratio = (result.annual_return - self.risk_free_rate) / result.volatility if result.volatility > 0 else 0.0
        
        # 连续盈亏
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        
        for t in sell_trades:
            if t.profit > 0:
                if current_streak > 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                if current_streak < 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))
        
        result.max_consecutive_wins = max_win_streak
        result.max_consecutive_losses = max_loss_streak
        
        # 高级指标
        win_profits = [t.profit for t in sell_trades if t.profit > 0]
        loss_profits = [t.profit for t in sell_trades if t.profit < 0]
        
        result.avg_win = avg_win
        result.avg_loss = avg_loss
        result.max_win = max(win_profits) if win_profits else 0.0
        result.max_loss = min(loss_profits) if loss_profits else 0.0
        
        # 利润因子 = 总盈利 / 总亏损
        total_win = sum(win_profits)
        total_loss = abs(sum(loss_profits)) if loss_profits else 1.0
        result.profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        
        # 恢复因子 = 总收益 / 最大回撤
        result.recovery_factor = result.total_profit / result.max_drawdown if result.max_drawdown > 0 else float('inf')
        
        # 期望值 = 胜率 * 平均盈利 - (1-胜率) * 平均亏损
        result.expectancy = result.win_rate * avg_win - (1 - result.win_rate) * avg_loss
        
        # 月度收益
        if sell_trades:
            monthly_returns = {}
            for t in sell_trades:
                month_key = t.timestamp.strftime('%Y-%m')
                if month_key not in monthly_returns:
                    monthly_returns[month_key] = 0.0
                monthly_returns[month_key] += t.profit
            result.monthly_returns = monthly_returns
        
        # 回撤周期记录
        if self.daily_returns:
            drawdown_periods = []
            in_drawdown = False
            start_idx = 0
            peak_capital = self.initial_capital
            
            for i, ret in enumerate(self.daily_returns):
                current_capital = self.initial_capital * (1 + ret)
                
                if current_capital > peak_capital:
                    # 新高，如果在回撤中，则结束回撤周期
                    if in_drawdown:
                        drawdown_periods.append({
                            'start_idx': start_idx,
                            'end_idx': i - 1,
                            'duration': i - start_idx,
                            'depth': (peak_capital - self.initial_capital * (1 + self.daily_returns[i-1])) / peak_capital
                        })
                        in_drawdown = False
                    peak_capital = current_capital
                elif current_capital < peak_capital and not in_drawdown:
                    # 开始新的回撤周期
                    in_drawdown = True
                    start_idx = i
            
            # 如果结束时仍在回撤中
            if in_drawdown:
                drawdown_periods.append({
                    'start_idx': start_idx,
                    'end_idx': len(self.daily_returns) - 1,
                    'duration': len(self.daily_returns) - start_idx,
                    'depth': (peak_capital - self.initial_capital * (1 + self.daily_returns[-1])) / peak_capital
                })
            
            result.drawdown_periods = drawdown_periods
        
        return result

    def backtest_strategy(self, data: pd.DataFrame, strategy_func, **strategy_params) -> BacktestResult:
        """回测策略
        
        Args:
            data: 回测数据
            strategy_func: 策略函数，接收数据和参数，返回交易信号
            **strategy_params: 策略参数
            
        Returns:
            回测结果
        """
        try:
            # 重置回测状态
            self.current_capital = self.initial_capital
            self.positions = {}
            self.trades = []
            self.daily_returns = []
            self.max_capital = self.initial_capital
            self.total_profit = 0.0
            self.max_drawdown = 0.0
            self.win_rate = 0.0
            self.current_drawdown = 0.0
            self.consecutive_losses = 0
            self.trade_history = {}
            self.pending_orders = []
            self.active_trailing_stops = {}
            
            # 生成交易信号
            signals = strategy_func(data, **strategy_params)
            
            # 执行回测
            for i, (timestamp, signal) in enumerate(signals.iterrows()):
                # 获取当前价格数据
                current_data = data.loc[timestamp]
                
                # 检查移动止损
                for symbol in list(self.positions.keys()):
                    # 获取当前价格
                    if 'Close' in current_data:
                        current_price = current_data['Close']
                    else:
                        current_price = current_data.get('close', 0)
                        
                    # 更新移动止损
                    new_stop = self.update_trailing_stop(symbol, current_price)
                    if new_stop is None:  # 触发止损
                        # 执行卖出
                        volume = self.positions[symbol]['volume']
                        self.execute_trade(
                            timestamp=timestamp,
                            symbol=symbol,
                            action='sell',
                            price=current_price,
                            volume=volume,
                            signal_quality=0.9,  # 止损信号质量高
                            market_condition="stop_loss",
                            trade_reason="触发移动止损"
                        )
                        
                # 检查时间止损
                for symbol in list(self.positions.keys()):
                    if self.check_time_stop(symbol, timestamp):
                        # 执行卖出
                        volume = self.positions[symbol]['volume']
                        current_price = current_data.get('Close', current_data.get('close', 0))
                        self.execute_trade(
                            timestamp=timestamp,
                            symbol=symbol,
                            action='sell',
                            price=current_price,
                            volume=volume,
                            signal_quality=0.8,
                            market_condition="time_stop",
                            trade_reason="触发时间止损"
                        )
                
                # 处理交易信号
                if signal.get('action') in ['buy', 'sell']:
                    symbol = signal.get('symbol', data.get('symbol', 'unknown'))
                    action = signal['action']
                    price = signal.get('price', current_data.get('Close', current_data.get('close', 0)))
                    
                    # 获取信号质量和市场状况
                    signal_quality = signal.get('signal_quality', 0.8)
                    market_condition = signal.get('market_condition', 'normal')
                    
                    # 计算交易量
                    if action == 'buy':
                        # 如果信号中指定了止损价格，使用它
                        stop_loss = signal.get('stop_loss', 0)
                        if stop_loss <= 0 or stop_loss >= price:
                            # 计算默认止损
                            volatility = signal.get('volatility', current_data.get('ATR', price * 0.02))
                            trend_strength = signal.get('trend_strength', 0.0)
                            stop_loss = self.calculate_stop_loss(price, volatility, trend_strength, signal_quality)
                        
                        # 计算仓位大小
                        if self.use_dynamic_position_sizing:
                            market_condition_score = 0.5  # 默认中性
                            if market_condition == 'bullish':
                                market_condition_score = 0.8
                            elif market_condition == 'bearish':
                                market_condition_score = 0.2
                            
                            volume = self.calculate_dynamic_position_size(
                                price, stop_loss, signal_quality, market_condition_score)
                        else:
                            # 固定仓位
                            position_value = self.current_capital * self.max_position_ratio
                            volume = position_value / price
                    
                    # 执行交易
                    trade = self.execute_trade(
                        timestamp=timestamp,
                        symbol=symbol,
                        action=action,
                        price=price,
                        volume=volume,
                        signal_quality=signal_quality,
                        market_condition=market_condition,
                        trade_reason=signal.get('reason', '')
                    )
                    
                    # 如果是买入交易，设置止损和止盈
                    if trade and action == 'buy':
                        # 设置止损
                        self.positions[symbol]['stop_loss'] = stop_loss
                        
                        # 计算止盈
                        take_profit = self.calculate_take_profit(
                            price, stop_loss, signal.get('trend_strength', 0.0), signal_quality)
                        self.positions[symbol]['take_profit'] = take_profit
                        
                        logger.info(f"设置交易参数: {symbol} 入场={price:.2f}, 止损={stop_loss:.2f}, "
                                  f"止盈={take_profit:.2f}, 仓位={volume}股")
            
            # 平仓所有持仓
            final_timestamp = data.index[-1] if not data.empty else datetime.now()
            for symbol, position in list(self.positions.items()):
                volume = position['volume']
                price = data.loc[final_timestamp, 'Close'] if 'Close' in data.columns else position['avg_price']
                
                self.execute_trade(
                    timestamp=final_timestamp,
                    symbol=symbol,
                    action='sell',
                    price=price,
                    volume=volume,
                    signal_quality=0.5,
                    market_condition="close_position",
                    trade_reason="回测结束平仓"
                )
            
            # 计算回测指标
            result = self.calculate_metrics()
            
            logger.info(f"回测完成: 总收益={result.total_profit:.2f}, 胜率={result.win_rate:.2%}, "
                      f"盈亏比={result.profit_ratio:.2f}, 最大回撤={result.max_drawdown:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"回测失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return BacktestResult()

    def _parallel_backtest(self, strategies):
        futures = [self.dask_client.submit(self._run_single_backtest, strat) for strat in strategies]
        return self.dask_client.gather(futures)
        
    def backtest_volume_price_strategy(self, data, symbol: str):
        """使用体积价格分析策略进行回测
        
        Args:
            data: DataFrame，包含OHLCV数据
            symbol: 股票代码
            
        Returns:
            BacktestResult: 回测结果
        """
        try:
            import logging
            logging.info(f"开始对 {symbol} 执行量价策略回测, 数据长度: {len(data)}")
            
            # 标准化列名 - 确保列名符合预期
            column_mapping = {
                '收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume',
                'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low', 'volume': 'volume',
                'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
            }
            
            # 创建一个新的DataFrame，以标准化列名
            standard_data = pd.DataFrame(index=data.index)
            
            # 复制数据并重命名列
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns:
                    standard_data[new_col] = data[old_col]
            
            # 确保所有必要的列都存在
            required_columns = ['close', 'open', 'high', 'low', 'volume']
            for col in required_columns:
                if col not in standard_data.columns:
                    logging.error(f"缺少必要的列: {col}, 可用列: {data.columns}")
                    return BacktestResult()
            
            # 计算技术指标
            standard_data['volume_ma20'] = standard_data['volume'].rolling(window=20).mean()
            standard_data['price_ma5'] = standard_data['close'].rolling(window=5).mean()
            standard_data['price_ma20'] = standard_data['close'].rolling(window=20).mean()
            standard_data['volume_ratio'] = standard_data['volume'] / standard_data['volume_ma20']
            
            # 初始化状态变量
            positions = []
            capital = self.initial_capital
            current_position = None
            self.trades = []  # 清空之前的交易记录
            self.current_capital = capital  # 初始化当前资金
            
            # 生成交易信号
            for i in range(20, len(standard_data)):  # 从第20天开始，确保有足够的历史数据
                current_date = standard_data.index[i]
                current_price = standard_data['close'].iloc[i]
                current_volume_ratio = standard_data['volume_ratio'].iloc[i]
                price_trend = standard_data['price_ma5'].iloc[i] > standard_data['price_ma20'].iloc[i]
                
                # 生成策略分数 (0-100)
                strategy_score = 0
                
                # 因素1: 成交量比率 (占40分)
                volume_score = min(current_volume_ratio * 20, 40)
                
                # 因素2: 价格趋势 (占30分)
                trend_score = 30 if price_trend else 0
                
                # 因素3: 价格突破 (占30分)
                breakthrough_score = 0
                if current_price > standard_data['high'].iloc[i-1] and current_volume_ratio > 1.5:
                    breakthrough_score = 30
                
                # 计算总分
                strategy_score = volume_score + trend_score + breakthrough_score
                
                # 交易逻辑
                if current_position is None:  # 没有持仓
                    if strategy_score >= 70:  # 高分买入信号
                        # 计算可买入数量
                        shares = int(capital * 0.9 / current_price)  # 使用90%资金
                        if shares > 0:
                            # 创建买入记录
                            trade_record = TradeRecord(
                                timestamp=current_date,
                                symbol=symbol,
                                action='buy',
                                price=current_price,
                                volume=shares,
                                position=shares,
                                profit=0.0,
                                drawdown=0.0,
                                entry_price=current_price,
                                signal_quality=strategy_score/100,
                                market_condition='bullish' if price_trend else 'neutral',
                                trade_reason=f"量价策略信号分数: {strategy_score}"
                            )
                            self.trades.append(trade_record)
                            
                            # 更新资金和当前持仓
                            current_position = {
                                'shares': shares,
                                'buy_price': current_price,
                                'buy_date': current_date,
                                'cost': shares * current_price,
                                'entry_record': trade_record
                            }
                            capital -= current_position['cost']
                            self.current_capital = capital
                            
                            logging.info(f"买入: 日期={current_date}, 价格={current_price:.2f}, "
                                       f"数量={shares}, 剩余资金={capital:.2f}")
                else:  # 有持仓
                    # 计算利润百分比
                    profit_pct = (current_price - current_position['buy_price']) / current_position['buy_price']
                    
                    # 止盈止损或分数过低时卖出
                    if profit_pct >= 0.15 or profit_pct <= -0.08 or (strategy_score < 40 and profit_pct > 0):
                        # 卖出
                        shares = current_position['shares']
                        sell_amount = shares * current_price
                        profit = sell_amount - current_position['cost']
                        
                        # 创建卖出记录
                        trade_record = TradeRecord(
                            timestamp=current_date,
                            symbol=symbol,
                            action='sell',
                            price=current_price,
                            volume=shares,
                            position=0,
                            profit=profit,
                            drawdown=self.current_drawdown,
                            entry_price=current_position['buy_price'],
                            exit_price=current_price,
                            holding_days=(current_date - current_position['buy_date']).days,
                            signal_quality=strategy_score/100,
                            market_condition=market_condition,
                            trade_reason=f"{'止盈' if profit_pct >= 0.15 else '止损' if profit_pct <= -0.08 else '信号转弱'}"
                        )
                        self.trades.append(trade_record)
                        
                        # 更新资金
                        capital += sell_amount
                        self.current_capital = capital
                        
                        # 记录交易
                        positions.append({
                            'buy_date': current_position['buy_date'],
                            'sell_date': current_date,
                            'buy_price': current_position['buy_price'],
                            'sell_price': current_price,
                            'shares': shares,
                            'profit': profit,
                            'profit_pct': profit_pct * 100
                        })
                        
                        logging.info(f"卖出: 日期={current_date}, 价格={current_price:.2f}, "
                                   f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                                   f"当前资金={capital:.2f}")
                        
                        current_position = None
            
            # 如果还有持仓，按最后价格卖出
            if current_position is not None:
                last_date = standard_data.index[-1]
                last_price = standard_data['close'].iloc[-1]
                shares = current_position['shares']
                sell_amount = shares * last_price
                profit = sell_amount - current_position['cost']
                profit_pct = (last_price - current_position['buy_price']) / current_position['buy_price']
                
                # 创建卖出记录
                trade_record = TradeRecord(
                    timestamp=last_date,
                    symbol=symbol,
                    action='sell',
                    price=last_price,
                    volume=shares,
                    position=0,
                    profit=profit,
                    drawdown=self.current_drawdown,
                    entry_price=current_position['buy_price'],
                    exit_price=last_price,
                    holding_days=(last_date - current_position['buy_date']).days,
                    signal_quality=0.5,
                    market_condition='neutral',
                    trade_reason="回测结束平仓"
                )
                self.trades.append(trade_record)
                
                # 更新资金
                capital += sell_amount
                self.current_capital = capital
                
                # 记录交易
                positions.append({
                    'buy_date': current_position['buy_date'],
                    'sell_date': last_date,
                    'buy_price': current_position['buy_price'],
                    'sell_price': last_price,
                    'shares': shares,
                    'profit': profit,
                    'profit_pct': profit_pct * 100
                })
                
                logging.info(f"回测结束平仓: 日期={last_date}, 价格={last_price:.2f}, "
                           f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                           f"最终资金={capital:.2f}")
            
            # 计算回测结果
            result = BacktestResult()
            result.initial_capital = self.initial_capital
            result.final_capital = capital
            result.total_profit = capital - self.initial_capital
            result.profit_pct = (capital - self.initial_capital) / self.initial_capital * 100
            
            # 计算交易统计
            win_trades = len([t for t in positions if t['profit'] > 0])
            total_trades = len(positions)
            result.trade_count = total_trades
            result.win_rate = win_trades / total_trades if total_trades > 0 else 0
            
            # 计算平均持仓周期
            if positions:
                avg_holding_days = sum([(p['sell_date'] - p['buy_date']).days for p in positions]) / len(positions)
                result.avg_holding_period = avg_holding_days
            
            # 计算最大回撤
            max_drawdown = 0
            peak_capital = self.initial_capital
            
            # 模拟资金曲线来计算最大回撤
            capital_curve = [self.initial_capital]
            for trade in positions:
                current_capital = capital_curve[-1] + trade['profit']
                capital_curve.append(current_capital)
                
                if current_capital > peak_capital:
                    peak_capital = current_capital
                else:
                    drawdown = (peak_capital - current_capital) / peak_capital
                    max_drawdown = max(max_drawdown, drawdown)
            
            result.max_drawdown = max_drawdown
            
            # 如果交易次数足够，计算年化收益率
            if total_trades > 0 and len(standard_data) > 20:
                trading_days = (standard_data.index[-1] - standard_data.index[20]).days
                if trading_days > 0:
                    annual_return = ((1 + result.profit_pct/100) ** (365/trading_days)) - 1
                    result.annual_return = annual_return
            
            # 计算盈亏比
            if win_trades > 0 and total_trades > win_trades:
                avg_win = sum([t['profit'] for t in positions if t['profit'] > 0]) / win_trades
                avg_loss = sum([-t['profit'] for t in positions if t['profit'] <= 0]) / (total_trades - win_trades)
                result.profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            # 更新类属性，以便app可以访问
            self.trades = self.trades  # 确保交易记录已更新
            self.current_capital = capital
            self.win_rate = result.win_rate
            self.trade_count = result.trade_count
            self.total_profit = result.total_profit
            self.max_drawdown = result.max_drawdown
            self.sharpe_ratio = 0  # 暂不计算
            self.profit_ratio = result.profit_ratio
            self.annual_return = result.annual_return if hasattr(result, 'annual_return') else 0
            self.avg_holding_period = result.avg_holding_period
            
            logging.info(f"量价策略回测完成: 股票={symbol}, 总利润={result.total_profit:.2f}, "
                       f"交易次数={result.trade_count}, 胜率={result.win_rate*100:.2f}%")
            
            return result
            
        except Exception as e:
            import logging
            logging.error(f"体积价格策略回测出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            
            # 返回空结果，但确保设置基本属性
            result = BacktestResult()
            self.current_capital = self.initial_capital
            self.win_rate = 0
            self.trade_count = 0
            self.total_profit = 0
            self.max_drawdown = 0
            self.sharpe_ratio = 0
            self.profit_ratio = 0
            self.annual_return = 0
            self.avg_holding_period = 0
            
            return result

    def backtest_macd_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """MACD金叉策略回测
        
        Args:
            data: 股票数据，包含OHLCV数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        try:
            import logging
            logging.info(f"开始对 {symbol} 执行MACD策略回测, 数据长度: {len(data)}")
            
            # 标准化列名
            column_mapping = {
                '收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume',
                'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low', 'volume': 'volume',
                'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
            }
            
            # 创建标准化数据
            standard_data = pd.DataFrame(index=data.index)
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns:
                    standard_data[new_col] = data[old_col]
            
            # 检查必要的列
            if 'close' not in standard_data.columns:
                logging.error(f"缺少必要的列: close, 可用列: {data.columns}")
                return BacktestResult()
            
            # 计算MACD指标
            close = standard_data['close']
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            # 添加到数据中
            standard_data['macd'] = macd
            standard_data['macd_signal'] = signal
            standard_data['macd_hist'] = histogram
            standard_data['atr'] = self._calculate_atr(data)
            
            # 生成交易信号
            signals = pd.DataFrame(index=standard_data.index)
            signals['action'] = 'hold'
            signals['price'] = standard_data['close']
            signals['volume'] = 0.0
            signals['signal_quality'] = 0.0
            signals['market_condition'] = 'normal'
            signals['stop_loss'] = 0.0
            
            # 初始化交易状态
            self.trades = []
            self.current_capital = self.initial_capital
            positions = {}
            
            # MACD金叉和死叉
            for i in range(26, len(standard_data)):
                # 金叉: MACD线从下方穿过信号线
                golden_cross = (standard_data['macd'].iloc[i-1] < standard_data['macd_signal'].iloc[i-1]) and \
                               (standard_data['macd'].iloc[i] > standard_data['macd_signal'].iloc[i])
                
                # 死叉: MACD线从上方穿过信号线
                death_cross = (standard_data['macd'].iloc[i-1] > standard_data['macd_signal'].iloc[i-1]) and \
                              (standard_data['macd'].iloc[i] < standard_data['macd_signal'].iloc[i])
                
                # 当前价格
                current_date = standard_data.index[i]
                current_price = standard_data['close'].iloc[i]
                
                # 信号质量 (0-1)
                signal_strength = abs(standard_data['macd_hist'].iloc[i]) / 2  # 标准化到0-1范围
                signal_quality = min(signal_strength, 1.0)
                
                # 市场状况
                if standard_data['macd'].iloc[i] > 0 and standard_data['macd_hist'].iloc[i] > 0:
                    market_condition = "bullish"
                elif standard_data['macd'].iloc[i] < 0 and standard_data['macd_hist'].iloc[i] < 0:
                    market_condition = "bearish"
                else:
                    market_condition = "neutral"
                
                # 处理买入信号
                if golden_cross and symbol not in positions:
                    # 计算止损价格
                    stop_loss = current_price - 2 * standard_data['atr'].iloc[i]
                    
                    # 计算买入资金
                    position_value = self.current_capital * self.max_position_ratio
                    shares = int(position_value / current_price)
                    
                    if shares > 0:
                        # 执行买入
                        trade_record = TradeRecord(
                            timestamp=current_date,
                            symbol=symbol,
                            action='buy',
                            price=current_price,
                            volume=shares,
                            position=shares,
                            profit=0.0,
                            drawdown=0.0,
                            entry_price=current_price,
                            signal_quality=signal_quality,
                            market_condition=market_condition,
                            trade_reason=f"MACD金叉信号"
                        )
                        self.trades.append(trade_record)
                        
                        # 更新资金和持仓
                        cost = shares * current_price
                        self.current_capital -= cost
                        positions[symbol] = {
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': current_date,
                            'cost': cost,
                            'stop_loss': stop_loss
                        }
                        
                        logging.info(f"买入: {symbol}, 日期={current_date}, 价格={current_price:.2f}, "
                                   f"数量={shares}, 止损={stop_loss:.2f}, 剩余资金={self.current_capital:.2f}")
                
                # 处理卖出信号
                elif (death_cross or current_price <= positions.get(symbol, {}).get('stop_loss', 0)) and symbol in positions:
                    position = positions[symbol]
                    shares = position['shares']
                    entry_price = position['entry_price']
                    
                    # 计算利润
                    profit = (current_price - entry_price) * shares
                    profit_pct = (current_price - entry_price) / entry_price
                    
                    # 执行卖出
                    trade_record = TradeRecord(
                        timestamp=current_date,
                        symbol=symbol,
                        action='sell',
                        price=current_price,
                        volume=shares,
                        position=0,
                        profit=profit,
                        drawdown=0.0,
                        entry_price=entry_price,
                        exit_price=current_price,
                        holding_days=(current_date - position['entry_date']).days,
                        signal_quality=signal_quality,
                        market_condition=market_condition,
                        trade_reason=f"{'MACD死叉信号' if death_cross else '止损触发'}"
                    )
                    self.trades.append(trade_record)
                    
                    # 更新资金和持仓
                    self.current_capital += shares * current_price
                    del positions[symbol]
                    
                    logging.info(f"卖出: {symbol}, 日期={current_date}, 价格={current_price:.2f}, "
                               f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                               f"当前资金={self.current_capital:.2f}")
            
            # 如果还有持仓，平仓
            if symbol in positions:
                position = positions[symbol]
                shares = position['shares']
                entry_price = position['entry_price']
                last_date = standard_data.index[-1]
                last_price = standard_data['close'].iloc[-1]
                
                # 计算利润
                profit = (last_price - entry_price) * shares
                profit_pct = (last_price - entry_price) / entry_price
                
                # 执行卖出
                trade_record = TradeRecord(
                    timestamp=last_date,
                    symbol=symbol,
                    action='sell',
                    price=last_price,
                    volume=shares,
                    position=0,
                    profit=profit,
                    drawdown=0.0,
                    entry_price=entry_price,
                    exit_price=last_price,
                    holding_days=(last_date - position['entry_date']).days,
                    signal_quality=0.5,
                    market_condition='neutral',
                    trade_reason="回测结束平仓"
                )
                self.trades.append(trade_record)
                
                # 更新资金
                self.current_capital += shares * last_price
                
                logging.info(f"回测结束平仓: {symbol}, 日期={last_date}, 价格={last_price:.2f}, "
                           f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                           f"最终资金={self.current_capital:.2f}")
            
            # 计算回测结果指标
            result = self.calculate_metrics()
            
            # 更新策略特定属性
            self.trade_count = len([t for t in self.trades if t.action == 'sell'])
            self.total_profit = self.current_capital - self.initial_capital
            
            # 计算胜率
            win_trades = len([t for t in self.trades if t.action == 'sell' and t.profit > 0])
            total_trades = len([t for t in self.trades if t.action == 'sell'])
            self.win_rate = win_trades / total_trades if total_trades > 0 else 0
            
            # 计算最大回撤
            max_drawdown = 0
            peak_capital = self.initial_capital
            current_capital = self.initial_capital
            
            # 模拟资金曲线
            for t in self.trades:
                if t.action == 'buy':
                    current_capital -= t.price * t.volume
                else:  # sell
                    current_capital += t.price * t.volume
                
                if current_capital > peak_capital:
                    peak_capital = current_capital
                else:
                    drawdown = (peak_capital - current_capital) / peak_capital
                    max_drawdown = max(max_drawdown, drawdown)
            
            self.max_drawdown = max_drawdown
            
            # 设置其他回测指标
            self.sharpe_ratio = 0  # 需要更多数据计算
            
            # 计算平均持仓周期
            holding_days = [t.holding_days for t in self.trades if t.action == 'sell']
            self.avg_holding_period = sum(holding_days) / len(holding_days) if holding_days else 0
            
            # 计算盈亏比
            win_profits = [t.profit for t in self.trades if t.action == 'sell' and t.profit > 0]
            loss_profits = [abs(t.profit) for t in self.trades if t.action == 'sell' and t.profit < 0]
            
            avg_win = sum(win_profits) / len(win_profits) if win_profits else 0
            avg_loss = sum(loss_profits) / len(loss_profits) if loss_profits else 1  # 避免除以零
            
            self.profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            # 计算年化收益率
            if len(standard_data) > 26:
                days = (standard_data.index[-1] - standard_data.index[26]).days
                if days > 0:
                    self.annual_return = ((self.current_capital / self.initial_capital) ** (365 / days)) - 1
                else:
                    self.annual_return = 0
            else:
                self.annual_return = 0
            
            logging.info(f"MACD策略回测完成: {symbol}, 总利润={self.total_profit:.2f}, "
                       f"交易次数={self.trade_count}, 胜率={self.win_rate*100:.2f}%, "
                       f"年化收益率={self.annual_return*100:.2f}%")
            
            return result
            
        except Exception as e:
            import logging
            import traceback
            logging.error(f"MACD策略回测出错: {str(e)}")
            logging.error(traceback.format_exc())
            
            # 设置默认值，避免属性错误
            self.current_capital = self.initial_capital
            self.win_rate = 0
            self.trade_count = 0
            self.total_profit = 0
            self.max_drawdown = 0
            self.sharpe_ratio = 0
            self.profit_ratio = 0
            self.annual_return = 0
            self.avg_holding_period = 0
            
            return BacktestResult()

    def _get_volatility_percentile(self) -> float:
        """获取当前市场波动率分位数
        
        如果未计算波动率分位数，返回默认值0.5
        
        Returns:
            波动率分位数 (0-1)
        """
        return self.market_volatility_percentile

    def backtest_ma_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """双均线策略回测
        
        Args:
            data: 股票数据，包含OHLCV数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        try:
            import logging
            logging.info(f"开始对 {symbol} 执行双均线策略回测, 数据长度: {len(data)}")
            
            # 标准化列名
            column_mapping = {
                '收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume',
                'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low', 'volume': 'volume',
                'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
            }
            
            # 创建标准化数据
            standard_data = pd.DataFrame(index=data.index)
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns:
                    standard_data[new_col] = data[old_col]
            
            # 检查必要的列
            if 'close' not in standard_data.columns:
                logging.error(f"缺少必要的列: close, 可用列: {data.columns}")
                return BacktestResult()
            
            # 计算移动平均线
            short_ma = 5  # 短期均线
            long_ma = 20  # 长期均线
            
            standard_data['ma_short'] = standard_data['close'].rolling(window=short_ma).mean()
            standard_data['ma_long'] = standard_data['close'].rolling(window=long_ma).mean()
            standard_data['atr'] = self._calculate_atr(data)
            
            # 初始化交易状态
            self.trades = []
            self.current_capital = self.initial_capital
            positions = {}
            
            # 生成交易信号
            for i in range(long_ma, len(standard_data)):
                # 金叉: 短期均线上穿长期均线
                golden_cross = (standard_data['ma_short'].iloc[i-1] <= standard_data['ma_long'].iloc[i-1]) and \
                             (standard_data['ma_short'].iloc[i] > standard_data['ma_long'].iloc[i])
                
                # 死叉: 短期均线下穿长期均线
                death_cross = (standard_data['ma_short'].iloc[i-1] >= standard_data['ma_long'].iloc[i-1]) and \
                            (standard_data['ma_short'].iloc[i] < standard_data['ma_long'].iloc[i])
                
                # 当前价格和日期
                current_date = standard_data.index[i]
                current_price = standard_data['close'].iloc[i]
                
                # 计算信号质量 (0-1)
                ma_diff = abs(standard_data['ma_short'].iloc[i] - standard_data['ma_long'].iloc[i]) / standard_data['close'].iloc[i]
                signal_quality = min(ma_diff * 20, 1.0)  # 标准化到0-1范围
                
                # 市场状况
                if standard_data['ma_short'].iloc[i] > standard_data['ma_long'].iloc[i]:
                    market_condition = "bullish"
                else:
                    market_condition = "bearish"
                
                # 处理买入信号
                if golden_cross and symbol not in positions:
                    # 计算止损价格
                    stop_loss = current_price - 2 * standard_data['atr'].iloc[i]
                    
                    # 计算买入资金
                    position_value = self.current_capital * self.max_position_ratio
                    shares = int(position_value / current_price)
                    
                    if shares > 0:
                        # 执行买入
                        trade_record = TradeRecord(
                            timestamp=current_date,
                            symbol=symbol,
                            action='buy',
                            price=current_price,
                            volume=shares,
                            position=shares,
                            profit=0.0,
                            drawdown=0.0,
                            entry_price=current_price,
                            signal_quality=signal_quality,
                            market_condition=market_condition,
                            trade_reason=f"MA{short_ma}上穿MA{long_ma}"
                        )
                        self.trades.append(trade_record)
                        
                        # 更新资金和持仓
                        cost = shares * current_price
                        self.current_capital -= cost
                        positions[symbol] = {
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': current_date,
                            'cost': cost,
                            'stop_loss': stop_loss
                        }
                        
                        logging.info(f"买入: {symbol}, 日期={current_date}, 价格={current_price:.2f}, "
                                   f"数量={shares}, 止损={stop_loss:.2f}, 剩余资金={self.current_capital:.2f}")
                
                # 处理卖出信号
                elif (death_cross or current_price <= positions.get(symbol, {}).get('stop_loss', 0)) and symbol in positions:
                    position = positions[symbol]
                    shares = position['shares']
                    entry_price = position['entry_price']
                    
                    # 计算利润
                    profit = (current_price - entry_price) * shares
                    profit_pct = (current_price - entry_price) / entry_price
                    
                    # 执行卖出
                    trade_record = TradeRecord(
                        timestamp=current_date,
                        symbol=symbol,
                        action='sell',
                        price=current_price,
                        volume=shares,
                        position=0,
                        profit=profit,
                        drawdown=0.0,
                        entry_price=entry_price,
                        exit_price=current_price,
                        holding_days=(current_date - position['entry_date']).days,
                        signal_quality=signal_quality,
                        market_condition=market_condition,
                        trade_reason=f"{'MA死叉信号' if death_cross else '止损触发'}"
                    )
                    self.trades.append(trade_record)
                    
                    # 更新资金和持仓
                    self.current_capital += shares * current_price
                    del positions[symbol]
                    
                    logging.info(f"卖出: {symbol}, 日期={current_date}, 价格={current_price:.2f}, "
                              f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                              f"当前资金={self.current_capital:.2f}")
            
            # 如果还有持仓，平仓
            if symbol in positions:
                position = positions[symbol]
                shares = position['shares']
                entry_price = position['entry_price']
                last_date = standard_data.index[-1]
                last_price = standard_data['close'].iloc[-1]
                
                # 计算利润
                profit = (last_price - entry_price) * shares
                profit_pct = (last_price - entry_price) / entry_price
                
                # 执行卖出
                trade_record = TradeRecord(
                    timestamp=last_date,
                    symbol=symbol,
                    action='sell',
                    price=last_price,
                    volume=shares,
                    position=0,
                    profit=profit,
                    drawdown=0.0,
                    entry_price=entry_price,
                    exit_price=last_price,
                    holding_days=(last_date - position['entry_date']).days,
                    signal_quality=0.5,
                    market_condition='neutral',
                    trade_reason="回测结束平仓"
                )
                self.trades.append(trade_record)
                
                # 更新资金
                self.current_capital += shares * last_price
                
                logging.info(f"回测结束平仓: {symbol}, 日期={last_date}, 价格={last_price:.2f}, "
                          f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                          f"最终资金={self.current_capital:.2f}")
            
            # 计算回测结果指标
            result = self.calculate_metrics()
            
            # 更新策略特定属性
            self.trade_count = len([t for t in self.trades if t.action == 'sell'])
            self.total_profit = self.current_capital - self.initial_capital
            
            # 计算胜率
            win_trades = len([t for t in self.trades if t.action == 'sell' and t.profit > 0])
            total_trades = len([t for t in self.trades if t.action == 'sell'])
            self.win_rate = win_trades / total_trades if total_trades > 0 else 0
            
            # 计算最大回撤
            max_drawdown = 0
            peak_capital = self.initial_capital
            current_capital = self.initial_capital
            
            # 模拟资金曲线
            for t in sorted(self.trades, key=lambda x: x.timestamp):
                if t.action == 'buy':
                    current_capital -= t.price * t.volume
                else:  # sell
                    current_capital += t.price * t.volume
                
                if current_capital > peak_capital:
                    peak_capital = current_capital
                else:
                    drawdown = (peak_capital - current_capital) / peak_capital
                    max_drawdown = max(max_drawdown, drawdown)
            
            self.max_drawdown = max_drawdown
            
            # 设置其他回测指标
            self.sharpe_ratio = 0  # 需要更多数据计算
            
            # 计算平均持仓周期
            holding_days = [t.holding_days for t in self.trades if t.action == 'sell']
            self.avg_holding_period = sum(holding_days) / len(holding_days) if holding_days else 0
            
            # 计算盈亏比
            win_profits = [t.profit for t in self.trades if t.action == 'sell' and t.profit > 0]
            loss_profits = [abs(t.profit) for t in self.trades if t.action == 'sell' and t.profit < 0]
            
            avg_win = sum(win_profits) / len(win_profits) if win_profits else 0
            avg_loss = sum(loss_profits) / len(loss_profits) if loss_profits else 1  # 避免除以零
            
            self.profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            # 计算年化收益率
            if len(standard_data) > long_ma:
                days = (standard_data.index[-1] - standard_data.index[long_ma]).days
                if days > 0:
                    self.annual_return = ((self.current_capital / self.initial_capital) ** (365 / days)) - 1
                else:
                    self.annual_return = 0
            else:
                self.annual_return = 0
            
            logging.info(f"双均线策略回测完成: {symbol}, 总利润={self.total_profit:.2f}, "
                       f"交易次数={self.trade_count}, 胜率={self.win_rate*100:.2f}%, "
                       f"年化收益率={self.annual_return*100:.2f}%")
            
            return result
            
        except Exception as e:
            import logging
            import traceback
            logging.error(f"双均线策略回测出错: {str(e)}")
            logging.error(traceback.format_exc())
            
            # 设置默认值，避免属性错误
            self.current_capital = self.initial_capital
            self.win_rate = 0
            self.trade_count = 0
            self.total_profit = 0
            self.max_drawdown = 0
            self.sharpe_ratio = 0
            self.profit_ratio = 0
            self.annual_return = 0
            self.avg_holding_period = 0
            
            return BacktestResult()

    def backtest_bollinger_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """布林带策略回测
        
        Args:
            data: 股票数据，包含OHLCV数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        try:
            import logging
            logging.info(f"开始对 {symbol} 执行布林带策略回测, 数据长度: {len(data)}")
            
            # 标准化列名
            column_mapping = {
                '收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume',
                'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low', 'volume': 'volume',
                'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
            }
            
            # 创建标准化数据
            standard_data = pd.DataFrame(index=data.index)
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns:
                    standard_data[new_col] = data[old_col]
            
            # 检查必要的列
            if 'close' not in standard_data.columns:
                logging.error(f"缺少必要的列: close, 可用列: {data.columns}")
                return BacktestResult()
            
            # 计算布林带指标
            period = 20
            std_dev = 2
            
            standard_data['middle_band'] = standard_data['close'].rolling(window=period).mean()
            std = standard_data['close'].rolling(window=period).std()
            standard_data['upper_band'] = standard_data['middle_band'] + (std * std_dev)
            standard_data['lower_band'] = standard_data['middle_band'] - (std * std_dev)
            standard_data['bandwidth'] = (standard_data['upper_band'] - standard_data['lower_band']) / standard_data['middle_band']
            standard_data['atr'] = self._calculate_atr(data)
            
            # 初始化交易状态
            self.trades = []
            self.current_capital = self.initial_capital
            positions = {}
            
            # 生成交易信号
            for i in range(period, len(standard_data)):
                # 当前价格和日期
                current_date = standard_data.index[i]
                current_price = standard_data['close'].iloc[i]
                
                # 计算信号质量 (0-1)
                # 带宽作为信号质量的指标，带宽越大，波动性越大，信号质量越低
                bandwidth = standard_data['bandwidth'].iloc[i]
                signal_quality = max(0, min(1, 1 - (bandwidth * 5)))  # 标准化到0-1范围
                
                # 下轨买入信号: 价格触及下轨
                lower_touch = current_price <= standard_data['lower_band'].iloc[i]
                
                # 上轨卖出信号: 价格触及上轨
                upper_touch = current_price >= standard_data['upper_band'].iloc[i]
                
                # 回归均值信号: 价格回归到中轨附近
                mean_reversion = abs(current_price - standard_data['middle_band'].iloc[i]) / standard_data['middle_band'].iloc[i] < 0.01
                
                # 市场状况
                if current_price > standard_data['middle_band'].iloc[i]:
                    market_condition = "bullish"
                elif current_price < standard_data['middle_band'].iloc[i]:
                    market_condition = "bearish"
                else:
                    market_condition = "neutral"
                
                # 处理买入信号
                if lower_touch and symbol not in positions:
                    # 计算止损价格
                    stop_loss = current_price - 1.5 * standard_data['atr'].iloc[i]
                    
                    # 计算买入资金
                    position_value = self.current_capital * self.max_position_ratio
                    shares = int(position_value / current_price)
                    
                    if shares > 0:
                        # 执行买入
                        trade_record = TradeRecord(
                            timestamp=current_date,
                            symbol=symbol,
                            action='buy',
                            price=current_price,
                            volume=shares,
                            position=shares,
                            profit=0.0,
                            drawdown=0.0,
                            entry_price=current_price,
                            signal_quality=signal_quality,
                            market_condition=market_condition,
                            trade_reason="价格触及布林带下轨"
                        )
                        self.trades.append(trade_record)
                        
                        # 更新资金和持仓
                        cost = shares * current_price
                        self.current_capital -= cost
                        positions[symbol] = {
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': current_date,
                            'cost': cost,
                            'stop_loss': stop_loss
                        }
                        
                        logging.info(f"买入: {symbol}, 日期={current_date}, 价格={current_price:.2f}, "
                                   f"数量={shares}, 止损={stop_loss:.2f}, 剩余资金={self.current_capital:.2f}")
                
                # 处理卖出信号
                elif ((upper_touch or (mean_reversion and symbol in positions and current_price > positions[symbol]['entry_price'])) or 
                      current_price <= positions.get(symbol, {}).get('stop_loss', 0)) and symbol in positions:
                    position = positions[symbol]
                    shares = position['shares']
                    entry_price = position['entry_price']
                    
                    # 计算利润
                    profit = (current_price - entry_price) * shares
                    profit_pct = (current_price - entry_price) / entry_price
                    
                    # 确定卖出原因
                    if upper_touch:
                        reason = "价格触及布林带上轨"
                    elif mean_reversion:
                        reason = "价格回归均值，盈利了结"
                    else:
                        reason = "止损触发"
                    
                    # 执行卖出
                    trade_record = TradeRecord(
                        timestamp=current_date,
                        symbol=symbol,
                        action='sell',
                        price=current_price,
                        volume=shares,
                        position=0,
                        profit=profit,
                        drawdown=0.0,
                        entry_price=entry_price,
                        exit_price=current_price,
                        holding_days=(current_date - position['entry_date']).days,
                        signal_quality=signal_quality,
                        market_condition=market_condition,
                        trade_reason=reason
                    )
                    self.trades.append(trade_record)
                    
                    # 更新资金和持仓
                    self.current_capital += shares * current_price
                    del positions[symbol]
                    
                    logging.info(f"卖出: {symbol}, 日期={current_date}, 价格={current_price:.2f}, "
                              f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                              f"当前资金={self.current_capital:.2f}, 原因={reason}")
            
            # 如果还有持仓，平仓
            if symbol in positions:
                position = positions[symbol]
                shares = position['shares']
                entry_price = position['entry_price']
                last_date = standard_data.index[-1]
                last_price = standard_data['close'].iloc[-1]
                
                # 计算利润
                profit = (last_price - entry_price) * shares
                profit_pct = (last_price - entry_price) / entry_price
                
                # 执行卖出
                trade_record = TradeRecord(
                    timestamp=last_date,
                    symbol=symbol,
                    action='sell',
                    price=last_price,
                    volume=shares,
                    position=0,
                    profit=profit,
                    drawdown=0.0,
                    entry_price=entry_price,
                    exit_price=last_price,
                    holding_days=(last_date - position['entry_date']).days,
                    signal_quality=0.5,
                    market_condition='neutral',
                    trade_reason="回测结束平仓"
                )
                self.trades.append(trade_record)
                
                # 更新资金
                self.current_capital += shares * last_price
                
                logging.info(f"回测结束平仓: {symbol}, 日期={last_date}, 价格={last_price:.2f}, "
                          f"数量={shares}, 利润={profit:.2f}, 收益率={profit_pct*100:.2f}%, "
                          f"最终资金={self.current_capital:.2f}")
            
            # 计算回测结果指标
            result = self.calculate_metrics()
            
            # 更新策略特定属性
            self.trade_count = len([t for t in self.trades if t.action == 'sell'])
            self.total_profit = self.current_capital - self.initial_capital
            
            # 计算胜率
            win_trades = len([t for t in self.trades if t.action == 'sell' and t.profit > 0])
            total_trades = len([t for t in self.trades if t.action == 'sell'])
            self.win_rate = win_trades / total_trades if total_trades > 0 else 0
            
            # 计算最大回撤
            max_drawdown = 0
            peak_capital = self.initial_capital
            current_capital = self.initial_capital
            
            # 模拟资金曲线
            for t in sorted(self.trades, key=lambda x: x.timestamp):
                if t.action == 'buy':
                    current_capital -= t.price * t.volume
                else:  # sell
                    current_capital += t.price * t.volume
                
                if current_capital > peak_capital:
                    peak_capital = current_capital
                else:
                    drawdown = (peak_capital - current_capital) / peak_capital
                    max_drawdown = max(max_drawdown, drawdown)
            
            self.max_drawdown = max_drawdown
            
            # 设置其他回测指标
            self.sharpe_ratio = 0  # 需要更多数据计算
            
            # 计算平均持仓周期
            holding_days = [t.holding_days for t in self.trades if t.action == 'sell']
            self.avg_holding_period = sum(holding_days) / len(holding_days) if holding_days else 0
            
            # 计算盈亏比
            win_profits = [t.profit for t in self.trades if t.action == 'sell' and t.profit > 0]
            loss_profits = [abs(t.profit) for t in self.trades if t.action == 'sell' and t.profit < 0]
            
            avg_win = sum(win_profits) / len(win_profits) if win_profits else 0
            avg_loss = sum(loss_profits) / len(loss_profits) if loss_profits else 1  # 避免除以零
            
            self.profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            # 计算年化收益率
            if len(standard_data) > period:
                days = (standard_data.index[-1] - standard_data.index[period]).days
                if days > 0:
                    self.annual_return = ((self.current_capital / self.initial_capital) ** (365 / days)) - 1
                else:
                    self.annual_return = 0
            else:
                self.annual_return = 0
            
            logging.info(f"布林带策略回测完成: {symbol}, 总利润={self.total_profit:.2f}, "
                       f"交易次数={self.trade_count}, 胜率={self.win_rate*100:.2f}%, "
                       f"年化收益率={self.annual_return*100:.2f}%")
            
            return result
            
        except Exception as e:
            import logging
            import traceback
            logging.error(f"布林带策略回测出错: {str(e)}")
            logging.error(traceback.format_exc())
            
            # 设置默认值，避免属性错误
            self.current_capital = self.initial_capital
            self.win_rate = 0
            self.trade_count = 0
            self.total_profit = 0
            self.max_drawdown = 0
            self.sharpe_ratio = 0
            self.profit_ratio = 0
            self.annual_return = 0
            self.avg_holding_period = 0
            
            return BacktestResult()

    def _init_risk_params(self, data: pd.DataFrame):
        """初始化风险控制参数，基于当前市场状态调整风险参数
        
        Args:
            data: 股票数据，用于分析市场状态
        """
        try:
            # 计算波动率
            if 'close' in data.columns:
                returns = data['close'].pct_change().dropna()
            elif '收盘' in data.columns:
                returns = data['收盘'].pct_change().dropna()
            else:
                returns = None
                
            if returns is not None and len(returns) > 20:
                # 计算波动率
                volatility = returns.std() * (252 ** 0.5)  # 年化波动率
                
                # 计算市场趋势强度
                if 'close' in data.columns:
                    price = data['close']
                elif '收盘' in data.columns:
                    price = data['收盘']
                else:
                    price = None
                    
                if price is not None and len(price) > 50:
                    ma50 = price.rolling(window=50).mean()
                    ma200 = price.rolling(window=200).mean()
                    
                    # 趋势强度
                    if not ma50.empty and not ma200.empty:
                        trend_strength = (ma50.iloc[-1] / ma200.iloc[-1] - 1) * 100  # 百分比形式
                        self.market_trend_strength = max(-1, min(1, trend_strength / 10))  # 归一化到[-1, 1]
                    
                # 根据波动率调整参数
                if volatility > 0.3:  # 高波动率
                    self.market_volatility_percentile = 0.9
                    self.max_position_ratio = 0.05  # 降低仓位
                    self.trailing_stop_pct = 0.06  # 提高止损幅度
                elif volatility > 0.2:  # 中高波动率
                    self.market_volatility_percentile = 0.7
                    self.max_position_ratio = 0.06
                    self.trailing_stop_pct = 0.05
                elif volatility > 0.15:  # 中等波动率
                    self.market_volatility_percentile = 0.5
                    self.max_position_ratio = 0.07
                    self.trailing_stop_pct = 0.05
                else:  # 低波动率
                    self.market_volatility_percentile = 0.3
                    self.max_position_ratio = 0.08
                    self.trailing_stop_pct = 0.04  # 降低止损幅度
                    
                # 根据趋势强度调整参数
                if hasattr(self, 'market_trend_strength'):
                    if self.market_trend_strength > 0.5:  # 强上升趋势
                        self.min_profit_ratio = 3.0  # 放宽止盈标准
                        self.max_holding_days = 15  # 延长持仓时间
                    elif self.market_trend_strength < -0.5:  # 强下降趋势
                        self.min_profit_ratio = 4.0  # 提高止盈标准
                        self.max_holding_days = 5  # 缩短持仓时间
                    else:  # 震荡市场
                        self.min_profit_ratio = 3.5
                        self.max_holding_days = 10
            
        except Exception as e:
            import logging
            logging.error(f"初始化风险参数出错: {str(e)}")
            
            # 使用默认值
            self.market_volatility_percentile = 0.5
            self.max_position_ratio = 0.08
            self.trailing_stop_pct = 0.05
            self.min_profit_ratio = 3.5
            self.max_holding_days = 10

    def _calculate_trailing_stop(self, row):
        """计算移动止损价格
        
        Args:
            row: 数据行
            
        Returns:
            移动止损价格
        """
        try:
            # 如果没有ATR，返回0
            if 'ATR' not in row:
                return 0
                
            # 计算基础止损价格
            if 'Dynamic_Stop' in row:
                # 使用已经计算的动态止损
                stop_price = row['Dynamic_Stop']
            else:
                # 使用ATR计算止损
                stop_price = row['收盘'] - 2 * row['ATR']
                
            return stop_price
            
        except Exception as e:
            import logging
            logging.error(f"计算移动止损价格时出错: {str(e)}")
            return 0

    def _calculate_position_size(self, data):
        """计算每行数据的动态仓位大小
        
        Args:
            data: 包含价格和技术指标的DataFrame
            
        Returns:
            包含仓位大小的Series
        """
        try:
            # 获取价格和ATR
            if 'close' in data.columns:
                price = data['close']
            elif '收盘' in data.columns:
                price = data['收盘']
            else:
                return pd.Series(0, index=data.index)
                
            if 'ATR' in data.columns:
                atr = data['ATR']
            else:
                atr = self._calculate_atr(data)
            
            # 计算仓位大小
            position_sizes = pd.Series(index=data.index)
            
            for i in range(len(data)):
                current_price = price.iloc[i]
                
                # 计算止损距离
                stop_loss_distance = 2 * atr.iloc[i]
                
                # 计算每手风险金额
                risk_per_unit = stop_loss_distance * 100  # 假设每手100股
                
                # 计算总风险金额（账户的1%）
                total_risk_amount = self.initial_capital * 0.01
                
                # 计算可以承担的手数
                units = total_risk_amount / risk_per_unit
                
                # 限制最大仓位
                max_units = (self.initial_capital * self.max_position_ratio) / (current_price * 100)
                units = min(units, max_units)
                
                # 保存到Series
                position_sizes.iloc[i] = max(0, units * 100)  # 转换为股数
            
            return position_sizes
            
        except Exception as e:
            import logging
            logging.error(f"计算动态仓位大小时出错: {str(e)}")
            return pd.Series(0, index=data.index)