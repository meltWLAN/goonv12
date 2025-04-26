#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import datetime
import time
import seaborn as sns
from datetime import timedelta

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from utils.tushare_api import (
    get_stock_basics, get_daily_data, get_stk_factor, 
    get_stk_factor_pro, get_stk_nineturn, get_stk_auction_o,
    get_stk_auction_c, get_stock_list, get_daily
)

class StockFactorAnalyzer:
    """股票技术因子分析器，用于分析股票技术指标"""
    
    def __init__(self, output_dir="./output"):
        """初始化分析器"""
        self.stock_basics = None
        self.update_stock_basics()
        self.stock_list = None
        self.output_dir = output_dir
        self.factor_dfs = {}  # 存储因子数据
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
    def update_stock_basics(self):
        """更新股票基本信息"""
        self.stock_basics = get_stock_basics()
        print(f"已更新{len(self.stock_basics)}只股票的基本信息")
    
    def update_stock_list(self):
        """更新股票列表"""
        self.stock_list = get_stock_list()
        return self.stock_list
    
    def get_stock_list(self):
        """获取股票列表"""
        if self.stock_list is None:
            self.update_stock_list()
        return self.stock_list
    
    def analyze_stock_factors(self, ts_code=None, trade_date=None, start_date=None, end_date=None):
        """分析股票技术面因子数据
        
        Args:
            ts_code (str): 股票代码，如 000001.SZ
            trade_date (str): 交易日期，格式YYYYMMDD
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            
        Returns:
            pd.DataFrame: 技术面因子数据
        """
        # 获取技术面因子数据
        factor_data = get_stk_factor(ts_code=ts_code, trade_date=trade_date, 
                                     start_date=start_date, end_date=end_date)
        
        if factor_data.empty:
            print(f"未获取到股票{ts_code}在指定日期的技术面因子数据")
            return pd.DataFrame()
        
        # 如果是单只股票的分析，尝试获取股票名称
        if ts_code and self.stock_basics is not None and not self.stock_basics.empty:
            stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
            if not stock_info.empty:
                print(f"股票: {stock_info.iloc[0]['name']} ({ts_code})")
        
        # 存储数据
        key = f"{ts_code}_{start_date}_{end_date}" if ts_code else f"market_{start_date}_{end_date}"
        self.factor_dfs[key] = factor_data
        
        return factor_data
    
    def analyze_stock_factors_pro(self, ts_code=None, trade_date=None, start_date=None, end_date=None):
        """分析股票技术面因子专业版数据
        
        Args:
            ts_code (str): 股票代码，如 000001.SZ
            trade_date (str): 交易日期，格式YYYYMMDD
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            
        Returns:
            pd.DataFrame: 技术面因子专业版数据
        """
        # 获取技术面因子专业版数据
        factor_pro_data = get_stk_factor_pro(ts_code=ts_code, trade_date=trade_date, 
                                           start_date=start_date, end_date=end_date)
        
        if factor_pro_data.empty:
            print(f"未获取到股票{ts_code}在指定日期的技术面因子专业版数据")
            return pd.DataFrame()
        
        # 如果是单只股票的分析，尝试获取股票名称
        if ts_code and self.stock_basics is not None and not self.stock_basics.empty:
            stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
            if not stock_info.empty:
                print(f"股票: {stock_info.iloc[0]['name']} ({ts_code})")
        
        # 存储数据
        key = f"{ts_code}_pro_{start_date}_{end_date}" if ts_code else f"market_pro_{start_date}_{end_date}"
        self.factor_dfs[key] = factor_pro_data
        
        return factor_pro_data
    
    def analyze_nineturn(self, ts_code=None, trade_date=None, freq=None, start_date=None, end_date=None):
        """分析神奇九转指标
        
        Args:
            ts_code (str): 股票代码，如 000001.SZ
            trade_date (str): 交易日期，格式YYYYMMDD
            freq (str): 周期类型 (D-日, W-周, M-月)
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            
        Returns:
            pd.DataFrame: 神奇九转指标数据
        """
        # 获取神奇九转指标数据
        nineturn_data = get_stk_nineturn(ts_code=ts_code, trade_date=trade_date, 
                                        freq=freq, start_date=start_date, end_date=end_date)
        
        if nineturn_data.empty:
            print(f"未获取到股票{ts_code}在指定日期的神奇九转指标数据")
            return pd.DataFrame()
        
        # 如果是单只股票的分析，尝试获取股票名称
        if ts_code and self.stock_basics is not None and not self.stock_basics.empty:
            stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
            if not stock_info.empty:
                print(f"股票: {stock_info.iloc[0]['name']} ({ts_code})")
        
        # 分析神奇九转指标
        # 统计各级别信号出现的次数
        if 'nt_remark' in nineturn_data.columns:
            signal_counts = nineturn_data['nt_remark'].value_counts()
            print("神奇九转级别统计:")
            print(signal_counts)
            
        # 统计买入/卖出信号出现的次数
        if 'nt_signal' in nineturn_data.columns:
            signal_stats = nineturn_data['nt_signal'].value_counts()
            print("神奇九转信号统计:")
            print(signal_stats)
        
        return nineturn_data
    
    def analyze_auction(self, ts_code=None, trade_date=None, auction_type='o'):
        """分析集合竞价数据
        
        Args:
            ts_code (str): 股票代码，如 000001.SZ
            trade_date (str): 交易日期，格式YYYYMMDD
            auction_type (str): 竞价类型，'o'表示开盘集合竞价，'c'表示收盘集合竞价
            
        Returns:
            pd.DataFrame: 集合竞价数据
        """
        # 获取集合竞价数据
        if auction_type == 'o':
            auction_data = get_stk_auction_o(ts_code=ts_code, trade_date=trade_date)
            auction_type_name = "开盘集合竞价"
        else:
            auction_data = get_stk_auction_c(ts_code=ts_code, trade_date=trade_date)
            auction_type_name = "收盘集合竞价"
        
        if auction_data.empty:
            print(f"未获取到股票{ts_code}在指定日期的{auction_type_name}数据")
            return pd.DataFrame()
        
        # 如果是单只股票的分析，尝试获取股票名称
        if ts_code and self.stock_basics is not None and not self.stock_basics.empty:
            stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
            if not stock_info.empty:
                print(f"股票: {stock_info.iloc[0]['name']} ({ts_code})")
        
        return auction_data
    
    def screen_stocks_by_factor(self, factors, trade_date=None, top_n=50, ascending=False):
        """根据技术因子筛选股票
        
        Args:
            factors (list): 因子名称列表, 例如 ['pe', 'turnover']
            trade_date (str): 交易日期，格式YYYYMMDD，默认为最近一个交易日
            top_n (int): 返回的股票数量
            ascending (bool): 排序方式，True为升序，False为降序
            
        Returns:
            pd.DataFrame: 筛选后的股票列表
        """
        if not trade_date:
            trade_date = datetime.datetime.now().strftime('%Y%m%d')
        
        # 获取当日所有股票的技术因子数据
        factor_data = get_stk_factor(trade_date=trade_date)
        
        if factor_data.empty:
            print(f"未获取到{trade_date}的技术因子数据")
            return pd.DataFrame()
        
        # 检查请求的因子是否存在于数据中
        valid_factors = [f for f in factors if f in factor_data.columns]
        if not valid_factors:
            print(f"请求的因子 {factors} 不存在于获取的数据中")
            print(f"可用的因子有: {', '.join(factor_data.columns)}")
            return pd.DataFrame()
        
        # 根据第一个因子进行排序
        sorted_data = factor_data.sort_values(by=valid_factors[0], ascending=ascending)
        
        # 如果有多个因子，进行多重筛选
        if len(valid_factors) > 1:
            for factor in valid_factors[1:]:
                # 取前100名
                temp_data = sorted_data.head(min(100, len(sorted_data)))
                # 再按下一个因子排序
                sorted_data = temp_data.sort_values(by=factor, ascending=ascending)
        
        # 取前N名
        result = sorted_data.head(min(top_n, len(sorted_data)))
        
        # 添加股票名称和行业信息
        if self.stock_basics is not None and not self.stock_basics.empty:
            result = pd.merge(
                result, 
                self.stock_basics[['ts_code', 'name', 'industry']], 
                on='ts_code', 
                how='left'
            )
        
        return result
    
    def plot_factor_trends(self, ts_code, factors, start_date, end_date, save_path=None):
        """绘制股票技术因子趋势图
        
        Args:
            ts_code (str): 股票代码，如 000001.SZ
            factors (list): 因子名称列表, 例如 ['pe', 'turnover']
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            save_path (str, optional): 保存路径
        """
        # 获取技术因子数据
        factor_data = get_stk_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if factor_data.empty:
            print(f"未获取到股票{ts_code}在{start_date}至{end_date}期间的技术因子数据")
            return
        
        # 检查请求的因子是否存在于数据中
        valid_factors = [f for f in factors if f in factor_data.columns]
        if not valid_factors:
            print(f"请求的因子 {factors} 不存在于获取的数据中")
            print(f"可用的因子有: {', '.join(factor_data.columns)}")
            return
        
        # 股票名称
        stock_name = ts_code
        if self.stock_basics is not None and not self.stock_basics.empty:
            stock_info = self.stock_basics[self.stock_basics['ts_code'] == ts_code]
            if not stock_info.empty:
                stock_name = f"{stock_info.iloc[0]['name']} ({ts_code})"
        
        # 绘制因子趋势图
        n_factors = len(valid_factors)
        fig = plt.figure(figsize=(15, 3 * n_factors))
        gs = GridSpec(n_factors, 1, figure=fig)
        
        for i, factor in enumerate(valid_factors):
            ax = fig.add_subplot(gs[i, 0])
            ax.plot(factor_data['trade_date'], factor_data[factor], 'b-', linewidth=2)
            ax.set_title(f"{factor} - {stock_name}")
            ax.set_xlabel('日期')
            ax.set_ylabel(factor)
            ax.grid(True)
        
        plt.tight_layout()
        
        # 保存图片
        if save_path:
            plt.savefig(save_path)
        else:
            default_path = os.path.join(self.output_dir, f"{ts_code}_factor_trends.png")
            plt.savefig(default_path)
            print(f"图片已保存至: {default_path}")
        
        plt.close()
    
    def factor_correlation_analysis(self, factors, ts_codes=None, trade_date=None, start_date=None, end_date=None):
        """因子相关性分析
        
        Args:
            factors (list): 因子列表，如 ['macd', 'kdj_j', 'rsi_6']
            ts_codes (list, optional): 股票代码列表
            trade_date (str, optional): 交易日期，格式YYYYMMDD
            start_date (str, optional): 开始日期，格式YYYYMMDD
            end_date (str, optional): 结束日期，格式YYYYMMDD
            
        Returns:
            pd.DataFrame: 相关性矩阵
        """
        # 如果未提供股票列表，使用所有股票
        if not ts_codes:
            if self.stock_list is None:
                self.update_stock_list()
            ts_codes = self.stock_list['ts_code'].tolist()[:100]  # 限制为前100只股票，避免数据过大
        
        # 获取因子数据
        all_data = []
        for ts_code in ts_codes:
            df = get_stk_factor(ts_code=ts_code, trade_date=trade_date, 
                               start_date=start_date, end_date=end_date)
            if not df.empty:
                all_data.append(df)
        
        if not all_data:
            print("未获取到任何技术因子数据")
            return pd.DataFrame()
        
        # 合并所有数据
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # 计算因子之间的相关性
        factor_cols = [col for col in merged_df.columns if col in factors]
        if not factor_cols:
            print("未找到指定的因子列")
            return pd.DataFrame()
        
        correlation_matrix = merged_df[factor_cols].corr()
        return correlation_matrix
    
    def plot_correlation_heatmap(self, correlation_matrix, save_path=None):
        """绘制相关性热力图
        
        Args:
            correlation_matrix (pd.DataFrame): 相关性矩阵
            save_path (str, optional): 保存路径
            
        Returns:
            None
        """
        plt.figure(figsize=(12, 10))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('Factor Correlation Heatmap')
        
        # 保存图片
        if save_path:
            plt.savefig(save_path)
        else:
            default_path = os.path.join(self.output_dir, "factor_correlation_heatmap.png")
            plt.savefig(default_path)
            print(f"图片已保存至: {default_path}")
        
        plt.close() 