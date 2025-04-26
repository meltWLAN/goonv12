import pandas as pd
import numpy as np
import yfinance as yf
import talib as ta
from stockstats import StockDataFrame
from datetime import datetime, timedelta
import pytz
from tqdm import tqdm

class StockRecommender:
    def __init__(self):
        self.china_tz = pytz.timezone('Asia/Shanghai')
        
    def get_stock_data(self, symbol, period='60d'):
        """获取股票历史数据"""
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            return df
        except Exception as e:
            print(f"获取{symbol}数据失败: {e}")
            return None

    def analyze_momentum(self, df):
        """动量分析
        计算EMA21、MACD等动量指标
        """
        if df is None or len(df) < 21:
            return None

        # 计算EMA21
        df['EMA21'] = ta.EMA(df['Close'], timeperiod=21)
        
        # 计算MACD
        macd, signal, hist = ta.MACD(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist

        return df

    def analyze_volume_price(self, df):
        """量价分析
        分析成交量与价格的关系
        """
        if df is None or len(df) < 20:
            return None

        # 确保Volume列存在且为数值类型
        if 'Volume' not in df.columns:
            print(f"错误：数据中缺少Volume列")
            return None

        # 将Volume转换为数值类型并处理空值
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        df['Volume'] = df['Volume'].fillna(method='ffill').fillna(method='bfill')

        if df['Volume'].isnull().any():
            print(f"警告：Volume数据包含无法处理的空值")
            return None

        # 计算20日均量
        df['Volume_MA20'] = df['Volume'].rolling(window=20, min_periods=1).mean()
        
        # 计算ATR
        df['ATR'] = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)

        # 计算量价背离
        df['Price_Change'] = df['Close'].pct_change()
        df['Volume_Change'] = df['Volume'].pct_change()
        
        return df

    def check_trend(self, df):
        """趋势判断
        基于EMA21和MACD判断趋势
        """
        if df is None or len(df) < 21:
            return 'unknown'

        last_close = df['Close'].iloc[-1]
        last_ema21 = df['EMA21'].iloc[-1]
        last_macd = df['MACD_Hist'].iloc[-1]

        if last_close > last_ema21 and last_macd > 0:
            return 'uptrend'
        elif last_close < last_ema21 and last_macd < 0:
            return 'downtrend'
        else:
            return 'sideways'

    def analyze_stock(self, symbol):
        """综合分析单个股票"""
        # 获取数据
        df = self.get_stock_data(symbol)
        if df is None:
            return None

        # 动量分析
        df = self.analyze_momentum(df)
        if df is None:
            return None

        # 量价分析
        df = self.analyze_volume_price(df)
        if df is None:
            return None

        # 趋势判断
        trend = self.check_trend(df)

        # 计算最新的技术指标
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        analysis = {
            'symbol': symbol,
            'trend': trend,
            'close': latest['Close'],
            'volume': latest['Volume'],
            'volume_ma20': latest['Volume_MA20'],
            'atr': latest['ATR'],
            'macd_hist': latest['MACD_Hist'],
            'price_change': latest['Price_Change'],
            'volume_change': latest['Volume_Change'],
            'ema21': latest['EMA21']
        }

        # 生成交易建议
        recommendation = self.generate_recommendation(analysis)
        analysis['recommendation'] = recommendation

        return analysis

    def generate_recommendation(self, analysis):
        """生成交易建议"""
        try:
            if analysis['trend'] == 'uptrend':
                # 安全地获取volume和volume_ma20值
                volume = analysis.get('volume', 0)
                volume_ma20 = analysis.get('volume_ma20', 1)  # 默认值设为1以避免除零错误
                
                if volume > 0 and volume_ma20 > 0 and volume > volume_ma20 * 1.5:
                    if analysis.get('macd_hist', 0) > 0:
                        return '强烈推荐买入'
                    else:
                        return '建议买入'
                else:
                    return '观望'
            elif analysis['trend'] == 'downtrend':
                return '建议卖出'
            else:
                return '观望'
        except Exception as e:
            print(f"生成交易建议时发生错误：{str(e)}")
            return '观望'

    def scan_stocks(self, symbols):
        """扫描多个股票并生成推荐列表"""
        recommendations = []
        for symbol in tqdm(symbols, desc="分析股票中"):
            analysis = self.analyze_stock(symbol)
            if analysis:
                recommendations.append(analysis)

        # 按照趋势强度排序
        recommendations.sort(key=lambda x: (
            1 if x['trend'] == 'uptrend' else 0,
            abs(x['macd_hist']),
            x['volume'] / x['volume_ma20']
        ), reverse=True)

        return recommendations

    def print_recommendations(self, recommendations):
        """打印股票推荐结果"""
        print("\n=== 股票推荐报告 ===")
        print(f"生成时间: {datetime.now(self.china_tz).strftime('%Y-%m-%d %H:%M:%S')}\n")

        for rec in recommendations:
            print(f"股票代码: {rec['symbol']}")
            print(f"当前趋势: {rec['trend']}")
            print(f"收盘价: {rec['close']:.2f}")
            print(f"成交量/20日均量: {rec['volume']/rec['volume_ma20']:.2f}")
            print(f"ATR: {rec['atr']:.2f}")
            print(f"建议: {rec['recommendation']}")
            print("-" * 50)

def main():
    # 创建推荐系统实例
    recommender = StockRecommender()
    
    # 交互式分析
    while True:
        symbol = input('请输入股票代码（按q退出）: ')
        if symbol.lower() == 'q':
            break
            
        # 分析股票并生成推荐
        analysis = recommender.analyze_stock(symbol)
        if analysis:
            # 打印推荐结果
            recommender.print_recommendations([analysis])

if __name__ == '__main__':
    main()