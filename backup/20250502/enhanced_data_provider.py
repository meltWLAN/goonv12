"""
增强型数据提供者
整合多个数据源，提供统一的数据获取接口

作者: 数据集成团队
最后更新: 2025-04-28
"""

import tushare as ts
import akshare as ak
import pandas as pd
import numpy as np
import logging
import os
import time
import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from tushare_data_center import TushareDataCenter

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DataSourceHealth:
    """数据源健康状态类"""
    def __init__(self):
        self.last_check_time = None
        self.is_healthy = True
        self.error_count = 0
        self.last_error = None
        self.avg_response_time = 0
        self.total_requests = 0
        
    def record_success(self, response_time: float):
        """记录成功请求"""
        self.is_healthy = True
        self.error_count = 0
        self.last_check_time = datetime.now()
        self.avg_response_time = (self.avg_response_time * self.total_requests + response_time) / (self.total_requests + 1)
        self.total_requests += 1
        
    def record_failure(self, error: Exception):
        """记录失败请求"""
        self.error_count += 1
        self.last_error = error
        self.last_check_time = datetime.now()
        if self.error_count >= 3:  # 连续三次失败则标记为不健康
            self.is_healthy = False

class EnhancedDataProvider:
    """增强型数据提供者"""
    
    def __init__(self, 
                 token: str = "0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10",
                 cache_dir: str = "./data_cache",
                 cache_expire_days: int = 1):
        """初始化数据提供者"""
        # 设置日志
        self.logger = logging.getLogger("EnhancedDataProvider")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # 初始化基本属性
        self.token = token
        self.cache_dir = cache_dir
        self.cache_expire_days = cache_expire_days
        
        # 初始化数据中心
        self.data_center = {
            'industry_map': {},  # 行业代码映射
            'stock_industry': {},  # 股票所属行业
            'industry_stocks': {}  # 行业包含的股票
        }
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 数据源状态 - 移到这里初始化
        self.data_sources = {
            'tushare': {
                'enabled': True, 
                'priority': 1, 
                'api': None,
                'health': DataSourceHealth()
            },
            'akshare': {
                'enabled': True, 
                'priority': 2, 
                'api': None,
                'health': DataSourceHealth()
            },
            'web_crawler': {
                'enabled': True,
                'priority': 3,
                'api': None,
                'health': DataSourceHealth()
            }
        }
        
        # 初始化数据源
        self._init_data_sources()
        
        try:
            self._init_industry_mappings()
        except Exception as e:
            self.logger.error(f"初始化行业分类映射失败: {str(e)}")
        
        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        
        # 异步会话
        self.aiohttp_session = None
        
    def _init_industry_mappings(self):
        """初始化行业分类映射"""
        try:
            # 从tushare获取行业分类数据
            if self.pro is not None:
                industry_data = self.pro.stock_basic(exchange='', list_status='L', 
                                                   fields='ts_code,industry')
                
                # 初始化映射
                for _, row in industry_data.iterrows():
                    if pd.notna(row['industry']):
                        # 更新行业到股票的映射
                        if row['industry'] not in self.data_center['industry_stocks']:
                            self.data_center['industry_stocks'][row['industry']] = []
                        self.data_center['industry_stocks'][row['industry']].append(row['ts_code'])
                        
                        # 更新股票到行业的映射
                        self.data_center['stock_industry'][row['ts_code']] = row['industry']
                
                self.logger.info(f"成功初始化行业映射，共 {len(self.data_center['industry_stocks'])} 个行业")
            
        except Exception as e:
            self.logger.error(f"初始化行业映射时发生错误: {str(e)}")
            raise
    
    @lru_cache(maxsize=100)
    def get_stock_data(self, ts_code, start_date=None, end_date=None, adj='qfq', limit=None):
        """
        获取股票数据，支持前复权、后复权
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            adj: 复权类型，None不复权，qfq前复权，hfq后复权
            limit: 限制返回的条数
            
        Returns:
            DataFrame: 股票数据，按日期降序排列
        """
        # 检查内存缓存
        cache_key = f"{ts_code}_{start_date}_{end_date}_{adj}"
        if cache_key in self.memory_cache:
            data = self.memory_cache[cache_key]
            if limit and len(data) > limit:
                return data.head(limit)
            return data
            
        # 获取数据
        df = self.data_center.get_daily_data(ts_code, start_date, end_date, adj)
        
        if df.empty:
            self.logger.warning(f"未获取到股票 {ts_code} 的数据")
            return df
            
        # 确保数据按日期降序排列
        if 'trade_date' in df.columns:
            df = df.sort_values('trade_date', ascending=False)
            
        # 添加技术指标
        df = self.add_technical_indicators(df)
        
        # 缓存数据
        self.memory_cache[cache_key] = df
        
        # 限制返回条数
        if limit and len(df) > limit:
            return df.head(limit)
            
        return df
    
    def add_technical_indicators(self, df):
        """
        添加技术指标
        
        Args:
            df: 股票数据DataFrame
            
        Returns:
            DataFrame: 添加了技术指标的数据
        """
        if df.empty:
            return df
            
        # 确保按日期升序排列进行计算
        df_sorted = df.sort_values('trade_date') if 'trade_date' in df.columns else df
        
        # 计算移动平均线
        df_sorted['ma5'] = df_sorted['close'].rolling(window=5).mean()
        df_sorted['ma10'] = df_sorted['close'].rolling(window=10).mean()
        df_sorted['ma20'] = df_sorted['close'].rolling(window=20).mean()
        df_sorted['ma30'] = df_sorted['close'].rolling(window=30).mean()
        df_sorted['ma60'] = df_sorted['close'].rolling(window=60).mean()
        
        # 计算成交量移动平均
        if 'vol' in df_sorted.columns:
            df_sorted['vol_ma5'] = df_sorted['vol'].rolling(window=5).mean()
            df_sorted['vol_ma10'] = df_sorted['vol'].rolling(window=10).mean()
        
        # 计算MACD
        df_sorted = self._calculate_macd(df_sorted)
        
        # 计算RSI
        df_sorted = self._calculate_rsi(df_sorted)
        
        # 计算KDJ
        df_sorted = self._calculate_kdj(df_sorted)
        
        # 计算布林带
        df_sorted = self._calculate_bollinger_bands(df_sorted)
        
        # 恢复原始排序
        if 'trade_date' in df.columns:
            df_sorted = df_sorted.sort_values('trade_date', ascending=False)
        
        return df_sorted
    
    def _calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标"""
        if len(df) > max(fast_period, slow_period, signal_period):
            # 计算快线和慢线的指数移动平均
            ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
            ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
            
            # 计算MACD线和信号线
            df['macd_dif'] = ema_fast - ema_slow
            df['macd_dea'] = df['macd_dif'].ewm(span=signal_period, adjust=False).mean()
            df['macd'] = 2 * (df['macd_dif'] - df['macd_dea'])
        return df
    
    def _calculate_rsi(self, df, periods=[6, 12, 24]):
        """计算RSI指标"""
        if len(df) < max(periods) + 1:
            return df
            
        # 计算价格变化
        df['diff'] = df['close'].diff()
        
        for period in periods:
            # 计算上涨和下跌
            df[f'up{period}'] = df['diff'].clip(lower=0)
            df[f'down{period}'] = -df['diff'].clip(upper=0)
            
            # 计算平均上涨和下跌
            df[f'up_avg{period}'] = df[f'up{period}'].rolling(window=period).mean()
            df[f'down_avg{period}'] = df[f'down{period}'].rolling(window=period).mean()
            
            # 计算相对强度和RSI
            rs = df[f'up_avg{period}'] / df[f'down_avg{period}']
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
            
            # 删除中间计算列
            df = df.drop([f'up{period}', f'down{period}', f'up_avg{period}', f'down_avg{period}'], axis=1)
            
        # 删除diff列
        df = df.drop('diff', axis=1)
        
        return df
    
    def _calculate_kdj(self, df, n=9, m1=3, m2=3):
        """计算KDJ指标"""
        if len(df) < n:
            return df
            
        # 计算最低价和最高价的n日滚动窗口
        low_min = df['low'].rolling(window=n).min()
        high_max = df['high'].rolling(window=n).max()
        
        # 计算RSV
        rsv = 100 * ((df['close'] - low_min) / (high_max - low_min))
        
        # 计算K、D、J值
        df['kdj_k'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(alpha=1/m2, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def _calculate_bollinger_bands(self, df, window=20, num_std=2):
        """计算布林带指标"""
        if len(df) < window:
            return df
            
        # 计算移动平均线
        df['boll_mid'] = df['close'].rolling(window=window).mean()
        
        # 计算标准差
        df['boll_std'] = df['close'].rolling(window=window).std()
        
        # 计算上轨和下轨
        df['boll_upper'] = df['boll_mid'] + num_std * df['boll_std']
        df['boll_lower'] = df['boll_mid'] - num_std * df['boll_std']
        
        return df
    
    def get_financial_data(self, ts_code, report_type=1):
        """
        获取财务数据，包括资产负债表、利润表、现金流量表和财务指标
        
        Args:
            ts_code: 股票代码
            report_type: 报表类型，默认为1（合并报表）
            
        Returns:
            dict: 包含各类财务数据的字典
        """
        try:
            # 获取最近3年的财务数据
            start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
            
            # 获取各类财务数据
            income = self.data_center.get_income(ts_code, start_date=start_date)
            balance = self.data_center.get_balance(ts_code, start_date=start_date)
            cashflow = self.data_center.get_cashflow(ts_code, start_date=start_date)
            indicator = self.data_center.get_financial_indicator(ts_code, start_date=start_date)
            
            # 筛选报表类型
            if not income.empty and 'report_type' in income.columns:
                income = income[income['report_type'] == report_type]
            if not balance.empty and 'report_type' in balance.columns:
                balance = balance[balance['report_type'] == report_type]
            if not cashflow.empty and 'report_type' in cashflow.columns:
                cashflow = cashflow[cashflow['report_type'] == report_type]
            
            # 按报告期排序
            if not income.empty and 'end_date' in income.columns:
                income = income.sort_values('end_date', ascending=False)
            if not balance.empty and 'end_date' in balance.columns:
                balance = balance.sort_values('end_date', ascending=False)
            if not cashflow.empty and 'end_date' in cashflow.columns:
                cashflow = cashflow.sort_values('end_date', ascending=False)
            if not indicator.empty and 'end_date' in indicator.columns:
                indicator = indicator.sort_values('end_date', ascending=False)
            
            return {
                'income': income,
                'balance': balance,
                'cashflow': cashflow,
                'indicator': indicator
            }
        except Exception as e:
            self.logger.error(f"获取股票 {ts_code} 的财务数据失败: {str(e)}")
            return {
                'income': pd.DataFrame(),
                'balance': pd.DataFrame(),
                'cashflow': pd.DataFrame(),
                'indicator': pd.DataFrame()
            }
    
    def get_stock_profile(self, ts_code):
        """
        获取股票完整画像
        
        Args:
            ts_code: 股票代码
            
        Returns:
            dict: 股票画像数据
        """
        try:
            profile = self.data_center.get_stock_profile(ts_code)
            
            # 获取最近60天的行情数据
            daily_data = self.get_stock_data(ts_code, limit=60)
            if not daily_data.empty:
                # 添加行情概要
                latest = daily_data.iloc[0]
                if len(daily_data) > 1:
                    prev = daily_data.iloc[1]
                    daily_change = (latest['close'] - prev['close']) / prev['close'] * 100
                else:
                    daily_change = 0
                    
                profile['market_summary'] = {
                    'latest_close': latest['close'],
                    'daily_change': daily_change,
                    'volume': latest.get('vol', 0),
                    'turnover': latest.get('amount', 0),
                    'pe': profile.get('latest_basic', {}).get('pe', 0),
                    'pb': profile.get('latest_basic', {}).get('pb', 0)
                }
                
                # 添加技术指标概要
                profile['technical_summary'] = {
                    'ma5': latest.get('ma5', 0),
                    'ma20': latest.get('ma20', 0),
                    'ma60': latest.get('ma60', 0),
                    'macd': latest.get('macd', 0),
                    'macd_dif': latest.get('macd_dif', 0),
                    'macd_dea': latest.get('macd_dea', 0),
                    'rsi_6': latest.get('rsi_6', 0),
                    'rsi_12': latest.get('rsi_12', 0),
                    'kdj_k': latest.get('kdj_k', 0),
                    'kdj_d': latest.get('kdj_d', 0),
                    'kdj_j': latest.get('kdj_j', 0),
                    'boll_upper': latest.get('boll_upper', 0),
                    'boll_mid': latest.get('boll_mid', 0),
                    'boll_lower': latest.get('boll_lower', 0)
                }
            
            # 获取财务数据摘要
            financial_data = self.get_financial_data(ts_code)
            if not financial_data['indicator'].empty:
                latest_indicator = financial_data['indicator'].iloc[0]
                profile['financial_summary'] = {
                    'eps': latest_indicator.get('eps', 0),
                    'bps': latest_indicator.get('bps', 0),
                    'roe': latest_indicator.get('roe', 0),
                    'netprofit_yoy': latest_indicator.get('netprofit_yoy', 0),
                    'revenue_yoy': latest_indicator.get('tr_yoy', 0),
                    'debt_to_assets': latest_indicator.get('debt_to_assets', 0)
                }
            
            # 添加行业信息
            profile['industry'] = self.data_center['stock_industry'].get(ts_code, '')
            
            return profile
        except Exception as e:
            self.logger.error(f"获取股票 {ts_code} 的画像失败: {str(e)}")
            return {}
    
    def get_industry_stocks(self, industry):
        """
        获取指定行业的所有股票
        
        Args:
            industry: 行业名称
            
        Returns:
            DataFrame: 指定行业的股票列表
        """
        try:
            # 获取所有股票列表
            stock_list = self.data_center.get_stock_list()
            if stock_list.empty:
                return pd.DataFrame()
                
            # 筛选指定行业的股票
            industry_stocks = stock_list[stock_list['industry'] == industry]
            return industry_stocks
        except Exception as e:
            self.logger.error(f"获取行业 {industry} 的股票失败: {str(e)}")
            return pd.DataFrame()
    
    def get_industry_performance(self, industry, days=30):
        """
        获取行业整体表现
        
        Args:
            industry: 行业名称
            days: 统计天数
            
        Returns:
            dict: 行业表现数据
        """
        try:
            # 获取行业股票
            stocks = self.get_industry_stocks(industry)
            if stocks.empty:
                return {}
                
            # 计算开始日期
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # 获取每只股票的行情数据
            performance_data = []
            for _, stock in stocks.iterrows():
                ts_code = stock['ts_code']
                stock_data = self.get_stock_data(ts_code, start_date=start_date)
                
                if not stock_data.empty and len(stock_data) >= 2:
                    # 计算区间涨跌幅
                    first_close = stock_data.iloc[-1]['close']
                    last_close = stock_data.iloc[0]['close']
                    change_pct = (last_close - first_close) / first_close * 100
                    
                    performance_data.append({
                        'ts_code': ts_code,
                        'name': stock['name'],
                        'first_close': first_close,
                        'last_close': last_close,
                        'change_pct': change_pct
                    })
            
            if not performance_data:
                return {}
                
            # 转换为DataFrame计算统计数据
            df = pd.DataFrame(performance_data)
            
            return {
                'industry': industry,
                'stock_count': len(df),
                'avg_change_pct': df['change_pct'].mean(),
                'max_change_pct': df['change_pct'].max(),
                'min_change_pct': df['change_pct'].min(),
                'median_change_pct': df['change_pct'].median(),
                'rise_count': (df['change_pct'] > 0).sum(),
                'fall_count': (df['change_pct'] < 0).sum(),
                'top_stocks': df.nlargest(5, 'change_pct')[['ts_code', 'name', 'change_pct']].to_dict('records'),
                'bottom_stocks': df.nsmallest(5, 'change_pct')[['ts_code', 'name', 'change_pct']].to_dict('records')
            }
        except Exception as e:
            self.logger.error(f"获取行业 {industry} 的表现失败: {str(e)}")
            return {}
    
    def get_market_overview(self):
        """
        获取市场概览
        
        Returns:
            dict: 市场概览数据
        """
        try:
            # 获取上证指数数据
            sh_index = self.data_sources['tushare']['api'].index_daily(ts_code='000001.SH', limit=30)
            # 获取深证成指数据
            sz_index = self.data_sources['tushare']['api'].index_daily(ts_code='399001.SZ', limit=30)
            # 获取创业板指数据
            cyb_index = self.data_sources['tushare']['api'].index_daily(ts_code='399006.SZ', limit=30)
            
            # 计算今日涨跌
            today_change = {}
            if not sh_index.empty and len(sh_index) >= 2:
                today = sh_index.iloc[0]
                yesterday = sh_index.iloc[1]
                today_change['sh'] = (today['close'] - yesterday['close']) / yesterday['close'] * 100
            
            if not sz_index.empty and len(sz_index) >= 2:
                today = sz_index.iloc[0]
                yesterday = sz_index.iloc[1]
                today_change['sz'] = (today['close'] - yesterday['close']) / yesterday['close'] * 100
            
            if not cyb_index.empty and len(cyb_index) >= 2:
                today = cyb_index.iloc[0]
                yesterday = cyb_index.iloc[1]
                today_change['cyb'] = (today['close'] - yesterday['close']) / yesterday['close'] * 100
            
            # 获取行业表现
            try:
                industry_df = self.data_sources['akshare']['api'].stock_board_industry_name_em()
                industry_performance = []
                
                if not industry_df.empty:
                    # 取前10个行业
                    top_industries = industry_df.head(10)
                    for _, row in top_industries.iterrows():
                        industry_performance.append({
                            'industry': row['板块名称'],
                            'avg_change_pct': float(row['涨跌幅']),
                            'stock_count': int(row['公司家数']) if '公司家数' in row else 0,
                            'rise_count': int(row['上涨家数']) if '上涨家数' in row else 0,
                            'fall_count': int(row['下跌家数']) if '下跌家数' in row else 0
                        })
            except Exception as e:
                self.logger.warning(f"获取行业表现数据失败: {str(e)}")
                industry_performance = []
            
            # 获取北向资金数据
            try:
                fund_flow = self.data_sources['akshare']['api'].stock_hsgt_fund_flow_summary_em()
                northbound_amount = 0
                
                if not fund_flow.empty:
                    # 获取沪股通和深股通的北向资金
                    sh_flow = fund_flow[fund_flow['类型'] == '沪港通'][fund_flow['板块'] == '沪股通']
                    sz_flow = fund_flow[fund_flow['类型'] == '深港通'][fund_flow['板块'] == '深股通']
                    
                    if not sh_flow.empty:
                        northbound_amount += float(sh_flow.iloc[0]['成交净买额'])
                    if not sz_flow.empty:
                        northbound_amount += float(sz_flow.iloc[0]['成交净买额'])
                
            except Exception as e:
                self.logger.warning(f"获取北向资金数据失败: {str(e)}")
                northbound_amount = 0
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'indices': {
                    'sh': sh_index.iloc[0]['close'] if not sh_index.empty else 0,
                    'sz': sz_index.iloc[0]['close'] if not sz_index.empty else 0,
                    'cyb': cyb_index.iloc[0]['close'] if not cyb_index.empty else 0
                },
                'today_change': today_change,
                'industry_performance': industry_performance,
                'northbound_amount': northbound_amount
            }
        except Exception as e:
            self.logger.error(f"获取市场概览失败: {str(e)}")
            return {}
    
    def screen_stocks(self, criteria):
        """
        基于条件筛选股票
        
        Args:
            criteria: 筛选条件字典
                示例: {
                    'industry': '银行',  # 行业
                    'min_pe': 0,        # 最小市盈率
                    'max_pe': 20,       # 最大市盈率
                    'min_pb': 0,        # 最小市净率
                    'max_pb': 2,        # 最大市净率
                    'min_roe': 10,      # 最小ROE
                    'min_market_cap': 100  # 最小市值（亿）
                }
                
        Returns:
            DataFrame: 满足条件的股票列表
        """
        try:
            # 获取股票列表
            stock_list = self.data_center.get_stock_list()
            if stock_list.empty:
                return pd.DataFrame()
                
            # 行业筛选
            if 'industry' in criteria and criteria['industry']:
                stock_list = stock_list[stock_list['industry'] == criteria['industry']]
            
            # 获取每日指标数据进行筛选
            latest_date = datetime.now().strftime('%Y%m%d')
            daily_basic = self.data_center.get_daily_basic(trade_date=latest_date)
            
            if daily_basic.empty:
                # 如果当天数据不可用，尝试获取前一天数据
                prev_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                daily_basic = self.data_center.get_daily_basic(trade_date=prev_date)
                
                if daily_basic.empty:
                    # 如果仍然不可用，尝试获取前一周数据
                    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                    daily_basic = self.data_center.get_daily_basic(trade_date=week_ago)
            
            if daily_basic.empty:
                self.logger.warning("未能获取每日指标数据，筛选结果可能不准确")
                return stock_list
            
            # 合并股票列表和每日指标
            merged = pd.merge(stock_list, daily_basic, on='ts_code', how='inner')
            
            # 应用筛选条件
            result = merged.copy()
            
            if 'min_pe' in criteria and criteria['min_pe'] is not None:
                result = result[result['pe'] >= criteria['min_pe']]
                
            if 'max_pe' in criteria and criteria['max_pe'] is not None:
                result = result[result['pe'] <= criteria['max_pe']]
                
            if 'min_pb' in criteria and criteria['min_pb'] is not None:
                result = result[result['pb'] >= criteria['min_pb']]
                
            if 'max_pb' in criteria and criteria['max_pb'] is not None:
                result = result[result['pb'] <= criteria['max_pb']]
                
            if 'min_market_cap' in criteria and criteria['min_market_cap'] is not None:
                result = result[result['total_mv'] >= criteria['min_market_cap'] * 10000]  # 转换为万元
                
            if 'max_market_cap' in criteria and criteria['max_market_cap'] is not None:
                result = result[result['total_mv'] <= criteria['max_market_cap'] * 10000]  # 转换为万元
                
            # 针对ROE和其他财务指标的筛选需要单独处理
            if 'min_roe' in criteria and criteria['min_roe'] is not None:
                # 获取最新一期的财务指标数据
                # 由于这会很慢，我们采用批量获取的方式
                # 这里简化处理，实际应用中可能需要更复杂的逻辑
                selected_codes = []
                
                for _, row in result.iterrows():
                    ts_code = row['ts_code']
                    indicator = self.data_center.get_financial_indicator(ts_code, limit=1)
                    
                    if not indicator.empty and 'roe' in indicator.columns:
                        roe = indicator.iloc[0]['roe']
                        if roe >= criteria['min_roe']:
                            selected_codes.append(ts_code)
                
                if selected_codes:
                    result = result[result['ts_code'].isin(selected_codes)]
            
            return result
        except Exception as e:
            self.logger.error(f"筛选股票失败: {str(e)}")
            return pd.DataFrame()
    
    def get_trading_calendar(self, start_date=None, end_date=None):
        """
        获取交易日历
        
        Args:
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        Returns:
            DataFrame: 交易日历数据
        """
        return self.data_center.get_trade_calendar(start_date=start_date, end_date=end_date)
    
    def is_trading_day(self, date=None):
        """
        判断是否为交易日
        
        Args:
            date: 日期，格式YYYYMMDD，默认为当天
            
        Returns:
            bool: 是否为交易日
        """
        return self.data_center.is_trade_date(date)

    def _init_data_sources(self):
        """初始化所有数据源"""
        # 初始化Tushare
        try:
            if self.token:
                ts.set_token(self.token)
                self.pro = ts.pro_api()
                self.data_sources['tushare']['api'] = self.pro
                self.logger.info("Tushare API初始化成功")
            else:
                self.data_sources['tushare']['enabled'] = False
                self.logger.warning("Tushare API未初始化：缺少token")
        except Exception as e:
            self.data_sources['tushare']['enabled'] = False
            self.logger.error(f"Tushare API初始化失败: {str(e)}")
            
        # 初始化Akshare
        try:
            # Akshare不需要token
            self.data_sources['akshare']['api'] = ak
            self.logger.info("Akshare API初始化成功")
        except Exception as e:
            self.data_sources['akshare']['enabled'] = False
            self.logger.error(f"Akshare API初始化失败: {str(e)}")
            
    def _get_cache_path(self, data_type: str, params: Dict) -> str:
        """生成缓存文件路径"""
        param_str = "_".join([f"{k}={v}" for k, v in sorted(params.items())])
        return os.path.join(self.cache_dir, f"{data_type}_{param_str}.csv")
        
    def _load_from_cache(self, cache_path: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        if not os.path.exists(cache_path):
            return None
            
        try:
            # 检查缓存是否过期
            file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
            if datetime.now() - file_mtime > timedelta(days=self.cache_expire_days):
                return None
                
            df = pd.read_csv(cache_path)
            self.logger.info(f"从缓存加载数据: {cache_path}")
            return df
        except Exception as e:
            self.logger.error(f"读取缓存失败: {str(e)}")
            return None
            
    def _save_to_cache(self, df: pd.DataFrame, cache_path: str):
        """保存数据到缓存"""
        if df is None or df.empty:
            return
            
        try:
            df.to_csv(cache_path, index=False)
            self.logger.info(f"数据已缓存: {cache_path}")
        except Exception as e:
            self.logger.error(f"缓存数据失败: {str(e)}")
            
    def get_stock_daily(self, 
                       code: str, 
                       start_date: str = None, 
                       end_date: str = None) -> pd.DataFrame:
        """获取股票日线数据"""
        # 标准化日期参数
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        params = {
            'code': code,
            'start_date': start_date,
            'end_date': end_date
        }
        
        # 检查缓存
        cache_path = self._get_cache_path('daily', params)
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
            
        # 尝试从Tushare获取数据
        if self.data_sources['tushare']['enabled']:
            try:
                df = self.data_sources['tushare']['api'].daily(
                    ts_code=code,
                    start_date=start_date,
                    end_date=end_date
                )
                if not df.empty:
                    self._save_to_cache(df, cache_path)
                    return df
            except Exception as e:
                self.logger.warning(f"从Tushare获取数据失败: {str(e)}")
                
        # 尝试从Akshare获取数据
        try:
            # 转换代码格式
            if '.SZ' in code:
                ak_code = code.split('.')[0]
            elif '.SH' in code:
                ak_code = code.split('.')[0]
            else:
                ak_code = code
                
            df = ak.stock_zh_a_hist(
                symbol=ak_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if not df.empty:
                # 获取列名
                columns = df.columns.tolist()
                
                # 创建列名映射
                column_map = {
                    '日期': 'trade_date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_chg',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                }
                
                # 重命名列
                df.rename(columns=column_map, inplace=True)
                
                # 确保日期格式正确
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
                
                # 按日期排序
                df.sort_values('trade_date', inplace=True)
                df.reset_index(drop=True, inplace=True)
                
                self._save_to_cache(df, cache_path)
                return df
                
        except Exception as e:
            self.logger.error(f"从Akshare获取数据失败: {str(e)}")
            
        return pd.DataFrame()
        
    def get_sector_list(self) -> List[Dict]:
        """获取行业列表"""
        sectors = []
        
        # 尝试从东方财富获取数据
        try:
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                for _, row in df.iterrows():
                    sectors.append({
                        'code': row.get('板块代码', ''),
                        'name': row.get('板块名称', ''),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'price': float(row.get('最新价', 0)),
                        'volume': float(row.get('总成交量', 0)),
                        'turnover': float(row.get('换手率', 0)) if '换手率' in row else 0,
                        'source': 'eastmoney'
                    })
        except Exception as e:
            self.logger.warning(f"从东方财富获取行业数据失败: {str(e)}")
            
        # 如果东方财富数据获取失败，尝试从新浪获取
        if not sectors:
            try:
                df = ak.stock_board_industry_cons_sina()
                if not df.empty:
                    unique_sectors = df['行业名称'].unique()
                    for sector_name in unique_sectors:
                        try:
                            sector_detail = ak.stock_board_industry_hist_sina(
                                symbol=sector_name, 
                                indicator="日频"
                            )
                            if not sector_detail.empty:
                                latest = sector_detail.iloc[0]
                                sectors.append({
                                    'code': f"SINA_{len(sectors)}",
                                    'name': sector_name,
                                    'change_pct': float(latest.get('涨跌幅', 0)),
                                    'price': float(latest.get('收盘点位', 0)),
                                    'volume': float(latest.get('成交量', 0)),
                                    'turnover': 0.0,
                                    'source': 'sina'
                                })
                        except Exception as e:
                            self.logger.warning(f"处理新浪行业{sector_name}数据失败: {str(e)}")
            except Exception as e:
                self.logger.warning(f"从新浪获取行业数据失败: {str(e)}")
                
        return sectors
        
    def get_sector_stocks(self, sector_name: str) -> List[str]:
        """获取行业成分股"""
        stocks = []
        
        # 尝试从东方财富获取数据
        try:
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
            if not df.empty:
                stocks = df['代码'].tolist()
        except Exception as e:
            self.logger.warning(f"从东方财富获取行业成分股失败: {str(e)}")
            
        # 如果东方财富失败，尝试从新浪获取
        if not stocks:
            try:
                df = ak.stock_board_industry_cons_sina()
                if not df.empty:
                    sector_stocks = df[df['行业名称'] == sector_name]
                    stocks = sector_stocks['代码'].tolist()
            except Exception as e:
                self.logger.warning(f"从新浪获取行业成分股失败: {str(e)}")
                
        return stocks
        
    def get_market_sentiment(self) -> Dict:
        """获取市场情绪数据"""
        market_data = {}
        
        # 获取大盘指数数据
        try:
            df = ak.stock_zh_index_daily_em(symbol="000001")  # 使用东方财富接口
            if not df.empty:
                # 标准化列名
                df.rename(columns={
                    '收盘': 'close',
                    '开盘': 'open',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_chg',
                    '涨跌额': 'change'
                }, inplace=True)
                
                # 计算20日波动率
                close_prices = df['close'].values[-20:]
                if len(close_prices) >= 20:
                    returns = np.diff(np.log(close_prices))
                    volatility = np.std(returns) * np.sqrt(252) * 100
                    market_data['volatility'] = volatility
                    
                    # 计算趋势
                    trend = (close_prices[-1] / close_prices[0] - 1) * 100
                    market_data['trend'] = trend
        except Exception as e:
            self.logger.warning(f"获取大盘指数数据失败: {str(e)}")
            market_data['volatility'] = 15
            market_data['trend'] = 0
            
        # 获取市场涨跌家数
        try:
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                up_counts = len(df[df['涨跌幅'] > 0])
                down_counts = len(df[df['涨跌幅'] < 0])
                flat_counts = len(df) - up_counts - down_counts
                
                market_data.update({
                    'up_counts': up_counts,
                    'down_counts': down_counts,
                    'flat_counts': flat_counts
                })
                
                # 计算市场情绪得分
                if up_counts + down_counts > 0:
                    sentiment_score = up_counts / (up_counts + down_counts) * 100
                    market_data['sentiment_score'] = sentiment_score
                    
                    if sentiment_score > 70:
                        market_data['market_sentiment'] = '看多'
                    elif sentiment_score < 30:
                        market_data['market_sentiment'] = '看空'
                    else:
                        market_data['market_sentiment'] = '中性'
                else:
                    market_data['sentiment_score'] = 50
                    market_data['market_sentiment'] = '中性'
        except Exception as e:
            self.logger.warning(f"获取市场涨跌家数失败: {str(e)}")
            market_data.update({
                'sentiment_score': 50,
                'market_sentiment': '中性'
            })
            
        # 获取北向资金数据
        try:
            # 使用东方财富网北向资金接口
            df = ak.stock_em_hsgt_north_net_flow()  # 获取北向资金净流入
            if not df.empty:
                # 获取最新一天的北向资金净流入
                latest_flow = df['净流入'].iloc[-1]
                market_data['north_flow'] = float(latest_flow)
                
                # 计算北向资金趋势（最近5日净流入总和）
                recent_flow = df['净流入'].iloc[-5:].sum()
                market_data['north_flow_trend'] = 'up' if recent_flow > 0 else 'down'
                market_data['north_flow_5d_sum'] = float(recent_flow)
        except Exception as e:
            self.logger.warning(f"获取北向资金数据失败: {str(e)}")
            market_data.update({
                'north_flow': 0,
                'north_flow_trend': 'neutral',
                'north_flow_5d_sum': 0
            })
            
        return market_data
        
    def check_data_source_health(self) -> Dict[str, Dict]:
        """检查所有数据源的健康状态"""
        health_status = {}
        for source_name, source_info in self.data_sources.items():
            health = source_info['health']
            health_status[source_name] = {
                'is_healthy': health.is_healthy,
                'error_count': health.error_count,
                'last_error': str(health.last_error) if health.last_error else None,
                'avg_response_time': health.avg_response_time,
                'total_requests': health.total_requests,
                'last_check_time': health.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if health.last_check_time else None
            }
        return health_status

    async def get_north_flow_data(self, days=5):
        """获取北向资金数据
        
        Args:
            days (int): 获取最近几天的数据
            
        Returns:
            dict: 包含北向资金数据的字典
        """
        try:
            # 尝试从东方财富获取北向资金数据
            cache_key = f"north_flow_days={days}"
            cache_path = self._get_cache_path(cache_key)
            
            if os.path.exists(cache_path):
                data = self._load_from_cache(cache_path)
                if data is not None:
                    return data
            
            # 如果缓存不存在或已过期，从API获取数据
            try:
                # 注意：由于akshare接口可能不稳定，这里使用try-except处理
                north_data = ak.stock_em_hsgt_north_net_flow_in(symbol="沪股通")
                # 转换数据格式
                if not north_data.empty:
                    flow_data = {
                        'dates': north_data['date'].tolist()[-days:],
                        'values': north_data['value'].tolist()[-days:],
                    }
                    
                    # 计算趋势
                    values = flow_data['values']
                    trend = 'neutral'
                    if len(values) >= 2:
                        if values[-1] > values[-2]:
                            trend = 'up'
                        elif values[-1] < values[-2]:
                            trend = 'down'
                    
                    result = {
                        'north_flow': values[-1] if values else 0,
                        'north_flow_trend': trend,
                        'north_flow_5d_sum': sum(values[-5:]) if len(values) >= 5 else sum(values),
                        'raw_data': flow_data
                    }
                    
                    # 保存到缓存
                    self._save_to_cache(cache_path, result)
                    return result
                
            except Exception as e:
                self.logger.warning(f"获取北向资金数据失败: {str(e)}")
                # 返回默认值
                return {
                    'north_flow': 0,
                    'north_flow_trend': 'neutral',
                    'north_flow_5d_sum': 0,
                    'raw_data': {'dates': [], 'values': []}
                }
                
        except Exception as e:
            self.logger.error(f"处理北向资金数据时发生错误: {str(e)}")
            return None


# 使用示例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_data_provider.py <tushare_token> [ts_code]")
        sys.exit(1)
        
    token = sys.argv[1]
    ts_code = sys.argv[2] if len(sys.argv) > 2 else '000001.SZ'
    
    # 初始化数据提供器
    provider = EnhancedDataProvider(token=token)
    
    # 获取股票数据
    stock_data = provider.get_stock_data(ts_code, limit=10)
    print(f"获取到 {len(stock_data)} 条股票数据")
    if not stock_data.empty:
        print(stock_data[['trade_date', 'open', 'high', 'low', 'close', 'ma5', 'ma20', 'rsi_6', 'macd']].head())
    
    # 获取股票画像
    profile = provider.get_stock_profile(ts_code)
    print(f"股票名称: {profile.get('basic_info', {}).get('name')}")
    print(f"所属行业: {profile.get('industry')}")
    print(f"最新收盘价: {profile.get('market_summary', {}).get('latest_close')}")
    
    # 获取市场概览
    overview = provider.get_market_overview()
    print(f"市场概览: {overview.get('date')}")
    print(f"上证指数: {overview.get('indices', {}).get('sh')}, 涨跌幅: {overview.get('today_change', {}).get('sh', 0):.2f}%")
    print(f"深证成指: {overview.get('indices', {}).get('sz')}, 涨跌幅: {overview.get('today_change', {}).get('sz', 0):.2f}%") 