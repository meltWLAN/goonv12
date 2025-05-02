#!/usr/bin/env python3
"""
简单股票信息终端显示程序
无需GUI界面，直接在终端中显示股票信息
"""

import os
import sys
import pandas as pd
from enhanced_data_provider import EnhancedDataProvider
import argparse
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description='显示股票基本信息和技术指标')
    parser.add_argument('--token', type=str, default=os.environ.get('TUSHARE_TOKEN', '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'),
                        help='Tushare API token')
    parser.add_argument('--code', type=str, default='000001.SZ',
                        help='股票代码 (默认: 000001.SZ)')
    parser.add_argument('--days', type=int, default=30,
                        help='查询天数 (默认: 30天)')
    
    args = parser.parse_args()
    
    # 设置日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y%m%d')
    
    try:
        print(f"\n{'='*60}")
        print(f"正在初始化数据提供者...")
        provider = EnhancedDataProvider(token=args.token)
        
        print(f"\n获取股票 {args.code} 的日线数据 ({start_date} 至 {end_date})...")
        daily_data = provider.get_stock_daily(args.code, start_date=start_date, end_date=end_date)
        
        if not daily_data.empty:
            # 尝试获取股票名称
            try:
                stock_name = provider.get_stock_name(args.code)
                print(f"\n股票名称: {stock_name}")
            except:
                print(f"\n股票代码: {args.code}")
            
            # 显示最近的5天数据
            print(f"\n最近5天交易数据:")
            print(daily_data.head(5)[['trade_date', 'open', 'high', 'low', 'close', 'pct_chg', 'vol']].to_string(index=False))
            
            # 计算简单技术指标
            latest = daily_data.iloc[0]
            print(f"\n最新技术指标 ({latest['trade_date']}):")
            
            # 计算MA5, MA10, MA20
            ma_columns = []
            for window in [5, 10, 20]:
                col_name = f'ma{window}'
                if col_name in daily_data.columns:
                    ma_columns.append((col_name, daily_data[col_name].iloc[0]))
                else:
                    daily_data[col_name] = daily_data['close'].rolling(window=window).mean()
                    ma_columns.append((col_name, daily_data[col_name].iloc[0]))
            
            print("\nMA均线指标:")
            for ma_name, ma_value in ma_columns:
                signal = "中性"
                if ma_name == 'ma5':
                    if ma_value > daily_data['ma10'].iloc[0]:
                        signal = "偏多"
                    else:
                        signal = "偏空"
                print(f"- {ma_name.upper()}: {ma_value:.2f} ({signal})")
            
            # 显示趋势判断
            latest_close = latest['close']
            ma5 = daily_data['ma5'].iloc[0]
            ma10 = daily_data['ma10'].iloc[0]
            ma20 = daily_data['ma20'].iloc[0]
            
            if latest_close > ma5 > ma10 > ma20:
                trend = "强势上涨"
            elif latest_close > ma5 and latest_close > ma10 and latest_close < ma20:
                trend = "上涨受阻"
            elif latest_close < ma5 and latest_close < ma10 and latest_close > ma20:
                trend = "下跌趋缓"
            elif latest_close < ma5 < ma10 < ma20:
                trend = "强势下跌"
            else:
                trend = "震荡整理"
            
            print(f"\n综合趋势判断: {trend}")
            
            # 显示建议
            if trend in ["强势上涨"]:
                advice = "可以考虑买入"
            elif trend in ["上涨受阻", "震荡整理"]:
                advice = "观望为主"
            else:
                advice = "建议暂时回避"
            
            print(f"操作建议: {advice}")
        
        # 获取市场概览
        try:
            print(f"\n获取市场概览...")
            provider.get_all_index_daily()  # 预先加载指数数据
            
            # 获取上证指数
            sh_index = provider.get_stock_daily('000001.SH', start_date=datetime.now().strftime('%Y%m%d'))
            if not sh_index.empty:
                sh_price = sh_index.iloc[0]['close']
                sh_change = sh_index.iloc[0]['pct_chg']
                print(f"上证指数: {sh_price:.2f} ({sh_change:+.2f}%)")
            
            # 获取深证成指
            sz_index = provider.get_stock_daily('399001.SZ', start_date=datetime.now().strftime('%Y%m%d'))
            if not sz_index.empty:
                sz_price = sz_index.iloc[0]['close']
                sz_change = sz_index.iloc[0]['pct_chg']
                print(f"深证成指: {sz_price:.2f} ({sz_change:+.2f}%)")
            
            # 获取创业板指
            cyb_index = provider.get_stock_daily('399006.SZ', start_date=datetime.now().strftime('%Y%m%d'))
            if not cyb_index.empty:
                cyb_price = cyb_index.iloc[0]['close']
                cyb_change = cyb_index.iloc[0]['pct_chg']
                print(f"创业板指: {cyb_price:.2f} ({cyb_change:+.2f}%)")
        except Exception as e:
            print(f"获取市场概览失败: {str(e)}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 