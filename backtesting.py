import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from cachetools import LRUCache
import os

@dataclass
class TradeRecord:
    """交易记录数据结构"""
    timestamp: datetime
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    volume: float
    position: float
    profit: float
    drawdown: float

class BacktestResult:
    """回测结果数据结构"""
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self.total_profit: float = 0.0
        self.max_drawdown: float = 0.0
        self.win_rate: float = 0.0
        self.profit_ratio: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.annual_return: float = 0.0
        self.volatility: float = 0.0
        self.trade_count: int = 0
        self.win_count: int = 0
        self.loss_count: int = 0
        self.avg_holding_period: float = 0.0
        self.max_consecutive_wins: int = 0
        self.max_consecutive_losses: int = 0

class Backtester:
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, float] = {}
        self.trades: List[TradeRecord] = []
        self.daily_returns: List[float] = []
        self.max_capital = initial_capital
        self.risk_free_rate = 0.03
        self.total_profit = 0.0  # 新增初始化
        self.max_drawdown = 0.0  # 新增初始化
        self.win_rate = 0.0  # 新增初始化
        self._thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count()*2)
        self._calculation_cache = LRUCache(maxsize=1024)
        self._metric_cache = {}

    @lru_cache(maxsize=1024)
    def calculate_position_size(self, price: float, risk_per_trade: float = 0.02) -> float:
        cache_key = (price, risk_per_trade)
        if cached := self._calculation_cache.get(cache_key):
            return cached
        position_value = self.current_capital * risk_per_trade
        result = position_value / price
        self._calculation_cache[cache_key] = result
        return result

    def execute_trade(self, timestamp: datetime, symbol: str, action: str,
                     price: float, volume: float) -> Optional[TradeRecord]:
        """执行交易并记录交易明细"""
        if any(x is None for x in [timestamp, symbol, action, price, volume]):
            error_msg = f"交易参数存在空值: timestamp={timestamp}, symbol={symbol}, action={action}, price={price}, volume={volume}"
            print(error_msg)
            with open('trade_errors.log', 'a') as f:
                f.write(error_msg + '\n')
            return None
        try:
            # 新增输入验证
            if price <= 0:
                raise ValueError(f"无效的价格: {price}")
            if volume <= 0:
                raise ValueError(f"无效的数量: {volume}")

            # 新增缓存清理
            self._calculation_cache.clear()
            self._metric_cache.clear()

            if action not in ['buy', 'sell']:
                raise ValueError(f"无效的交易动作: {action}")

            current_position = self.positions.get(symbol, 0.0)
            trade_value = price * volume

            if action == 'buy':
                if trade_value > self.current_capital:
                    self.daily_returns.append(-1)  # 记录交易失败影响
                    return None
            else:
                if volume > current_position:
                    self.daily_returns.append(-1)  # 记录交易失败影响
                    return None

            # 新增持仓比例限制 - 在计算滑点前应用持仓限制
            max_position_ratio = 0.3
            if action == 'buy' and trade_value > self.current_capital * max_position_ratio:
                volume = (self.current_capital * max_position_ratio) / price
                trade_value = price * volume  # 更新交易价值
                
            # 简化滑点计算 (0.1% 的固定滑点)
            effective_price = price * 1.001 if action == 'buy' else price * 0.999
            trade_value = effective_price * volume
            
            if action == 'buy' and trade_value > self.current_capital:
                with open('trade_errors.log', 'a') as f:
                    f.write(f"{json.dumps(error_msg)}\n")
                return None

            if action == 'buy':
                if trade_value > self.current_capital:
                    return None  # 资金不足
                self.current_capital -= trade_value
                new_position = current_position + volume
            else:  # sell
                if volume > current_position:
                    return None  # 持仓不足
                self.current_capital += trade_value
                new_position = current_position - volume

            # 更新持仓
            if new_position == 0:
                self.positions.pop(symbol, None)
            else:
                self.positions[symbol] = new_position

            # 计算收益和回撤
            profit = trade_value - (price * current_position) if action == 'sell' else 0.0
            drawdown = max(0, self.max_capital - self.current_capital)
            self.max_capital = max(self.max_capital, self.current_capital)

            # 记录交易
            trade = TradeRecord(
                timestamp=timestamp,
                symbol=symbol,
                action=action,
                price=price,
                volume=volume,
                position=new_position,
                profit=profit,
                drawdown=drawdown
            )
            self.trades.append(trade)

            # 计算每日收益率
            daily_return = (self.current_capital - self.initial_capital) / self.initial_capital
            self.daily_returns.append(daily_return)

            # 新增交易后检查
            if self.current_capital < 0:
                raise ValueError("资金余额异常，请检查交易逻辑")
                
            # 更新最大回撤值
            self.max_drawdown = max(self.max_drawdown, drawdown)

            # 在return前添加风控检查
            if self.max_drawdown > 0.2 * self.initial_capital:
                print("风险警告：最大回撤超过初始资金的20%")
                
            # 更新总收益和胜率
            if action == 'sell' and profit != 0:
                self.total_profit += profit
                if profit > 0:
                    self.win_rate = (self.win_rate * (result.win_count) + 1) / (result.win_count + 1) if hasattr(self, 'result') and hasattr(self.result, 'win_count') else 1.0

            return trade
        except Exception as e:
            # 增强异常处理
            self.daily_returns.append(-1)
            error_msg = f"{timestamp} - {symbol} {action} 交易失败: {str(e)}"
            with open('trade_errors.log', 'a') as f:
                f.write(error_msg + '\n')
            return None

    def _parallel_calculate_metrics(self, trades: List[TradeRecord]) -> Tuple:
        if not trades:
            return ({}, {}, {}, {})
        try:
            try:
                timestamps = [t.timestamp.isoformat() for t in trades if t.timestamp]
                cache_key = hash(frozenset(zip(timestamps, [t.symbol for t in trades], [t.action for t in trades])))
            except Exception:
                cache_key = hash((len(trades), trades[0].symbol if trades else ''))
            if cached := self._metric_cache.get(cache_key):
                return cached
        except Exception as e:
            print(f"缓存键生成失败: {str(e)}")

        futures = []
        with self._thread_pool as executor:
            for batch in [trades[i:i+len(trades)//4] for i in range(0, len(trades), len(trades)//4)]:
                futures.append(executor.submit(self._calculate_profit_metrics, batch))
                futures.append(executor.submit(self._calculate_risk_metrics, batch))
                futures.append(executor.submit(self._calculate_trade_metrics, batch))
                futures.append(executor.submit(self._calculate_holding_metrics, batch))

        results = [future.result() for future in futures]
        aggregated = (
            self._aggregate_profit(results[::4]),
            self._aggregate_risk(results[1::4]),
            self._aggregate_trade(results[2::4]),
            self._aggregate_holding(results[3::4])
        )
        self._metric_cache[cache_key] = aggregated
        return aggregated

    def _calculate_profit_metrics(self, trades: List[TradeRecord]) -> Dict:
        if not trades:
            return {
                'total_profit': 0.0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'profit_ratio': 0.0
            }
        profits = [trade.profit for trade in trades]
        total_profit = sum(profits)
        win_count = sum(1 for p in profits if p > 0)
        loss_count = sum(1 for p in profits if p < 0)
        win_rate = win_count / len(trades) if trades else 0
        avg_win = np.mean([p for p in profits if p > 0]) if win_count > 0 else 0
        avg_loss = abs(np.mean([p for p in profits if p < 0])) if loss_count > 0 else 1
        profit_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'total_profit': total_profit,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'profit_ratio': profit_ratio
        }

    def _calculate_risk_metrics(self, trades: List[TradeRecord]) -> Dict:
        if not trades:
            return {
                'max_drawdown': 0.0,
                'annual_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0
            }
        max_drawdown = max(trade.drawdown for trade in trades) if trades else 0
        returns = np.array(self.daily_returns)
        annual_return = np.mean(returns) * 252 if len(returns) > 0 else 0
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0
        sharpe_ratio = (annual_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        return {
            'max_drawdown': max_drawdown,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio
        }

    def _calculate_trade_metrics(self, trades: List[TradeRecord]) -> Dict:
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        profits = [trade.profit for trade in trades]
        
        for profit in profits:
            if profit > 0:
                if current_streak > 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_win_streak = max(max_win_streak, current_streak)
            elif profit < 0:
                if current_streak < 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_loss_streak = min(max_loss_streak, current_streak)
        
        return {
            'max_consecutive_wins': max_win_streak,
            'max_consecutive_losses': abs(max_loss_streak)
        }

    def _calculate_holding_metrics(self, trades: List[TradeRecord]) -> Dict:
        holding_periods = []
        try:
            # 优化持仓周期计算逻辑
            buy_trades = {}
            for trade in trades:
                if trade.action == 'buy':
                    if trade.symbol not in buy_trades:
                        buy_trades[trade.symbol] = []
                    buy_trades[trade.symbol].append(trade)
                elif trade.action == 'sell' and trade.symbol in buy_trades and buy_trades[trade.symbol]:
                    buy_trade = buy_trades[trade.symbol].pop(0)  # 获取最早的买入交易
                    period = (trade.timestamp - buy_trade.timestamp).days
                    if period >= 0:  # 确保周期有效
                        holding_periods.append(period)
            
            # 如果没有配对的交易，使用传统方法
            if not holding_periods:
                for i in range(0, len(trades)-1, 2):
                    if i+1 < len(trades):
                        period = (trades[i+1].timestamp - trades[i].timestamp).days
                        if period >= 0:  # 确保周期有效
                            holding_periods.append(period)
        except Exception as e:
            print(f"计算持仓周期时出错: {str(e)}")
            # 出错时使用简化方法
            for i in range(0, len(trades)-1, 2):
                if i+1 < len(trades):
                    try:
                        period = (trades[i+1].timestamp - trades[i].timestamp).days
                        if period >= 0:
                            holding_periods.append(period)
                    except:
                        continue
        
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0
        return {'avg_holding_period': avg_holding_period}

    def calculate_metrics(self) -> BacktestResult:
        if not self.trades:
            return BacktestResult()
        result = BacktestResult()
        result.trades = self.trades
        result.trade_count = len(self.trades)

        if result.trade_count == 0:
            return result

        profit_metrics, risk_metrics, trade_metrics, holding_metrics = self._parallel_calculate_metrics(self.trades)

        result.total_profit = profit_metrics['total_profit']
        result.win_count = profit_metrics['win_count']
        result.loss_count = profit_metrics['loss_count']
        result.win_rate = profit_metrics['win_rate']
        result.profit_ratio = profit_metrics['profit_ratio']

        result.max_drawdown = risk_metrics['max_drawdown']
        result.annual_return = risk_metrics['annual_return']
        result.volatility = risk_metrics['volatility']
        result.sharpe_ratio = risk_metrics['sharpe_ratio']

        result.max_consecutive_wins = trade_metrics['max_consecutive_wins']
        result.max_consecutive_losses = trade_metrics['max_consecutive_losses']

        result.avg_holding_period = holding_metrics['avg_holding_period']

        # 保存结果到JSON文件
        self._save_results_to_json(result)
        return result
        
    def _save_results_to_json(self, result: BacktestResult) -> None:
        """将回测结果保存到JSON文件"""
        try:
            result_dict = {
                'total_profit': result.total_profit,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'sharpe_ratio': result.sharpe_ratio,
                'annual_return': result.annual_return,
                'volatility': result.volatility,
                'trade_count': result.trade_count,
                'win_count': result.win_count,
                'loss_count': result.loss_count,
                'profit_ratio': result.profit_ratio,
                'avg_holding_period': result.avg_holding_period,
                'max_consecutive_wins': result.max_consecutive_wins,
                'max_consecutive_losses': result.max_consecutive_losses,
                'trades': [{
                    'timestamp': t.timestamp.isoformat(),
                    'symbol': t.symbol,
                    'action': t.action,
                    'price': t.price,
                    'volume': t.volume,
                    'position': t.position,
                    'profit': t.profit,
                    'drawdown': t.drawdown
                } for t in result.trades],
                'daily_returns': self.daily_returns
            }
            with open('backtest_results.json', 'w') as f:
                json.dump(result_dict, f, indent=2)
        except Exception as e:
            print(f"保存回测结果失败: {str(e)}")

    def generate_report(self, result: BacktestResult) -> str:
        report = [
            "回测结果报告",
            "==============\n",
            f"交易次数: {result.trade_count}",
            f"总收益: {result.total_profit:.2f}",
            f"年化收益率: {result.annual_return*100:.2f}%",
            f"最大回撤: {result.max_drawdown:.2f}",
            f"胜率: {result.win_rate*100:.2f}%",
            f"盈亏比: {result.profit_ratio:.2f}",
            f"夏普比率: {result.sharpe_ratio:.2f}",
            f"波动率: {result.volatility*100:.2f}%",
            f"平均持仓周期: {result.avg_holding_period:.1f}天",
            f"最大连续盈利次数: {result.max_consecutive_wins}",
            f"最大连续亏损次数: {result.max_consecutive_losses}\n",
            "详细交易记录:",
            "-------------"
        ]

        for trade in result.trades:
            report.append(
                f"{trade.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{trade.symbol} | {trade.action} | "
                f"价格: {trade.price:.2f} | "
                f"数量: {trade.volume:.2f} | "
                f"收益: {trade.profit:.2f}"
            )

        return '\n'.join(report)

    def _aggregate_profit(self, results: List[Dict]) -> Dict:
        return {
            'total_profit': sum(r['total_profit'] for r in results),
            'win_count': sum(r['win_count'] for r in results),
            'loss_count': sum(r['loss_count'] for r in results),
            'win_rate': np.mean([r['win_rate'] for r in results]) if results else 0,
            'profit_ratio': np.mean([r['profit_ratio'] for r in results]) if results else 0
        }

    def _aggregate_risk(self, results: List[Dict]) -> Dict:
        return {
            'max_drawdown': max(r['max_drawdown'] for r in results) if results else 0,
            'annual_return': np.mean([r['annual_return'] for r in results]) if results else 0,
            'volatility': np.mean([r['volatility'] for r in results]) if results else 0,
            'sharpe_ratio': np.mean([r['sharpe_ratio'] for r in results]) if results else 0
        }

    def _aggregate_trade(self, results: List[Dict]) -> Dict:
        return {
            'max_consecutive_wins': max(r['max_consecutive_wins'] for r in results) if results else 0,
            'max_consecutive_losses': max(r['max_consecutive_losses'] for r in results) if results else 0
        }

    def _aggregate_holding(self, results: List[Dict]) -> Dict:
        try:
            if not results:
                return {'avg_holding_period': 0}
            valid_periods = [r['avg_holding_period'] for r in results if r and r.get('avg_holding_period') is not None]
            return {
                'avg_holding_period': np.mean(valid_periods) if valid_periods else 0
            }
        except Exception as e:
            print(f"计算持仓指标时出错: {str(e)}")
            return {'avg_holding_period': 0}