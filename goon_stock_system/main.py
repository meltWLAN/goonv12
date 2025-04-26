#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import pandas as pd
import numpy as np
import datetime
import time
import json
import traceback

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from analysis.stock_analyzer import StockAnalyzer
from goon_stock_system.analyzers.stock_analyzer import (
    analyze_today_stocks,
    analyze_stock_history,
    analyze_potential_stocks,
    analyze_technical_factors,
    analyze_nineturn,
    analyze_auction_data
)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票分析工具')
    
    # 添加子命令解析器
    subparsers = parser.add_subparsers(dest='mode', help='运行模式')
    
    # 今日行情模式
    today_parser = subparsers.add_parser('today', help='查看今日行情')
    today_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    today_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量限制')
    today_parser.add_argument('--sort', '-s', type=str, default='pct_chg', help='排序字段')
    
    # 股票分析模式
    analyze_parser = subparsers.add_parser('analyze', help='分析股票数据')
    analyze_parser.add_argument('--stock', '-s', type=str, help='股票代码')
    analyze_parser.add_argument('--start', type=str, help='开始日期 (YYYYMMDD)')
    analyze_parser.add_argument('--end', type=str, help='结束日期 (YYYYMMDD)')
    analyze_parser.add_argument('--period', '-p', type=str, default='daily', choices=['daily', 'weekly', 'monthly'], help='数据周期')
    analyze_parser.add_argument('--ma', type=str, help='计算移动平均, 例如: 5,10,20,30')
    analyze_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 潜力股分析模式
    potential_parser = subparsers.add_parser('potential', help='发现潜力股')
    potential_parser.add_argument('--date', '-d', type=str, help='分析日期 (YYYYMMDD)')
    potential_parser.add_argument('--threshold', '-t', type=float, default=5.0, help='涨幅阈值')
    potential_parser.add_argument('--vol-ratio', '-v', type=float, default=2.0, help='成交量放大阈值')
    potential_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量限制')
    potential_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 业绩预告分析模式
    forecast_parser = subparsers.add_parser('forecast', help='分析业绩预告数据')
    forecast_parser.add_argument('--period', '-p', type=str, help='报告期 (YYYYMMDD,例如20211231)')
    forecast_parser.add_argument('--type', '-t', type=str, choices=['预增', '预减', '扭亏', '首亏', '续亏', '续盈', '略增', '略减'], help='预告类型')
    forecast_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量限制')
    forecast_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 业绩快报分析模式
    express_parser = subparsers.add_parser('express', help='分析业绩快报数据')
    express_parser.add_argument('--period', '-p', type=str, help='报告期 (YYYYMMDD,例如20211231)')
    express_parser.add_argument('--min-yoy', type=float, default=10.0, help='最小净利润同比增长率(%)')
    express_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量限制')
    express_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 高分红股票分析模式
    dividend_parser = subparsers.add_parser('dividend', help='查找高分红股票')
    dividend_parser.add_argument('--min-yield', type=float, default=2.0, help='最小股息率(%)')
    dividend_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量限制')
    dividend_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 财报披露计划分析模式
    disclosure_parser = subparsers.add_parser('disclosure', help='分析财报披露计划')
    disclosure_parser.add_argument('--period', '-p', type=str, help='报告期 (YYYYMMDD,例如20211231)')
    disclosure_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 限售股解禁分析模式
    float_parser = subparsers.add_parser('float', help='分析限售股解禁情况')
    float_parser.add_argument('--start', type=str, help='开始日期 (YYYYMMDD)')
    float_parser.add_argument('--end', type=str, help='结束日期 (YYYYMMDD)')
    float_parser.add_argument('--min-ratio', type=float, default=5.0, help='最小解禁比例(%)')
    float_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 股东人数变化趋势分析模式
    holder_parser = subparsers.add_parser('holder', help='分析股东人数变化趋势')
    holder_parser.add_argument('--stock', '-s', type=str, required=True, help='股票代码')
    holder_parser.add_argument('--start', type=str, help='开始日期 (YYYYMMDD)')
    holder_parser.add_argument('--end', type=str, help='结束日期 (YYYYMMDD)')
    holder_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 股东增减持分析模式
    holdertrade_parser = subparsers.add_parser('holdertrade', help='分析股东增减持情况')
    holdertrade_parser.add_argument('--days', '-d', type=int, default=30, help='分析最近的天数')
    holdertrade_parser.add_argument('--trade-type', '-t', type=str, choices=['IN', 'DE'], help='交易类型(IN增持 DE减持)')
    holdertrade_parser.add_argument('--holder-type', type=str, choices=['C', 'P', 'G'], help='股东类型(C公司 P个人 G高管)')
    holdertrade_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 卖方研报分析模式
    report_parser = subparsers.add_parser('report', help='分析卖方研报盈利预测')
    report_parser.add_argument('--date', '-d', type=str, help='报告日期 (YYYYMMDD)')
    report_parser.add_argument('--days', type=int, default=7, help='如果未指定日期，则分析最近几天的研报')
    report_parser.add_argument('--output', '-o', type=str, choices=['csv', 'json', 'excel'], help='输出格式')
    
    # 筹码分析模式
    chips_parser = subparsers.add_parser('chips', help='分析个股筹码分布')
    chips_parser.add_argument('--stock', '-s', type=str, required=True, help='股票代码')
    chips_parser.add_argument('--date', '-d', type=str, help='交易日期 (YYYYMMDD)')
    
    # 技术面因子分析模式
    factor_parser = subparsers.add_parser('factor', help='分析股票技术面因子')
    factor_parser.add_argument('--ts-code', required=True, help='股票代码')
    factor_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    factor_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    factor_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    factor_parser.add_argument('--output-file', help='输出文件路径')
    
    # 神奇九转指标分析模式
    nineturn_parser = subparsers.add_parser('nineturn', help='分析神奇九转指标')
    nineturn_parser.add_argument('--ts-code', required=True, help='股票代码')
    nineturn_parser.add_argument('--freq', choices=['D', 'W', 'M'], default='D', help='周期类型 (D-日, W-周, M-月)')
    nineturn_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    nineturn_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    nineturn_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    nineturn_parser.add_argument('--output-file', help='输出文件路径')
    
    # 集合竞价分析模式
    auction_parser = subparsers.add_parser('auction', help='分析集合竞价数据')
    auction_parser.add_argument('--ts-code', required=True, help='股票代码')
    auction_parser.add_argument('--type', choices=['open', 'close'], default='open', help='竞价类型 (open-开盘竞价, close-收盘竞价)')
    auction_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    auction_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    auction_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    auction_parser.add_argument('--output-file', help='输出文件路径')
    
    # === 新增命令行选项 ===
    # 东方财富板块成分分析模式
    dc_member_parser = subparsers.add_parser('dc_member', help='分析东方财富板块成分')
    dc_member_parser.add_argument('--ts-code', help='板块指数代码')
    dc_member_parser.add_argument('--con-code', help='成分股票代码')
    dc_member_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    dc_member_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 游资名录查询模式
    hm_list_parser = subparsers.add_parser('hm_list', help='查询游资名录')
    hm_list_parser.add_argument('--name', help='游资名称')
    hm_list_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 游资明细查询模式
    hm_detail_parser = subparsers.add_parser('hm_detail', help='查询游资每日交易明细')
    hm_detail_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    hm_detail_parser.add_argument('--ts-code', help='股票代码')
    hm_detail_parser.add_argument('--hm-name', help='游资名称')
    hm_detail_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    hm_detail_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    hm_detail_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 同花顺热榜查询模式
    ths_hot_parser = subparsers.add_parser('ths_hot', help='查询同花顺App热榜数据')
    ths_hot_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    ths_hot_parser.add_argument('--ts-code', help='TS代码')
    ths_hot_parser.add_argument('--market', help='热榜类型(热股、ETF、可转债、行业板块、概念板块、期货、港股、热基、美股)')
    ths_hot_parser.add_argument('--is-new', choices=['Y', 'N'], default='Y', help='是否最新')
    ths_hot_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 东方财富热榜查询模式
    dc_hot_parser = subparsers.add_parser('dc_hot', help='查询东方财富App热榜数据')
    dc_hot_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    dc_hot_parser.add_argument('--ts-code', help='TS代码')
    dc_hot_parser.add_argument('--market', help='类型(A股市场、ETF基金、港股市场、美股市场)')
    dc_hot_parser.add_argument('--hot-type', choices=['人气榜', '飙升榜'], help='热点类型')
    dc_hot_parser.add_argument('--is-new', choices=['Y', 'N'], default='Y', help='是否最新')
    dc_hot_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 指数基本信息查询模式
    index_basic_parser = subparsers.add_parser('index_basic', help='查询指数基础信息')
    index_basic_parser.add_argument('--ts-code', help='指数代码')
    index_basic_parser.add_argument('--name', help='指数简称')
    index_basic_parser.add_argument('--market', help='交易所或服务商，例如：SSE、SZSE、SW、MSCI等')
    index_basic_parser.add_argument('--publisher', help='发布商')
    index_basic_parser.add_argument('--category', help='指数类别')
    index_basic_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 指数成分和权重查询模式
    index_weight_parser = subparsers.add_parser('index_weight', help='查询指数成分和权重')
    index_weight_parser.add_argument('--index-code', required=True, help='指数代码')
    index_weight_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    index_weight_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    index_weight_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    index_weight_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 申万行业分类查询模式
    sw_industry_parser = subparsers.add_parser('sw_industry', help='查询申万行业分类')
    sw_industry_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 申万行业成分查询模式
    sw_member_parser = subparsers.add_parser('sw_member', help='查询申万行业成分')
    sw_member_parser.add_argument('--l1-code', help='一级行业代码')
    sw_member_parser.add_argument('--l2-code', help='二级行业代码')
    sw_member_parser.add_argument('--l3-code', help='三级行业代码')
    sw_member_parser.add_argument('--ts-code', help='股票代码')
    sw_member_parser.add_argument('--is-new', choices=['Y', 'N'], default='Y', help='是否最新')
    sw_member_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 申万行业日线行情查询模式
    sw_daily_parser = subparsers.add_parser('sw_daily', help='查询申万行业日线行情')
    sw_daily_parser.add_argument('--ts-code', help='行业代码')
    sw_daily_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    sw_daily_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    sw_daily_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    sw_daily_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 中信行业成分查询模式
    ci_member_parser = subparsers.add_parser('ci_member', help='查询中信行业成分')
    ci_member_parser.add_argument('--l1-code', help='一级行业代码')
    ci_member_parser.add_argument('--l2-code', help='二级行业代码')
    ci_member_parser.add_argument('--l3-code', help='三级行业代码')
    ci_member_parser.add_argument('--ts-code', help='股票代码')
    ci_member_parser.add_argument('--is-new', choices=['Y', 'N'], default='Y', help='是否最新')
    ci_member_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 中信行业指数行情查询模式
    ci_daily_parser = subparsers.add_parser('ci_daily', help='查询中信行业指数行情')
    ci_daily_parser.add_argument('--ts-code', help='行业代码')
    ci_daily_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    ci_daily_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    ci_daily_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    ci_daily_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 市场交易统计查询模式
    market_info_parser = subparsers.add_parser('market_info', help='查询交易所股票交易统计')
    market_info_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    market_info_parser.add_argument('--ts-code', help='板块代码')
    market_info_parser.add_argument('--exchange', choices=['SH', 'SZ'], help='股票市场')
    market_info_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    market_info_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    market_info_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 深圳市场每日交易概况查询模式
    sz_market_parser = subparsers.add_parser('sz_market', help='查询深圳市场每日交易概况')
    sz_market_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    sz_market_parser.add_argument('--ts-code', help='板块代码')
    sz_market_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    sz_market_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    sz_market_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 新闻快讯查询模式
    news_parser = subparsers.add_parser('news', help='查询主流新闻网站的快讯新闻数据')
    news_parser.add_argument('--start-date', required=True, help='开始日期(格式：2018-11-20 09:00:00)')
    news_parser.add_argument('--end-date', required=True, help='结束日期(格式：2018-11-20 22:00:00)')
    news_parser.add_argument('--src', required=True, choices=['sina', 'wallstreetcn', '10jqka', 'eastmoney', 'yuncaijing', 'fenghuang', 'jinrongjie'], help='新闻来源')
    news_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 上市公司公告查询模式
    announcement_parser = subparsers.add_parser('announcement', help='查询上市公司全量公告数据')
    announcement_parser.add_argument('--ts-code', help='股票代码')
    announcement_parser.add_argument('--ann-date', help='公告日期，格式YYYYMMDD')
    announcement_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    announcement_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    announcement_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 上交所e互动查询模式
    sh_irm_parser = subparsers.add_parser('sh_irm', help='查询上交所e互动董秘问答文本数据')
    sh_irm_parser.add_argument('--ts-code', help='股票代码')
    sh_irm_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    sh_irm_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    sh_irm_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    sh_irm_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    # 深证互动易查询模式
    sz_irm_parser = subparsers.add_parser('sz_irm', help='查询深证互动易数据')
    sz_irm_parser.add_argument('--ts-code', help='股票代码')
    sz_irm_parser.add_argument('--trade-date', help='交易日期，格式YYYYMMDD')
    sz_irm_parser.add_argument('--start-date', help='开始日期，格式YYYYMMDD')
    sz_irm_parser.add_argument('--end-date', help='结束日期，格式YYYYMMDD')
    sz_irm_parser.add_argument('--output', choices=['table', 'json', 'csv', 'excel'], default='table', help='输出格式')
    
    return parser.parse_args()

def print_dataframe(df, limit=None):
    """打印DataFrame"""
    if df is None or df.empty:
        print("没有数据")
        return
    
    # 显示所有列
    pd.set_option('display.max_columns', None)
    # 显示所有行
    if limit:
        print(df.head(limit))
    else:
        pd.set_option('display.max_rows', None)
        print(df)
    # 重置显示设置
    pd.reset_option('display.max_columns')
    pd.reset_option('display.max_rows')

def save_to_file(df, output_format, filename_prefix='output'):
    """保存DataFrame到文件"""
    if df is None or df.empty:
        print("没有数据可保存")
        return
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}"
    
    if output_format == 'csv':
        output_file = f"{filename}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
    elif output_format == 'json':
        output_file = f"{filename}.json"
        df.to_json(output_file, orient='records', force_ascii=False)
    elif output_format == 'excel':
        output_file = f"{filename}.xlsx"
        df.to_excel(output_file, index=False)
    else:
        print(f"不支持的输出格式: {output_format}")
        return
    
    print(f"数据已保存到 {output_file}")

def main():
    """主程序"""
    args = parse_args()
    analyzer = StockAnalyzer()
    
    try:
        if args.mode == 'today':
            result = analyze_today_stocks(
                top=args.top,
                sort_by=args.sort_by,
                order=args.order
            )
            print_dataframe(result, args.limit)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'today_market')
        
        elif args.mode == 'analyze':
            result = analyze_stock_history(
                ts_code=args.stock,
                start_date=args.start,
                end_date=args.end,
                ma_list=args.ma,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'stock_analysis_{args.stock}')
        
        elif args.mode == 'potential':
            result = analyze_potential_stocks(
                strategy=args.strategy,
                date=args.date,
                top=args.top,
                min_vol=args.min_vol,
                output_format=args.output
            )
            print_dataframe(result, args.limit)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'potential_stocks')
        
        elif args.mode == 'forecast':
            result = analyzer.analyze_forecast(
                period=args.period,
                type=args.type,
                top_n=args.limit
            )
            print_dataframe(result, args.limit)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'forecast_analysis')
        
        elif args.mode == 'express':
            result = analyzer.analyze_express(
                period=args.period,
                top_n=args.limit,
                min_yoy_profit=args.min_yoy
            )
            print_dataframe(result, args.limit)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'express_analysis')
        
        elif args.mode == 'dividend':
            result = analyzer.find_dividend_stocks(
                min_div_yield=args.min_yield,
                top_n=args.limit
            )
            print_dataframe(result, args.limit)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'high_dividend_stocks')
        
        elif args.mode == 'disclosure':
            result = analyzer.analyze_disclosure_date(
                end_date=args.period
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'disclosure_plan')
        
        elif args.mode == 'float':
            result = analyzer.analyze_share_float(
                start_date=args.start,
                end_date=args.end,
                min_ratio=args.min_ratio
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'share_float_analysis')
        
        elif args.mode == 'holder':
            result = analyzer.analyze_holdernumber_trend(
                ts_code=args.stock,
                start_date=args.start,
                end_date=args.end
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'holder_trend_{args.stock}')
        
        elif args.mode == 'holdertrade':
            result = analyzer.analyze_holdertrade(
                days=args.days,
                trade_type=args.trade_type,
                holder_type=args.holder_type
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'holdertrade_analysis')
        
        elif args.mode == 'report':
            result = analyzer.analyze_report_rc(
                trade_date=args.date,
                days=args.days
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'report_analysis')
        
        elif args.mode == 'chips':
            analyzer.analyze_chips(
                ts_code=args.stock,
                trade_date=args.date
            )
            # 筹码分析结果会自动保存为图片
        
        elif args.mode == 'factor':
            result = analyze_technical_factors(
                ts_code=args.ts_code,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'technical_factors_{args.ts_code}')
        
        elif args.mode == 'nineturn':
            result = analyze_nineturn(
                ts_code=args.ts_code,
                freq=args.freq,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'nineturn_{args.ts_code}')
        
        elif args.mode == 'auction':
            result = analyze_auction_data(
                ts_code=args.ts_code,
                auction_type=args.type,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'auction_{args.ts_code}')
        
        elif args.mode == 'dc_member':
            result = analyzer.analyze_dc_member(
                ts_code=args.ts_code,
                con_code=args.con_code,
                trade_date=args.trade_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'dc_member_{args.ts_code}')
        
        elif args.mode == 'hm_list':
            result = analyzer.analyze_hm_list(
                name=args.name,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'hm_list')
        
        elif args.mode == 'hm_detail':
            result = analyzer.analyze_hm_detail(
                trade_date=args.trade_date,
                ts_code=args.ts_code,
                hm_name=args.hm_name,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'hm_detail')
        
        elif args.mode == 'ths_hot':
            result = analyzer.analyze_ths_hot(
                trade_date=args.trade_date,
                ts_code=args.ts_code,
                market=args.market,
                is_new=args.is_new,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'ths_hot')
        
        elif args.mode == 'dc_hot':
            result = analyzer.analyze_dc_hot(
                trade_date=args.trade_date,
                ts_code=args.ts_code,
                market=args.market,
                hot_type=args.hot_type,
                is_new=args.is_new,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'dc_hot')
        
        elif args.mode == 'index_basic':
            result = analyzer.analyze_index_basic(
                ts_code=args.ts_code,
                name=args.name,
                market=args.market,
                publisher=args.publisher,
                category=args.category,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'index_basic')
        
        elif args.mode == 'index_weight':
            result = analyzer.analyze_index_weight(
                index_code=args.index_code,
                trade_date=args.trade_date,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'index_weight')
        
        elif args.mode == 'sw_industry':
            result = analyzer.analyze_sw_industry(
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'sw_industry')
        
        elif args.mode == 'sw_member':
            result = analyzer.analyze_sw_member(
                l1_code=args.l1_code,
                l2_code=args.l2_code,
                l3_code=args.l3_code,
                ts_code=args.ts_code,
                is_new=args.is_new,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'sw_member_{args.l1_code}_{args.l2_code}_{args.l3_code}')
        
        elif args.mode == 'sw_daily':
            result = analyzer.analyze_sw_daily(
                ts_code=args.ts_code,
                trade_date=args.trade_date,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'sw_daily_{args.ts_code}')
        
        elif args.mode == 'ci_member':
            result = analyzer.analyze_ci_member(
                l1_code=args.l1_code,
                l2_code=args.l2_code,
                l3_code=args.l3_code,
                ts_code=args.ts_code,
                is_new=args.is_new,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'ci_member_{args.l1_code}_{args.l2_code}_{args.l3_code}')
        
        elif args.mode == 'ci_daily':
            result = analyzer.analyze_ci_daily(
                ts_code=args.ts_code,
                trade_date=args.trade_date,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, f'ci_daily_{args.ts_code}')
        
        elif args.mode == 'market_info':
            result = analyzer.analyze_market_info(
                trade_date=args.trade_date,
                ts_code=args.ts_code,
                exchange=args.exchange,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'market_info')
        
        elif args.mode == 'sz_market':
            result = analyzer.analyze_sz_market(
                trade_date=args.trade_date,
                ts_code=args.ts_code,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'sz_market')
        
        elif args.mode == 'news':
            result = analyzer.analyze_news(
                start_date=args.start_date,
                end_date=args.end_date,
                src=args.src,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'news')
        
        elif args.mode == 'announcement':
            result = analyzer.analyze_announcement(
                ts_code=args.ts_code,
                ann_date=args.ann_date,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'announcement')
        
        elif args.mode == 'sh_irm':
            result = analyzer.analyze_sh_irm(
                ts_code=args.ts_code,
                trade_date=args.trade_date,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'sh_irm')
        
        elif args.mode == 'sz_irm':
            result = analyzer.analyze_sz_irm(
                ts_code=args.ts_code,
                trade_date=args.trade_date,
                start_date=args.start_date,
                end_date=args.end_date,
                output_format=args.output
            )
            print_dataframe(result)
            
            # 如果指定了输出格式，保存到文件
            if hasattr(args, 'output') and args.output:
                save_to_file(result, args.output, 'sz_irm')
        
        else:
            print("请指定运行模式")
    except Exception as e:
        print(f"运行出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 