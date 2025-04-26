import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import akshare as ak
import time
import threading
import logging
from visual_stock_system import VisualStockSystem
from backtesting_wrapper import Backtesting
from stock_review import StockReview
from volume_price_strategy import VolumePriceStrategy

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='enhanced_stock_review.log')
logger = logging.getLogger('EnhancedStockReview')

class EnhancedStockReview(StockReview):
    """增强版股票复盘模块
    扩展了原有StockReview的功能，增加了自动跟踪、实时提醒、更多技术指标分析和优化的绩效统计
    """
    def __init__(self, token=None):
        super().__init__(token)
        # 增强版配置参数
        self.auto_tracking_enabled = False  # 自动跟踪功能开关
        self.tracking_interval = 60 * 30  # 默认30分钟检查一次
        self.notification_threshold = 3.0  # 价格变动超过3%触发提醒
        self.tracking_thread = None  # 跟踪线程
        self.stop_tracking = False  # 停止跟踪标志
        self.technical_indicators = ['MACD', 'RSI', 'KDJ', 'BOLL', 'MA', 'VOL']  # 支持的技术指标
        self.risk_management_enabled = True  # 风险管理功能开关
        self.max_positions = 5  # 最大持仓数量
        self.max_position_ratio = 0.2  # 单只股票最大仓位比例
        self.stop_loss_ratio = 0.05  # 止损比例
        self.take_profit_ratio = 0.15  # 止盈比例
        self.market_sentiment_cache = {}  # 市场情绪缓存
        self.market_sentiment_expiry = 60 * 60 * 24  # 市场情绪缓存过期时间（24小时）
        self.last_market_update = 0  # 上次市场更新时间
        
        # 创建增强版数据文件
        self.enhanced_review_file = 'enhanced_review_pool.json'
        self.alert_history_file = 'alert_history.json'
        self.strategy_performance_file = 'strategy_performance.json'
        
        # 加载增强版数据
        self.enhanced_review_data = self._load_enhanced_data()
        self.alert_history = self._load_alert_history()
        self.strategy_performance = self._load_strategy_performance()
        
        logger.info("增强版股票复盘模块初始化完成")
    
    def _load_enhanced_data(self):
        """加载增强版复盘数据"""
        if os.path.exists(self.enhanced_review_file):
            try:
                with open(self.enhanced_review_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载增强版复盘数据失败: {str(e)}")
                return {'stocks': [], 'settings': {}}
        else:
            return {'stocks': [], 'settings': {}}
    
    def _save_enhanced_data(self):
        """保存增强版复盘数据"""
        try:
            with open(self.enhanced_review_file, 'w', encoding='utf-8') as f:
                json.dump(self.enhanced_review_data, f, ensure_ascii=False, indent=4)
            logger.info(f"增强版复盘数据已保存到 {self.enhanced_review_file}")
            return True
        except Exception as e:
            logger.error(f"保存增强版复盘数据失败: {str(e)}")
            return False
    
    def _load_alert_history(self):
        """加载提醒历史"""
        if os.path.exists(self.alert_history_file):
            try:
                with open(self.alert_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载提醒历史失败: {str(e)}")
                return {'alerts': []}
        else:
            return {'alerts': []}
    
    def _save_alert_history(self):
        """保存提醒历史"""
        try:
            with open(self.alert_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"保存提醒历史失败: {str(e)}")
            return False
    
    def _load_strategy_performance(self):
        """加载策略绩效数据"""
        if os.path.exists(self.strategy_performance_file):
            try:
                with open(self.strategy_performance_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载策略绩效数据失败: {str(e)}")
                return {'strategies': {}}
        else:
            return {'strategies': {}}
    
    def _save_strategy_performance(self):
        """保存策略绩效数据"""
        try:
            with open(self.strategy_performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.strategy_performance, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"保存策略绩效数据失败: {str(e)}")
            return False
    
    def start_auto_tracking(self):
        """启动自动跟踪功能"""
        if self.auto_tracking_enabled:
            logger.warning("自动跟踪已经在运行中")
            return False
        
        try:
            self.auto_tracking_enabled = True
            self.stop_tracking = False
            
            # 创建并启动跟踪线程
            self.tracking_thread = threading.Thread(target=self._tracking_worker)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
            
            logger.info("自动跟踪功能已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动自动跟踪失败: {str(e)}")
            return False
    
    def _tracking_worker(self):
        """跟踪工作线程"""
        while not self.stop_tracking:
            try:
                self._check_all_stocks()
                time.sleep(self.tracking_interval)
            except Exception as e:
                logger.error(f"跟踪检查出错: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    def _check_all_stocks(self):
        """检查所有跟踪中的股票"""
        for stock in self.enhanced_review_data['stocks']:
            if stock['status'] in ['watching', 'bought']:
                self._check_single_stock(stock)
    
    def _check_single_stock(self, stock):
        """检查单只股票的状态和指标"""
        try:
            # 获取最新数据
            data = self.visual_system.get_stock_data(stock['symbol'])
            if data is None or data.empty:
                return
            
            current_price = data['收盘'].iloc[-1]
            
            # 计算技术指标
            indicators = self._calculate_indicators(data)
            
            # 生成买入信号
            if stock['status'] == 'watching':
                signal = self._generate_buy_signal(data, indicators)
                if signal['strength'] >= 0.8:  # 强烈买入信号
                    self._generate_alert('buy', stock, signal)
            
            # 检查止盈止损
            elif stock['status'] == 'bought':
                if self._check_stop_conditions(stock, current_price):
                    self._generate_alert('sell', stock, {
                        'reason': '触发止盈止损',
                        'current_price': current_price
                    })
            
        except Exception as e:
            logger.error(f"检查股票{stock['symbol']}时出错: {str(e)}")
    
    def _generate_alert(self, alert_type, stock, details):
        """生成交易提醒"""
        alert = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': alert_type,
            'symbol': stock['symbol'],
            'name': stock['name'],
            'details': details
        }
        
        # 保存到提醒历史
        self.alert_history['alerts'].append(alert)
        self._save_alert_history()
        
        # 输出日志
        logger.info(f"生成{alert_type}提醒: {stock['name']}({stock['symbol']})")
    
    def stop_auto_tracking(self):
        """停止自动跟踪功能"""
        if not self.auto_tracking_enabled:
            logger.info("自动跟踪功能未启动")
            return False
        
        self.stop_tracking = True
        self.auto_tracking_enabled = False
        
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=5)
        
        logger.info("自动跟踪功能已停止")
        return True
    
    def _tracking_worker(self):
        """跟踪工作线程"""
        logger.info("跟踪工作线程已启动")
        
        while not self.stop_tracking:
            try:
                # 获取需要跟踪的股票
                watching_stocks = self.get_review_pool(status='watching')
                bought_stocks = self.get_review_pool(status='bought')
                
                # 跟踪观察中的股票
                for stock in watching_stocks:
                    self._check_stock_signal(stock)
                
                # 跟踪已买入的股票
                for stock in bought_stocks:
                    self._check_position_status(stock)
                
                # 更新市场情绪
                self._update_market_sentiment()
                
                # 保存数据
                self._save_enhanced_data()
                self._save_alert_history()
                
            except Exception as e:
                logger.error(f"跟踪过程中出错: {str(e)}")
            
            # 等待下一次检查
            for _ in range(self.tracking_interval):
                if self.stop_tracking:
                    break
                time.sleep(1)
    
    def _check_stock_signal(self, stock):
        """检查股票信号"""
        try:
            symbol = stock['symbol']
            
            # 获取最新行情
            latest_data = self.visual_system.get_stock_data(symbol, limit=20)
            if latest_data is None or latest_data.empty:
                logger.warning(f"获取股票 {symbol} 数据失败")
                return
            
            # 计算技术指标
            indicators = self._calculate_indicators(latest_data)
            
            # 检查买入信号
            buy_signals = self._check_buy_signals(indicators)
            if buy_signals['strength'] > 0.7:  # 强烈买入信号
                # 添加到提醒历史
                alert = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'symbol': symbol,
                    'name': stock.get('name', ''),
                    'type': 'buy_signal',
                    'price': latest_data['收盘'].iloc[-1],
                    'signal_strength': buy_signals['strength'],
                    'reason': buy_signals['reason']
                }
                
                self.alert_history['alerts'].append(alert)
                self._save_alert_history()
                
                logger.info(f"发现买入信号: {symbol}, 强度: {buy_signals['strength']}, 原因: {buy_signals['reason']}")
        
        except Exception as e:
            logger.error(f"检查股票 {stock.get('symbol', 'unknown')} 信号时出错: {str(e)}")
    
    def _check_position_status(self, stock):
        """检查持仓状态"""
        try:
            symbol = stock['symbol']
            buy_price = stock.get('buy_price', 0)
            if not buy_price:
                return
            
            # 获取最新行情
            latest_data = self.visual_system.get_stock_data(symbol, limit=5)
            if latest_data is None or latest_data.empty:
                return
            
            current_price = latest_data['收盘'].iloc[-1]
            price_change_pct = (current_price - buy_price) / buy_price * 100
            
            # 检查止盈止损
            if self.risk_management_enabled:
                # 止损检查
                if price_change_pct < -self.stop_loss_ratio * 100:
                    alert = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'symbol': symbol,
                        'name': stock.get('name', ''),
                        'type': 'stop_loss',
                        'price': current_price,
                        'change_pct': price_change_pct,
                        'reason': f"触发止损: 亏损 {price_change_pct:.2f}%"
                    }
                    
                    self.alert_history['alerts'].append(alert)
                    self._save_alert_history()
                    
                    logger.warning(f"股票 {symbol} 触发止损: 当前价格 {current_price}, 亏损 {price_change_pct:.2f}%")
                
                # 止盈检查
                elif price_change_pct > self.take_profit_ratio * 100:
                    alert = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'symbol': symbol,
                        'name': stock.get('name', ''),
                        'type': 'take_profit',
                        'price': current_price,
                        'change_pct': price_change_pct,
                        'reason': f"触发止盈: 盈利 {price_change_pct:.2f}%"
                    }
                    
                    self.alert_history['alerts'].append(alert)
                    self._save_alert_history()
                    
                    logger.info(f"股票 {symbol} 触发止盈: 当前价格 {current_price}, 盈利 {price_change_pct:.2f}%")
            
            # 价格变动提醒
            if abs(price_change_pct) >= self.notification_threshold:
                alert = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'symbol': symbol,
                    'name': stock.get('name', ''),
                    'type': 'price_change',
                    'price': current_price,
                    'change_pct': price_change_pct,
                    'reason': f"价格变动: {'上涨' if price_change_pct > 0 else '下跌'} {abs(price_change_pct):.2f}%"
                }
                
                self.alert_history['alerts'].append(alert)
                self._save_alert_history()
                
                logger.info(f"股票 {symbol} 价格变动: 当前价格 {current_price}, {'上涨' if price_change_pct > 0 else '下跌'} {abs(price_change_pct):.2f}%")
        
        except Exception as e:
            logger.error(f"检查持仓 {stock.get('symbol', 'unknown')} 状态时出错: {str(e)}")
    
    def _calculate_indicators(self, data):
        """计算技术指标"""
        try:
            indicators = {}
            
            # 确保数据足够
            if len(data) < 30:
                logger.warning("数据量不足，无法计算完整技术指标")
                return indicators
            
            # 计算MACD
            close = data['收盘']
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            indicators['MACD'] = {
                'macd': macd.iloc[-1],
                'signal': signal.iloc[-1],
                'hist': hist.iloc[-1],
                'trend': 'bullish' if macd.iloc[-1] > signal.iloc[-1] else 'bearish',
                'crossover': macd.iloc[-2] <= signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1],
                'crossunder': macd.iloc[-2] >= signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]
            }
            
            # 计算RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            indicators['RSI'] = {
                'value': rsi.iloc[-1],
                'overbought': rsi.iloc[-1] > 70,
                'oversold': rsi.iloc[-1] < 30,
                'trend': 'bullish' if rsi.iloc[-1] > 50 else 'bearish'
            }
            
            # 计算KDJ
            low_list = data['最低'].rolling(9, min_periods=9).min()
            high_list = data['最高'].rolling(9, min_periods=9).max()
            rsv = (close - low_list) / (high_list - low_list) * 100
            k = pd.DataFrame(rsv).ewm(com=2).mean()
            d = pd.DataFrame(k).ewm(com=2).mean()
            j = 3 * k - 2 * d
            
            indicators['KDJ'] = {
                'k': k.iloc[-1, 0],
                'd': d.iloc[-1, 0],
                'j': j.iloc[-1, 0],
                'overbought': k.iloc[-1, 0] > 80 or j.iloc[-1, 0] > 100,
                'oversold': k.iloc[-1, 0] < 20 or j.iloc[-1, 0] < 0,
                'golden_cross': k.iloc[-2, 0] <= d.iloc[-2, 0] and k.iloc[-1, 0] > d.iloc[-1, 0],
                'death_cross': k.iloc[-2, 0] >= d.iloc[-2, 0] and k.iloc[-1, 0] < d.iloc[-1, 0]
            }
            
            # 计算布林带
            ma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            
            indicators['BOLL'] = {
                'middle': ma20.iloc[-1],
                'upper': upper.iloc[-1],
                'lower': lower.iloc[-1],
                'width': (upper.iloc[-1] - lower.iloc[-1]) / ma20.iloc[-1],
                'position': (close.iloc[-1] - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]),
                'breakout_up': close.iloc[-1] > upper.iloc[-1],
                'breakout_down': close.iloc[-1] < lower.iloc[-1]
            }
            
            # 计算均线
            ma5 = close.rolling(window=5).mean()
            ma10 = close.rolling(window=10).mean()
            ma20 = close.rolling(window=20).mean()
            ma60 = close.rolling(window=60).mean()
            
            indicators['MA'] = {
                'ma5': ma5.iloc[-1],
                'ma10': ma10.iloc[-1],
                'ma20': ma20.iloc[-1],
                'ma60': ma60.iloc[-1] if len(close) >= 60 else None,
                'ma5_trend': 'up' if ma5.iloc[-1] > ma5.iloc[-2] else 'down',
                'price_above_ma20': close.iloc[-1] > ma20.iloc[-1],
                'ma5_above_ma20': ma5.iloc[-1] > ma20.iloc[-1],
                'ma_alignment': ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1] if len(close) >= 20 else False
            }
            
            # 计算成交量指标
            volume = data['成交量']
            volume_ma5 = volume.rolling(window=5).mean()
            volume_ma20 = volume.rolling(window=20).mean()
            
            indicators['VOL'] = {
                'current': volume.iloc[-1],
                'ma5': volume_ma5.iloc[-1],
                'ma20': volume_ma20.iloc[-1],
                'ratio_to_ma5': volume.iloc[-1] / volume_ma5.iloc[-1] if volume_ma5.iloc[-1] > 0 else 0,
                'ratio_to_ma20': volume.iloc[-1] / volume_ma20.iloc[-1] if volume_ma20.iloc[-1] > 0 else 0,
                'increasing': volume.iloc[-1] > volume.iloc[-2],
                'above_average': volume.iloc[-1] > volume_ma20.iloc[-1]
            }
            
            # 综合评分
            indicators['overall_score'] = self._calculate_overall_score(indicators)
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
            return {}
    
    def _calculate_overall_score(self, indicators):
        """计算综合评分
        优化的评分系统，考虑市场状态和技术指标的综合权重
        """
        score = 50  # 基础分数
        market_weight = self._get_market_sentiment_weight()  # 获取市场情绪权重
        
        # MACD评分（权重：30%）
        if 'MACD' in indicators:
            macd = indicators['MACD']
            macd_score = 0
            if macd['crossover']:
                macd_score += 15
            elif macd['crossunder']:
                macd_score -= 15
            if macd['trend'] == 'bullish':
                macd_score += 10
            else:
                macd_score -= 5
            if abs(macd['hist']) > abs(macd.get('prev_hist', 0)):
                macd_score += 5
            score += macd_score * 0.3 * market_weight
        
        # RSI评分
        if 'RSI' in indicators:
            rsi = indicators['RSI']
            if rsi['oversold']:
                score += 10
            elif rsi['overbought']:
                score -= 10
            if rsi['trend'] == 'bullish':
                score += 5
            else:
                score -= 5
        
        # KDJ评分
        if 'KDJ' in indicators:
            kdj = indicators['KDJ']
            if kdj['golden_cross']:
                score += 10
            elif kdj['death_cross']:
                score -= 10
            if kdj['oversold']:
                score += 8
            elif kdj['overbought']:
                score -= 8
        
        # 布林带评分
        if 'BOLL' in indicators:
            boll = indicators['BOLL']
            if boll['breakout_up']:
                score += 5
            elif boll['breakout_down']:
                score -= 5
            if boll['position'] < 0.2:
                score += 8  # 接近下轨，可能超卖
            elif boll['position'] > 0.8:
                score -= 8  # 接近上轨，可能超买
        
        # 均线评分
        if 'MA' in indicators:
            ma = indicators['MA']
            if ma['price_above_ma20']:
                score += 5
            else:
                score -= 5
            if ma['ma5_above_ma20']:
                score += 5
            else:
                score -= 5
            if ma['ma_alignment']:
                score += 10  # 均线多头排列
        
        # 成交量评分
        if 'VOL' in indicators:
            vol = indicators['VOL']
            if vol['above_average'] and vol['increasing']:
                score += 10  # 放量上涨
            if vol['ratio_to_ma20'] > 2:
                score += 5  # 成交量显著放大
        
        # 限制分数范围
        return max(0, min(100, score))
    
    def _check_buy_signals(self, indicators):
        """检查买入信号"""
        signals = {
            'strength': 0,  # 信号强度，0-1
            'reason': [],   # 信号原因
            'score': 0      # 信号评分
        }
        
        if not indicators:
            return signals
        
        # 检查MACD金叉
        if 'MACD' in indicators and indicators['MACD']['crossover']:
            signals['reason'].append('MACD金叉')
            signals['score'] += 20
        
        # 检查RSI超卖反弹
        if 'RSI' in indicators:
            rsi = indicators['RSI']
            if rsi['oversold'] and rsi['value'] > rsi.get('prev_value', 0):
                signals['reason'].append('RSI超卖反弹')
                signals['score'] += 15
        
        # 检查KDJ金叉
        if 'KDJ' in indicators and indicators['KDJ']['golden_cross']:
            signals['reason'].append('KDJ金叉')
            signals['score'] += 20
        
        # 检查布林带支撑
        if 'BOLL' in indicators:
            boll = indicators['BOLL']
            if boll['position'] < 0.2 and not boll['breakout_down']:
                signals['reason'].append('布林带下轨支撑')
                signals['score'] += 15
        
        # 检查均线支撑和多头排列
        if 'MA' in indicators:
            ma = indicators['MA']
            if ma['ma_alignment']:
                signals['reason'].append('均线多头排列')
                signals['score'] += 15
            if ma['price_above_ma20'] and ma['ma5_trend'] == 'up':
                signals['reason'].append('站上20日均线且5日均线向上')
                signals['score'] += 10
        
        # 检查成交量配合
        if 'VOL' in indicators:
            vol = indicators['VOL']
            if vol['above_average'] and vol['increasing']:
                signals['reason'].append('成交量放大')
                signals['score'] += 15
        
        # 计算信号强度
        signals['strength'] = min(1.0, signals['score'] / 100)
        
        return signals
    
    def _update_market_sentiment(self):
        """更新市场情绪
        优化的市场情绪计算，考虑更多市场指标和近期趋势
        """
        current_time = time.time()
        
        # 检查是否需要更新
        if current_time - self.last_market_update < self.market_sentiment_expiry:
            return
        
        try:
            # 获取大盘指数数据
            indices = [
                {'code': '000001', 'name': '上证指数', 'weight': 0.4},
                {'code': '399001', 'name': '深证成指', 'weight': 0.3},
                {'code': '399006', 'name': '创业板指', 'weight': 0.3}
            ]
            
            sentiment_score = 50  # 基础分数
            market_trend = {'up': 0, 'down': 0, 'neutral': 0}
            volume_trend = {'up': 0, 'down': 0}
            
            for index in indices:
                # 获取指数数据（扩展历史数据获取范围）
                index_data = self.visual_system.get_stock_data(index['code'], limit=30)
                if index_data is None or index_data.empty:
                    continue
                
                # 计算技术指标
                indicators = self._calculate_indicators(index_data)
                
                # 计算指数情绪分数
                index_score = indicators.get('overall_score', 50)
                
                # 趋势分析
                if 'MA' in indicators:
                    ma = indicators['MA']
                    if ma['ma5_above_ma20'] and ma['ma5_trend'] == 'up':
                        market_trend['up'] += index['weight']
                    elif not ma['ma5_above_ma20'] and ma['ma5_trend'] == 'down':
                        market_trend['down'] += index['weight']
                    else:
                        market_trend['neutral'] += index['weight']
                
                # 成交量分析
                if 'VOL' in indicators:
                    vol = indicators['VOL']
                    if vol['above_average'] and vol['increasing']:
                        volume_trend['up'] += index['weight']
                    else:
                        volume_trend['down'] += index['weight']
                
                # 加权计算基础分数
                sentiment_score += (index_score - 50) * index['weight']
            
            # 调整市场情绪分数
            sentiment_score += market_trend['up'] * 10 - market_trend['down'] * 10
            sentiment_score += volume_trend['up'] * 5 - volume_trend['down'] * 5
            
            # 更新市场情绪
            self.market_sentiment_cache = {
                'score': sentiment_score,
                'status': self._get_sentiment_status(sentiment_score),
                'timestamp': current_time
            }
            
            self.last_market_update = current_time
            logger.info(f"市场情绪更新: 分数={sentiment_score}, 状态={self.market_sentiment_cache['status']}")
            
        except Exception as e:
            logger.error(f"更新市场情绪时出错: {str(e)}")
    
    def _get_sentiment_status(self, score):
        """根据分数获取情绪状态"""
        if score >= 80:
            return "极度乐观"
        elif score >= 65:
            return "乐观"
        elif score >= 45:
            return "中性"
        elif score >= 30:
            return "悲观"
        else:
            return "极度悲观"
    
    def get_enhanced_review_pool(self, status=None):
        """获取增强版复盘股票池，包含更丰富的股票信息"""
        try:
            stocks = self.enhanced_review_data.get('stocks', [])
            result = []
            
            for stock in stocks:
                if status is None or stock.get('status') == status:
                    # 获取最新行情数据
                    latest_data = self.visual_system.get_stock_data(stock['symbol'], limit=20)
                    if latest_data is not None and not latest_data.empty:
                        # 计算最新技术指标
                        indicators = self._calculate_indicators(latest_data)
                        
                        # 更新市场情绪
                        self._update_market_sentiment()
                        
                        # 扩展股票信息
                        stock_info = {
                            **stock,
                            'current_price': latest_data['收盘'].iloc[-1],
                            'price_change': round((latest_data['收盘'].iloc[-1] - latest_data['收盘'].iloc[-2]) / latest_data['收盘'].iloc[-2] * 100, 2),
                            'volume_ratio': round(latest_data['成交量'].iloc[-1] / latest_data['成交量'].iloc[-5:].mean(), 2),
                            'macd_signal': indicators.get('MACD', {}).get('signal', '中性'),
                            'rsi_value': indicators.get('RSI', {}).get('value', 50),
                            'kdj_signal': indicators.get('KDJ', {}).get('signal', '中性'),
                            'boll_position': indicators.get('BOLL', {}).get('position', '中轨'),
                            'ma_trend': indicators.get('MA', {}).get('trend', '盘整'),
                            'volume_analysis': indicators.get('VOL', {}).get('signal', '成交量正常'),
                            'market_sentiment': self.market_sentiment_cache.get('status', '未知'),
                            'industry_trend': self._get_industry_trend(stock['symbol']),
                            'signal_strength': indicators.get('overall_score', 50),
                            'last_update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        result.append(stock_info)
                    else:
                        result.append(stock)
            
            # 按信号强度排序
            result.sort(key=lambda x: x.get('signal_strength', 0), reverse=True)
            return result
            
        except Exception as e:
            logger.error(f"获取增强版复盘池数据时出错: {str(e)}")
            return []
    
    def _get_industry_trend(self, symbol):
        """获取行业趋势"""
        try:
            # 这里可以添加获取行业趋势的具体实现
            # 暂时返回默认值
            return '行业趋势向上'
        except Exception as e:
            logger.error(f"获取行业趋势时出错: {str(e)}")
            return '未知'
    
    def add_stock_to_pool(self, stock_code, stock_name=None):
        """将股票添加到增强版复盘池，优化的去重逻辑"""
        try:
            if not stock_name:
                stock_name = self.visual_system.get_stock_name(stock_code)
            
            # 检查股票是否已存在
            for stock in self.enhanced_review_data.get('stocks', []):
                if stock['symbol'] == stock_code:
                    logger.info(f"股票 {stock_code} 已在复盘池中，更新其状态")
                    stock['name'] = stock_name
                    stock['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save_enhanced_data()
                    return True
            
            # 添加新股票
            new_stock = {
                'symbol': stock_code,
                'name': stock_name,
                'add_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'watching',
                'analysis': {},
                'notes': '',
                'source': '手动添加'
            }
            
            if 'stocks' not in self.enhanced_review_data:
                self.enhanced_review_data['stocks'] = []
                
            self.enhanced_review_data['stocks'].append(new_stock)
            self._save_enhanced_data()
            logger.info(f"成功添加股票 {stock_code} 到复盘池")
            return True
            
        except Exception as e:
            logger.error(f"添加股票 {stock_code} 到复盘池时出错: {str(e)}")
            return False
    
    def add_stock_with_analysis(self, symbol, name=None, source='手动添加'):
        """添加股票到复盘池并进行分析"""
        try:
            # 获取股票数据
            stock_data = self.visual_system.get_stock_data(symbol, limit=60)
            if stock_data is None or stock_data.empty:
                logger.error(f"获取股票 {symbol} 数据失败")
                return False
            
            # 获取股票名称
            if name is None:
                name = self.visual_system.get_stock_name(symbol) or symbol
            
            # 计算技术指标
            indicators = self._calculate_indicators(stock_data)
            
            # 检查买入信号
            buy_signals = self._check_buy_signals(indicators)
            
            # 获取市场情绪
            self._update_market_sentiment()
            market_status = self.market_sentiment_cache.get('status', '未知')
            
            # 创建股票记录
            today = datetime.now().strftime("%Y-%m-%d")
            stock_record = {
                'symbol': symbol,
                'name': name,
                'date_added': today,
                'status': 'watching',
                'buy_price': None,
                'sell_price': None,
                'buy_date': None,
                'sell_date': None,
                'profit_percent': None,
                'holding_days': None,
                'notes': '',
                'source': source,
                'analysis_score': indicators.get('overall_score', 0),
                'market_status': market_status,
                'technical_indicators': indicators,
                'buy_signals': buy_signals,
                'last_update': today,
                'price_history': [{
                    'date': today,
                    'price': stock_data['收盘'].iloc[-1],
                    'volume': stock_data['成交量'].iloc[-1]
                }]
            }
            
            # 添加到增强版复盘池
            exists = False
            for i, stock in enumerate(self.enhanced_review_data['stocks']):
                if stock['symbol'] == symbol:
                    self.enhanced_review_data['stocks'][i] = stock_record
                    exists = True
                    break
            
            if not exists:
                self.enhanced_review_data['stocks'].append(stock_record)
            # 保存数据
            self._save_enhanced_data()
            
            # 同时添加到原始复盘池
            super().add_to_review_pool([{
                'symbol': symbol,
                'name': name,
                'recommendation': '强烈推荐买入',
                'score': indicators.get('overall_score', 0),
                'market_status': market_status
            }])
            
            logger.info(f"已添加股票 {symbol} 到复盘池并完成分析")
            return True
            
        except Exception as e:
            logger.error(f"添加股票 {symbol} 到复盘池时出错: {str(e)}")
            return False
    
    def update_enhanced_stock_status(self, symbol, status, price=None, date=None, notes=None):
        """更新增强版股票状态"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 更新增强版复盘池
        updated = False
        for stock in self.enhanced_review_data['stocks']:
            if stock['symbol'] == symbol:
                stock['status'] = status
                
                if status == 'bought':
                    stock['buy_price'] = price
                    stock['buy_date'] = date
                    # 添加买入记录到价格历史
                    stock['price_history'].append({
                        'date': date,
                        'price': price,
                        'action': 'buy'
                    })
                    
                elif status == 'sold' and stock['buy_price'] is not None:
                    stock['sell_price'] = price
                    stock['sell_date'] = date
                    
                    # 计算收益率和持有天数
                    if stock['buy_price'] > 0:
                        stock['profit_percent'] = round((price - stock['buy_price']) / stock['buy_price'] * 100, 2)
                    
                    buy_date_obj = datetime.strptime(stock['buy_date'], "%Y-%m-%d")
                    sell_date_obj = datetime.strptime(date, "%Y-%m-%d")
                    stock['holding_days'] = (sell_date_obj - buy_date_obj).days
                    
                    # 添加卖出记录到价格历史
                    stock['price_history'].append({
                        'date': date,
                        'price': price,
                        'action': 'sell',
                        'profit_percent': stock['profit_percent'],
                        'holding_days': stock['holding_days']
                    })
                    
                    # 更新策略绩效
                    self._update_strategy_performance(stock)
                
                if notes:
                    stock['notes'] = notes
                
                stock['last_update'] = date
                updated = True
                break
        
        if updated:
            self._save_enhanced_data()
            
            # 同时更新原始复盘池
            super().update_stock_status(symbol, status, price, date, notes)
            
            logger.info(f"已更新股票 {symbol} 的状态为 {status}")
            return True
        else:
            logger.warning(f"未找到股票 {symbol}")
            return False
    
    def _update_strategy_performance(self, stock):
        """更新策略绩效数据"""
        if 'buy_signals' not in stock or not stock.get('profit_percent'):
            return
        
        # 获取交易使用的策略
        strategies = []
        if 'MACD金叉' in stock['buy_signals'].get('reason', []):
            strategies.append('MACD金叉策略')
        if 'KDJ金叉' in stock['buy_signals'].get('reason', []):
            strategies.append('KDJ金叉策略')
        if '均线多头排列' in stock['buy_signals'].get('reason', []):
            strategies.append('均线策略')
        if '布林带下轨支撑' in stock['buy_signals'].get('reason', []):
            strategies.append('布林带策略')
        if '成交量放大' in stock['buy_signals'].get('reason', []):
            strategies.append('量价策略')
        
        # 如果没有明确的策略，使用综合策略
        if not strategies:
            strategies.append('综合策略')
        
        # 更新每个策略的绩效
        for strategy in strategies:
            if strategy not in self.strategy_performance['strategies']:
                self.strategy_performance['strategies'][strategy] = {
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_profit': 0,
                    'max_profit': 0,
                    'max_loss': 0,
                    'avg_holding_days': 0,
                    'total_holding_days': 0,
                    'history': []
                }
            
            perf = self.strategy_performance['strategies'][strategy]
            perf['trades'] += 1
            
            profit = stock['profit_percent']
            perf['total_profit'] += profit
            
            if profit > 0:
                perf['wins'] += 1
                perf['max_profit'] = max(perf['max_profit'], profit)
            else:
                perf['losses'] += 1
                perf['max_loss'] = min(perf['max_loss'], profit)
            
            perf['total_holding_days'] += stock['holding_days']
            perf['avg_holding_days'] = perf['total_holding_days'] / perf['trades']
            
            # 添加交易历史
            perf['history'].append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'buy_date': stock['buy_date'],
                'sell_date': stock['sell_date'],
                'buy_price': stock['buy_price'],
                'sell_price': stock['sell_price'],
                'profit_percent': profit,
                'holding_days': stock['holding_days']
            })
        
        # 保存策略绩效数据
        self._save_strategy_performance()
    
    def get_strategy_performance_stats(self):
        """获取策略绩效统计"""
        result = {}
        
        for strategy, perf in self.strategy_performance['strategies'].items():
            if perf['trades'] == 0:
                continue
                
            win_rate = round(perf['wins'] / perf['trades'] * 100, 2) if perf['trades'] > 0 else 0
            avg_profit = round(perf['total_profit'] / perf['trades'], 2) if perf['trades'] > 0 else 0
            
            result[strategy] = {
                'trades': perf['trades'],
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'max_profit': perf['max_profit'],
                'max_loss': perf['max_loss'],
                'avg_holding_days': round(perf['avg_holding_days'], 1),
                'total_profit': round(perf['total_profit'], 2)
            }
        
        return result
    
    def get_alerts(self, limit=10, alert_type=None):
        """获取提醒历史"""
        alerts = self.alert_history.get('alerts', [])
        
        # 按时间倒序排序
        alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 筛选类型
        if alert_type is not None:
            alerts = [a for a in alerts if a.get('type') == alert_type]
        
        # 限制数量
        return alerts[:limit] if limit > 0 else alerts
    
    def get_market_sentiment(self):
        """获取市场情绪"""
        # 如果缓存过期，更新市场情绪
        current_time = time.time()
        if current_time - self.last_market_update >= self.market_sentiment_expiry:
            self._update_market_sentiment()
        
        return self.market_sentiment_cache
    
    def visualize_enhanced_performance(self):
        """可视化增强版绩效分析结果"""
        try:
            # 获取所有已完成的交易
            completed_trades = []
            for stock in self.enhanced_review_data['stocks']:
                if stock['status'] == 'sold' and stock.get('profit_percent') is not None:
                    completed_trades.append(stock)
            
            if not completed_trades:
                return None
            
            # 创建绩效分析图表
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('策略绩效对比', '月度收益趋势', '持仓时间分析', '盈亏分布'),
                specs=[[{'type': 'bar'}, {'type': 'scatter'}],
                       [{'type': 'box'}, {'type': 'histogram'}]]
            )
            
            # 策略绩效对比
            strategy_stats = self.get_strategy_performance_stats()
            strategies = list(strategy_stats.keys())
            win_rates = [stats['win_rate'] for stats in strategy_stats.values()]
            avg_profits = [stats['avg_profit'] for stats in strategy_stats.values()]
            
            fig.add_trace(
                go.Bar(x=strategies, y=win_rates, name='胜率(%)', marker_color='blue'),
                row=1, col=1
            )
            fig.add_trace(
                go.Bar(x=strategies, y=avg_profits, name='平均收益(%)', marker_color='green'),
                row=1, col=1
            )
            
            # 月度收益趋势
            df = pd.DataFrame(completed_trades)
            df['sell_date'] = pd.to_datetime(df['sell_date'])
            monthly_profits = df.groupby(df['sell_date'].dt.strftime('%Y-%m'))['profit_percent'].mean()
            
            fig.add_trace(
                go.Scatter(x=monthly_profits.index, y=monthly_profits.values, 
                          mode='lines+markers', name='月度平均收益(%)',
                          line=dict(color='purple', width=2)),
                row=1, col=2
            )
            
            # 持仓时间分析
            holding_days = [trade['holding_days'] for trade in completed_trades]
            profits = [trade['profit_percent'] for trade in completed_trades]
            
            fig.add_trace(
                go.Box(y=holding_days, name='持仓天数分布'),
                row=2, col=1
            )
            
            # 盈亏分布
            fig.add_trace(
                go.Histogram(x=profits, name='收益分布', 
                            marker_color=['green' if p > 0 else 'red' for p in profits]),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                showlegend=True,
                title_text='增强版交易绩效分析'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成增强版绩效分析图表时出错：{str(e)}")
            return None
    
    def get_enhanced_performance_summary(self):
        """获取增强版绩效摘要"""
        try:
            # 获取所有已完成的交易
            completed_trades = [stock for stock in self.enhanced_review_data['stocks'] 
                               if stock['status'] == 'sold' and stock.get('profit_percent') is not None]
            
            if not completed_trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'avg_profit': 0,
                    'avg_holding_days': 0,
                    'max_profit': 0,
                    'max_loss': 0,
                    'total_profit': 0,
                    'best_strategy': '无数据',
                    'market_sentiment': '未知'
                }
            
            # 基本统计
            total_trades = len(completed_trades)
            win_trades = len([t for t in completed_trades if t['profit_percent'] > 0])
            win_rate = round(win_trades / total_trades * 100, 2) if total_trades > 0 else 0
            
            profits = [t['profit_percent'] for t in completed_trades]
            avg_profit = round(sum(profits) / len(profits), 2) if profits else 0
            max_profit = round(max(profits), 2) if profits else 0
            max_loss = round(min(profits), 2) if profits else 0
            total_profit = round(sum(profits), 2) if profits else 0
            
            holding_days = [t['holding_days'] for t in completed_trades]
            avg_holding_days = round(sum(holding_days) / len(holding_days), 2) if holding_days else 0
            
            # 最佳策略
            strategy_stats = self.get_strategy_performance_stats()
            best_strategy = '无数据'
            best_profit = -float('inf')
            
            for strategy, stats in strategy_stats.items():
                if stats['trades'] >= 3 and stats['avg_profit'] > best_profit:  # 至少3次交易才有参考价值
                    best_strategy = strategy
                    best_profit = stats['avg_profit']
            
            # 市场情绪
            market_sentiment = self.get_market_sentiment().get('status', '未知')
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'avg_holding_days': avg_holding_days,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'total_profit': total_profit,
                'best_strategy': best_strategy,
                'market_sentiment': market_sentiment
            }
            
        except Exception as e:
            logger.error(f"获取增强版绩效摘要时出错：{str(e)}")
            return None
    
    def integrate_with_ui(self, app):
        """与股票分析应用UI集成"""
        try:
            from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QApplication
            from PyQt5.QtCore import Qt
            
            # 添加增强版复盘功能到应用
            def show_enhanced_stock_review():
                # 清空之前的结果
                app.result_text.clear()
                app.result_text.append('正在加载增强版复盘数据...')
                QApplication.processEvents()
                
                # 获取复盘股票池
                all_stocks = self.get_enhanced_review_pool()
                watching_stocks = self.get_enhanced_review_pool(status='watching')
                bought_stocks = self.get_enhanced_review_pool(status='bought')
                sold_stocks = self.get_enhanced_review_pool(status='sold')
                
                # 获取绩效统计
                performance = self.get_enhanced_performance_summary()
                
                # 获取市场情绪
                market_sentiment = self.get_market_sentiment()
                
                # 获取最近提醒
                recent_alerts = self.get_alerts(limit=5)
                
                # 格式化输出复盘结果
                output = f"""增强版股票复盘分析：

市场情绪：{market_sentiment.get('status', '未知')} (分数: {market_sentiment.get('score', 0):.1f})

复盘池概况：
- 总股票数：{len(all_stocks)}只
- 观察中：{len(watching_stocks)}只
- 已买入：{len(bought_stocks)}只
- 已卖出：{len(sold_stocks)}只

交易绩效统计：
- 总交易次数：{performance['total_trades']}次
- 胜率：{performance['win_rate']}%
- 平均收益：{performance['avg_profit']}%
- 平均持仓天数：{performance['avg_holding_days']}天
- 最大收益：{performance['max_profit']}%
- 最大亏损：{performance['max_loss']}%
- 总收益：{performance['total_profit']}%
- 最佳策略：{performance['best_strategy']}

最近提醒："""
                
                # 添加最近提醒
                if recent_alerts:
                    for i, alert in enumerate(recent_alerts, 1):
                        output += f"\n{i}. [{alert.get('timestamp', '')}] {alert.get('name', '')}({alert.get('symbol', '')})："
                        output += f"\n   - 类型：{alert.get('type', '')}"
                        output += f"\n   - 价格：{alert.get('price', 0)}"
                        output += f"\n   - 原因：{alert.get('reason', '')}"
                else:
                    output += "\n暂无提醒"
                
                # 添加最近的交易记录
                output += "\n\n最近交易记录："
                recent_trades = sorted(
                    [s for s in all_stocks if s['status'] == 'sold'],
                    key=lambda x: x.get('sell_date', ''),
                    reverse=True
                )[:5]  # 最近5条记录
                
                if recent_trades:
                    for i, trade in enumerate(recent_trades, 1):
                        profit_color = '红色' if trade.get('profit_percent', 0) > 0 else '绿色'
                        output += f"\n{i}. {trade.get('name', '')}({trade.get('symbol', '')})："
                        output += f"\n   - 买入日期：{trade.get('buy_date', '')}"
                        output += f"\n   - 买入价格：{trade.get('buy_price', 0)}"
                        output += f"\n   - 卖出日期：{trade.get('sell_date', '')}"
                        output += f"\n   - 卖出价格：{trade.get('sell_price', 0)}"
                        output += f"\n   - 收益率：{trade.get('profit_percent', 0)}%"
                        output += f"\n   - 持有天数：{trade.get('holding_days', 0)}天"
                        output += f"\n   - 交易策略：{', '.join(trade.get('buy_signals', {}).get('reason', ['综合策略']))}"
                else:
                    output += "\n暂无交易记录"
                
                # 添加当前持仓
                output += "\n\n当前持仓："
                if bought_stocks:
                    for i, stock in enumerate(bought_stocks, 1):
                        buy_date = stock.get('buy_date', datetime.now().strftime('%Y-%m-%d'))
                        buy_date_obj = datetime.strptime(buy_date, '%Y-%m-%d')
                        holding_days = (datetime.now() - buy_date_obj).days
                        
                        output += f"\n{i}. {stock.get('name', '')}({stock.get('symbol', '')})："
                        output += f"\n   - 买入日期：{buy_date}"
                        output += f"\n   - 买入价格：{stock.get('buy_price', 0)}"
                        output += f"\n   - 持有天数：{holding_days}天"
                        output += f"\n   - 技术评分：{stock.get('analysis_score', 0)}"
                        output += f"\n   - 买入策略：{', '.join(stock.get('buy_signals', {}).get('reason', ['综合策略']))}"
                else:
                    output += "\n暂无持仓"
                
                # 添加观察中的股票
                output += "\n\n观察中的股票："
                if watching_stocks:
                    # 按分析得分排序
                    watching_stocks = sorted(watching_stocks, key=lambda x: x.get('analysis_score', 0), reverse=True)
                    for i, stock in enumerate(watching_stocks, 1):
                        output += f"\n{i}. {stock.get('name', '')}({stock.get('symbol', '')}) - 添加日期：{stock.get('date_added', '')}"
                        output += f"\n   - 分析得分：{stock.get('analysis_score', 0)}"
                        output += f"\n   - 市场状态：{stock.get('market_status', '')}"
                        output += f"\n   - 来源：{stock.get('source', '')}"
                        if stock.get('buy_signals', {}).get('reason'):
                            output += f"\n   - 买入信号：{', '.join(stock['buy_signals']['reason'])}"
                        if stock.get('notes'):
                            output += f"\n   - 备注：{stock.get('notes', '')}"
                else:
                    output += "\n暂无观察中的股票"
                
                # 显示结果
                app.result_text.clear()
                app.result_text.append(output)
            
            # 添加自动跟踪控制功能
            def toggle_auto_tracking():
                if self.auto_tracking_enabled:
                    if self.stop_auto_tracking():
                        QMessageBox.information(app, '提示', '自动跟踪功能已停止')
                    else:
                        QMessageBox.warning(app, '警告', '停止自动跟踪功能失败')
                else:
                    interval, ok = QInputDialog.getInt(
                        app, '设置跟踪间隔',
                        '请输入跟踪间隔（分钟）：',
                        30, 5, 120, 5
                    )
                    
                    if ok:
                        self.tracking_interval = interval * 60
                        if self.start_auto_tracking():
                            QMessageBox.information(app, '提示', f'自动跟踪功能已启动，间隔：{interval}分钟')
                        else:
                            QMessageBox.warning(app, '警告', '启动自动跟踪功能失败')
            
            # 添加手动添加股票功能
            def add_stock_manually():
                symbol, ok = QInputDialog.getText(
                    app, '添加股票',
                    '请输入股票代码：',
                    QLineEdit.Normal
                )
                
                if ok and symbol:
                    name, ok = QInputDialog.getText(
                        app, '添加股票',
                        '请输入股票名称（可选）：',
                        QLineEdit.Normal
                    )
                    
                    if ok:
                        notes, ok = QInputDialog.getText(
                            app, '添加股票',
                            '请输入备注（可选）：',
                            QLineEdit.Normal
                        )
                        
                        if ok:
                            if self.add_stock_with_analysis(symbol, name if name else None):
                                # 如果有备注，更新备注
                                if notes:
                                    for stock in self.enhanced_review_data['stocks']:
                                        if stock['symbol'] == symbol:
                                            stock['notes'] = notes
                                            self._save_enhanced_data()
                                            break
                                
                                QMessageBox.information(app, '提示', f'已添加股票 {symbol} 到复盘池并完成分析')
                                show_enhanced_stock_review()  # 刷新显示
                            else:
                                QMessageBox.warning(app, '警告', f'添加股票 {symbol} 失败')
            
            # 返回功能字典，可以被应用集成
            return {
                'show_enhanced_review': show_enhanced_stock_review,
                'toggle_auto_tracking': toggle_auto_tracking,
                'add_stock_manually': add_stock_manually,
                'review_instance': self
            }
            
        except Exception as e:
            logger.error(f"与UI集成时出错：{str(e)}")
            return None

    def analyze_with_volume_price_strategy(self, symbol):
        """使用体积价格分析策略分析股票"""
        try:
            # 获取股票数据
            data = self.visual_system.get_stock_data(symbol, limit=100)
            if data is None or data.empty:
                logger.warning(f"获取股票 {symbol} 数据失败")
                return None
            
            # 创建策略实例并分析
            strategy = VolumePriceStrategy()
            analysis = strategy.analyze(data)
    
            if analysis:
                # 更新股票的分析得分和市场状态
                for stock in self.review_pool['stocks']:
                    if stock['symbol'] == symbol:
                        stock['analysis_score'] = analysis['strategy_score']
                        stock['market_status'] = self._get_market_status_from_analysis(analysis)
                        break
            
            # 保存更新
            self._save_review_pool()
    
            return analysis
    
        except Exception as e:
            logger.error(f"体积价格策略分析出错: {str(e)}")
            return None

    def _get_market_status_from_analysis(self, analysis):
        """根据分析结果生成市场状态描述"""
        status = []
        
        if analysis['volume_trend']['trend'] == 'increasing':
            status.append('成交量上升')
        else:
            status.append('成交量下降')
        
        if analysis['price_volume_divergence']['exists']:
            if analysis['price_volume_divergence']['type'] == 'positive':
                status.append('价量正背离')
            else:
                status.append('价量负背离')
        
        if analysis['volume_breakout']['exists']:
            if analysis['volume_breakout']['type'] == 'up':
                status.append('成交量突破')
            else:
                status.append('成交量跌破')
        
        return '、'.join(status)