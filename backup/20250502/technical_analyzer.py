import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timedelta
import os
import sys
from simple_stock_provider import SimpleStockProvider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TechnicalAnalyzer')

class TechnicalAnalyzer:
    """
    A comprehensive technical analysis tool for stock data
    """
    
    def __init__(self, token=None):
        """
        Initialize the analyzer with a data provider
        
        Args:
            token: Tushare API token
        """
        self.token = token or os.environ.get('TUSHARE_TOKEN')
        if not self.token:
            logger.error("No Tushare token provided")
            sys.exit(1)
            
        # Initialize data provider
        self.provider = SimpleStockProvider(token=self.token)
        
        # Define signal thresholds
        self.thresholds = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'kdj_oversold': 20,
            'kdj_overbought': 80,
            'macd_signal': 0
        }
    
    def get_data(self, symbol, days=90):
        """
        Get stock data for the specified symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days of data to retrieve
            
        Returns:
            DataFrame with stock data
        """
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        data = self.provider.get_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            logger.error(f"No data retrieved for {symbol}")
            return None
            
        # Ensure data is sorted by date
        data = data.sort_values('trade_date')
        
        # Convert date to datetime for plotting
        data['date'] = pd.to_datetime(data['trade_date'])
        data.set_index('date', inplace=True)
        
        return data
    
    def get_stock_info(self, symbol):
        """Get basic information about the stock"""
        return self.provider.get_stock_info(symbol)
    
    def analyze_trends(self, data):
        """
        Analyze price trends
        
        Args:
            data: DataFrame with stock data
            
        Returns:
            Dictionary of trend analysis results
        """
        if data is None or data.empty:
            return {}
            
        # Get latest data point
        latest = data.iloc[-1]
        
        # Calculate short-term and long-term trends
        short_ma = data['close'].rolling(window=5).mean().iloc[-1]
        medium_ma = data['close'].rolling(window=20).mean().iloc[-1]
        long_ma = data['close'].rolling(window=60).mean().iloc[-1]
        
        current_price = latest['close']
        
        # Calculate trends
        short_trend = "Up" if current_price > short_ma else "Down"
        medium_trend = "Up" if current_price > medium_ma else "Down"
        long_trend = "Up" if current_price > long_ma else "Down"
        
        # Calculate price momentum
        price_change_5d = (current_price / data['close'].iloc[-6]) - 1 if len(data) > 5 else 0
        price_change_20d = (current_price / data['close'].iloc[-21]) - 1 if len(data) > 20 else 0
        
        # Determine overall trend
        if short_trend == "Up" and medium_trend == "Up" and long_trend == "Up":
            overall_trend = "Strong Up"
        elif short_trend == "Down" and medium_trend == "Down" and long_trend == "Down":
            overall_trend = "Strong Down"
        elif short_trend == "Up" and medium_trend == "Up":
            overall_trend = "Moderate Up"
        elif short_trend == "Down" and medium_trend == "Down":
            overall_trend = "Moderate Down"
        elif short_trend == "Up":
            overall_trend = "Weak Up"
        else:
            overall_trend = "Weak Down"
        
        return {
            "current_price": current_price,
            "short_ma": short_ma,
            "medium_ma": medium_ma,
            "long_ma": long_ma,
            "short_trend": short_trend,
            "medium_trend": medium_trend,
            "long_trend": long_trend,
            "overall_trend": overall_trend,
            "price_change_5d": price_change_5d,
            "price_change_20d": price_change_20d
        }
    
    def analyze_indicators(self, data):
        """
        Analyze technical indicators
        
        Args:
            data: DataFrame with stock data
            
        Returns:
            Dictionary of indicator analysis results
        """
        if data is None or data.empty:
            return {}
            
        # Get latest data point
        latest = data.iloc[-1]
        
        # Check if we have indicators from stk_factor
        if 'macd' in data.columns and 'rsi_6' in data.columns:
            # MACD analysis
            macd = latest['macd']
            macd_dif = latest['macd_dif']
            macd_dea = latest['macd_dea']
            
            if macd > 0 and macd_dif > macd_dea:
                macd_signal = "Buy"
            elif macd < 0 and macd_dif < macd_dea:
                macd_signal = "Sell"
            else:
                macd_signal = "Neutral"
                
            # RSI analysis
            rsi_6 = latest['rsi_6']
            rsi_12 = latest['rsi_12']
            rsi_24 = latest['rsi_24']
            
            if rsi_6 < self.thresholds['rsi_oversold']:
                rsi_signal = "Oversold (Buy)"
            elif rsi_6 > self.thresholds['rsi_overbought']:
                rsi_signal = "Overbought (Sell)"
            else:
                rsi_signal = "Neutral"
                
            # KDJ analysis
            kdj_k = latest['kdj_k']
            kdj_d = latest['kdj_d']
            kdj_j = latest['kdj_j']
            
            if kdj_j < self.thresholds['kdj_oversold']:
                kdj_signal = "Oversold (Buy)"
            elif kdj_j > self.thresholds['kdj_overbought']:
                kdj_signal = "Overbought (Sell)"
            else:
                kdj_signal = "Neutral"
                
            # Bollinger Bands
            boll_upper = latest['boll_upper']
            boll_mid = latest['boll_mid']
            boll_lower = latest['boll_lower']
            current_price = latest['close']
            
            bb_width = (boll_upper - boll_lower) / boll_mid * 100
            bb_position = (current_price - boll_lower) / (boll_upper - boll_lower) * 100
            
            if current_price < boll_lower:
                boll_signal = "Oversold (Buy)"
            elif current_price > boll_upper:
                boll_signal = "Overbought (Sell)"
            else:
                boll_signal = "Neutral"
                
            return {
                "macd": macd,
                "macd_dif": macd_dif,
                "macd_dea": macd_dea,
                "macd_signal": macd_signal,
                "rsi_6": rsi_6,
                "rsi_12": rsi_12,
                "rsi_24": rsi_24,
                "rsi_signal": rsi_signal,
                "kdj_k": kdj_k,
                "kdj_d": kdj_d,
                "kdj_j": kdj_j,
                "kdj_signal": kdj_signal,
                "boll_upper": boll_upper,
                "boll_mid": boll_mid,
                "boll_lower": boll_lower,
                "boll_width": bb_width,
                "boll_position": bb_position,
                "boll_signal": boll_signal
            }
        else:
            logger.warning("No technical indicators available in data")
            return {}
    
    def generate_trading_signal(self, trend_analysis, indicator_analysis):
        """
        Generate a comprehensive trading signal
        
        Args:
            trend_analysis: Results from trend analysis
            indicator_analysis: Results from indicator analysis
            
        Returns:
            Trading signal and confidence level
        """
        if not trend_analysis or not indicator_analysis:
            return {"signal": "Neutral", "confidence": 0, "reasons": ["Insufficient data"]}
            
        # Count bullish and bearish signals
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        reasons = []
        
        # Trend signals
        if trend_analysis['overall_trend'] in ["Strong Up", "Moderate Up"]:
            bullish_count += 1
            reasons.append(f"Price trend is {trend_analysis['overall_trend']}")
        elif trend_analysis['overall_trend'] in ["Strong Down", "Moderate Down"]:
            bearish_count += 1
            reasons.append(f"Price trend is {trend_analysis['overall_trend']}")
        else:
            neutral_count += 1
        
        # MACD signal
        if indicator_analysis.get('macd_signal') == "Buy":
            bullish_count += 1
            reasons.append("MACD indicates buying opportunity")
        elif indicator_analysis.get('macd_signal') == "Sell":
            bearish_count += 1
            reasons.append("MACD indicates selling opportunity")
        else:
            neutral_count += 1
            
        # RSI signal
        if indicator_analysis.get('rsi_signal') == "Oversold (Buy)":
            bullish_count += 1
            reasons.append(f"RSI is oversold at {indicator_analysis.get('rsi_6', 0):.2f}")
        elif indicator_analysis.get('rsi_signal') == "Overbought (Sell)":
            bearish_count += 1
            reasons.append(f"RSI is overbought at {indicator_analysis.get('rsi_6', 0):.2f}")
        else:
            neutral_count += 1
            
        # KDJ signal
        if indicator_analysis.get('kdj_signal') == "Oversold (Buy)":
            bullish_count += 1
            reasons.append(f"KDJ is oversold with J at {indicator_analysis.get('kdj_j', 0):.2f}")
        elif indicator_analysis.get('kdj_signal') == "Overbought (Sell)":
            bearish_count += 1
            reasons.append(f"KDJ is overbought with J at {indicator_analysis.get('kdj_j', 0):.2f}")
        else:
            neutral_count += 1
            
        # Bollinger Bands signal
        if indicator_analysis.get('boll_signal') == "Oversold (Buy)":
            bullish_count += 1
            reasons.append("Price is below the lower Bollinger Band")
        elif indicator_analysis.get('boll_signal') == "Overbought (Sell)":
            bearish_count += 1
            reasons.append("Price is above the upper Bollinger Band")
        else:
            neutral_count += 1
            
        # Determine signal and confidence
        total_signals = bullish_count + bearish_count + neutral_count
        
        if bullish_count > bearish_count:
            signal = "Buy"
            confidence = bullish_count / total_signals * 100
        elif bearish_count > bullish_count:
            signal = "Sell"
            confidence = bearish_count / total_signals * 100
        else:
            signal = "Neutral"
            confidence = neutral_count / total_signals * 100
            
        return {
            "signal": signal,
            "confidence": confidence,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "reasons": reasons
        }
    
    def plot_data(self, data, symbol, output_file=None):
        """
        Create a comprehensive plot of price and indicators
        
        Args:
            data: DataFrame with stock data
            symbol: Stock symbol
            output_file: Path to save the plot (if None, display only)
            
        Returns:
            True if successful, False otherwise
        """
        if data is None or data.empty:
            logger.error("No data to plot")
            return False
            
        # Get stock info for title
        stock_info = self.get_stock_info(symbol)
        if not stock_info.empty:
            stock_name = stock_info.iloc[0]['name']
            title = f"{symbol} - {stock_name}"
        else:
            title = symbol
            
        # Create OHLC dataframe for mplfinance
        ohlc = data[['open', 'high', 'low', 'close']].copy()
        if 'vol' in data.columns:
            ohlc['volume'] = data['vol']
        elif 'volume' in data.columns:
            ohlc['volume'] = data['volume']
            
        # Create the figure and subplots
        fig, axes = plt.subplots(4, 1, figsize=(12, 16), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        # Plot candlestick chart
        mpf.plot(ohlc, type='candle', style='yahoo', ax=axes[0])
        axes[0].set_title(title)
        axes[0].grid(True)
        
        # Add moving averages to price chart
        ma5 = data['close'].rolling(window=5).mean()
        ma20 = data['close'].rolling(window=20).mean()
        ma60 = data['close'].rolling(window=60).mean()
        
        axes[0].plot(data.index, ma5, label='MA5', color='blue', linewidth=1)
        axes[0].plot(data.index, ma20, label='MA20', color='orange', linewidth=1)
        axes[0].plot(data.index, ma60, label='MA60', color='purple', linewidth=1)
        axes[0].legend()
        
        # Add Bollinger Bands if available
        if 'boll_upper' in data.columns:
            axes[0].plot(data.index, data['boll_upper'], label='Upper BB', color='red', linestyle='--', linewidth=1)
            axes[0].plot(data.index, data['boll_mid'], label='Middle BB', color='green', linestyle='--', linewidth=1)
            axes[0].plot(data.index, data['boll_lower'], label='Lower BB', color='red', linestyle='--', linewidth=1)
            
        # Add MACD to subplot
        if 'macd' in data.columns:
            axes[1].plot(data.index, data['macd_dif'], label='DIF', color='blue')
            axes[1].plot(data.index, data['macd_dea'], label='DEA', color='orange')
            axes[1].bar(data.index, data['macd'], label='MACD', color='green')
            axes[1].set_title('MACD')
            axes[1].grid(True)
            axes[1].legend()
            
            # Add a horizontal line at y=0
            axes[1].axhline(y=0, color='r', linestyle='-', alpha=0.3)
        
        # Add RSI to subplot
        if 'rsi_6' in data.columns:
            axes[2].plot(data.index, data['rsi_6'], label='RSI(6)', color='red')
            axes[2].plot(data.index, data['rsi_12'], label='RSI(12)', color='blue')
            axes[2].plot(data.index, data['rsi_24'], label='RSI(24)', color='purple')
            axes[2].axhline(y=70, color='r', linestyle='--', alpha=0.3)
            axes[2].axhline(y=30, color='g', linestyle='--', alpha=0.3)
            axes[2].set_title('RSI')
            axes[2].set_ylim(0, 100)
            axes[2].grid(True)
            axes[2].legend()
        
        # Add KDJ to subplot
        if 'kdj_k' in data.columns:
            axes[3].plot(data.index, data['kdj_k'], label='K', color='blue')
            axes[3].plot(data.index, data['kdj_d'], label='D', color='orange')
            axes[3].plot(data.index, data['kdj_j'], label='J', color='green')
            axes[3].axhline(y=80, color='r', linestyle='--', alpha=0.3)
            axes[3].axhline(y=20, color='g', linestyle='--', alpha=0.3)
            axes[3].set_title('KDJ')
            axes[3].grid(True)
            axes[3].legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or display
        if output_file:
            plt.savefig(output_file)
            logger.info(f"Plot saved to {output_file}")
        else:
            plt.show()
            
        plt.close()
        return True
    
    def generate_report(self, symbol, days=90):
        """
        Generate a comprehensive analysis report
        
        Args:
            symbol: Stock symbol
            days: Number of days of data to analyze
            
        Returns:
            Analysis report as a string
        """
        # Get the data
        data = self.get_data(symbol, days)
        if data is None:
            return "Could not retrieve data for analysis"
            
        # Get stock info
        stock_info = self.get_stock_info(symbol)
        stock_name = stock_info.iloc[0]['name'] if not stock_info.empty else "Unknown"
        
        # Perform analysis
        trend_analysis = self.analyze_trends(data)
        indicator_analysis = self.analyze_indicators(data)
        trading_signal = self.generate_trading_signal(trend_analysis, indicator_analysis)
        
        # Create report
        report = []
        report.append(f"Technical Analysis Report for {symbol} - {stock_name}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"Analysis Period: {days} days")
        report.append("\n")
        
        # Add price information
        if trend_analysis:
            report.append("PRICE INFORMATION")
            report.append(f"Current Price: {trend_analysis['current_price']:.2f}")
            report.append(f"5-Day MA: {trend_analysis['short_ma']:.2f}")
            report.append(f"20-Day MA: {trend_analysis['medium_ma']:.2f}")
            report.append(f"60-Day MA: {trend_analysis['long_ma']:.2f}")
            report.append(f"5-Day Change: {trend_analysis['price_change_5d']*100:.2f}%")
            report.append(f"20-Day Change: {trend_analysis['price_change_20d']*100:.2f}%")
            report.append(f"Overall Trend: {trend_analysis['overall_trend']}")
            report.append("\n")
        
        # Add technical indicators
        if indicator_analysis:
            report.append("TECHNICAL INDICATORS")
            
            report.append("MACD Analysis:")
            report.append(f"MACD: {indicator_analysis['macd']:.3f}")
            report.append(f"MACD Signal (DIF): {indicator_analysis['macd_dif']:.3f}")
            report.append(f"MACD History (DEA): {indicator_analysis['macd_dea']:.3f}")
            report.append(f"MACD Signal: {indicator_analysis['macd_signal']}")
            report.append("")
            
            report.append("RSI Analysis:")
            report.append(f"RSI(6): {indicator_analysis['rsi_6']:.2f}")
            report.append(f"RSI(12): {indicator_analysis['rsi_12']:.2f}")
            report.append(f"RSI(24): {indicator_analysis['rsi_24']:.2f}")
            report.append(f"RSI Signal: {indicator_analysis['rsi_signal']}")
            report.append("")
            
            report.append("KDJ Analysis:")
            report.append(f"K: {indicator_analysis['kdj_k']:.2f}")
            report.append(f"D: {indicator_analysis['kdj_d']:.2f}")
            report.append(f"J: {indicator_analysis['kdj_j']:.2f}")
            report.append(f"KDJ Signal: {indicator_analysis['kdj_signal']}")
            report.append("")
            
            report.append("Bollinger Bands:")
            report.append(f"Upper Band: {indicator_analysis['boll_upper']:.2f}")
            report.append(f"Middle Band: {indicator_analysis['boll_mid']:.2f}")
            report.append(f"Lower Band: {indicator_analysis['boll_lower']:.2f}")
            report.append(f"Band Width: {indicator_analysis['boll_width']:.2f}%")
            report.append(f"Price Position: {indicator_analysis['boll_position']:.2f}%")
            report.append(f"Bollinger Signal: {indicator_analysis['boll_signal']}")
            report.append("\n")
        
        # Add trading signal
        if trading_signal:
            report.append("TRADING SIGNAL")
            report.append(f"Signal: {trading_signal['signal']}")
            report.append(f"Confidence: {trading_signal['confidence']:.2f}%")
            report.append(f"Bullish Signals: {trading_signal['bullish_count']}")
            report.append(f"Bearish Signals: {trading_signal['bearish_count']}")
            report.append(f"Neutral Signals: {trading_signal['neutral_count']}")
            report.append("\nReasons:")
            for reason in trading_signal['reasons']:
                report.append(f"- {reason}")
            report.append("\n")
        
        # Add trading advice
        report.append("TRADING ADVICE")
        if trading_signal['signal'] == "Buy" and trading_signal['confidence'] > 60:
            advice = "Strong buy recommendation based on technical indicators."
        elif trading_signal['signal'] == "Buy":
            advice = "Consider buying, but monitor closely for confirmation."
        elif trading_signal['signal'] == "Sell" and trading_signal['confidence'] > 60:
            advice = "Strong sell recommendation based on technical indicators."
        elif trading_signal['signal'] == "Sell":
            advice = "Consider selling or reducing position, but monitor closely."
        else:
            advice = "Hold current position or stay neutral. Wait for clearer signals."
        
        report.append(advice)
        report.append("\n")
        
        # Add disclaimer
        report.append("DISCLAIMER")
        report.append("This analysis is based solely on technical indicators and historical price data.")
        report.append("It does not consider fundamental factors, news, or market conditions.")
        report.append("Always conduct your own research before making investment decisions.")
        
        # Generate visualization
        output_file = f"{symbol}_analysis.png"
        self.plot_data(data, symbol, output_file)
        report.append(f"\nA visualization has been saved to {output_file}")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Technical Stock Analyzer')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--symbol', type=str, default='000001.SZ', help='Stock symbol to analyze')
    parser.add_argument('--days', type=int, default=90, help='Number of days to analyze')
    parser.add_argument('--output', type=str, help='Output file for the report')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = TechnicalAnalyzer(token=args.token)
    
    # Generate report
    report = analyzer.generate_report(args.symbol, args.days)
    
    # Save or display report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main() 