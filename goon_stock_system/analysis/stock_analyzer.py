#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import time
from collections import defaultdict

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from utils.tushare_api import (
    get_stock_basics, get_daily_data, get_limit_list,
    get_daily_basic, get_today_all, get_trade_calendar,
    get_minute_data, get_pro_bar_data, get_weekly_data, 
    get_monthly_data, get_stock_limit, get_index_daily,
    get_suspend_data, get_hsgt_top10, get_ggt_top10,
    get_ggt_daily, get_income, get_balancesheet, get_cashflow, 
    get_hs_const, get_stock_company, get_forecast, get_express,
    get_dividend, get_fina_indicator, get_disclosure_date,
    get_concept, get_concept_detail, get_share_float,
    get_stk_holdernumber, get_stk_holdertrade, get_report_rc,
    get_cyq_perf, get_cyq_chips
)
from config import SURGE_THRESHOLD, DEFAULT_START_DATE, DEFAULT_END_DATE

class StockAnalyzer:
    """股票分析器，用于发现暴涨股票"""
    
    def __init__(self):
        """初始化分析器"""
        self.stock_basics = None
        self.update_stock_basics()
        
    def update_stock_basics(self):
        """更新股票基本信息"""
        self.stock_basics = get_stock_basics()
        print(f"已更新{len(self.stock_basics)}只股票的基本信息")
        
    def find_surge_stocks(self, trade_date=None, threshold=SURGE_THRESHOLD):
        """查找某天涨幅超过阈值的股票
        
        Args:
            trade_date (str, optional): 交易日期，格式YYYYMMDD，默认为最近一个交易日
            threshold (float, optional): 涨幅阈值，默认为配置中的SURGE_THRESHOLD
            
        Returns:
            pd.DataFrame: 涨幅超过阈值的股票信息
        """
        # 如果未指定日期，使用最近一个交易日
        if trade_date is None:
            today = datetime.datetime.now().strftime('%Y%m%d')
            calendar = get_trade_calendar(
                (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d'),
                today
            )
            if calendar:
                trade_date = calendar[-1]
            else:
                trade_date = today
                
        # 获取当日所有股票行情
        daily_data = get_today_all() if trade_date == datetime.datetime.now().strftime('%Y%m%d') else None
        
        # 如果未能获取到当日数据，尝试通过pro.daily获取
        if daily_data is None or daily_data.empty:
            daily_data = pd.DataFrame()
            # 分批获取股票数据，避免超出接口限制
            if self.stock_basics is not None and not self.stock_basics.empty:
                for i in range(0, len(self.stock_basics), 100):
                    batch = self.stock_basics.iloc[i:i+100]
                    for _, stock in batch.iterrows():
                        ts_code = stock['ts_code']
                        df = get_daily_data(ts_code, trade_date, trade_date)
                        if not df.empty:
                            daily_data = pd.concat([daily_data, df])
        
        if daily_data.empty:
            print(f"未能获取到{trade_date}的股票数据")
            return pd.DataFrame()
            
        # 筛选涨幅超过阈值的股票
        surge_stocks = daily_data[daily_data['pct_chg'] > threshold].copy()
        
        # 如果有股票基本信息，添加股票名称和行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            surge_stocks = pd.merge(
                surge_stocks, 
                self.stock_basics[['ts_code', 'name', 'industry']], 
                on='ts_code', 
                how='left'
            )
            
        # 按涨幅排序
        surge_stocks = surge_stocks.sort_values(by='pct_chg', ascending=False)
        
        return surge_stocks
        
    def analyze_surge_patterns(self, start_date=DEFAULT_START_DATE, end_date=DEFAULT_END_DATE, 
                              threshold=SURGE_THRESHOLD):
        """分析时间段内暴涨股票的模式
        
        Args:
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            threshold (float): 涨幅阈值
            
        Returns:
            dict: 分析结果
        """
        # 获取交易日历
        trade_dates = get_trade_calendar(start_date, end_date)
        
        if not trade_dates:
            print("无法获取交易日历")
            return {}
            
        # 各行业暴涨股票统计
        industry_stats = {}
        # 每日暴涨股票数量
        daily_surge_counts = {}
        # 暴涨后第二天表现
        next_day_performance = []
        
        for i, date in enumerate(trade_dates):
            print(f"分析{date}的股票数据 ({i+1}/{len(trade_dates)})")
            surge_stocks = self.find_surge_stocks(date, threshold)
            
            if surge_stocks.empty:
                daily_surge_counts[date] = 0
                continue
                
            daily_surge_counts[date] = len(surge_stocks)
            
            # 统计行业分布
            if 'industry' in surge_stocks.columns:
                for industry in surge_stocks['industry'].dropna().unique():
                    if industry not in industry_stats:
                        industry_stats[industry] = 0
                    industry_stats[industry] += len(surge_stocks[surge_stocks['industry'] == industry])
            
            # 分析暴涨后第二天表现
            if i < len(trade_dates) - 1:
                next_date = trade_dates[i + 1]
                for _, stock in surge_stocks.iterrows():
                    ts_code = stock['ts_code']
                    next_day_data = get_daily_data(ts_code, next_date, next_date)
                    
                    if not next_day_data.empty:
                        next_day_performance.append({
                            'ts_code': ts_code,
                            'name': stock.get('name', ''),
                            'surge_date': date,
                            'surge_pct': stock['pct_chg'],
                            'next_date': next_date,
                            'next_pct': next_day_data.iloc[0]['pct_chg'] if not next_day_data.empty else None
                        })
        
        # 计算暴涨后第二天平均涨幅
        next_day_df = pd.DataFrame(next_day_performance)
        if not next_day_df.empty:
            avg_next_day_pct = next_day_df['next_pct'].mean()
            positive_ratio = (next_day_df['next_pct'] > 0).mean() * 100
        else:
            avg_next_day_pct = None
            positive_ratio = None
            
        # 行业排名
        industry_rank = pd.Series(industry_stats).sort_values(ascending=False)
        
        return {
            'total_days': len(trade_dates),
            'total_surge_stocks': sum(daily_surge_counts.values()),
            'avg_surge_stocks_per_day': sum(daily_surge_counts.values()) / len(trade_dates) if trade_dates else 0,
            'max_surge_day': max(daily_surge_counts.items(), key=lambda x: x[1]) if daily_surge_counts else None,
            'industry_rank': industry_rank,
            'avg_next_day_pct': avg_next_day_pct,
            'positive_ratio_next_day': positive_ratio,
            'daily_surge_counts': daily_surge_counts,
            'next_day_performance': next_day_df
        }
        
    def plot_surge_stats(self, analysis_result):
        """绘制暴涨股票统计图表
        
        Args:
            analysis_result (dict): 分析结果
        """
        if not analysis_result:
            print("分析结果为空，无法绘制图表")
            return
            
        # 创建图表
        plt.figure(figsize=(15, 10))
        
        # 每日暴涨股票数量
        plt.subplot(2, 2, 1)
        daily_counts = analysis_result.get('daily_surge_counts', {})
        if daily_counts:
            dates = list(daily_counts.keys())
            counts = list(daily_counts.values())
            plt.bar(range(len(dates)), counts)
            plt.xticks(range(0, len(dates), max(1, len(dates)//10)), 
                      [dates[i] for i in range(0, len(dates), max(1, len(dates)//10))], 
                      rotation=45)
            plt.title('每日暴涨股票数量')
            plt.xlabel('日期')
            plt.ylabel('股票数量')
        
        # 行业分布
        plt.subplot(2, 2, 2)
        industry_rank = analysis_result.get('industry_rank')
        if industry_rank is not None and not industry_rank.empty:
            top_industries = industry_rank.head(10)
            plt.barh(range(len(top_industries)), top_industries.values)
            plt.yticks(range(len(top_industries)), top_industries.index)
            plt.title('暴涨股票行业分布Top10')
            plt.xlabel('股票数量')
        
        # 暴涨后第二天表现
        plt.subplot(2, 1, 2)
        next_day_df = analysis_result.get('next_day_performance')
        if next_day_df is not None and not next_day_df.empty:
            plt.scatter(next_day_df['surge_pct'], next_day_df['next_pct'])
            plt.axhline(y=0, color='r', linestyle='-')
            plt.title('暴涨股票第二天表现')
            plt.xlabel('暴涨幅度(%)')
            plt.ylabel('次日涨幅(%)')
            
            # 添加相关系数
            corr = next_day_df['surge_pct'].corr(next_day_df['next_pct'])
            plt.annotate(f'相关系数: {corr:.4f}', xy=(0.05, 0.95), xycoords='axes fraction')
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('surge_analysis.png')
        print("统计图表已保存为surge_analysis.png")
        
    def find_potential_surge_stocks(self):
        """查找可能即将暴涨的股票"""
        today = datetime.datetime.now().strftime('%Y%m%d')
        calendar = get_trade_calendar(
            (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d'),
            today
        )
        
        if not calendar:
            print("无法获取交易日历")
            return pd.DataFrame()
            
        # 获取最近的交易日
        latest_trade_dates = calendar[-5:] if len(calendar) >= 5 else calendar
        
        # 获取所有股票
        all_stocks = get_stock_basics()
        if all_stocks.empty:
            print("无法获取股票列表")
            return pd.DataFrame()
            
        # 筛选条件
        potential_stocks = []
        
        # 分批处理股票
        for i in range(0, len(all_stocks), 50):
            batch = all_stocks.iloc[i:i+50]
            for _, stock in batch.iterrows():
                ts_code = stock['ts_code']
                
                # 获取最近几天的数据
                df = get_daily_data(ts_code, latest_trade_dates[0], latest_trade_dates[-1])
                if df.empty or len(df) < 3:
                    continue
                    
                # 按日期排序
                df = df.sort_values('trade_date')
                
                # 计算指标：连续3天量能增长，最后一天涨幅大于3%
                if len(df) >= 3:
                    vol_increase = True
                    for j in range(1, min(3, len(df))):
                        if df.iloc[j]['vol'] <= df.iloc[j-1]['vol']:
                            vol_increase = False
                            break
                            
                    last_day_change = df.iloc[-1]['pct_chg'] if not df.empty else 0
                    
                    # 检查是否满足筛选条件
                    if vol_increase and 2 < last_day_change < SURGE_THRESHOLD:
                        potential_stocks.append({
                            'ts_code': ts_code,
                            'name': stock['name'],
                            'industry': stock.get('industry', ''),
                            'last_pct_chg': last_day_change,
                            'vol_ratio': df.iloc[-1]['vol'] / df.iloc[-3]['vol'] if len(df) >= 3 else None
                        })
        
        # 转换为DataFrame并排序
        result = pd.DataFrame(potential_stocks)
        if not result.empty:
            result = result.sort_values(by=['vol_ratio', 'last_pct_chg'], ascending=False)
            
        return result

    # ===== 新增功能：基于财务数据的分析 =====
    def find_value_stocks(self, pe_max=15, pb_max=1.5, roe_min=10, min_profit_yoy=5):
        """筛选具有投资价值的股票
        
        Args:
            pe_max (float): 最大市盈率
            pb_max (float): 最大市净率
            roe_min (float): 最小净资产收益率(%)
            min_profit_yoy (float): 最小净利润同比增长率(%)
            
        Returns:
            pd.DataFrame: 符合条件的价值股列表
        """
        print("正在筛选价值股...")
        
        # 获取所有股票列表
        if self.stock_basics is None or self.stock_basics.empty:
            self.update_stock_basics()
            
        if self.stock_basics.empty:
            print("无法获取股票列表")
            return pd.DataFrame()
            
        # 获取最近一个交易日
        today = datetime.datetime.now().strftime('%Y%m%d')
        calendar = get_trade_calendar(
            (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d'),
            today
        )
        latest_trade_date = calendar[-1] if calendar else today
        
        # 获取最近交易日的每日指标数据
        daily_basic = get_daily_basic(trade_date=latest_trade_date)
        if daily_basic.empty:
            print(f"无法获取{latest_trade_date}的每日指标数据")
            return pd.DataFrame()
            
        # 筛选PE和PB符合条件的股票
        filtered_stocks = daily_basic[(daily_basic['pe'] > 0) & (daily_basic['pe'] <= pe_max) & 
                                    (daily_basic['pb'] > 0) & (daily_basic['pb'] <= pb_max)].copy()
        
        if filtered_stocks.empty:
            print("没有找到符合PE和PB条件的股票")
            return pd.DataFrame()
            
        # 获取最近财报期
        today_dt = datetime.datetime.now()
        year = today_dt.year
        month = today_dt.month
        
        # 根据当前月份确定最近的财报期
        if month >= 10:  # 第三季度报告
            report_date = f"{year}0930"
        elif month >= 7:  # 半年报
            report_date = f"{year}0630"
        elif month >= 4:  # 第一季度报告
            report_date = f"{year}0331"
        else:  # 去年年报
            report_date = f"{year-1}1231"
            
        print(f"使用财报期: {report_date}")
        
        # 初始化结果列表
        result_list = []
        
        # 为了避免频繁请求API导致超限，添加统计计数和休息逻辑
        count = 0
        total = len(filtered_stocks)
        
        for _, stock in filtered_stocks.iterrows():
            ts_code = stock['ts_code']
            count += 1
            
            if count % 50 == 0:
                print(f"已处理 {count}/{total} 只股票")
                time.sleep(1)  # 避免频繁调用API
                
            # 获取利润表数据
            income_data = get_income(ts_code=ts_code, period=report_date)
            if income_data.empty:
                continue
                
            # 获取资产负债表数据
            balance_data = get_balancesheet(ts_code=ts_code, period=report_date)
            if balance_data.empty:
                continue
                
            # 计算ROE
            try:
                net_profit = income_data.iloc[0]['n_income_attr_p']
                equity = balance_data.iloc[0]['total_hldr_eqy_exc_min_int']
                roe = (net_profit / equity) * 100 if equity != 0 else 0
                
                # 获取利润同比增长率
                profit_yoy = income_data.iloc[0].get('profit_yoy', 0)
                if pd.isna(profit_yoy):
                    profit_yoy = 0
                    
                # 检查是否满足条件
                if roe >= roe_min and profit_yoy >= min_profit_yoy:
                    # 获取公司名称
                    stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
                    name = stock_info.iloc[0]['name'] if not stock_info.empty else ""
                    industry = stock_info.iloc[0]['industry'] if not stock_info.empty else ""
                    
                    result_list.append({
                        'ts_code': ts_code,
                        'name': name,
                        'industry': industry,
                        'pe': stock['pe'],
                        'pb': stock['pb'],
                        'roe': roe,
                        'profit_yoy': profit_yoy,
                        'total_mv': stock.get('total_mv', 0) / 10000  # 转换为亿元
                    })
            except Exception as e:
                print(f"处理股票 {ts_code} 时出错: {e}")
                continue
        
        # 转换为DataFrame并排序
        result = pd.DataFrame(result_list)
        if not result.empty:
            result = result.sort_values(by=['roe', 'profit_yoy'], ascending=False)
            
        return result
        
    def analyze_hsgt_stocks(self, top_n=20, days=30):
        """分析北向资金(沪深股通)持续流入的股票
        
        Args:
            top_n (int): 返回前N个北向资金流入最多的股票
            days (int): 分析最近的天数
            
        Returns:
            pd.DataFrame: 北向资金流入排名靠前的股票
        """
        print(f"分析最近{days}天北向资金流入情况...")
        
        # 获取日期范围
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
        
        # 获取交易日历
        trade_dates = get_trade_calendar(start_date, end_date)
        if not trade_dates:
            print("无法获取交易日历")
            return pd.DataFrame()
        
        # 初始化股票资金流入统计
        stock_funds = defaultdict(float)
        stock_info = {}
        
        # 遍历每个交易日，获取沪深股通十大成交股
        for date in trade_dates:
            print(f"获取 {date} 沪深股通数据...")
            
            # 获取沪市十大成交股
            sh_data = get_hsgt_top10(trade_date=date, market_type='1')
            if not sh_data.empty:
                for _, row in sh_data.iterrows():
                    ts_code = row['ts_code']
                    net_amount = row['net_amount'] / 10000  # 转换为万元
                    stock_funds[ts_code] += net_amount
                    
                    if ts_code not in stock_info:
                        stock_info[ts_code] = {
                            'name': row['name'],
                            'count': 0,
                            'pos_days': 0
                        }
                    
                    stock_info[ts_code]['count'] += 1
                    if net_amount > 0:
                        stock_info[ts_code]['pos_days'] += 1
            
            # 获取深市十大成交股
            sz_data = get_hsgt_top10(trade_date=date, market_type='3')
            if not sz_data.empty:
                for _, row in sz_data.iterrows():
                    ts_code = row['ts_code']
                    net_amount = row['net_amount'] / 10000  # 转换为万元
                    stock_funds[ts_code] += net_amount
                    
                    if ts_code not in stock_info:
                        stock_info[ts_code] = {
                            'name': row['name'],
                            'count': 0,
                            'pos_days': 0
                        }
                    
                    stock_info[ts_code]['count'] += 1
                    if net_amount > 0:
                        stock_info[ts_code]['pos_days'] += 1
            
            time.sleep(0.5)  # 避免频繁调用API
        
        # 转换为DataFrame并排序
        result_list = []
        for ts_code, net_amount in stock_funds.items():
            info = stock_info.get(ts_code, {})
            result_list.append({
                'ts_code': ts_code,
                'name': info.get('name', ''),
                'net_inflow': net_amount,  # 单位: 万元
                'appear_days': info.get('count', 0),
                'positive_days': info.get('pos_days', 0),
                'positive_ratio': info.get('pos_days', 0) / info.get('count', 1) * 100 if info.get('count', 0) > 0 else 0
            })
        
        result = pd.DataFrame(result_list)
        if not result.empty:
            # 根据净流入金额排序
            result = result.sort_values(by='net_inflow', ascending=False)
            
            # 获取这些股票的行业信息
            if self.stock_basics is None or self.stock_basics.empty:
                self.update_stock_basics()
                
            if not self.stock_basics.empty:
                result = pd.merge(
                    result, 
                    self.stock_basics[['ts_code', 'industry']], 
                    on='ts_code', 
                    how='left'
                )
            
            # 获取最近一个交易日的收盘价和涨跌幅
            latest_date = trade_dates[-1]
            for i, row in result.iterrows():
                ts_code = row['ts_code']
                df = get_daily_data(ts_code, latest_date, latest_date)
                if not df.empty:
                    result.loc[i, 'price'] = df.iloc[0]['close']
                    result.loc[i, 'pct_chg'] = df.iloc[0]['pct_chg']
        
        return result.head(top_n)
    
    def analyze_minute_pattern(self, ts_code, trade_date=None, freq='5min'):
        """分析股票分钟级别的交易模式
        
        Args:
            ts_code (str): 股票代码
            trade_date (str, optional): 交易日期，默认为最近交易日
            freq (str): 分钟频度，默认5分钟
            
        Returns:
            pd.DataFrame: 分钟级别的交易数据及分析结果
        """
        # 确定分析日期
        if trade_date is None:
            today = datetime.datetime.now()
            # 如果是交易时段，使用当天，否则使用最近的交易日
            if today.hour < 15 and today.weekday() < 5:
                trade_date = today.strftime('%Y%m%d')
            else:
                # 获取最近交易日
                calendar = get_trade_calendar(
                    (today - datetime.timedelta(days=10)).strftime('%Y%m%d'),
                    today.strftime('%Y%m%d')
                )
                trade_date = calendar[-1] if calendar else today.strftime('%Y%m%d')
        
        print(f"分析 {ts_code} 在 {trade_date} 的分钟级别交易模式...")
        
        # 构造时间范围
        date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
        start_time = f"{date_str} 09:30:00"
        end_time = f"{date_str} 15:00:00"
        
        # 获取分钟数据
        minute_data = get_minute_data(ts_code, start_time, end_time, freq=freq)
        if minute_data.empty:
            print(f"未能获取 {ts_code} 在 {trade_date} 的分钟数据")
            return pd.DataFrame()
        
        # 按时间排序
        minute_data = minute_data.sort_values('trade_time')
        
        # 计算分析指标
        minute_data['vol_change'] = minute_data['vol'].pct_change() * 100
        minute_data['amount_change'] = minute_data['amount'].pct_change() * 100
        minute_data['price_change'] = minute_data['close'].pct_change() * 100
        
        # 分析成交量分布
        am_vol = minute_data[minute_data['trade_time'].str[:11] + '11:30:00' >= minute_data['trade_time']]['vol'].sum()
        pm_vol = minute_data[minute_data['trade_time'].str[:11] + '13:00:00' <= minute_data['trade_time']]['vol'].sum()
        
        # 获取日线数据作为参考
        daily_data = get_daily_data(ts_code, trade_date, trade_date)
        
        # 构建分析结果
        analysis = {
            'ts_code': ts_code,
            'trade_date': trade_date,
            'freq': freq,
            'data_points': len(minute_data),
            'open': minute_data.iloc[0]['open'] if not minute_data.empty else None,
            'close': minute_data.iloc[-1]['close'] if not minute_data.empty else None,
            'high': minute_data['high'].max() if not minute_data.empty else None,
            'low': minute_data['low'].min() if not minute_data.empty else None,
            'am_vol_ratio': am_vol / (am_vol + pm_vol) * 100 if (am_vol + pm_vol) > 0 else 0,
            'pm_vol_ratio': pm_vol / (am_vol + pm_vol) * 100 if (am_vol + pm_vol) > 0 else 0,
            'total_vol': minute_data['vol'].sum() if not minute_data.empty else 0,
            'max_vol_time': minute_data.loc[minute_data['vol'].idxmax(), 'trade_time'] if not minute_data.empty else None,
            'max_vol': minute_data['vol'].max() if not minute_data.empty else 0,
            'min_vol_time': minute_data.loc[minute_data['vol'].idxmin(), 'trade_time'] if not minute_data.empty else None,
            'min_vol': minute_data['vol'].min() if not minute_data.empty else 0,
            'daily_close': daily_data.iloc[0]['close'] if not daily_data.empty else None,
            'daily_pct_chg': daily_data.iloc[0]['pct_chg'] if not daily_data.empty else None
        }
        
        # 绘制分钟级别K线图和成交量图
        self.plot_minute_chart(minute_data, ts_code, trade_date, freq)
        
        return minute_data, analysis
    
    def plot_minute_chart(self, minute_data, ts_code, trade_date, freq):
        """绘制分钟级别K线图和成交量图
        
        Args:
            minute_data (pd.DataFrame): 分钟数据
            ts_code (str): 股票代码
            trade_date (str): 交易日期
            freq (str): 频率
        """
        if minute_data.empty:
            print("数据为空，无法绘制图表")
            return
        
        # 获取股票名称
        stock_name = ""
        if self.stock_basics is not None and not self.stock_basics.empty:
            stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
            if not stock_info.empty:
                stock_name = stock_info.iloc[0]['name']
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # 绘制价格走势图
        ax1.plot(range(len(minute_data)), minute_data['close'], 'b-')
        ax1.set_title(f"{stock_name}({ts_code}) {trade_date} {freq}K线图")
        ax1.set_ylabel('价格')
        ax1.grid(True)
        
        # 设置x轴刻度
        ticks = range(0, len(minute_data), max(1, len(minute_data) // 10))
        ax1.set_xticks(ticks)
        ax1.set_xticklabels([minute_data.iloc[i]['trade_time'][11:16] for i in ticks], rotation=45)
        
        # 绘制成交量图
        ax2.bar(range(len(minute_data)), minute_data['vol'], color='g')
        ax2.set_ylabel('成交量')
        ax2.set_xlabel('时间')
        ax2.grid(True)
        
        # 设置x轴刻度
        ax2.set_xticks(ticks)
        ax2.set_xticklabels([minute_data.iloc[i]['trade_time'][11:16] for i in ticks], rotation=45)
        
        plt.tight_layout()
        
        # 保存图表
        output_file = f"{ts_code}_{trade_date}_{freq}_chart.png"
        plt.savefig(output_file)
        print(f"分钟图表已保存为 {output_file}")
        plt.close()
    
    def find_continuous_rise_stocks(self, days=5, min_rise_days=3):
        """查找连续上涨的股票
        
        Args:
            days (int): 查看最近几天的数据
            min_rise_days (int): 最少连续上涨天数
            
        Returns:
            pd.DataFrame: 连续上涨的股票列表
        """
        print(f"查找连续上涨的股票(最近{days}天数据，最少连续上涨{min_rise_days}天)...")
        
        # 获取交易日历
        today = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days+5)).strftime('%Y%m%d')
        calendar = get_trade_calendar(start_date, today)
        
        if len(calendar) < days:
            print(f"获取的交易日历数量({len(calendar)})小于要求的天数({days})")
            return pd.DataFrame()
        
        # 使用最近的days个交易日
        trade_dates = calendar[-days:]
        
        # 获取所有股票
        if self.stock_basics is None or self.stock_basics.empty:
            self.update_stock_basics()
            
        if self.stock_basics.empty:
            print("无法获取股票列表")
            return pd.DataFrame()
        
        # 初始化结果列表
        result_list = []
        
        # 为了避免频繁请求API导致超限，添加统计计数和休息逻辑
        count = 0
        total = len(self.stock_basics)
        
        for _, stock in self.stock_basics.iterrows():
            ts_code = stock['ts_code']
            count += 1
            
            if count % 100 == 0:
                print(f"已处理 {count}/{total} 只股票")
                time.sleep(1)  # 避免频繁调用API
            
            # 获取股票行情数据
            daily_data = get_daily_data(ts_code, trade_dates[0], trade_dates[-1])
            if daily_data.empty or len(daily_data) < min_rise_days:
                continue
            
            # 按日期排序
            daily_data = daily_data.sort_values('trade_date')
            
            # 检查是否连续上涨
            rise_days = 0
            current_rise_days = 0
            max_rise_pct = 0
            
            for i in range(len(daily_data)):
                if daily_data.iloc[i]['pct_chg'] > 0:
                    current_rise_days += 1
                    max_rise_pct += daily_data.iloc[i]['pct_chg']
                else:
                    rise_days = max(rise_days, current_rise_days)
                    current_rise_days = 0
            
            # 更新最大连续上涨天数
            rise_days = max(rise_days, current_rise_days)
            
            # 如果达到最小连续上涨天数要求
            if rise_days >= min_rise_days:
                result_list.append({
                    'ts_code': ts_code,
                    'name': stock['name'],
                    'industry': stock.get('industry', ''),
                    'rise_days': rise_days,
                    'max_rise_pct': max_rise_pct,
                    'latest_price': daily_data.iloc[-1]['close'],
                    'latest_pct_chg': daily_data.iloc[-1]['pct_chg']
                })
        
        # 转换为DataFrame并排序
        result = pd.DataFrame(result_list)
        if not result.empty:
            result = result.sort_values(by=['rise_days', 'max_rise_pct'], ascending=False)
        
        return result

    # ===== 业绩和财务分析功能 =====
    def analyze_forecast(self, period=None, type=None, top_n=20):
        """分析业绩预告数据
        
        Args:
            period (str): 报告期(每个季度最后一天的日期，如20171231)
            type (str): 预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)
            top_n (int): 返回前N个结果
            
        Returns:
            pd.DataFrame: 业绩预告分析结果
        """
        print(f"分析业绩预告数据...")
        
        # 获取最近的报告期，如果未指定
        if period is None:
            today = datetime.datetime.now()
            year = today.year
            month = today.month
            
            if month >= 10:  # 第三季度报告
                period = f"{year}0930"
            elif month >= 7:  # 半年报
                period = f"{year}0630"
            elif month >= 4:  # 第一季度报告
                period = f"{year}0331"
            else:  # 去年年报
                period = f"{year-1}1231"
        
        print(f"使用报告期: {period}")
        
        # 获取业绩预告数据
        forecast_data = get_forecast(period=period, type=type)
        
        if forecast_data.empty:
            print(f"未找到{period}期间的业绩预告数据")
            return pd.DataFrame()
        
        # 如果有股票基本信息，添加行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            forecast_data = pd.merge(
                forecast_data, 
                self.stock_basics[['ts_code', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        # 按预告净利润变动幅度排序
        if 'p_change_max' in forecast_data.columns:
            forecast_data = forecast_data.sort_values(by='p_change_max', ascending=False)
        
        # 分析行业分布
        if 'industry' in forecast_data.columns:
            industry_counts = forecast_data['industry'].value_counts()
            print("\n行业分布:")
            for ind, count in industry_counts.head(10).items():
                print(f"{ind}: {count}只")
        
        # 分析预告类型分布
        type_counts = forecast_data['type'].value_counts()
        print("\n预告类型分布:")
        for typ, count in type_counts.items():
            print(f"{typ}: {count}只")
        
        return forecast_data.head(top_n)
    
    def analyze_express(self, period=None, top_n=20, min_yoy_profit=10):
        """分析业绩快报数据
        
        Args:
            period (str): 报告期(每个季度最后一天的日期，如20171231)
            top_n (int): 返回前N个结果
            min_yoy_profit (float): 最小净利润同比增长率(%)
            
        Returns:
            pd.DataFrame: 业绩快报分析结果
        """
        print(f"分析业绩快报数据...")
        
        # 获取最近的报告期，如果未指定
        if period is None:
            today = datetime.datetime.now()
            year = today.year
            month = today.month
            
            if month >= 10:  # 第三季度报告
                period = f"{year}0930"
            elif month >= 7:  # 半年报
                period = f"{year}0630"
            elif month >= 4:  # 第一季度报告
                period = f"{year}0331"
            else:  # 去年年报
                period = f"{year-1}1231"
        
        print(f"使用报告期: {period}")
        
        # 获取业绩快报数据
        express_data = get_express(period=period)
        
        if express_data.empty:
            print(f"未找到{period}期间的业绩快报数据")
            return pd.DataFrame()
        
        # 筛选净利润同比增长超过阈值的公司
        if 'yoy_net_profit' in express_data.columns:
            express_data = express_data[express_data['yoy_net_profit'] >= min_yoy_profit]
        
        # 如果有股票基本信息，添加行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            express_data = pd.merge(
                express_data, 
                self.stock_basics[['ts_code', 'name', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        # 按净利润同比增长率排序
        if 'yoy_net_profit' in express_data.columns:
            express_data = express_data.sort_values(by='yoy_net_profit', ascending=False)
        
        # 分析行业分布
        if 'industry' in express_data.columns:
            industry_counts = express_data['industry'].value_counts()
            print("\n行业分布:")
            for ind, count in industry_counts.head(10).items():
                print(f"{ind}: {count}只")
        
        return express_data.head(top_n)
    
    def find_dividend_stocks(self, min_div_yield=2.0, top_n=20):
        """查找高分红股票
        
        Args:
            min_div_yield (float): 最小股息率(%)
            top_n (int): 返回前N个结果
            
        Returns:
            pd.DataFrame: 高分红股票列表
        """
        print(f"查找股息率大于{min_div_yield}%的高分红股票...")
        
        # 获取所有股票
        if self.stock_basics is None or self.stock_basics.empty:
            self.update_stock_basics()
            
        if self.stock_basics.empty:
            print("无法获取股票列表")
            return pd.DataFrame()
        
        # 获取最近一个交易日
        today = datetime.datetime.now().strftime('%Y%m%d')
        calendar = get_trade_calendar(
            (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d'),
            today
        )
        latest_trade_date = calendar[-1] if calendar else today
        
        # 获取每日指标数据，包含股息率
        daily_basic = get_daily_basic(trade_date=latest_trade_date)
        if daily_basic.empty:
            print(f"无法获取{latest_trade_date}的每日指标数据")
            return pd.DataFrame()
        
        # 筛选股息率符合条件的股票
        high_div_stocks = daily_basic[daily_basic['dv_ratio'] >= min_div_yield].copy()
        
        if high_div_stocks.empty:
            print(f"未找到股息率大于{min_div_yield}%的股票")
            return pd.DataFrame()
        
        # 如果有股票基本信息，添加股票名称和行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            high_div_stocks = pd.merge(
                high_div_stocks, 
                self.stock_basics[['ts_code', 'name', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        # 按股息率排序
        high_div_stocks = high_div_stocks.sort_values(by='dv_ratio', ascending=False)
        
        # 获取分红送股数据作为参考
        result_list = []
        
        for _, stock in high_div_stocks.head(top_n).iterrows():
            ts_code = stock['ts_code']
            
            # 获取最近的分红记录
            div_data = get_dividend(ts_code=ts_code)
            
            latest_div = None
            if not div_data.empty:
                div_data = div_data.sort_values('ann_date', ascending=False)
                latest_div = div_data.iloc[0] if len(div_data) > 0 else None
            
            result_list.append({
                'ts_code': ts_code,
                'name': stock.get('name', ''),
                'industry': stock.get('industry', ''),
                'dv_ratio': stock['dv_ratio'],  # 股息率
                'close': stock['close'],  # 当前价格
                'pe': stock.get('pe', None),  # 市盈率
                'pb': stock.get('pb', None),  # 市净率
                'total_mv': stock.get('total_mv', 0) / 10000,  # 总市值(亿元)
                'latest_div_date': latest_div['ann_date'] if latest_div is not None else None,
                'latest_div': latest_div['cash_div'] if latest_div is not None else None
            })
        
        return pd.DataFrame(result_list)
    
    def analyze_disclosure_date(self, end_date=None):
        """分析财报披露计划
        
        Args:
            end_date (str): 财报周期(每个季度最后一天的日期，如20171231)
            
        Returns:
            pd.DataFrame: 财报披露计划分析结果
        """
        print(f"分析财报披露计划...")
        
        # 获取最近的报告期，如果未指定
        if end_date is None:
            today = datetime.datetime.now()
            year = today.year
            month = today.month
            
            if month >= 10:  # 第三季度报告
                end_date = f"{year}0930"
            elif month >= 7:  # 半年报
                end_date = f"{year}0630"
            elif month >= 4:  # 第一季度报告
                end_date = f"{year}0331"
            else:  # 去年年报
                end_date = f"{year-1}1231"
        
        print(f"使用财报周期: {end_date}")
        
        # 获取财报披露计划数据
        disclosure_data = get_disclosure_date(end_date=end_date)
        
        if disclosure_data.empty:
            print(f"未找到{end_date}期间的财报披露计划数据")
            return pd.DataFrame()
        
        # 如果有股票基本信息，添加股票名称和行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            disclosure_data = pd.merge(
                disclosure_data, 
                self.stock_basics[['ts_code', 'name', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        # 按计划披露日期排序
        disclosure_data = disclosure_data.sort_values(by='pre_date')
        
        # 分析披露日期分布
        date_counts = disclosure_data['pre_date'].value_counts().sort_index()
        print("\n披露日期分布:")
        for date, count in date_counts.items():
            print(f"{date}: {count}只")
        
        return disclosure_data
    
    def analyze_share_float(self, start_date=None, end_date=None, min_ratio=5.0):
        """分析限售股解禁情况
        
        Args:
            start_date (str): 解禁开始日期
            end_date (str): 解禁结束日期
            min_ratio (float): 最小解禁比例(%)
            
        Returns:
            pd.DataFrame: 限售股解禁分析结果
        """
        print(f"分析限售股解禁情况...")
        
        # 如果未指定日期，使用未来3个月
        if start_date is None:
            start_date = datetime.datetime.now().strftime('%Y%m%d')
        
        if end_date is None:
            end_date = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y%m%d')
        
        print(f"分析期间: {start_date} 至 {end_date}")
        
        # 获取限售股解禁数据
        float_data = get_share_float(start_date=start_date, end_date=end_date)
        
        if float_data.empty:
            print(f"未找到{start_date}至{end_date}期间的限售股解禁数据")
            return pd.DataFrame()
        
        # 筛选解禁比例超过阈值的
        if 'float_ratio' in float_data.columns:
            float_data = float_data[float_data['float_ratio'] >= min_ratio]
        
        # 如果有股票基本信息，添加股票名称和行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            float_data = pd.merge(
                float_data, 
                self.stock_basics[['ts_code', 'name', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        # 按解禁日期和解禁比例排序
        float_data = float_data.sort_values(by=['float_date', 'float_ratio'], ascending=[True, False])
        
        # 分析解禁类型分布
        if 'share_type' in float_data.columns:
            type_counts = float_data['share_type'].value_counts()
            print("\n解禁类型分布:")
            for typ, count in type_counts.items():
                print(f"{typ}: {count}只")
        
        # 分析行业分布
        if 'industry' in float_data.columns:
            industry_counts = float_data['industry'].value_counts()
            print("\n行业分布:")
            for ind, count in industry_counts.head(10).items():
                print(f"{ind}: {count}只")
        
        return float_data
    
    def analyze_holdernumber_trend(self, ts_code, start_date=None, end_date=None):
        """分析股东人数变化趋势
        
        Args:
            ts_code (str): 股票代码
            start_date (str): 开始日期
            end_date (str): 结束日期
            
        Returns:
            pd.DataFrame: 股东人数变化趋势分析结果
        """
        print(f"分析{ts_code}股东人数变化趋势...")
        
        # 如果未指定日期，使用过去1年
        if start_date is None:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y%m%d')
        
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
        
        # 获取股东人数数据
        holder_data = get_stk_holdernumber(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if holder_data.empty:
            print(f"未找到{ts_code}在{start_date}至{end_date}期间的股东人数数据")
            return pd.DataFrame()
        
        # 按截止日期排序
        holder_data = holder_data.sort_values('end_date')
        
        # 计算环比变化
        holder_data['holder_num_chg'] = holder_data['holder_num'].diff()
        holder_data['holder_num_chg_pct'] = holder_data['holder_num'].pct_change() * 100
        
        # 统计总体变化
        first_record = holder_data.iloc[0] if len(holder_data) > 0 else None
        last_record = holder_data.iloc[-1] if len(holder_data) > 0 else None
        
        if first_record is not None and last_record is not None:
            total_chg = last_record['holder_num'] - first_record['holder_num']
            total_chg_pct = (total_chg / first_record['holder_num']) * 100
            
            print(f"\n从{first_record['end_date']}到{last_record['end_date']}:")
            print(f"起始股东人数: {first_record['holder_num']}")
            print(f"最新股东人数: {last_record['holder_num']}")
            print(f"变化幅度: {total_chg} ({total_chg_pct:.2f}%)")
            
            # 判断趋势
            if total_chg > 0:
                print("总体趋势: 股东人数增加，散户可能增加")
            elif total_chg < 0:
                print("总体趋势: 股东人数减少，可能有集中持股现象")
            else:
                print("总体趋势: 股东人数稳定")
        
        return holder_data
    
    def analyze_holdertrade(self, days=30, trade_type=None, holder_type=None):
        """分析股东增减持情况
        
        Args:
            days (int): 分析最近的天数
            trade_type (str): 交易类型(IN增持 DE减持)
            holder_type (str): 股东类型(C公司 P个人 G高管)
            
        Returns:
            pd.DataFrame: 股东增减持分析结果
        """
        print(f"分析最近{days}天的股东{'增持' if trade_type == 'IN' else '减持' if trade_type == 'DE' else '增减持'}情况...")
        
        # 计算日期范围
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
        
        # 获取股东增减持数据
        holder_trade_data = get_stk_holdertrade(
            start_date=start_date, 
            end_date=end_date, 
            trade_type=trade_type,
            holder_type=holder_type
        )
        
        if holder_trade_data.empty:
            print(f"未找到{start_date}至{end_date}期间的股东增减持数据")
            return pd.DataFrame()
        
        # 如果有股票基本信息，添加行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            holder_trade_data = pd.merge(
                holder_trade_data, 
                self.stock_basics[['ts_code', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        # 按公告日期排序
        holder_trade_data = holder_trade_data.sort_values('ann_date', ascending=False)
        
        # 分析行业分布
        if 'industry' in holder_trade_data.columns:
            industry_counts = holder_trade_data['industry'].value_counts()
            print("\n行业分布:")
            for ind, count in industry_counts.head(10).items():
                print(f"{ind}: {count}只")
        
        # 分析股东类型分布
        holder_type_counts = holder_trade_data['holder_type'].value_counts()
        print("\n股东类型分布:")
        for typ, count in holder_type_counts.items():
            holder_type_name = "高管" if typ == "G" else "个人" if typ == "P" else "公司" if typ == "C" else typ
            print(f"{holder_type_name}: {count}条记录")
        
        # 分析交易类型分布
        trade_type_counts = holder_trade_data['in_de'].value_counts()
        print("\n交易类型分布:")
        for typ, count in trade_type_counts.items():
            trade_type_name = "增持" if typ == "IN" else "减持" if typ == "DE" else typ
            print(f"{trade_type_name}: {count}条记录")
        
        # 计算总体增减持金额
        try:
            total_in_amount = holder_trade_data[holder_trade_data['in_de'] == 'IN']['change_vol'].sum()
            total_de_amount = holder_trade_data[holder_trade_data['in_de'] == 'DE']['change_vol'].sum()
            
            print(f"\n总增持量: {total_in_amount:.2f}股")
            print(f"总减持量: {total_de_amount:.2f}股")
            print(f"净增持量: {total_in_amount - total_de_amount:.2f}股")
        except:
            pass
        
        return holder_trade_data
    
    def analyze_report_rc(self, trade_date=None, days=7):
        """分析卖方研报盈利预测
        
        Args:
            trade_date (str): 报告日期
            days (int): 如果未指定日期，则分析最近几天的研报
            
        Returns:
            pd.DataFrame: 卖方研报分析结果
        """
        print(f"分析卖方研报盈利预测...")
        
        # 如果未指定日期，使用最近几天
        if trade_date is None:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
            
            # 获取研报数据
            report_data = get_report_rc(start_date=start_date, end_date=end_date)
        else:
            # 获取指定日期的研报数据
            report_data = get_report_rc(report_date=trade_date)
        
        if report_data.empty:
            print(f"未找到相关的卖方研报数据")
            return pd.DataFrame()
        
        # 分析研报机构分布
        org_counts = report_data['org_name'].value_counts()
        print("\n研报机构分布(TOP10):")
        for org, count in org_counts.head(10).items():
            print(f"{org}: {count}条研报")
        
        # 分析评级分布
        rating_counts = report_data['rating'].value_counts()
        print("\n评级分布:")
        for rating, count in rating_counts.items():
            print(f"{rating}: {count}条研报")
        
        # 获取热门推荐个股(评级为买入或增持的股票)
        pos_reports = report_data[report_data['rating'].str.contains('买入|增持', na=False)]
        popular_stocks = pos_reports['ts_code'].value_counts()
        
        print("\n热门推荐个股(TOP20):")
        for ts_code, count in popular_stocks.head(20).items():
            stock_name = report_data[report_data['ts_code'] == ts_code]['name'].values[0] if len(report_data[report_data['ts_code'] == ts_code]) > 0 else ""
            print(f"{ts_code} {stock_name}: {count}条买入/增持研报")
        
        return report_data
    
    def analyze_chips(self, ts_code, trade_date=None):
        """分析个股筹码分布
        
        Args:
            ts_code (str): 股票代码
            trade_date (str): 交易日期，默认为最近交易日
            
        Returns:
            dict: 筹码分析结果
        """
        print(f"分析{ts_code}筹码分布情况...")
        
        # 如果未指定日期，使用最近交易日
        if trade_date is None:
            today = datetime.datetime.now().strftime('%Y%m%d')
            calendar = get_trade_calendar(
                (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d'),
                today
            )
            trade_date = calendar[-1] if calendar else today
        
        # 获取筹码及胜率数据
        perf_data = get_cyq_perf(ts_code=ts_code, trade_date=trade_date)
        
        if perf_data.empty:
            print(f"未找到{ts_code}在{trade_date}的筹码及胜率数据")
            return {}
        
        # 获取筹码分布数据
        chips_data = get_cyq_chips(ts_code=ts_code, trade_date=trade_date)
        
        if chips_data.empty:
            print(f"未找到{ts_code}在{trade_date}的筹码分布数据")
            return {}
        
        # 获取当日股价
        daily_data = get_daily_data(ts_code=ts_code, start_date=trade_date, end_date=trade_date)
        current_price = daily_data.iloc[0]['close'] if not daily_data.empty else None
        
        # 分析筹码分布结果
        perf_record = perf_data.iloc[0]
        
        result = {
            'ts_code': ts_code,
            'trade_date': trade_date,
            'current_price': current_price,
            'historical_low': perf_record['his_low'],
            'historical_high': perf_record['his_high'],
            'cost_5pct': perf_record['cost_5pct'],
            'cost_15pct': perf_record['cost_15pct'],
            'cost_50pct': perf_record['cost_50pct'],
            'cost_85pct': perf_record['cost_85pct'],
            'cost_95pct': perf_record['cost_95pct'],
            'weight_avg_cost': perf_record['weight_avg'],
            'winner_rate': perf_record['winner_rate'],
            'chips_distribution': chips_data
        }
        
        # 打印筹码分布分析
        print(f"\n{ts_code} 在 {trade_date} 的筹码分布分析:")
        print(f"当前价格: {current_price}")
        print(f"历史最低: {result['historical_low']}")
        print(f"历史最高: {result['historical_high']}")
        print(f"加权平均成本: {result['weight_avg_cost']}")
        print(f"获利比例: {result['winner_rate']}%")
        
        # 判断价格区域
        if current_price is not None:
            if current_price <= result['cost_5pct']:
                print("价格处于极低区域，5%的持仓在亏损，可能是底部区域")
            elif current_price <= result['cost_15pct']:
                print("价格处于低位区域，15%的持仓在亏损")
            elif current_price <= result['cost_50pct']:
                print("价格处于中低位，50%的持仓在亏损")
            elif current_price <= result['cost_85pct']:
                print("价格处于中高位，50%-85%的持仓在盈利")
            elif current_price <= result['cost_95pct']:
                print("价格处于高位区域，85%的持仓在盈利")
            else:
                print("价格处于极高区域，95%以上的持仓在盈利，可能是阶段性高点")
        
        # 绘制筹码分布图
        self.plot_chips_distribution(result)
        
        return result
    
    def plot_chips_distribution(self, chips_result):
        """绘制筹码分布图
        
        Args:
            chips_result (dict): 筹码分析结果
        """
        if not chips_result or 'chips_distribution' not in chips_result or chips_result['chips_distribution'].empty:
            print("无法绘制筹码分布图，数据不完整")
            return
        
        ts_code = chips_result['ts_code']
        trade_date = chips_result['trade_date']
        chips_data = chips_result['chips_distribution']
        current_price = chips_result['current_price']
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 绘制筹码分布图
        plt.bar(chips_data['price'], chips_data['percent'], width=0.02, alpha=0.7)
        
        # 添加当前价格线
        if current_price is not None:
            plt.axvline(x=current_price, color='r', linestyle='--', label=f'当前价格: {current_price}')
        
        # 添加各个成本分位线
        plt.axvline(x=chips_result['cost_5pct'], color='g', linestyle='-.', label=f'5%成本: {chips_result["cost_5pct"]}')
        plt.axvline(x=chips_result['cost_50pct'], color='b', linestyle='-.', label=f'50%成本: {chips_result["cost_50pct"]}')
        plt.axvline(x=chips_result['cost_95pct'], color='y', linestyle='-.', label=f'95%成本: {chips_result["cost_95pct"]}')
        plt.axvline(x=chips_result['weight_avg_cost'], color='m', linestyle='-', label=f'加权平均: {chips_result["weight_avg_cost"]}')
        
        plt.title(f"{ts_code} {trade_date} 筹码分布图 (获利比例: {chips_result['winner_rate']}%)")
        plt.xlabel('价格')
        plt.ylabel('占比(%)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 保存图表
        output_file = f"{ts_code}_{trade_date}_chips_distribution.png"
        plt.savefig(output_file)
        print(f"筹码分布图已保存为 {output_file}")
        plt.close() 