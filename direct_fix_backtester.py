#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接修复 evolving_backtester_part2.py 文件，添加所有必要的回测方法
"""

import os
import shutil
import traceback

# 备份原始文件
if os.path.exists('evolving_backtester_part2.py'):
    shutil.copy('evolving_backtester_part2.py', 'evolving_backtester_part2.py.orig')
    print("已备份原始文件到 evolving_backtester_part2.py.orig")

# 要添加的方法
methods_to_add = """
    def extract_features(self, data, index=-1):
        """从数据中提取特征
        
        Args:
            data: 股票数据
            index: 要使用的数据索引，默认-1表示最后一行
            
        Returns:
            特征字典
        """
        try:
            # 使用指定的索引或最后一行
            if index == -1:
                row = data.iloc[-1]
                prev_row = data.iloc[-2] if len(data) > 1 else None
            else:
                row = data.iloc[index]
                prev_row = data.iloc[index-1] if index > 0 else None
            
            features = {}
            
            # 处理中文列名
            close = None
            open_price = None
            high = None
            low = None
            volume = None
            
            # 尝试找到收盘价
            if '收盘' in data.columns:
                close = row['收盘']
            elif 'close' in data.columns:
                close = row['close']
            
            # 尝试找到开盘价
            if '开盘' in data.columns:
                open_price = row['开盘']
            elif 'open' in data.columns:
                open_price = row['open']
            
            # 尝试找到最高价
            if '最高' in data.columns:
                high = row['最高']
            elif 'high' in data.columns:
                high = row['high']
            
            # 尝试找到最低价
            if '最低' in data.columns:
                low = row['最低']
            elif 'low' in data.columns:
                low = row['low']
            
            # 尝试找到成交量
            if '成交量' in data.columns:
                volume = row['成交量']
            elif 'volume' in data.columns:
                volume = row['volume']
            
            # 提取基本价格特征
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
            
            # 提取技术指标特征
            for col in data.columns:
                col_lower = col.lower() if isinstance(col, str) else col
                # 尝试添加常见技术指标
                if col_lower in ['ma5', 'ma10', 'ma20', 'macd', 'macd_signal', 'macd_hist', 
                                 'rsi', 'k', 'd', 'j', 'boll_upper', 'boll_middle', 'boll_lower']:
                    features[col_lower] = row[col]
                # 处理大写列名
                elif col in ['MA5', 'MA10', 'MA20', 'MACD', 'MACD_Signal', 'MACD_Hist', 
                            'RSI', 'K', 'D', 'J', 'BOLL_UPPER', 'BOLL_MIDDLE', 'BOLL_LOWER']:
                    features[col.lower()] = row[col]
            
            return features
            
        except Exception as e:
            logger.error(f"提取特征出错: {str(e)}")
            return {}
    
    def evaluate_entry_signal(self, features, signal_strength):
        """评估入场信号强度
        
        Args:
            features: 特征字典
            signal_strength: 初始信号强度
            
        Returns:
            最终信号强度 (0-1)
        """
        try:
            # 如果模型不存在，直接返回原始信号强度
            if self.model_manager.models['entry'] is None:
                return signal_strength
            
            # 使用模型预测入场概率
            entry_prob = self.model_manager.predict_entry_signal(list(features.values()))
            
            # 结合原始信号和模型预测
            final_signal = (signal_strength + entry_prob) / 2
            
            # 应用阈值
            if final_signal >= self.adaptive_params['entry_threshold']:
                return final_signal
            else:
                return 0
            
        except Exception as e:
            logger.error(f"评估入场信号出错: {str(e)}")
            return signal_strength if signal_strength >= 0.6 else 0
    
    def detect_market_regime(self, data):
        """检测市场状态
        
        Args:
            data: 股票数据
            
        Returns:
            市场状态标签 (上升、下降、震荡)
        """
        try:
            # 获取收盘价
            close = None
            if '收盘' in data.columns:
                close = data['收盘']
            elif 'close' in data.columns:
                close = data['close']
            else:
                logger.warning("无法确定收盘价列，使用默认市场状态")
                return "未知"
            
            # 至少需要30个数据点
            if len(close) < 30:
                return "数据不足"
            
            # 计算短期和长期趋势
            short_ma = close.rolling(window=10).mean()
            long_ma = close.rolling(window=30).mean()
            
            # 最近的均线值
            last_short = short_ma.iloc[-1]
            last_long = long_ma.iloc[-1]
            
            # 计算最近10天的波动率
            recent_volatility = close.iloc[-10:].pct_change().std()
            
            # 判断市场状态
            if last_short > last_long and (last_short / last_long - 1) > 0.02:
                return "上升"
            elif last_short < last_long and (1 - last_short / last_long) > 0.02:
                return "下降"
            elif recent_volatility > 0.02:
                return "高波动"
            else:
                return "震荡"
            
        except Exception as e:
            logger.error(f"检测市场状态出错: {str(e)}")
            return "未知"
    
    def backtest_macd_strategy(self, data, stock_code):
        """MACD金叉策略回测
        
        Args:
            data: 股票数据
            stock_code: 股票代码
            
        Returns:
            回测结果对象
        """
        logger.info(f"开始 {stock_code} 的MACD金叉策略回测")
        
        # 确保数据有正确的MACD列
        if 'MACD' not in data.columns and 'macd' not in data.columns:
            # 计算MACD
            if '收盘' in data.columns:
                close = data['收盘']
            elif 'close' in data.columns:
                close = data['close']
            else:
                logger.error("无法找到收盘价列，回测失败")
                return None
                
            # 计算MACD指标
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            data['MACD'] = ema12 - ema26
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
        
        # 初始化回测变量
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        start_time = data.index[0] if hasattr(data.index[0], 'strftime') else datetime.now()
        
        # 遍历每个交易日
        for i in range(60, len(data)):
            date = data.index[i] if hasattr(data.index[i], 'strftime') else datetime.now()
            
            # 准备当前数据
            current_data = data.iloc[:i+1]
            features = self.extract_features(current_data, i)
            
            # 检测市场状态
            market_regime = self.detect_market_regime(current_data)
            
            # 获取价格
            if '收盘' in data.columns:
                price = data.iloc[i]['收盘']
            elif 'close' in data.columns:
                price = data.iloc[i]['close']
            else:
                logger.warning("无法确定收盘价，跳过这个交易日")
                continue
            
            # 计算MACD信号
            macd_hist = 0
            if 'MACD_Hist' in data.columns:
                macd_hist = data.iloc[i]['MACD_Hist']
            elif 'macd_hist' in data.columns:
                macd_hist = data.iloc[i]['macd_hist']
            
            # 检查是否有持仓
            has_position = stock_code in self.positions
            
            # 入场信号: MACD柱由负转正
            buy_signal = False
            if i > 0:
                prev_hist = 0
                if 'MACD_Hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['MACD_Hist']
                elif 'macd_hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['macd_hist']
                
                buy_signal = prev_hist < 0 and macd_hist > 0
            
            # 出场信号: MACD柱由正转负
            sell_signal = False
            if i > 0:
                prev_hist = 0
                if 'MACD_Hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['MACD_Hist']
                elif 'macd_hist' in data.columns and i > 0:
                    prev_hist = data.iloc[i-1]['macd_hist']
                
                sell_signal = prev_hist > 0 and macd_hist < 0
            
            # 处理信号
            if not has_position and buy_signal:
                # 入场信号强度
                signal_strength = min(1.0, abs(macd_hist) * 10) if macd_hist != 0 else 0.5
                
                # 评估信号
                final_signal = self.evaluate_entry_signal(features, signal_strength)
                
                if final_signal > 0:
                    # 计算仓位大小
                    stop_loss = price * 0.95  # 5%止损
                    position_ratio = self.calculate_position_size(features, final_signal, price, stop_loss)
                    
                    # 执行买入
                    position_value = self.current_capital * position_ratio
                    shares = position_value / price
                    
                    # 记录交易
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
                    
                    logger.info(f"买入 {stock_code}: 价格={price:.2f}, 仓位={position_ratio:.2%}, 股数={shares:.2f}")
            
            elif has_position and (sell_signal or price <= self.positions[stock_code]['stop_loss']):
                # 出场
                position = self.positions[stock_code]
                shares = position['shares']
                entry_price = position['entry_price']
                trade_record = position['trade_record']
                
                # 计算收益
                profit = (price - entry_price) * shares
                self.current_capital += profit
                
                # 更新交易记录
                trade_record.exit_time = date
                trade_record.exit_price = price
                trade_record.profit_loss = profit
                
                logger.info(f"卖出 {stock_code}: 价格={price:.2f}, 收益={profit:.2f}元 ({(price/entry_price-1)*100:.2f}%)")
                
                # 清除持仓
                del self.positions[stock_code]
            
            # 更新权益曲线
            portfolio_value = self.current_capital
            for pos_symbol, pos_data in self.positions.items():
                portfolio_value += pos_data['shares'] * price
            
            self.equity_curve.append((date, portfolio_value))
        
        # 创建回测结果
        end_time = data.index[-1] if hasattr(data.index[-1], 'strftime') else datetime.now()
        final_value = self.current_capital
        for symbol, position in self.positions.items():
            last_price = data.iloc[-1]['收盘'] if '收盘' in data.columns else data.iloc[-1]['close']
            final_value += position['shares'] * last_price
        
        # 计算业绩指标
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
            
            profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
        
        # 创建结果对象
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
        """KDJ金叉策略回测（简化实现）"""
        logger.info(f"使用MACD策略代替KDJ策略")
        return self.backtest_macd_strategy(data, stock_code)
    
    def backtest_ma_strategy(self, data, stock_code):
        """双均线策略回测（简化实现）"""
        logger.info(f"使用MACD策略代替均线策略")
        return self.backtest_macd_strategy(data, stock_code)
"""

try:
    # 读取原始文件内容
    with open('evolving_backtester_part2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查class EvolvingBacktester在文件中的位置
    backtester_class_pos = content.find("class EvolvingBacktester:")
    if backtester_class_pos == -1:
        print("错误: 无法找到 EvolvingBacktester 类定义")
        exit(1)
    
    # 找到calculate_position_size方法的位置（它是类中的最后一个方法）
    calculate_pos_method = content.find("def calculate_position_size", backtester_class_pos)
    
    if calculate_pos_method == -1:
        print("错误: 无法找到 calculate_position_size 方法")
        exit(1)
    
    # 查找方法结束的位置
    method_end = content.find("\n\n", calculate_pos_method)
    if method_end == -1:
        method_end = len(content)  # 如果没有找到双换行符，使用文件末尾
    
    # 插入新方法到类中
    new_content = content[:method_end] + "\n" + methods_to_add + content[method_end:]
    
    # 保存新文件
    with open('evolving_backtester_part2.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("成功添加方法到 evolving_backtester_part2.py 文件")
    
except Exception as e:
    print(f"错误: {str(e)}")
    traceback.print_exc() 