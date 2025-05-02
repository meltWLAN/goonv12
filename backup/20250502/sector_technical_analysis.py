#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业技术分析模块
为增强版行业分析器提供技术分析支持
"""

import os
import time
import json
import logging
import numpy as np
import pandas as pd
import tushare as ts
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SectorTechnical')

class SectorTechnicalAnalyzer:
    """行业技术分析器"""
    
    def __init__(self, token: str = None, cache_dir: str = './data_cache'):
        """初始化
        
        Args:
            token: Tushare API token
            cache_dir: 缓存目录
        """
        self.token = token or os.environ.get('TUSHARE_TOKEN') or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化Tushare
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        # 缓存有效期 (秒)
        self.cache_expiry = 3600  # 1小时
        
    def analyze_sector(self, sector_code: str, sector_name: str) -> Dict:
        """对行业进行技术分析
        
        Args:
            sector_code: 行业指数代码
            sector_name: 行业名称
            
        Returns:
            技术分析结果字典
        """
        cache_path = os.path.join(self.cache_dir, f"sector_tech_{sector_code}.json")
        
        # 检查缓存
        if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < self.cache_expiry):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
                
        try:
            # 获取行业指数历史数据 (90天)
            df = self.pro.index_daily(
                ts_code=sector_code, 
                start_date=(datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            )
            
            if df is None or df.empty:
                return {
                    'status': 'error',
                    'message': f"无法获取行业 {sector_name} 的历史数据"
                }
            
            # 按日期排序 (从旧到新)
            df = df.sort_values(by='trade_date')
            
            # 计算技术指标
            df = self._calculate_indicators(df)
            
            # 获取最新数据
            latest = df.iloc[-1]
            
            # 技术分析结果
            tech_result = {
                'status': 'success',
                'data': {
                    'sector': sector_name,
                    'code': sector_code,
                    'date': latest['trade_date'],
                    'price': latest['close'],
                    'change': latest['pct_chg'],
                    'volume': latest['vol'],
                    'amount': latest['amount'],
                    'indicators': {
                        'macd': {
                            'dif': latest['dif'],
                            'dea': latest['dea'],
                            'macd': latest['macd'],
                            'signal': self._get_macd_signal(latest)
                        },
                        'kdj': {
                            'k': latest['kdj_k'],
                            'd': latest['kdj_d'],
                            'j': latest['kdj_j'],
                            'signal': self._get_kdj_signal(latest)
                        },
                        'rsi': {
                            'rsi6': latest['rsi_6'],
                            'rsi12': latest['rsi_12'],
                            'rsi24': latest['rsi_24'],
                            'signal': self._get_rsi_signal(latest)
                        },
                        'ma': {
                            'ma5': latest['ma5'],
                            'ma10': latest['ma10'],
                            'ma20': latest['ma20'],
                            'ma60': latest['ma60'],
                            'signal': self._get_ma_signal(latest)
                        },
                        'boll': {
                            'upper': latest['boll_upper'],
                            'mid': latest['boll_mid'],
                            'lower': latest['boll_lower'],
                            'signal': self._get_boll_signal(latest)
                        }
                    },
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            # 添加趋势分析
            tech_result['data']['trend_analysis'] = self._analyze_trend(df, sector_name)
            
            # 添加综合技术评分 (0-100)
            tech_result['data']['tech_score'] = self._calculate_tech_score(latest, tech_result['data']['trend_analysis'])
            
            # 添加交易信号
            tech_result['data']['trade_signal'] = self._get_trade_signal(tech_result['data'])
            
            # 保存到缓存
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(tech_result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存行业技术分析缓存失败: {e}")
            
            return tech_result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"行业 {sector_name} 技术分析失败: {str(e)}"
            }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 确保数据按时间升序排序
        df = df.sort_values(by='trade_date').reset_index(drop=True)
        
        # MACD
        short_ema = df['close'].ewm(span=12, adjust=False).mean()
        long_ema = df['close'].ewm(span=26, adjust=False).mean()
        df['dif'] = short_ema - long_ema
        df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
        df['macd'] = 2 * (df['dif'] - df['dea'])
        
        # KDJ
        low_9 = df['low'].rolling(window=9).min()
        high_9 = df['high'].rolling(window=9).max()
        df['rsv'] = (df['close'] - low_9) / (high_9 - low_9) * 100
        df['kdj_k'] = df['rsv'].ewm(alpha=1/3, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(alpha=1/3, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        # RSI
        delta = df['close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        
        avg_up_6 = up.rolling(window=6).mean()
        avg_down_6 = down.rolling(window=6).mean()
        rs_6 = avg_up_6 / avg_down_6
        df['rsi_6'] = 100 - (100 / (1 + rs_6))
        
        avg_up_12 = up.rolling(window=12).mean()
        avg_down_12 = down.rolling(window=12).mean()
        rs_12 = avg_up_12 / avg_down_12
        df['rsi_12'] = 100 - (100 / (1 + rs_12))
        
        avg_up_24 = up.rolling(window=24).mean()
        avg_down_24 = down.rolling(window=24).mean()
        rs_24 = avg_up_24 / avg_down_24
        df['rsi_24'] = 100 - (100 / (1 + rs_24))
        
        # 移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # 布林带
        df['boll_mid'] = df['close'].rolling(window=20).mean()
        df['boll_std'] = df['close'].rolling(window=20).std()
        df['boll_upper'] = df['boll_mid'] + 2 * df['boll_std']
        df['boll_lower'] = df['boll_mid'] - 2 * df['boll_std']
        
        # 成交量指标
        df['vol_ma5'] = df['vol'].rolling(window=5).mean()
        df['vol_ma10'] = df['vol'].rolling(window=10).mean()
        
        return df.fillna(0)
    
    def _get_macd_signal(self, row: pd.Series) -> str:
        """获取MACD信号"""
        if row['macd'] > 0 and row['dif'] > 0 and row['dif'] > row['dea']:
            return '强烈买入'
        elif row['macd'] > 0 and row['dif'] > row['dea']:
            return '买入'
        elif row['macd'] < 0 and row['dif'] < 0 and row['dif'] < row['dea']:
            return '强烈卖出'
        elif row['macd'] < 0 and row['dif'] < row['dea']:
            return '卖出'
        else:
            return '中性'
    
    def _get_kdj_signal(self, row: pd.Series) -> str:
        """获取KDJ信号"""
        k, d, j = row['kdj_k'], row['kdj_d'], row['kdj_j']
        
        if k > d and j > 0 and k < 20:
            return '超卖反弹买入'
        elif k > d and k < 50:
            return '买入'
        elif k < d and j < 100 and k > 80:
            return '超买调整卖出'
        elif k < d and k > 50:
            return '卖出'
        else:
            return '中性'
    
    def _get_rsi_signal(self, row: pd.Series) -> str:
        """获取RSI信号"""
        rsi6, rsi12 = row['rsi_6'], row['rsi_12']
        
        if rsi6 < 20:
            return '严重超卖'
        elif rsi6 < 30:
            return '超卖'
        elif rsi6 > 80:
            return '严重超买'
        elif rsi6 > 70:
            return '超买'
        elif rsi6 > rsi12 and rsi6 > 50:
            return '偏多'
        elif rsi6 < rsi12 and rsi6 < 50:
            return '偏空'
        else:
            return '中性'
    
    def _get_ma_signal(self, row: pd.Series) -> str:
        """获取均线信号"""
        price = row['close']
        ma5, ma10, ma20, ma60 = row['ma5'], row['ma10'], row['ma20'], row['ma60']
        
        if price > ma5 > ma10 > ma20:
            return '强势上涨'
        elif price > ma5 > ma10:
            return '初步上涨'
        elif price < ma5 < ma10 < ma20:
            return '强势下跌'
        elif price < ma5 < ma10:
            return '初步下跌'
        elif price > ma5 and ma5 < ma10:
            return '反弹'
        elif price < ma5 and ma5 > ma10:
            return '回调'
        elif ma5 > ma10 > ma20:
            return '多头排列'
        elif ma5 < ma10 < ma20:
            return '空头排列'
        else:
            return '震荡'
    
    def _get_boll_signal(self, row: pd.Series) -> str:
        """获取布林带信号"""
        price = row['close']
        upper, mid, lower = row['boll_upper'], row['boll_mid'], row['boll_lower']
        
        if price > upper:
            return '超买区间'
        elif price < lower:
            return '超卖区间'
        elif price > mid and price < upper:
            return '上轨压力'
        elif price < mid and price > lower:
            return '下轨支撑'
        else:
            return '中轨徘徊'
    
    def _analyze_trend(self, df: pd.DataFrame, sector_name: str) -> Dict:
        """分析行业趋势"""
        # 确保至少有60条数据
        if len(df) < 60:
            return {
                'trend': '数据不足',
                'strength': 0,
                'support': 0,
                'resistance': 0,
                'analysis': '历史数据不足，无法分析趋势'
            }
        
        # 获取最近的数据
        recent = df.iloc[-60:].reset_index(drop=True)
        
        # 计算趋势
        close_prices = recent['close'].values
        period = len(close_prices)
        x = np.arange(period)
        slope, intercept = np.polyfit(x, close_prices, 1)
        
        # 趋势强度 (斜率 / 均价的百分比)
        avg_price = np.mean(close_prices)
        trend_strength = (slope * period / avg_price) * 100
        
        # 确定支撑位和阻力位
        latest_price = close_prices[-1]
        price_std = np.std(close_prices)
        
        # 寻找局部最低点作为支撑位
        support_levels = []
        for i in range(2, len(recent) - 2):
            if (recent['low'].iloc[i] < recent['low'].iloc[i-1] and 
                recent['low'].iloc[i] < recent['low'].iloc[i-2] and
                recent['low'].iloc[i] < recent['low'].iloc[i+1] and
                recent['low'].iloc[i] < recent['low'].iloc[i+2]):
                support_levels.append(recent['low'].iloc[i])
        
        # 寻找局部最高点作为阻力位
        resistance_levels = []
        for i in range(2, len(recent) - 2):
            if (recent['high'].iloc[i] > recent['high'].iloc[i-1] and 
                recent['high'].iloc[i] > recent['high'].iloc[i-2] and
                recent['high'].iloc[i] > recent['high'].iloc[i+1] and
                recent['high'].iloc[i] > recent['high'].iloc[i+2]):
                resistance_levels.append(recent['high'].iloc[i])
        
        # 筛选接近当前价格的支撑位和阻力位
        support = 0
        if support_levels:
            valid_supports = [s for s in support_levels if s < latest_price and s > latest_price * 0.9]
            if valid_supports:
                support = max(valid_supports)
        
        resistance = 0
        if resistance_levels:
            valid_resistances = [r for r in resistance_levels if r > latest_price and r < latest_price * 1.1]
            if valid_resistances:
                resistance = min(valid_resistances)
        
        # 如果没有找到合适的支撑位或阻力位，使用统计方法估算
        if support == 0:
            support = round(latest_price - price_std * 1.5, 2)
        if resistance == 0:
            resistance = round(latest_price + price_std * 1.5, 2)
        
        # 确定趋势方向和强度描述
        if trend_strength > 15:
            trend = '强势上升'
            analysis = f"{sector_name}行业处于强势上升通道，短期突破阻力位{resistance}概率较大"
        elif trend_strength > 5:
            trend = '上升'
            analysis = f"{sector_name}行业处于上升趋势，支撑位于{support}，阻力位于{resistance}"
        elif trend_strength < -15:
            trend = '强势下降'
            analysis = f"{sector_name}行业处于强势下降通道，短期跌破支撑位{support}风险较大"
        elif trend_strength < -5:
            trend = '下降'
            analysis = f"{sector_name}行业处于下降趋势，支撑位于{support}，阻力位于{resistance}"
        else:
            trend = '震荡'
            analysis = f"{sector_name}行业处于震荡整理阶段，区间{support}-{resistance}内波动"
        
        return {
            'trend': trend,
            'strength': round(trend_strength, 2),
            'support': support,
            'resistance': resistance,
            'analysis': analysis
        }
    
    def _calculate_tech_score(self, row: pd.Series, trend_analysis: Dict) -> int:
        """计算技术分析评分 (0-100)"""
        score = 50  # 基础分
        
        # 1. 趋势分数 (±25分)
        trend_strength = trend_analysis['strength']
        trend_score = min(max(trend_strength * 1.5, -25), 25)
        
        # 2. MACD分数 (±10分)
        macd_signal = self._get_macd_signal(row)
        macd_score = 0
        if macd_signal == '强烈买入':
            macd_score = 10
        elif macd_signal == '买入':
            macd_score = 5
        elif macd_signal == '卖出':
            macd_score = -5
        elif macd_signal == '强烈卖出':
            macd_score = -10
        
        # 3. KDJ分数 (±10分)
        kdj_signal = self._get_kdj_signal(row)
        kdj_score = 0
        if kdj_signal == '超卖反弹买入':
            kdj_score = 10
        elif kdj_signal == '买入':
            kdj_score = 5
        elif kdj_signal == '卖出':
            kdj_score = -5
        elif kdj_signal == '超买调整卖出':
            kdj_score = -10
        
        # 4. RSI分数 (±10分)
        rsi_signal = self._get_rsi_signal(row)
        rsi_score = 0
        if rsi_signal in ['严重超卖', '超卖']:
            rsi_score = 8
        elif rsi_signal == '偏多':
            rsi_score = 5
        elif rsi_signal == '偏空':
            rsi_score = -5
        elif rsi_signal in ['严重超买', '超买']:
            rsi_score = -8
        
        # 5. 均线分数 (±10分)
        ma_signal = self._get_ma_signal(row)
        ma_score = 0
        if ma_signal == '强势上涨':
            ma_score = 10
        elif ma_signal == '初步上涨' or ma_signal == '多头排列':
            ma_score = 7
        elif ma_signal == '反弹':
            ma_score = 5
        elif ma_signal == '回调':
            ma_score = -5
        elif ma_signal == '初步下跌' or ma_signal == '空头排列':
            ma_score = -7
        elif ma_signal == '强势下跌':
            ma_score = -10
        
        # 计算总分
        total_score = score + trend_score + macd_score + kdj_score + rsi_score + ma_score
        
        # 限制在0-100范围内
        return max(min(round(total_score), 100), 0)
    
    def _get_trade_signal(self, data: Dict) -> Dict:
        """获取交易信号"""
        tech_score = data['tech_score']
        trend = data['trend_analysis']['trend']
        
        # 根据技术评分和趋势确定交易信号
        if tech_score >= 80:
            signal = '强烈买入'
            desc = '技术指标高度看多，建议积极买入'
            action = f"可考虑买入{data['sector']}行业龙头股"
        elif tech_score >= 65:
            signal = '买入'
            desc = '技术指标偏多，可以考虑买入'
            action = f"关注{data['sector']}行业绩优股"
        elif tech_score <= 20:
            signal = '强烈卖出'
            desc = '技术指标高度看空，建议清仓观望'
            action = f"建议暂时回避{data['sector']}行业风险"
        elif tech_score <= 35:
            signal = '卖出'
            desc = '技术指标偏空，建议减持'
            action = f"减持{data['sector']}行业表现弱势的个股"
        elif tech_score > 55 and '上升' in trend:
            signal = '持有'
            desc = '技术指标中性偏多，可持有或少量加仓'
            action = f"持有{data['sector']}行业绩优股"
        elif tech_score < 45 and '下降' in trend:
            signal = '观望'
            desc = '技术指标中性偏空，建议观望为主'
            action = f"暂时观望{data['sector']}行业"
        else:
            signal = '中性'
            desc = '技术指标中性，可根据个股表现决策'
            action = f"关注{data['sector']}行业个股分化"
        
        return {
            'signal': signal,
            'description': desc,
            'action': action,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# 单元测试
if __name__ == "__main__":
    analyzer = SectorTechnicalAnalyzer()
    # 使用申万电子行业进行测试
    result = analyzer.analyze_sector('801080.SI', '电子')
    print(json.dumps(result, indent=2, ensure_ascii=False)) 