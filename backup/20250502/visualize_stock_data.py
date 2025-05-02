import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import argparse
import sys
import os
from datetime import datetime, timedelta


# Fix Chinese font display
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def format_date(date_str):
    """Convert date from YYYYMMDD to YYYY-MM-DD format"""
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Visualize Stock Data with Technical Indicators')
    parser.add_argument('--token', type=str, required=True, help='Tushare API token')
    parser.add_argument('--ts_code', type=str, default='000001.SZ', help='Stock code (default: 000001.SZ)')
    parser.add_argument('--days', type=int, default=60, help='Number of days to analyze (default: 60)')
    parser.add_argument('--output', type=str, help='Output file for the chart (default: None, displays on screen)')
    
    args = parser.parse_args()
    
    try:
        # Calculate dates
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y%m%d')
        
        # Set up the Tushare API connection
        ts.set_token(args.token)
        pro = ts.pro_api()
        print(f"API connection initialized with token: {args.token[:4]}{'*' * (len(args.token) - 8)}{args.token[-4:]}")
        
        # Retrieve basic stock info
        stock_info = pro.stock_basic(ts_code=args.ts_code, fields='name,industry,market,list_date')
        if not stock_info.empty:
            stock_name = stock_info.iloc[0]['name']
            industry = stock_info.iloc[0]['industry']
            print(f"\nAnalyzing: {args.ts_code} - {stock_name} ({industry})")
        
        # Retrieve technical indicator data
        print(f"Retrieving stk_factor data from {start_date} to {end_date}...")
        df = pro.stk_factor(ts_code=args.ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            print("No data returned. This could mean no data exists for the specified parameters.")
            return 1
        
        # Process data for plotting
        df = df.sort_values('trade_date')
        df['trade_date'] = df['trade_date'].apply(format_date)
        df.set_index(pd.DatetimeIndex(df['trade_date']), inplace=True)
        
        # Create OHLC dataframe for mplfinance
        ohlc = df[['open', 'high', 'low', 'close', 'vol']].copy()
        ohlc.rename(columns={'vol': 'volume'}, inplace=True)
        
        # Create subplots
        fig, axes = plt.subplots(4, 1, figsize=(12, 16), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        # Plot candlestick chart
        mpf.plot(ohlc, type='candle', style='yahoo', ax=axes[0])
        axes[0].set_title(f"{args.ts_code} - {stock_name if 'stock_name' in locals() else ''} Price Chart")
        axes[0].grid(True)
        
        # Add MACD to subplot
        axes[1].plot(df.index, df['macd_dif'], label='DIF', color='blue')
        axes[1].plot(df.index, df['macd_dea'], label='DEA', color='orange')
        axes[1].bar(df.index, df['macd'], label='MACD', color='green')
        axes[1].set_title('MACD')
        axes[1].grid(True)
        axes[1].legend()
        
        # Add RSI to subplot
        axes[2].plot(df.index, df['rsi_6'], label='RSI(6)', color='red')
        axes[2].plot(df.index, df['rsi_12'], label='RSI(12)', color='blue')
        axes[2].plot(df.index, df['rsi_24'], label='RSI(24)', color='purple')
        axes[2].axhline(y=70, color='r', linestyle='--', alpha=0.3)
        axes[2].axhline(y=30, color='g', linestyle='--', alpha=0.3)
        axes[2].set_title('RSI')
        axes[2].set_ylim(0, 100)
        axes[2].grid(True)
        axes[2].legend()
        
        # Add KDJ to subplot
        axes[3].plot(df.index, df['kdj_k'], label='K', color='blue')
        axes[3].plot(df.index, df['kdj_d'], label='D', color='orange')
        axes[3].plot(df.index, df['kdj_j'], label='J', color='green')
        axes[3].axhline(y=80, color='r', linestyle='--', alpha=0.3)
        axes[3].axhline(y=20, color='g', linestyle='--', alpha=0.3)
        axes[3].set_title('KDJ')
        axes[3].grid(True)
        axes[3].legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or display
        if args.output:
            output_path = args.output
            if not output_path.endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                output_path += '.png'
            plt.savefig(output_path)
            print(f"Chart saved to {output_path}")
        else:
            plt.show()
            
        # Print summary of technical indicators
        latest = df.iloc[-1]
        print("\nLatest Technical Indicators:")
        print(f"Date: {latest.name.strftime('%Y-%m-%d')}")
        print(f"Close: {latest['close']}")
        
        # MACD Analysis
        macd_signal = "Buy" if latest['macd'] > 0 and latest['macd_dif'] > latest['macd_dea'] else "Sell" if latest['macd'] < 0 and latest['macd_dif'] < latest['macd_dea'] else "Neutral"
        print(f"MACD: DIF={latest['macd_dif']:.3f}, DEA={latest['macd_dea']:.3f}, MACD={latest['macd']:.3f} ({macd_signal})")
        
        # RSI Analysis
        rsi_signal = "Oversold (Buy)" if latest['rsi_6'] < 30 else "Overbought (Sell)" if latest['rsi_6'] > 70 else "Neutral"
        print(f"RSI: 6={latest['rsi_6']:.2f}, 12={latest['rsi_12']:.2f}, 24={latest['rsi_24']:.2f} ({rsi_signal})")
        
        # KDJ Analysis
        kdj_signal = "Oversold (Buy)" if latest['kdj_j'] < 20 else "Overbought (Sell)" if latest['kdj_j'] > 80 else "Neutral"
        print(f"KDJ: K={latest['kdj_k']:.2f}, D={latest['kdj_d']:.2f}, J={latest['kdj_j']:.2f} ({kdj_signal})")
        
        # Bollinger Bands
        bb_width = (latest['boll_upper'] - latest['boll_lower']) / latest['boll_mid'] * 100
        bb_position = (latest['close'] - latest['boll_lower']) / (latest['boll_upper'] - latest['boll_lower']) * 100
        bb_signal = "Oversold (Buy)" if latest['close'] < latest['boll_lower'] else "Overbought (Sell)" if latest['close'] > latest['boll_upper'] else "Neutral"
        print(f"Bollinger Bands: Upper={latest['boll_upper']:.2f}, Mid={latest['boll_mid']:.2f}, Lower={latest['boll_lower']:.2f}")
        print(f"BB Width: {bb_width:.2f}%, Position: {bb_position:.2f}% ({bb_signal})")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 