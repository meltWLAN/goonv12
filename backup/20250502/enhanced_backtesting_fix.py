import pandas as pd
import numpy as np
import talib as ta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
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
        self._thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count()*2)
        self._calculation_cache = LRUCache(maxsize=1024)
        self._metric_cache = {}
        self.market_volatility_percentile = 0.5  # 市场波动率分位数
        
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
        # 初始化线程锁
        self.cache_lock = threading.Lock()
        
        # 初始化日志
        logger.info(f"初始化增强版回测系统，初始资金: {initial_capital}")
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标
        
        Args:
            prices: 价格序列
            period: 计算周期
            
        Returns:
            RSI指标值序列
        """
        # 计算价格变化
        delta = prices.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 计算相对强度
        rs = avg_gain / avg_loss.where(avg_loss != 0, 1)  # 避免除以零
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _get_volatility_percentile(self) -> float:
        """获取当前市场波动率分位数
        
        Returns:
            波动率分位数 (0-1)
        """
        # 这里简化处理，实际应用中应该基于历史数据计算
        return self.market_volatility_percentile

    def backtest_kdj_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """KDJ金叉策略回测
        
        Args:
            data: 股票数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
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

    def calculate_dynamic_position_size(self, price: float, stop_loss: float, 
                                      signal_quality: float = 0.8, 
                                      market_condition: float = 0.5) -> float:
        """计算动态仓位大小
        
        Args:
            price: 当前价格
            stop_loss: 止损价格
            signal_quality: 信号质量 (0-1)
            market_condition: 市场状况评分 (0-1)
            
        Returns:
            建议的仓位大小（股数）
        """
        # 计算风险金额（当前资金的一定比例）
        risk_per_trade_base = 0.01  # 基础风险比例1%
        
        # 根据信号质量和市场状况调整风险比例
        quality_factor = 0.5 + signal_quality * 0.5  # 0.5-1.0
        market_factor = 0.7 + market_condition * 0.6  # 0.7-1.3
        
        # 连续亏损调整因子
        # 改进后的连续亏损因子（指数衰减算法）
        loss_factor = max(0.3, 0.9 ** self.consecutive_losses)
        # 加入市场波动率状态影响
        market_vol_state = 1.0 + (self.market_volatility_percentile - 0.5) * 0.4
        
        # 回撤调整因子
        drawdown_ratio = self.current_drawdown / (self.max_drawdown_limit * self.initial_capital)
        drawdown_factor = max(0.5, 1.0 - drawdown_ratio)
        
        # 综合风险比例
        # 加入波动率状态调整
        adjusted_risk = risk_per_trade_base * quality_factor * market_factor * loss_factor * drawdown_factor * market_vol_state
        
        # 确保风险比例不超过最大限制
        adjusted_risk = min(adjusted_risk, 0.02)  # 最大2%
        
        # 计算风险金额
        risk_amount = self.current_capital * adjusted_risk
        
        # 计算每股风险
        per_share_risk = abs(price - stop_loss)
        if per_share_risk <= 0 or price <= 0:
            logger.warning(f"无效的风险计算参数: 价格={price}, 止损={stop_loss}")
            per_share_risk = price * 0.01  # 默认使用1%作为止损距离
        
        # 计算仓位大小
        position_size = risk_amount / per_share_risk
        
        # 确保仓位不超过最大限制
        max_position_value = self.current_capital * self.max_position_ratio
        position_size = min(position_size, max_position_value / price)
        
        # 检查总仓位限制
        total_position_value = sum(pos.get('value', 0) for pos in self.positions.values())
        available_position_value = (self.current_capital * self.max_total_position) - total_position_value
        position_size = min(position_size, available_position_value / price)
        
        logger.info(f"动态仓位计算: 信号质量={signal_quality:.2f}, 市场状况={market_condition:.2f}, "
                  f"连续亏损={self.consecutive_losses}, 回撤因子={drawdown_factor:.2f}, "
                  f"建议仓位={position_size:.2f}股")
        
        return position_size
        
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
                    volume = 0
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
                    elif action == 'sell':
                        # 卖出时使用当前持仓量
                        if symbol in self.positions:
                            volume = self.positions[symbol]['volume']
                        else:
                            continue  # 没有持仓，跳过卖出信号
                    
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
                price = data.loc[final_timestamp, '收盘'] if '收盘' in data.columns else position['avg_price']
                
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
        
    # 添加更多策略方法
    def backtest_macd_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """MACD金叉策略回测
        
        Args:
            data: 股票数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        # 计算MACD指标
        data['EMA12'] = data['收盘'].ewm(span=12, adjust=False).mean()
        data['EMA26'] = data['收盘'].ewm(span=26, adjust=False).mean()
        data['DIF'] = data['EMA12'] - data['EMA26']
        data['DEA'] = data['DIF'].ewm(span=9, adjust=False).mean()
        data['MACD'] = (data['DIF'] - data['DEA']) * 2
        
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
        
        # MACD金叉和死叉
        buy_signals = (data['DIF'] > data['DEA']) & (data['DIF'].shift(1) <= data['DEA'].shift(1))
        sell_signals = (data['DIF'] < data['DEA']) & (data['DIF'].shift(1) >= data['DEA'].shift(1))
        
        # 结合成交量和趋势强度优化信号
        for i in range(len(data)):
            if i < 30:  # 跳过前30个数据点，确保指标已经稳定
                continue
                
            current_price = data['收盘'].iloc[i]
            current_volume = data['成交量'].iloc[i]
            volume_ma = data['Volume_MA'].iloc[i]
            
            if buy_signals.iloc[i] and current_volume > volume_ma * 1.2:
                # 计算信号质量
                trend_score = data['Trend'].iloc[i]
                volume_score = min((current_volume / volume_ma - 1) * 0.5, 1.0)
                rsi_score = 1.0 - abs(50 - data['RSI'].iloc[i]) / 50
                macd_strength = abs(data['MACD'].iloc[i]) / data['收盘'].iloc[i] * 1000  # 归一化MACD强度
                signal_quality = (trend_score + volume_score + rsi_score + min(macd_strength, 1.0)) / 4
                
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
        
    def backtest_ma_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """双均线策略回测
        
        Args:
            data: 股票数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        # 计算均线
        data['MA5'] = data['收盘'].rolling(5).mean()
        data['MA20'] = data['收盘'].rolling(20).mean()
        
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
        
        # 均线金叉和死叉
        buy_signals = (data['MA5'] > data['MA20']) & (data['MA5'].shift(1) <= data['MA20'].shift(1))
        sell_signals = (data['MA5'] < data['MA20']) & (data['MA5'].shift(1) >= data['MA20'].shift(1))
        
        # 结合成交量和趋势强度优化信号
        for i in range(len(data)):
            if i < 20:  # 跳过前20个数据点，确保均线已经计算出来
                continue
                
            current_price = data['收盘'].iloc[i]
            current_volume = data['成交量'].iloc[i]
            volume_ma = data['Volume_MA'].iloc[i]
            
            if buy_signals.iloc[i] and current_volume > volume_ma * 1.1:
                # 计算信号质量
                trend_score = data['Trend'].iloc[i]
                volume_score = min((current_volume / volume_ma - 1) * 0.5, 1.0)
                rsi_score = 1.0 - abs(50 - data['RSI'].iloc[i]) / 50
                ma_distance = (data['MA5'].iloc[i] / data['MA20'].iloc[i] - 1) * 10  # 归一化均线距离
                signal_quality = (trend_score + volume_score + rsi_score + min(ma_distance, 1.0)) / 4
                
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
        
    def backtest_bollinger_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """布林带策略回测
        
        Args:
            data: 股票数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        # 计算布林带指标
        window = 20
        data['MA20'] = data['收盘'].rolling(window).mean()
        data['STD20'] = data['收盘'].rolling(window).std()
        data['UPPER'] = data['MA20'] + 2 * data['STD20']
        data['LOWER'] = data['MA20'] - 2 * data['STD20']
        data['BB_WIDTH'] = (data['UPPER'] - data['LOWER']) / data['MA20']  # 布林带宽度
        
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
        
        # 布林带策略信号
        # 价格触及下轨且RSI低于30时买入
        buy_condition = (data['收盘'] <= data['LOWER']) & (data['RSI'] < 30)
        # 价格触及上轨且RSI高于70时卖出
        sell_condition = (data['收盘'] >= data['UPPER']) & (data['RSI'] > 70)
        
        # 结合成交量和趋势强度优化信号
        for i in range(len(data)):
            if i < 20:  # 跳过前20个数据点，确保指标已经计算出来
                continue
                
            current_price = data['收盘'].iloc[i]
            current_volume = data['成交量'].iloc[i]
            volume_ma = data['Volume_MA'].iloc[i]
            
            if buy_condition.iloc[i] and current_volume > volume_ma * 1.2:
                # 计算信号质量
                trend_score = data['Trend'].iloc[i]
                volume_score = min((current_volume / volume_ma - 1) * 0.5, 1.0)
                rsi_score = (30 - data['RSI'].iloc[i]) / 30  # RSI越低，信号质量越高
                bb_score = min(data['BB_WIDTH'].iloc[i] * 5, 1.0)  # 布林带宽度越大，信号质量越高
                signal_quality = (trend_score + volume_score + rsi_score + bb_score) / 4
                
                signals.iloc[i, signals.columns.get_loc('action')] = 'buy'
                signals.iloc[i, signals.columns.get_loc('signal_quality')] = signal_quality
                
                # 设置止损价格
                atr = data['ATR'].iloc[i]
                stop_loss = current_price - 2 * atr
                signals.iloc[i, signals.columns.get_loc('stop_loss')] = stop_loss
                
                # 根据趋势判断市场状况
                if trend_score > 0.3:
                    signals.iloc[i, signals.columns.get_loc('market_condition')] = 'bullish'
                
            elif sell_condition.iloc[i]:
                signals.iloc[i, signals.columns.get_loc('action')] = 'sell'
                signals.iloc[i, signals.columns.get_loc('signal_quality')] = 0.8
                if data['Trend'].iloc[i] < -0.3:
                    signals.iloc[i, signals.columns.get_loc('market_condition')] = 'bearish'
        
        # 执行回测
        return self.backtest_strategy(data, lambda x: signals)
        
    def backtest_volume_price_strategy(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """量价策略回测
        
        Args:
            data: 股票数据
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        # 计算量价指标
        data['Volume_MA5'] = data['成交量'].rolling(5).mean()
        data['Volume_MA20'] = data['成交量'].rolling(20).mean()
        data['Volume_Ratio'] = data['成交量'] / data['Volume_MA20']
        data['Price_MA5'] = data['收盘'].rolling(5).mean()
        data['Price_MA10'] = data['收盘'].rolling(10).mean()
        data['Price_MA20'] = data['收盘'].rolling(20).mean()
        
        # 计算其他技术指标
        data['RSI'] = self._calculate_rsi(data['收盘'])
        data['ATR'] = self._calculate_atr(data)
        data['Trend'] = self._calculate_trend_strength(data)
        
        # 生成交易信号
        signals = pd.DataFrame(index=data.index)
        signals['action'] = 'hold'
        signals['price'] = data['收盘']
        signals['volume'] = 0.0
        signals['signal_quality'] = 0.0
        signals['market_condition'] = 'normal'
        signals['stop_loss'] = 0.0
        
        # 量价策略信号
        # 放量突破5日均线且10日均线向上时买入
        buy_condition = (data['收盘'] > data['Price_MA5']) & \
                        (data['Price_MA5'] > data['Price_MA10']) & \
                        (data['Volume_Ratio'] > 2.0) & \
                        (data['收盘'] > data['收盘'].shift(1))
        
        # 量能萎缩且价格跌破10日均线时卖出
        sell_condition = (data['收盘'] < data['Price_MA10']) & \
                         ((data['Volume_Ratio'] < 0.8) | (data['收盘'] < data['收盘'].shift(1)))
        
        # 结合成交量和趋势强度优化信号
        for i in range(len(data)):
            if i < 20:  # 跳过前20个数据点，确保指标已经计算出来
                continue
                
            current_price = data['收盘'].iloc[i]
            
            if buy_condition.iloc[i]:
                # 计算信号质量
                trend_score = data['Trend'].iloc[i]
                volume_score = min((data['Volume_Ratio'].iloc[i] - 1) * 0.3, 1.0)
                rsi_score = 1.0 - abs(50 - data['RSI'].iloc[i]) / 50
                ma_score = min((data['Price_MA5'].iloc[i] / data['Price_MA20'].iloc[i] - 1) * 10, 1.0)
                signal_quality = (trend_score + volume_score + rsi_score + ma_score) / 4
                
                signals.iloc[i, signals.columns.get_loc('action')] = 'buy'
                signals.iloc[i, signals.columns.get_loc('signal_quality')] = signal_quality
                
                # 设置止损价格
                atr = data['ATR'].iloc[i]
                stop_loss = current_price - 2 * atr
                signals.iloc[i, signals.columns.get_loc('stop_loss')] = stop_loss
                
                # 根据趋势判断市场状况
                if trend_score > 0.5 and data['RSI'].iloc[i] > 50:
                    signals.iloc[i, signals.columns.get_loc('market_condition')] = 'bullish'
                
            elif sell_condition.iloc[i]:
                signals.iloc[i, signals.columns.get_loc('action')] = 'sell'
                signals.iloc[i, signals.columns.get_loc('signal_quality')] = 0.8
                if data['Trend'].iloc[i] < -0.3:
                    signals.iloc[i, signals.columns.get_loc('market_condition')] = 'bearish'
        
        # 执行回测
        return self.backtest_strategy(data, lambda x: signals)