#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import tushare as ts
import datetime
import time

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config import TUSHARE_TOKEN

# 初始化Tushare Pro接口
try:
    pro = ts.pro_api(TUSHARE_TOKEN)
    print("Tushare Pro API 连接成功")
except Exception as e:
    print(f"Tushare Pro API 连接失败: {e}")
    sys.exit(1)

# ===== 基础数据接口 =====
def get_stock_basics():
    """获取所有A股基本信息"""
    try:
        df = pro.stock_basic(exchange='', list_status='L', 
                             fields='ts_code,symbol,name,area,industry,list_date')
        return df
    except Exception as e:
        print(f"获取股票基本信息失败: {e}")
        return pd.DataFrame()

def get_trade_calendar(start_date, end_date):
    """获取交易日历
    
    Args:
        start_date (str): 开始日期，格式YYYYMMDD
        end_date (str): 结束日期，格式YYYYMMDD
        
    Returns:
        list: 交易日历数据列表
    """
    try:
        df = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
        return df[df.is_open == 1]['cal_date'].tolist()
    except Exception as e:
        print(f"获取交易日历失败: {e}")
        return []

def get_hs_const(hs_type='SH'):
    """获取沪深股通成分股
    
    Args:
        hs_type (str): 类型SH沪股通SZ深股通
    
    Returns:
        pd.DataFrame: 沪深股通成分股数据
    """
    try:
        df = pro.hs_const(hs_type=hs_type)
        return df
    except Exception as e:
        print(f"获取沪深股通成分股失败: {e}")
        return pd.DataFrame()

def get_stock_company(ts_code=None, exchange=None):
    """获取上市公司基本信息
    
    Args:
        ts_code (str): 股票代码
        exchange (str): 交易所代码，SSE上交所 SZSE深交所
    
    Returns:
        pd.DataFrame: 上市公司基本信息
    """
    try:
        df = pro.stock_company(ts_code=ts_code, exchange=exchange)
        return df
    except Exception as e:
        print(f"获取上市公司基本信息失败: {e}")
        return pd.DataFrame()

# ===== 行情数据接口 =====
def get_daily_data(ts_code, start_date, end_date):
    """获取股票日线数据
    
    Args:
        ts_code (str): 股票代码，如 000001.SZ
        start_date (str): 开始日期，格式YYYYMMDD
        end_date (str): 结束日期，格式YYYYMMDD
        
    Returns:
        pd.DataFrame: 股票日线数据
    """
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取{ts_code}日线数据失败: {e}")
        return pd.DataFrame()

def get_minute_data(ts_code, start_time, end_time, freq='1min'):
    """获取股票分钟线数据
    
    Args:
        ts_code (str): 股票代码，如 000001.SZ
        start_time (str): 开始时间，格式YYYY-MM-DD HH:MM:SS
        end_time (str): 结束时间，格式YYYY-MM-DD HH:MM:SS
        freq (str): 分钟频度（1min/5min/15min/30min/60min）
        
    Returns:
        pd.DataFrame: 股票分钟线数据
    """
    try:
        df = pro.stk_mins(ts_code=ts_code, start_date=start_time, end_date=end_time, freq=freq)
        return df
    except Exception as e:
        print(f"获取{ts_code}分钟线数据失败: {e}")
        return pd.DataFrame()

def get_pro_bar_data(ts_code, start_date, end_date, adj=None, freq='D', ma=None, factors=None):
    """获取复权行情数据
    
    Args:
        ts_code (str): 股票代码，如 000001.SZ
        start_date (str): 开始日期，格式YYYYMMDD
        end_date (str): 结束日期，格式YYYYMMDD
        adj (str): 复权类型(None/qfq/hfq)
        freq (str): 频率(D日/W周/M月/min分钟)
        ma (list): 均线周期，如 [5, 10, 20]
        factors (list): 股票因子 tor换手率 vr量比
        
    Returns:
        pd.DataFrame: 复权行情数据
    """
    try:
        df = ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date,
                      adj=adj, freq=freq, ma=ma, factors=factors)
        return df
    except Exception as e:
        print(f"获取{ts_code}复权行情数据失败: {e}")
        return pd.DataFrame()

def get_weekly_data(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取周线行情
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 周线行情数据
    """
    try:
        df = pro.weekly(ts_code=ts_code, trade_date=trade_date, 
                      start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取周线行情失败: {e}")
        return pd.DataFrame()

def get_monthly_data(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取月线行情
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 月线行情数据
    """
    try:
        df = pro.monthly(ts_code=ts_code, trade_date=trade_date, 
                       start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取月线行情失败: {e}")
        return pd.DataFrame()

def get_today_all():
    """获取当日所有股票行情"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    try:
        df = pro.daily(trade_date=today)
        return df
    except Exception as e:
        print(f"获取当日行情数据失败: {e}")
        return pd.DataFrame()

def get_daily_basic(trade_date=None, ts_code=None):
    """获取每日指标
    
    Args:
        trade_date (str, optional): 交易日期，格式YYYYMMDD
        ts_code (str, optional): 股票代码，格式000001.SZ
        
    Returns:
        pd.DataFrame: 每日指标数据
    """
    try:
        df = pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
        return df
    except Exception as e:
        print(f"获取每日指标数据失败: {e}")
        return pd.DataFrame()

def get_stock_limit(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取涨跌停价格
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 涨跌停价格数据
    """
    try:
        df = pro.stk_limit(ts_code=ts_code, trade_date=trade_date,
                         start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取涨跌停价格失败: {e}")
        return pd.DataFrame()

def get_limit_list(trade_date):
    """获取涨跌停股票列表
    
    Args:
        trade_date (str): 交易日期，格式YYYYMMDD
        
    Returns:
        pd.DataFrame: 涨跌停股票数据
    """
    try:
        df = pro.limit_list(trade_date=trade_date)
        return df
    except Exception as e:
        print(f"获取涨跌停板数据失败: {e}")
        return pd.DataFrame()

def get_index_daily(ts_code, start_date, end_date):
    """获取指数日线数据
    
    Args:
        ts_code (str): 指数代码，如 000001.SH
        start_date (str): 开始日期，格式YYYYMMDD
        end_date (str): 结束日期，格式YYYYMMDD
        
    Returns:
        pd.DataFrame: 指数日线数据
    """
    try:
        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取指数{ts_code}日线数据失败: {e}")
        return pd.DataFrame()

def get_suspend_data(ts_code=None, trade_date=None, start_date=None, end_date=None, suspend_type=None):
    """获取停复牌信息
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        suspend_type (str): 停复牌类型：S-停牌,R-复牌
        
    Returns:
        pd.DataFrame: 停复牌信息
    """
    try:
        df = pro.suspend_d(ts_code=ts_code, trade_date=trade_date,
                         start_date=start_date, end_date=end_date,
                         suspend_type=suspend_type)
        return df
    except Exception as e:
        print(f"获取停复牌信息失败: {e}")
        return pd.DataFrame()

# ===== 沪深港通数据 =====
def get_hsgt_top10(trade_date=None, ts_code=None, start_date=None, end_date=None, market_type=None):
    """获取沪深股通十大成交股
    
    Args:
        trade_date (str): 交易日期
        ts_code (str): 股票代码
        start_date (str): 开始日期
        end_date (str): 结束日期
        market_type (str): 市场类型（1：沪市 3：深市）
        
    Returns:
        pd.DataFrame: 沪深股通十大成交股数据
    """
    try:
        df = pro.hsgt_top10(trade_date=trade_date, ts_code=ts_code,
                          start_date=start_date, end_date=end_date,
                          market_type=market_type)
        return df
    except Exception as e:
        print(f"获取沪深股通十大成交股失败: {e}")
        return pd.DataFrame()

def get_ggt_top10(trade_date=None, ts_code=None, start_date=None, end_date=None, market_type=None):
    """获取港股通十大成交股
    
    Args:
        trade_date (str): 交易日期
        ts_code (str): 股票代码
        start_date (str): 开始日期
        end_date (str): 结束日期
        market_type (str): 市场类型 2：港股通（沪） 4：港股通（深）
        
    Returns:
        pd.DataFrame: 港股通十大成交股数据
    """
    try:
        df = pro.ggt_top10(trade_date=trade_date, ts_code=ts_code,
                         start_date=start_date, end_date=end_date,
                         market_type=market_type)
        return df
    except Exception as e:
        print(f"获取港股通十大成交股失败: {e}")
        return pd.DataFrame()

def get_ggt_daily(trade_date=None, start_date=None, end_date=None):
    """获取港股通每日成交统计
    
    Args:
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 港股通每日成交统计数据
    """
    try:
        df = pro.ggt_daily(trade_date=trade_date, start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取港股通每日成交统计失败: {e}")
        return pd.DataFrame()

# ===== 财务数据接口 =====
def get_income(ts_code=None, ann_date=None, start_date=None, end_date=None, period=None, report_type=None, comp_type=None):
    """获取利润表
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 公告开始日期
        end_date (str): 公告结束日期
        period (str): 报告期(季度最后一天的日期，如20171231)
        report_type (str): 报告类型
        comp_type (str): 公司类型(1一般工商业2银行3保险4证券)
        
    Returns:
        pd.DataFrame: 利润表数据
    """
    try:
        df = pro.income(ts_code=ts_code, ann_date=ann_date,
                      start_date=start_date, end_date=end_date,
                      period=period, report_type=report_type,
                      comp_type=comp_type)
        return df
    except Exception as e:
        print(f"获取利润表失败: {e}")
        return pd.DataFrame()

def get_balancesheet(ts_code=None, ann_date=None, start_date=None, end_date=None, period=None, report_type=None, comp_type=None):
    """获取资产负债表
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 公告开始日期
        end_date (str): 公告结束日期
        period (str): 报告期(季度最后一天的日期，如20171231)
        report_type (str): 报告类型
        comp_type (str): 公司类型(1一般工商业2银行3保险4证券)
        
    Returns:
        pd.DataFrame: 资产负债表数据
    """
    try:
        df = pro.balancesheet(ts_code=ts_code, ann_date=ann_date,
                            start_date=start_date, end_date=end_date,
                            period=period, report_type=report_type,
                            comp_type=comp_type)
        return df
    except Exception as e:
        print(f"获取资产负债表失败: {e}")
        return pd.DataFrame()

def get_cashflow(ts_code=None, ann_date=None, start_date=None, end_date=None, period=None, report_type=None, comp_type=None):
    """获取现金流量表
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 公告开始日期
        end_date (str): 公告结束日期
        period (str): 报告期(季度最后一天的日期，如20171231)
        report_type (str): 报告类型
        comp_type (str): 公司类型(1一般工商业2银行3保险4证券)
        
    Returns:
        pd.DataFrame: 现金流量表数据
    """
    try:
        df = pro.cashflow(ts_code=ts_code, ann_date=ann_date,
                        start_date=start_date, end_date=end_date,
                        period=period, report_type=report_type,
                        comp_type=comp_type)
        return df
    except Exception as e:
        print(f"获取现金流量表失败: {e}")
        return pd.DataFrame()

def get_forecast(ts_code=None, ann_date=None, start_date=None, end_date=None, period=None, type=None):
    """获取业绩预告数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 公告开始日期
        end_date (str): 公告结束日期
        period (str): 报告期(每个季度最后一天的日期，如20171231)
        type (str): 预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)
        
    Returns:
        pd.DataFrame: 业绩预告数据
    """
    try:
        df = pro.forecast(ts_code=ts_code, ann_date=ann_date, 
                        start_date=start_date, end_date=end_date, 
                        period=period, type=type)
        return df
    except Exception as e:
        print(f"获取业绩预告数据失败: {e}")
        return pd.DataFrame()

def get_express(ts_code=None, ann_date=None, start_date=None, end_date=None, period=None):
    """获取业绩快报数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 公告开始日期
        end_date (str): 公告结束日期
        period (str): 报告期(每个季度最后一天的日期，如20171231)
        
    Returns:
        pd.DataFrame: 业绩快报数据
    """
    try:
        df = pro.express(ts_code=ts_code, ann_date=ann_date, 
                       start_date=start_date, end_date=end_date, 
                       period=period)
        return df
    except Exception as e:
        print(f"获取业绩快报数据失败: {e}")
        return pd.DataFrame()

def get_dividend(ts_code=None, ann_date=None, record_date=None, ex_date=None, imp_ann_date=None):
    """获取分红送股数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        record_date (str): 股权登记日
        ex_date (str): 除权除息日
        imp_ann_date (str): 实施公告日
        
    Returns:
        pd.DataFrame: 分红送股数据
    """
    try:
        df = pro.dividend(ts_code=ts_code, ann_date=ann_date, 
                        record_date=record_date, ex_date=ex_date, 
                        imp_ann_date=imp_ann_date)
        return df
    except Exception as e:
        print(f"获取分红送股数据失败: {e}")
        return pd.DataFrame()

def get_fina_indicator(ts_code=None, ann_date=None, start_date=None, end_date=None, period=None):
    """获取财务指标数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 报告期开始日期
        end_date (str): 报告期结束日期
        period (str): 报告期(每个季度最后一天的日期，如20171231)
        
    Returns:
        pd.DataFrame: 财务指标数据
    """
    try:
        df = pro.fina_indicator(ts_code=ts_code, ann_date=ann_date, 
                              start_date=start_date, end_date=end_date, 
                              period=period)
        return df
    except Exception as e:
        print(f"获取财务指标数据失败: {e}")
        return pd.DataFrame()

def get_disclosure_date(ts_code=None, end_date=None, pre_date=None, actual_date=None):
    """获取财报披露计划日期
    
    Args:
        ts_code (str): 股票代码
        end_date (str): 财报周期
        pre_date (str): 计划披露日期
        actual_date (str): 实际披露日期
        
    Returns:
        pd.DataFrame: 财报披露计划数据
    """
    try:
        df = pro.disclosure_date(ts_code=ts_code, end_date=end_date, 
                               pre_date=pre_date, actual_date=actual_date)
        return df
    except Exception as e:
        print(f"获取财报披露计划数据失败: {e}")
        return pd.DataFrame()

def get_concept(src='ts'):
    """获取概念股分类
    
    Args:
        src (str): 来源，默认为ts
        
    Returns:
        pd.DataFrame: 概念股分类数据
    """
    try:
        df = pro.concept(src=src)
        return df
    except Exception as e:
        print(f"获取概念股分类数据失败: {e}")
        return pd.DataFrame()

def get_concept_detail(id=None, ts_code=None):
    """获取概念股分类明细
    
    Args:
        id (str): 概念分类ID
        ts_code (str): 股票代码
        
    Returns:
        pd.DataFrame: 概念股分类明细数据
    """
    try:
        df = pro.concept_detail(id=id, ts_code=ts_code)
        return df
    except Exception as e:
        print(f"获取概念股分类明细数据失败: {e}")
        return pd.DataFrame()

def get_share_float(ts_code=None, ann_date=None, float_date=None, start_date=None, end_date=None):
    """获取限售股解禁数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        float_date (str): 解禁日期
        start_date (str): 解禁开始日期
        end_date (str): 解禁结束日期
        
    Returns:
        pd.DataFrame: 限售股解禁数据
    """
    try:
        df = pro.share_float(ts_code=ts_code, ann_date=ann_date, 
                           float_date=float_date, start_date=start_date, 
                           end_date=end_date)
        return df
    except Exception as e:
        print(f"获取限售股解禁数据失败: {e}")
        return pd.DataFrame()

def get_stk_holdernumber(ts_code=None, ann_date=None, end_date=None, start_date=None, end_date2=None):
    """获取股东人数数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        end_date (str): 截止日期
        start_date (str): 公告开始日期
        end_date2 (str): 公告结束日期
        
    Returns:
        pd.DataFrame: 股东人数数据
    """
    try:
        df = pro.stk_holdernumber(ts_code=ts_code, ann_date=ann_date, 
                                end_date=end_date, start_date=start_date, 
                                end_date=end_date2)
        return df
    except Exception as e:
        print(f"获取股东人数数据失败: {e}")
        return pd.DataFrame()

def get_stk_holdertrade(ts_code=None, ann_date=None, start_date=None, end_date=None, trade_type=None, holder_type=None):
    """获取股东增减持数据
    
    Args:
        ts_code (str): 股票代码
        ann_date (str): 公告日期
        start_date (str): 公告开始日期
        end_date (str): 公告结束日期
        trade_type (str): 交易类型(IN增持 DE减持)
        holder_type (str): 股东类型(C公司 P个人 G高管)
        
    Returns:
        pd.DataFrame: 股东增减持数据
    """
    try:
        df = pro.stk_holdertrade(ts_code=ts_code, ann_date=ann_date, 
                               start_date=start_date, end_date=end_date, 
                               trade_type=trade_type, holder_type=holder_type)
        return df
    except Exception as e:
        print(f"获取股东增减持数据失败: {e}")
        return pd.DataFrame()

def get_report_rc(ts_code=None, report_date=None, start_date=None, end_date=None):
    """获取卖方盈利预测数据
    
    Args:
        ts_code (str): 股票代码
        report_date (str): 报告日期
        start_date (str): 报告开始日期
        end_date (str): 报告结束日期
        
    Returns:
        pd.DataFrame: 卖方盈利预测数据
    """
    try:
        df = pro.report_rc(ts_code=ts_code, report_date=report_date, 
                         start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取卖方盈利预测数据失败: {e}")
        return pd.DataFrame()

def get_cyq_perf(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取每日筹码及胜率数据
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 每日筹码及胜率数据
    """
    try:
        df = pro.cyq_perf(ts_code=ts_code, trade_date=trade_date, 
                        start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取每日筹码及胜率数据失败: {e}")
        return pd.DataFrame()

def get_cyq_chips(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取每日筹码分布数据
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 每日筹码分布数据
    """
    try:
        df = pro.cyq_chips(ts_code=ts_code, trade_date=trade_date, 
                         start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取每日筹码分布数据失败: {e}")
        return pd.DataFrame()

def get_stock_list_by_date(date):
    """获取指定日期的股票列表"""
    try:
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return pd.DataFrame()

# ===== 技术因子相关接口 =====
def get_stk_factor(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取股票每日技术面因子数据
    
    Args:
        ts_code (str, optional): 股票代码，如 000001.SZ
        trade_date (str, optional): 交易日期，格式YYYYMMDD
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
            
    Returns:
        pd.DataFrame: 包含以下字段:
            ts_code: 股票代码
            trade_date: 交易日期
            close: 收盘价
            open: 开盘价
            high: 最高价
            low: 最低价
            pre_close: 昨收价
            change: 涨跌额
            pct_change: 涨跌幅
            vol: 成交量 
            amount: 成交额
            adj_factor: 复权因子
            open_hfq: 开盘价后复权
            open_qfq: 开盘价前复权
            close_hfq: 收盘价后复权
            close_qfq: 收盘价前复权
            high_hfq: 最高价后复权
            high_qfq: 最高价前复权
            low_hfq: 最低价后复权
            low_qfq: 最低价前复权
            pre_close_hfq: 昨收价后复权
            pre_close_qfq: 昨收价前复权
            macd_dif: MACD_DIF
            macd_dea: MACD_DEA
            macd: MACD
            kdj_k: KDJ_K
            kdj_d: KDJ_D
            kdj_j: KDJ_J
            rsi_6: RSI_6
            rsi_12: RSI_12
            rsi_24: RSI_24
            boll_upper: BOLL_UPPER
            boll_mid: BOLL_MID
            boll_lower: BOLL_LOWER
            cci: CCI
            macd_dif_h1: MACD_DIF (1h)
            macd_dea_h1: MACD_DEA (1h)
            macd_h1: MACD (1h)
            kdj_k_h1: KDJ_K (1h)
            ma5: MA5
            ma10: MA10
            ma20: MA20
            ma30: MA30
            ma60: MA60
            ma120: MA120
            ma250: MA250
            max_dd: 最大回撤
            bias: 乖离率
            bias_2: 乖离率_2
            vol_ratio: 量比
            pe: 市盈率
            pe_ttm: 市盈率TTM
            pb: 市净率
            ps: 市销率
            ps_ttm: 市销率TTM
            dv_ratio: 股息率
            dv_ttm: 股息率TTM
            net_profit_ratio: 净利率
            roe: ROE
            roe_ttm: ROE TTM
            roe_yearly: 年化ROE
            roa: ROA
            npta: 净利润/总资产
            roic: 投入资本回报率
            roe_diluted: 摊薄净资产收益率
            roa_diluted: 摊薄总资产收益率
            ebit: 息税前利润
            ebitda: EBITDA
            fcff: 企业自由现金流量
            fcfe: 股权自由现金流量
            current_ratio: 流动比率
            quick_ratio: 速动比率
            debt_to_assets: 资产负债率
            op_to_total_revenue: 营业利润/营业总收入
            op_to_tp: 营业利润/利润总额
            roic_yearly: 年化投入资本回报率
            total_fa_trun: 固定资产合计周转率
            profit_to_op: 利润总额/营业收入
            q_dtprofit_to_profit: 扣除非经常损益后的净利润/净利润
            q_profit_to_total_revenue: 净利润/营业总收入
            q_sales_yoy: 营业收入同比增长率
            q_op_qoq: 营业利润环比增长率
            equity_yoy: 净资产同比增长
    """
    try:
        # 构建查询参数
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # 查询数据
        df = pro.stk_factor(**params)
        return df
    
    except Exception as e:
        print(f"获取股票技术面因子数据失败: {e}")
        return pd.DataFrame()

def get_stk_factor_pro(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取股票技术面因子专业版数据
    
    Args:
        ts_code (str, optional): 股票代码，如 000001.SZ
        trade_date (str, optional): 交易日期，格式YYYYMMDD
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
            
    Returns:
        pd.DataFrame: 包含技术因子专业版数据
    """
    try:
        # 构建查询参数
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # 查询数据
        df = pro.stk_factor_pro(**params)
        return df
    
    except Exception as e:
        print(f"获取股票技术面因子专业版数据失败: {e}")
        return pd.DataFrame()

def get_stk_nineturn(ts_code=None, trade_date=None, freq=None, start_date=None, end_date=None):
    """获取神奇九转指标数据
    
    Args:
        ts_code (str, optional): 股票代码，如 000001.SZ
        trade_date (str, optional): 交易日期，格式YYYYMMDD
        freq (str, optional): 周期类型 (D-日, W-周, M-月)
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
            
    Returns:
        pd.DataFrame: 包含以下字段:
            ts_code: 股票代码
            trade_date: 交易日期
            freq: 周期类型
            nturn_value: 神奇九转值
            nt_remark: 神奇九转级别
            nt_signal: 神奇九转信号
    """
    try:
        # 构建查询参数
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if freq:
            params['freq'] = freq
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # 查询数据
        df = pro.stk_nineturn(**params)
        return df
    
    except Exception as e:
        print(f"获取神奇九转指标数据失败: {e}")
        return pd.DataFrame()

def get_stk_auction_o(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取股票开盘集合竞价数据
    
    Args:
        ts_code (str, optional): 股票代码，如 000001.SZ
        trade_date (str, optional): 交易日期，格式YYYYMMDD
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
            
    Returns:
        pd.DataFrame: 包含开盘集合竞价数据
    """
    try:
        # 构建查询参数
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # 查询数据
        df = pro.stk_auction_o(**params)
        return df
    
    except Exception as e:
        print(f"获取股票开盘集合竞价数据失败: {e}")
        return pd.DataFrame()

def get_stk_auction_c(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取股票收盘集合竞价数据
    
    Args:
        ts_code (str, optional): 股票代码，如 000001.SZ
        trade_date (str, optional): 交易日期，格式YYYYMMDD
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
            
    Returns:
        pd.DataFrame: 包含收盘集合竞价数据
    """
    try:
        # 构建查询参数
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # 查询数据
        df = pro.stk_auction_c(**params)
        return df
    
    except Exception as e:
        print(f"获取股票收盘集合竞价数据失败: {e}")
        return pd.DataFrame()

# ===== 资金流向相关接口 =====
def get_moneyflow(ts_code=None, trade_date=None, start_date=None, end_date=None, fields=None):
    """获取个股资金流向数据
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 资金流向数据
    """
    try:
        df = pro.moneyflow(ts_code=ts_code, trade_date=trade_date, 
                         start_date=start_date, end_date=end_date, 
                         fields=fields)
        return df
    except Exception as e:
        print(f"获取个股资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_ths(ts_code=None, trade_date=None, start_date=None, end_date=None, fields=None):
    """获取同花顺个股资金流向数据
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 同花顺资金流向数据
    """
    try:
        df = pro.moneyflow_ths(ts_code=ts_code, trade_date=trade_date, 
                             start_date=start_date, end_date=end_date, 
                             fields=fields)
        return df
    except Exception as e:
        print(f"获取同花顺个股资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_dc(ts_code=None, trade_date=None, start_date=None, end_date=None, fields=None):
    """获取东方财富个股资金流向数据
    
    Args:
        ts_code (str): 股票代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 东方财富资金流向数据
    """
    try:
        df = pro.moneyflow_dc(ts_code=ts_code, trade_date=trade_date, 
                            start_date=start_date, end_date=end_date, 
                            fields=fields)
        return df
    except Exception as e:
        print(f"获取东方财富个股资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_hsgt(trade_date=None, start_date=None, end_date=None, fields=None):
    """获取沪深港通资金流向数据
    
    Args:
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 沪深港通资金流向数据
    """
    try:
        df = pro.moneyflow_hsgt(trade_date=trade_date, 
                              start_date=start_date, end_date=end_date, 
                              fields=fields)
        return df
    except Exception as e:
        print(f"获取沪深港通资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_ind_ths(ts_code=None, trade_date=None, start_date=None, end_date=None, fields=None):
    """获取同花顺行业资金流向数据
    
    Args:
        ts_code (str): 行业代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 同花顺行业资金流向数据
    """
    try:
        df = pro.moneyflow_ind_ths(ts_code=ts_code, trade_date=trade_date, 
                                 start_date=start_date, end_date=end_date, 
                                 fields=fields)
        return df
    except Exception as e:
        print(f"获取同花顺行业资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_cnt_ths(ts_code=None, trade_date=None, start_date=None, end_date=None, fields=None):
    """获取同花顺概念板块资金流向数据
    
    Args:
        ts_code (str): 板块代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 同花顺概念板块资金流向数据
    """
    try:
        df = pro.moneyflow_cnt_ths(ts_code=ts_code, trade_date=trade_date, 
                                 start_date=start_date, end_date=end_date, 
                                 fields=fields)
        return df
    except Exception as e:
        print(f"获取同花顺概念板块资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_ind_dc(ts_code=None, trade_date=None, start_date=None, end_date=None, content_type=None, fields=None):
    """获取东方财富概念及行业板块资金流向数据
    
    Args:
        ts_code (str): 板块代码
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        content_type (str): 资金类型(行业、概念、地域)
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 东方财富板块资金流向数据
    """
    try:
        df = pro.moneyflow_ind_dc(ts_code=ts_code, trade_date=trade_date, 
                                start_date=start_date, end_date=end_date, 
                                content_type=content_type, fields=fields)
        return df
    except Exception as e:
        print(f"获取东方财富板块资金流向数据失败: {e}")
        return pd.DataFrame()

def get_moneyflow_mkt_dc(trade_date=None, start_date=None, end_date=None, fields=None):
    """获取东方财富大盘资金流向数据
    
    Args:
        trade_date (str): 交易日期
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 东方财富大盘资金流向数据
    """
    try:
        df = pro.moneyflow_mkt_dc(trade_date=trade_date, 
                                start_date=start_date, end_date=end_date, 
                                fields=fields)
        return df
    except Exception as e:
        print(f"获取东方财富大盘资金流向数据失败: {e}")
        return pd.DataFrame()

# ===== 涨跌停板相关接口 =====
def get_limit_list_ths(trade_date=None, ts_code=None, limit_type=None, market=None, 
                      start_date=None, end_date=None, fields=None):
    """获取同花顺涨跌停板单数据
    
    Args:
        trade_date (str): 交易日期
        ts_code (str): 股票代码
        limit_type (str): 涨停池、连板池、冲刺涨停、炸板池、跌停池
        market (str): HS-沪深主板 GEM-创业板 STAR-科创板
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: 同花顺涨跌停板单数据
    """
    try:
        df = pro.limit_list_ths(trade_date=trade_date, ts_code=ts_code, 
                              limit_type=limit_type, market=market, 
                              start_date=start_date, end_date=end_date, 
                              fields=fields)
        return df
    except Exception as e:
        print(f"获取同花顺涨跌停板单数据失败: {e}")
        return pd.DataFrame()

def get_limit_list_d(trade_date=None, ts_code=None, limit_type=None, exchange=None, 
                    start_date=None, end_date=None, fields=None):
    """获取A股每日涨跌停、炸板数据情况
    
    Args:
        trade_date (str): 交易日期
        ts_code (str): 股票代码
        limit_type (str): 涨跌停类型（U涨停D跌停Z炸板）
        exchange (str): 交易所（SH上交所SZ深交所BJ北交所）
        start_date (str): 开始日期
        end_date (str): 结束日期
        fields (str): 指定字段，如不指定，则返回所有字段
        
    Returns:
        pd.DataFrame: A股每日涨跌停、炸板数据
    """
    try:
        df = pro.limit_list_d(trade_date=trade_date, ts_code=ts_code, 
                            limit_type=limit_type, exchange=exchange, 
                            start_date=start_date, end_date=end_date, 
                            fields=fields)
        return df
    except Exception as e:
        print(f"获取A股每日涨跌停、炸板数据失败: {e}")
        return pd.DataFrame()

def get_limit_step(trade_date=None, ts_code=None, start_date=None, end_date=None, nums=None):
    """获取每天连板个数晋级的股票
    
    Args:
        trade_date (str): 交易日期
        ts_code (str): 股票代码
        start_date (str): 开始日期
        end_date (str): 结束日期
        nums (str): 连板次数，支持多个输入，例如nums='2,3'
        
    Returns:
        pd.DataFrame: 连板天梯数据
    """
    try:
        df = pro.limit_step(trade_date=trade_date, ts_code=ts_code, 
                          start_date=start_date, end_date=end_date, 
                          nums=nums)
        return df
    except Exception as e:
        print(f"获取连板天梯数据失败: {e}")
        return pd.DataFrame()

def get_limit_cpt_list(trade_date=None, ts_code=None, start_date=None, end_date=None):
    """获取每天涨停股票最多最强的概念板块
    
    Args:
        trade_date (str): 交易日期
        ts_code (str): 板块代码
        start_date (str): 开始日期
        end_date (str): 结束日期
        
    Returns:
        pd.DataFrame: 最强板块统计数据
    """
    try:
        df = pro.limit_cpt_list(trade_date=trade_date, ts_code=ts_code, 
                              start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"获取最强板块统计数据失败: {e}")
        return pd.DataFrame()

def get_stock_list_by_date(date):
    """获取指定日期的股票列表"""
    try:
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return pd.DataFrame()

# ===== 东方财富板块成分 =====
def get_dc_member(ts_code=None, con_code=None, trade_date=None):
    """获取东方财富板块每日成分数据
    
    Args:
        ts_code (str, optional): 板块指数代码
        con_code (str, optional): 成分股票代码
        trade_date (str, optional): 交易日期（YYYYMMDD格式）
        
    Returns:
        pd.DataFrame: 板块成分数据，包含以下字段:
            trade_date: 交易日期
            ts_code: 概念代码
            con_code: 成分代码
            name: 成分股名称
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if con_code:
            params['con_code'] = con_code
        if trade_date:
            params['trade_date'] = trade_date
            
        df = pro.dc_member(**params)
        return df
    except Exception as e:
        print(f"获取东方财富板块成分数据失败: {e}")
        return pd.DataFrame()

# ===== 游资相关接口 =====
def get_hm_list(name=None):
    """获取游资分类名录信息
    
    Args:
        name (str, optional): 游资名称
        
    Returns:
        pd.DataFrame: 游资名录数据，包含以下字段:
            name: 游资名称
            desc: 说明
            orgs: 关联机构
    """
    try:
        params = {}
        if name:
            params['name'] = name
            
        df = pro.hm_list(**params)
        return df
    except Exception as e:
        print(f"获取游资分类名录信息失败: {e}")
        return pd.DataFrame()

def get_hm_detail(trade_date=None, ts_code=None, hm_name=None, start_date=None, end_date=None):
    """获取每日游资交易明细
    
    Args:
        trade_date (str, optional): 交易日期(YYYYMMDD)
        ts_code (str, optional): 股票代码
        hm_name (str, optional): 游资名称
        start_date (str, optional): 开始日期(YYYYMMDD)
        end_date (str, optional): 结束日期(YYYYMMDD)
        
    Returns:
        pd.DataFrame: 游资交易明细数据，包含以下字段:
            trade_date: 交易日期
            ts_code: 股票代码
            ts_name: 股票名称
            buy_amount: 买入金额（元）
            sell_amount: 卖出金额（元）
            net_amount: 净买卖（元）
            hm_name: 游资名称
            hm_orgs: 关联机构（一般为营业部或机构专用）
            tag: 标签
    """
    try:
        params = {}
        if trade_date:
            params['trade_date'] = trade_date
        if ts_code:
            params['ts_code'] = ts_code
        if hm_name:
            params['hm_name'] = hm_name
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.hm_detail(**params)
        return df
    except Exception as e:
        print(f"获取每日游资交易明细失败: {e}")
        return pd.DataFrame()

# ===== 热榜数据 =====
def get_ths_hot(trade_date=None, ts_code=None, market=None, is_new=None):
    """获取同花顺App热榜数据
    
    Args:
        trade_date (str, optional): 交易日期
        ts_code (str, optional): TS代码
        market (str, optional): 热榜类型(热股、ETF、可转债、行业板块、概念板块、期货、港股、热基、美股)
        is_new (str, optional): 是否最新（默认Y，N为盘中和盘后阶段采集）
        
    Returns:
        pd.DataFrame: 同花顺热榜数据，包含以下字段:
            trade_date: 交易日期
            data_type: 数据类型
            ts_code: 股票代码
            ts_name: 股票名称
            rank: 排行
            pct_change: 涨跌幅%
            current_price: 当前价格
            concept: 标签
            rank_reason: 上榜解读
            hot: 热度值
            rank_time: 排行榜获取时间
    """
    try:
        params = {}
        if trade_date:
            params['trade_date'] = trade_date
        if ts_code:
            params['ts_code'] = ts_code
        if market:
            params['market'] = market
        if is_new is not None:
            params['is_new'] = is_new
            
        df = pro.ths_hot(**params)
        return df
    except Exception as e:
        print(f"获取同花顺App热榜数据失败: {e}")
        return pd.DataFrame()

def get_dc_hot(trade_date=None, ts_code=None, market=None, hot_type=None, is_new=None):
    """获取东方财富App热榜数据
    
    Args:
        trade_date (str, optional): 交易日期
        ts_code (str, optional): TS代码
        market (str, optional): 类型(A股市场、ETF基金、港股市场、美股市场)
        hot_type (str, optional): 热点类型(人气榜、飙升榜)
        is_new (str, optional): 是否最新（默认Y，N为盘中和盘后阶段采集）
        
    Returns:
        pd.DataFrame: 东方财富热榜数据，包含以下字段:
            trade_date: 交易日期
            data_type: 数据类型
            ts_code: 股票代码
            ts_name: 股票名称
            rank: 排行或者热度
            pct_change: 涨跌幅%
            current_price: 当前价
            rank_time: 排行榜获取时间
    """
    try:
        params = {}
        if trade_date:
            params['trade_date'] = trade_date
        if ts_code:
            params['ts_code'] = ts_code
        if market:
            params['market'] = market
        if hot_type:
            params['hot_type'] = hot_type
        if is_new is not None:
            params['is_new'] = is_new
            
        df = pro.dc_hot(**params)
        return df
    except Exception as e:
        print(f"获取东方财富App热榜数据失败: {e}")
        return pd.DataFrame()

# ===== 指数相关接口 =====
def get_index_basic(ts_code=None, name=None, market=None, publisher=None, category=None):
    """获取指数基础信息
    
    Args:
        ts_code (str, optional): 指数代码
        name (str, optional): 指数简称
        market (str, optional): 交易所或服务商(默认SSE)
        publisher (str, optional): 发布商
        category (str, optional): 指数类别
        
    Returns:
        pd.DataFrame: 指数基础信息数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if name:
            params['name'] = name
        if market:
            params['market'] = market
        if publisher:
            params['publisher'] = publisher
        if category:
            params['category'] = category
            
        df = pro.index_basic(**params)
        return df
    except Exception as e:
        print(f"获取指数基础信息失败: {e}")
        return pd.DataFrame()

def get_index_weekly(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取指数周线行情
    
    Args:
        ts_code (str, optional): TS代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 指数周线行情数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.index_weekly(**params)
        return df
    except Exception as e:
        print(f"获取指数周线行情失败: {e}")
        return pd.DataFrame()

def get_index_monthly(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取指数月线行情
    
    Args:
        ts_code (str, optional): TS代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 指数月线行情数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.index_monthly(**params)
        return df
    except Exception as e:
        print(f"获取指数月线行情失败: {e}")
        return pd.DataFrame()

def get_index_weight(index_code, trade_date=None, start_date=None, end_date=None):
    """获取各类指数成分和权重
    
    Args:
        index_code (str): 指数代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 指数成分和权重数据
    """
    try:
        params = {
            'index_code': index_code
        }
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.index_weight(**params)
        return df
    except Exception as e:
        print(f"获取指数成分和权重失败: {e}")
        return pd.DataFrame()

def get_index_dailybasic(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取大盘指数每日指标数据
    
    Args:
        ts_code (str, optional): TS代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 大盘指数每日指标数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.index_dailybasic(**params)
        return df
    except Exception as e:
        print(f"获取大盘指数每日指标数据失败: {e}")
        return pd.DataFrame()

# ===== 行业分类相关接口 =====
def get_index_classify():
    """获取申万行业分类
    
    Returns:
        pd.DataFrame: 申万行业分类数据
    """
    try:
        df = pro.index_classify()
        return df
    except Exception as e:
        print(f"获取申万行业分类失败: {e}")
        return pd.DataFrame()

def get_index_member_all(l1_code=None, l2_code=None, l3_code=None, ts_code=None, is_new=None):
    """获取申万行业成分构成(分级)
    
    Args:
        l1_code (str, optional): 一级行业代码
        l2_code (str, optional): 二级行业代码
        l3_code (str, optional): 三级行业代码
        ts_code (str, optional): 股票代码
        is_new (str, optional): 是否最新（默认为"Y是"）
        
    Returns:
        pd.DataFrame: 申万行业成分构成数据
    """
    try:
        params = {}
        if l1_code:
            params['l1_code'] = l1_code
        if l2_code:
            params['l2_code'] = l2_code
        if l3_code:
            params['l3_code'] = l3_code
        if ts_code:
            params['ts_code'] = ts_code
        if is_new:
            params['is_new'] = is_new
            
        df = pro.index_member_all(**params)
        return df
    except Exception as e:
        print(f"获取申万行业成分构成数据失败: {e}")
        return pd.DataFrame()

def get_sw_daily(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取申万行业日线行情
    
    Args:
        ts_code (str, optional): 行业代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 申万行业日线行情数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.sw_daily(**params)
        return df
    except Exception as e:
        print(f"获取申万行业日线行情失败: {e}")
        return pd.DataFrame()

def get_ci_index_member(l1_code=None, l2_code=None, l3_code=None, ts_code=None, is_new=None):
    """获取中信行业成分
    
    Args:
        l1_code (str, optional): 一级行业代码
        l2_code (str, optional): 二级行业代码
        l3_code (str, optional): 三级行业代码
        ts_code (str, optional): 股票代码
        is_new (str, optional): 是否最新（默认为"Y是"）
        
    Returns:
        pd.DataFrame: 中信行业成分数据
    """
    try:
        params = {}
        if l1_code:
            params['l1_code'] = l1_code
        if l2_code:
            params['l2_code'] = l2_code
        if l3_code:
            params['l3_code'] = l3_code
        if ts_code:
            params['ts_code'] = ts_code
        if is_new:
            params['is_new'] = is_new
            
        df = pro.ci_index_member(**params)
        return df
    except Exception as e:
        print(f"获取中信行业成分数据失败: {e}")
        return pd.DataFrame()

def get_ci_daily(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取中信行业指数行情
    
    Args:
        ts_code (str, optional): 行业代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 中信行业指数行情数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.ci_daily(**params)
        return df
    except Exception as e:
        print(f"获取中信行业指数行情失败: {e}")
        return pd.DataFrame()

def get_idx_factor_pro(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取指数技术因子(专业版)
    
    Args:
        ts_code (str, optional): 指数代码(大盘指数 申万指数 中信指数)
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 指数技术因子数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.idx_factor_pro(**params)
        return df
    except Exception as e:
        print(f"获取指数技术因子数据失败: {e}")
        return pd.DataFrame()

# ===== 市场交易统计 =====
def get_daily_info(trade_date=None, ts_code=None, exchange=None, start_date=None, end_date=None, fields=None):
    """获取交易所股票交易统计
    
    Args:
        trade_date (str, optional): 交易日期
        ts_code (str, optional): 板块代码
        exchange (str, optional): 股票市场（SH上交所 SZ深交所）
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        fields (str, optional): 指定提取字段
        
    Returns:
        pd.DataFrame: 交易所股票交易统计数据
    """
    try:
        params = {}
        if trade_date:
            params['trade_date'] = trade_date
        if ts_code:
            params['ts_code'] = ts_code
        if exchange:
            params['exchange'] = exchange
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if fields:
            params['fields'] = fields
            
        df = pro.daily_info(**params)
        return df
    except Exception as e:
        print(f"获取交易所股票交易统计失败: {e}")
        return pd.DataFrame()

def get_sz_daily_info(trade_date=None, ts_code=None, start_date=None, end_date=None):
    """获取深圳市场每日交易概况
    
    Args:
        trade_date (str, optional): 交易日期
        ts_code (str, optional): 板块代码
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 深圳市场每日交易概况数据
    """
    try:
        params = {}
        if trade_date:
            params['trade_date'] = trade_date
        if ts_code:
            params['ts_code'] = ts_code
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.sz_daily_info(**params)
        return df
    except Exception as e:
        print(f"获取深圳市场每日交易概况失败: {e}")
        return pd.DataFrame()

# ===== 新闻数据接口 =====
def get_news(start_date, end_date, src):
    """获取主流新闻网站的快讯新闻数据
    
    Args:
        start_date (datetime): 开始日期(格式：2018-11-20 09:00:00)
        end_date (datetime): 结束日期
        src (str): 新闻来源
        
    Returns:
        pd.DataFrame: 新闻快讯数据
    """
    try:
        df = pro.news(start_date=start_date, end_date=end_date, src=src)
        return df
    except Exception as e:
        print(f"获取新闻快讯数据失败: {e}")
        return pd.DataFrame()

def get_anns_d(ts_code=None, ann_date=None, start_date=None, end_date=None):
    """获取上市公司全量公告数据
    
    Args:
        ts_code (str, optional): 股票代码
        ann_date (str, optional): 公告日期
        start_date (str, optional): 公告开始日期
        end_date (str, optional): 公告结束日期
        
    Returns:
        pd.DataFrame: 上市公司公告数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if ann_date:
            params['ann_date'] = ann_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.anns_d(**params)
        return df
    except Exception as e:
        print(f"获取上市公司公告数据失败: {e}")
        return pd.DataFrame()

def get_irm_qa_sh(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取上交所e互动董秘问答文本数据
    
    Args:
        ts_code (str, optional): 股票代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 上交所e互动数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.irm_qa_sh(**params)
        return df
    except Exception as e:
        print(f"获取上交所e互动数据失败: {e}")
        return pd.DataFrame()

def get_irm_qa_sz(ts_code=None, trade_date=None, start_date=None, end_date=None):
    """获取深证互动易数据
    
    Args:
        ts_code (str, optional): 股票代码
        trade_date (str, optional): 交易日期
        start_date (str, optional): 开始日期
        end_date (str, optional): 结束日期
        
    Returns:
        pd.DataFrame: 深证互动易数据
    """
    try:
        params = {}
        if ts_code:
            params['ts_code'] = ts_code
        if trade_date:
            params['trade_date'] = trade_date
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        df = pro.irm_qa_sz(**params)
        return df
    except Exception as e:
        print(f"获取深证互动易数据失败: {e}")
        return pd.DataFrame() 