#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取真实行业数据脚本
根据测试结果优化的Tushare行业数据获取方案
"""

import os
import sys
import time
import pickle
import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("real_sector_data.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RealSectorData")

class RealSectorDataFetcher:
    """真实行业数据获取器"""
    
    def __init__(self, token=None, cache_dir='data_cache/advanced_sectors'):
        """初始化
        
        Args:
            token: Tushare API token
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        
        # 创建缓存目录
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # 初始化Tushare API
        self.token = token or self._load_token()
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        # 测试API连接
        self._test_api_connection()
    
    def _load_token(self):
        """从配置文件加载Token"""
        config_path = 'config/api_keys.txt'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('TUSHARE_TOKEN='):
                            token = line.strip().split('=')[1]
                            return token
            except Exception as e:
                logger.error(f"读取Token配置失败: {str(e)}")
        
        # 使用默认Token
        return '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    
    def _test_api_connection(self):
        """测试API连接"""
        try:
            # 简单测试 - 获取交易日历
            cal = self.pro.trade_cal(exchange='SSE', start_date='20250401', end_date='20250430')
            if cal is not None and not cal.empty:
                logger.info(f"Tushare API连接正常，Token: {self.token[:4]}...{self.token[-4:]}")
                return True
            else:
                logger.error("Tushare API返回空数据")
                return False
        except Exception as e:
            logger.error(f"Tushare API连接失败: {str(e)}")
            return False
    
    def _save_to_cache(self, key, data):
        """保存数据到缓存"""
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.pkl")
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"数据已保存到缓存: {key}")
            return True
        except Exception as e:
            logger.error(f"保存缓存失败: {str(e)}")
            return False
    
    def _get_from_cache(self, key):
        """从缓存获取数据"""
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.pkl")
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                logger.info(f"从缓存读取数据: {key}")
                return data
            return None
        except Exception as e:
            logger.error(f"读取缓存失败: {str(e)}")
            return None
    
    def _get_latest_trade_date(self):
        """获取最新交易日"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            cal_df = self.pro.trade_cal(exchange='SSE', start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'), end_date=today)
            if not cal_df.empty:
                open_dates = cal_df[cal_df['is_open'] == 1]['cal_date']
                if not open_dates.empty:
                    return open_dates.iloc[-1]
            return today
        except Exception as e:
            logger.error(f"获取最新交易日失败: {str(e)}")
            return datetime.now().strftime('%Y%m%d')
    
    def fetch_industry_list(self):
        """获取行业列表
        
        根据测试结果，不使用src='SW'参数，避免返回空数据
        """
        logger.info("获取行业列表")
        
        try:
            # 方法1: 不带参数获取完整行业列表，然后筛选
            industries = self.pro.index_classify()
            if industries is not None and not industries.empty:
                # 筛选一级行业
                l1_industries = industries[industries['level'] == 'L1']
                
                if not l1_industries.empty:
                    logger.info(f"成功获取一级行业列表，共 {len(l1_industries)} 个行业")
                    
                    # 转换为标准格式
                    latest_trade_date = self._get_latest_trade_date()
                    sectors = []
                    
                    for _, row in l1_industries.iterrows():
                        sector = {
                            'code': row['index_code'],
                            'name': row['industry_name'],
                            'level': '一级行业',
                            'price': 0,
                            'change_pct': 0,
                            'volume': 0,
                            'trade_date': latest_trade_date,
                            'source': row.get('src', 'SW'),
                            'is_real_data': True
                        }
                        sectors.append(sector)
                    
                    # 保存到缓存
                    self._save_to_cache('sector_list', sectors)
                    return sectors
                else:
                    logger.warning("未找到一级行业")
            
            logger.warning("未能获取行业列表，尝试使用概念板块")
            return self.fetch_concept_list()
            
        except Exception as e:
            logger.error(f"获取行业列表失败: {str(e)}")
            return self.fetch_concept_list()
    
    def fetch_concept_list(self):
        """获取概念板块列表作为备选"""
        logger.info("获取概念板块列表")
        
        try:
            concepts = self.pro.concept()
            if concepts is not None and not concepts.empty:
                logger.info(f"成功获取概念板块列表，共 {len(concepts)} 个概念")
                
                # 选取前15个概念作为主要行业
                top_concepts = concepts.head(15)
                
                # 转换为标准格式
                latest_trade_date = self._get_latest_trade_date()
                sectors = []
                
                for _, row in top_concepts.iterrows():
                    sector = {
                        'code': row['code'],
                        'name': row['name'],
                        'level': '概念板块',
                        'price': 0,
                        'change_pct': 0,
                        'volume': 0,
                        'trade_date': latest_trade_date,
                        'source': '概念板块',
                        'is_real_data': True
                    }
                    sectors.append(sector)
                
                # 保存到缓存
                self._save_to_cache('sector_list', sectors)
                return sectors
            
            logger.error("未能获取概念板块列表")
            return []
            
        except Exception as e:
            logger.error(f"获取概念板块列表失败: {str(e)}")
            return []
    
    def fetch_industry_components(self, industry_code):
        """获取行业成分股
        
        根据测试结果，index_member可以正常工作
        """
        logger.info(f"获取行业 {industry_code} 的成分股")
        
        try:
            components = self.pro.index_member(index_code=industry_code)
            if components is not None and not components.empty:
                logger.info(f"成功获取行业成分股，共 {len(components)} 个股票")
                
                # 获取当前成分股（is_new为Y或无out_date的记录）
                current_components = components[(components['is_new'] == 'Y') | (components['out_date'].isna())]
                
                if current_components.empty:
                    # 如果没有当前成分股，取最新的几个
                    current_components = components.sort_values('in_date', ascending=False).head(10)
                
                # 提取股票代码列表
                stock_codes = current_components['con_code'].tolist()
                
                logger.info(f"当前成分股: {stock_codes[:5]}...")
                return stock_codes
            
            logger.warning(f"未能获取行业 {industry_code} 的成分股")
            return []
            
        except Exception as e:
            logger.error(f"获取行业成分股失败: {str(e)}")
            return []
    
    def fetch_stock_daily_data(self, stock_code, start_date, end_date):
        """获取股票日线数据"""
        try:
            data = self.pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
            if data is not None and not data.empty:
                logger.info(f"成功获取股票 {stock_code} 的日线数据，共 {len(data)} 条记录")
                return data
            
            logger.warning(f"未能获取股票 {stock_code} 的日线数据")
            return None
            
        except Exception as e:
            logger.error(f"获取股票日线数据失败: {str(e)}")
            return None
    
    def build_industry_index(self, industry_code, industry_name):
        """构建行业指数
        
        基于成分股数据构建综合行业指数
        """
        logger.info(f"构建行业 {industry_name} 指数")
        
        # 获取日期范围
        end_date = self._get_latest_trade_date()
        start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=60)).strftime('%Y%m%d')
        
        # 获取行业成分股
        stock_codes = self.fetch_industry_components(industry_code)
        
        if not stock_codes:
            logger.warning(f"行业 {industry_name} 无成分股，无法构建指数")
            return None
        
        # 最多取前10个成分股
        stock_codes = stock_codes[:10]
        
        # 获取成分股数据
        stock_data_list = []
        for stock_code in stock_codes:
            data = self.fetch_stock_daily_data(stock_code, start_date, end_date)
            if data is not None and not data.empty:
                stock_data_list.append(data)
                # 避免频繁请求
                time.sleep(0.5)
        
        if not stock_data_list:
            logger.warning(f"行业 {industry_name} 无成分股数据，无法构建指数")
            return None
        
        try:
            # 合并成分股数据
            combined_data = pd.concat(stock_data_list)
            
            # 按日期分组
            grouped = combined_data.groupby('trade_date')
            
            # 计算综合指数
            index_data = grouped.agg({
                'open': 'mean',
                'high': 'mean',
                'low': 'mean',
                'close': 'mean',
                'vol': 'sum',
                'amount': 'sum'
            }).reset_index()
            
            # 计算涨跌幅
            index_data['pre_close'] = index_data['close'].shift(-1)
            index_data['pct_chg'] = (index_data['close'] - index_data['pre_close']) / index_data['pre_close'] * 100
            
            # 按日期升序排序
            index_data = index_data.sort_values('trade_date')
            
            # 重命名列以匹配标准格式
            index_data = index_data.rename(columns={
                'trade_date': '日期',
                'open': '开盘',
                'high': '最高',
                'low': '最低',
                'close': '收盘',
                'vol': '成交量',
                'amount': '成交额',
                'pct_chg': '涨跌幅'
            })
            
            # 添加标记
            index_data['是真实数据'] = True
            index_data['是合成数据'] = True
            
            logger.info(f"成功构建行业 {industry_name} 指数，共 {len(index_data)} 条记录")
            
            # 保存到缓存
            self._save_to_cache(f'history_{industry_code}', index_data)
            
            return index_data
            
        except Exception as e:
            logger.error(f"构建行业指数失败: {str(e)}")
            return None
    
    def fetch_all_industry_data(self):
        """获取所有行业数据"""
        # 获取行业列表
        sectors = self.fetch_industry_list()
        
        if not sectors:
            logger.error("未能获取行业列表")
            return False
        
        # 保存行业列表
        self._save_to_cache('sector_list', sectors)
        
        # 限制处理的行业数量，避免请求过多
        max_sectors = 10
        if len(sectors) > max_sectors:
            logger.info(f"限制为前 {max_sectors} 个行业")
            sectors = sectors[:max_sectors]
        
        # 为每个行业获取历史数据
        success_count = 0
        for sector in sectors:
            sector_code = sector['code']
            sector_name = sector['name']
            
            # 构建行业指数
            data = self.build_industry_index(sector_code, sector_name)
            if data is not None:
                success_count += 1
            
            # 避免频繁请求
            time.sleep(1)
        
        logger.info(f"行业数据获取完成，成功 {success_count}/{len(sectors)} 个行业")
        return success_count > 0

def main():
    """主函数"""
    print("\n===== 真实行业数据获取工具 =====\n")
    
    fetcher = RealSectorDataFetcher()
    
    print("\n1. 获取行业列表...")
    sectors = fetcher.fetch_industry_list()
    if sectors:
        print(f"成功获取行业列表，共 {len(sectors)} 个行业")
        print("行业列表示例:")
        for sector in sectors[:5]:
            print(f"  - {sector['name']} (代码: {sector['code']})")
    else:
        print("获取行业列表失败")
    
    print("\n2. 获取所有行业数据...")
    if fetcher.fetch_all_industry_data():
        print("行业数据获取成功")
    else:
        print("行业数据获取失败")
    
    print("\n获取完成！现在可以运行股票分析系统，它将使用真实数据。")
    print("运行命令: python stock_analyzer_app.py")

if __name__ == "__main__":
    main() 