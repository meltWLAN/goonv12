#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级智能行业分析模块
基于真实数据的行业分析系统，提供更准确的行业热点识别和分析
"""

import tushare as ts
import pandas as pd
import numpy as np
import talib as ta
import logging
import time
import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union

class AdvancedSectorAnalyzer:
    """高级智能行业分析器
    
    专注于使用真实数据进行行业分析，不使用模拟数据
    具有多级数据获取策略和高级分析算法
    """
    
    def __init__(self, token=None, top_n=10, cache_dir='data_cache/advanced_sectors'):
        """初始化高级行业分析器
        
        Args:
            token: Tushare API token，如果为None则尝试从环境变量获取
            top_n: 返回热门行业的数量
            cache_dir: 缓存目录
        """
        self.top_n = top_n
        self.cache_dir = cache_dir
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger('AdvancedSectorAnalyzer')
        self._setup_logging()
        
        # 初始化Tushare API
        self.token = token or os.environ.get('TUSHARE_TOKEN') or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.ts_api = None
        self._init_tushare_api()
        
        # 缓存和状态管理
        self.data_cache = {}
        self.cache_timestamps = {}
        self.cache_expiry = {
            'sector_list': 3600,        # 行业列表1小时过期
            'sector_history': 7200,     # 行业历史数据2小时过期
            'hot_sectors': 1800,        # 热门行业30分钟过期
            'north_flow': 3600,         # 北向资金1小时过期
        }
        
        # 数据质量控制
        self.real_data_threshold = 0.7  # 实时数据比例阈值
        
        # 行业分析参数
        self.analysis_depth = 90        # 分析历史数据的天数
        self.technical_params = {
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'volume_ma': 5,
            'price_ma': [5, 10, 20, 60]
        }
        
        self.logger.info("高级行业分析器初始化完成")
        
    def _setup_logging(self):
        """设置日志"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        
        self.logger.setLevel(logging.INFO)
        
    def _init_tushare_api(self):
        """初始化Tushare API连接"""
        try:
            ts.set_token(self.token)
            self.ts_api = ts.pro_api()
            
            # 验证API连接
            test_data = self.ts_api.trade_cal(exchange='SSE', start_date='20230101', end_date='20230110')
            if test_data is not None and not test_data.empty:
                self.logger.info(f"Tushare API初始化成功，Token: {self.token[:4]}...{self.token[-4:]}")
                return True
            else:
                self.logger.error("Tushare API返回空数据，请检查网络连接和Token")
                return False
        except Exception as e:
            self.logger.error(f"Tushare API初始化失败: {str(e)}")
            return False
    
    def get_sector_list(self) -> List[Dict]:
        """获取行业列表
        
        包括申万一级行业分类，返回标准化的行业信息
        
        返回:
            List[Dict]: 行业信息列表，每个行业包含代码、名称、指数等信息
        """
        cache_key = 'sector_list'
        
        # 检查缓存
        if self._check_cache(cache_key):
            self.logger.info("从缓存获取行业列表")
            return self.data_cache[cache_key]
        
        self.logger.info("从Tushare API获取行业列表")
        sectors = []
        
        try:
            # 获取申万一级行业
            sw_sectors = self.ts_api.index_classify(level='L1', src='SW')
            
            if sw_sectors is not None and not sw_sectors.empty:
                self.logger.info(f"获取到 {len(sw_sectors)} 个申万一级行业")
                
                # 获取最新交易日
                latest_trade_date = self._get_latest_trade_date()
                prev_trade_date = self._get_prev_trade_date(latest_trade_date, n=1)
                
                # 处理每个行业
                for _, row in sw_sectors.iterrows():
                    industry_code = row['index_code']
                    industry_name = row['industry_name']
                    
                    # 获取行业指数数据
                    index_data = self._get_index_data(industry_code, limit=2)
                    
                    # 提取关键指标
                    price = 0
                    change_pct = 0
                    volume = 0
                    
                    if index_data is not None and not index_data.empty:
                        latest_data = index_data.iloc[0]
                        price = latest_data.get('close', 0)
                        
                        # 计算涨跌幅
                        if len(index_data) > 1:
                            prev_data = index_data.iloc[1]
                            prev_close = prev_data.get('close', 0)
                            if prev_close > 0:
                                change_pct = (price - prev_close) / prev_close * 100
                        
                        # 成交量
                        volume = latest_data.get('amount', 0) / 100000000  # 转换为亿元
                    
                    # 创建行业信息字典
                    sector = {
                        'code': industry_code,
                        'name': industry_name,
                        'level': '申万一级',
                        'price': price,
                        'change_pct': change_pct,
                        'volume': volume,
                        'trade_date': latest_trade_date,
                        'source': '申万',
                        'is_real_data': True  # 标记为真实数据
                    }
                    
                    sectors.append(sector)
            else:
                self.logger.warning("无法获取申万行业分类数据")
        
        except Exception as e:
            self.logger.error(f"获取行业列表失败: {str(e)}")
        
        # 检查是否获取到足够的行业
        if not sectors:
            self.logger.warning("未能获取到任何行业数据，将使用备份数据")
            sectors = self._load_backup_sectors()
        
        # 更新缓存
        self._update_cache(cache_key, sectors)
        
        return sectors
    
    def _get_latest_trade_date(self) -> str:
        """获取最新交易日"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            cal_df = self.ts_api.trade_cal(exchange='SSE', start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'), end_date=today)
            if cal_df is not None and not cal_df.empty:
                # 过滤出开市日期并获取最新的
                open_dates = cal_df[cal_df['is_open'] == 1]['cal_date']
                if not open_dates.empty:
                    return open_dates.iloc[-1]
            return today  # 如果无法获取，返回今天的日期
        except Exception as e:
            self.logger.error(f"获取最新交易日失败: {str(e)}")
            return datetime.now().strftime('%Y%m%d')
    
    def _get_prev_trade_date(self, date_str: str, n: int = 1) -> str:
        """获取指定日期前n个交易日"""
        try:
            # 计算一个合理的开始日期，默认往前推30天足够找到n个交易日
            start_date = (datetime.strptime(date_str, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d')
            cal_df = self.ts_api.trade_cal(exchange='SSE', start_date=start_date, end_date=date_str)
            
            if cal_df is not None and not cal_df.empty:
                # 过滤出开市日期
                open_dates = cal_df[cal_df['is_open'] == 1]['cal_date'].tolist()
                # 找到当前日期的位置
                if date_str in open_dates:
                    idx = open_dates.index(date_str)
                    if idx >= n:
                        return open_dates[idx - n]
                
                # 如果找不到或者位置不够，返回列表中最早的日期
                return open_dates[0] if open_dates else date_str
            return date_str  # 如果无法获取，返回输入日期
        except Exception as e:
            self.logger.error(f"获取前一交易日失败: {str(e)}")
            return date_str
    
    def _get_index_data(self, index_code: str, start_date: str = None, end_date: str = None, limit: int = None) -> pd.DataFrame:
        """获取指数数据"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
                
            index_data = self.ts_api.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
            
            if index_data is not None and not index_data.empty:
                # 按日期降序排序
                index_data = index_data.sort_values('trade_date', ascending=False)
                
                # 如果有限制，只返回前n条
                if limit is not None:
                    return index_data.head(limit)
                return index_data
            
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"获取指数 {index_code} 数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _check_cache(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key in self.data_cache and key in self.cache_timestamps:
            # 获取过期时间，默认1小时
            expiry = self.cache_expiry.get(key, 3600)
            # 判断是否过期
            return (time.time() - self.cache_timestamps[key]) < expiry
        return False
    
    def _update_cache(self, key: str, data: any) -> None:
        """更新缓存"""
        self.data_cache[key] = data
        self.cache_timestamps[key] = time.time()
        
        # 同时保存到磁盘
        self._save_to_disk(key, data)
    
    def _save_to_disk(self, key: str, data: any) -> None:
        """保存数据到磁盘缓存"""
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.pkl")
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            self.logger.debug(f"数据已保存到磁盘: {file_path}")
        except Exception as e:
            self.logger.error(f"保存数据到磁盘失败: {str(e)}")
    
    def _load_from_disk(self, key: str) -> any:
        """从磁盘加载数据"""
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.pkl")
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                self.logger.debug(f"从磁盘加载数据: {file_path}")
                return data
        except Exception as e:
            self.logger.error(f"从磁盘加载数据失败: {str(e)}")
        return None
    
    def _load_backup_sectors(self) -> List[Dict]:
        """加载备份的行业数据"""
        backup_data = self._load_from_disk('sector_list')
        if backup_data:
            self.logger.info(f"成功加载备份行业数据，共 {len(backup_data)} 个行业")
            return backup_data
            
        # 如果没有备份，返回一个空列表
        self.logger.warning("没有可用的行业备份数据")
        return []
    
    def get_sector_history(self, sector_code: str, sector_name: str = None, days: int = 90) -> pd.DataFrame:
        """获取行业历史数据
        
        Args:
            sector_code: 行业代码
            sector_name: 行业名称(可选)
            days: 历史数据天数
            
        Returns:
            pd.DataFrame: 行业历史数据
        """
        cache_key = f"history_{sector_code}"
        
        # 检查缓存
        if self._check_cache(cache_key):
            self.logger.debug(f"从缓存获取行业 {sector_name or sector_code} 历史数据")
            return self.data_cache[cache_key]
        
        self.logger.info(f"获取行业 {sector_name or sector_code} 历史数据")
        
        # 计算起始日期
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        try:
            # 获取行业指数历史数据
            history_data = self.ts_api.index_daily(ts_code=sector_code, start_date=start_date, end_date=end_date)
            
            if history_data is not None and not history_data.empty:
                # 对列名进行标准化，保证后续处理一致性
                column_map = {
                    'trade_date': '日期',
                    'open': '开盘',
                    'high': '最高',
                    'low': '最低',
                    'close': '收盘',
                    'vol': '成交量',
                    'amount': '成交额',
                    'pct_chg': '涨跌幅'
                }
                
                # 重命名列
                history_data = history_data.rename(columns={k: v for k, v in column_map.items() if k in history_data.columns})
                
                # 添加标记，标识为真实数据
                history_data['是真实数据'] = True
                
                # 按日期升序排序
                if '日期' in history_data.columns:
                    history_data = history_data.sort_values('日期')
                
                # 缓存数据
                self._update_cache(cache_key, history_data)
                
                self.logger.info(f"成功获取行业 {sector_name or sector_code} 历史数据，共 {len(history_data)} 条记录")
                return history_data
            else:
                self.logger.warning(f"行业 {sector_name or sector_code} 没有返回历史数据")
                
                # 尝试获取成分股并计算指数
                if sector_name:
                    self.logger.info(f"尝试通过成分股计算行业 {sector_name} 指数")
                    component_df = self._calculate_index_from_components(sector_code)
                    
                    if component_df is not None and not component_df.empty:
                        self._update_cache(cache_key, component_df)
                        return component_df
        
        except Exception as e:
            self.logger.error(f"获取行业 {sector_name or sector_code} 历史数据失败: {str(e)}")
        
        # 尝试从磁盘加载备份数据
        backup_data = self._load_from_disk(cache_key)
        if backup_data is not None:
            self.logger.info(f"使用备份数据: {sector_name or sector_code}")
            # 更新内存缓存但不写入磁盘
            self.data_cache[cache_key] = backup_data
            self.cache_timestamps[cache_key] = time.time()
            return backup_data
        
        self.logger.error(f"无法获取行业 {sector_name or sector_code} 历史数据")
        return pd.DataFrame()
    
    def _calculate_index_from_components(self, sector_code: str) -> pd.DataFrame:
        """通过成分股计算行业指数
        
        当无法直接获取行业指数时，使用成分股加权计算
        
        Args:
            sector_code: 行业代码
            
        Returns:
            pd.DataFrame: 计算的行业指数历史数据
        """
        try:
            # 获取行业成分股
            components = self.ts_api.index_member(index_code=sector_code)
            
            if components is not None and not components.empty:
                self.logger.info(f"获取到行业 {sector_code} 的 {len(components)} 个成分股")
                
                # 最多使用10个成分股避免请求过多
                component_stocks = components['con_code'].head(10).tolist()
                
                # 设置日期范围
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
                
                # 获取每个成分股的历史数据
                stock_data_list = []
                
                for stock_code in component_stocks:
                    try:
                        # 加入延迟避免请求过快
                        time.sleep(0.5)
                        
                        stock_data = self.ts_api.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
                        if stock_data is not None and not stock_data.empty:
                            stock_data_list.append(stock_data)
                    except Exception as e:
                        self.logger.warning(f"获取股票 {stock_code} 数据失败: {str(e)}")
                
                if stock_data_list:
                    # 合并所有成分股数据
                    all_data = pd.concat(stock_data_list)
                    
                    # 按日期分组并计算指数
                    index_data = all_data.groupby('trade_date').agg({
                        'open': 'mean',
                        'high': 'mean',
                        'low': 'mean',
                        'close': 'mean',
                        'vol': 'sum',
                        'amount': 'sum'
                    }).reset_index()
                    
                    # 计算涨跌幅
                    index_data['pct_chg'] = index_data['close'].pct_change() * 100
                    
                    # 重命名列
                    column_map = {
                        'trade_date': '日期',
                        'open': '开盘',
                        'high': '最高',
                        'low': '最低',
                        'close': '收盘',
                        'vol': '成交量',
                        'amount': '成交额',
                        'pct_chg': '涨跌幅'
                    }
                    
                    index_data = index_data.rename(columns={k: v for k, v in column_map.items() if k in index_data.columns})
                    
                    # 添加标记，标识为合成数据
                    index_data['是真实数据'] = False
                    index_data['是合成数据'] = True
                    
                    # 按日期升序排序
                    if '日期' in index_data.columns:
                        index_data = index_data.sort_values('日期')
                    
                    self.logger.info(f"通过成分股合成行业指数成功，共计 {len(index_data)} 条记录")
                    return index_data
            
            self.logger.warning(f"行业 {sector_code} 没有成分股或无法获取成分股数据")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"通过成分股计算行业指数失败: {str(e)}")
            return pd.DataFrame()
    
    def get_north_flow(self) -> float:
        """获取北向资金流入
        
        Returns:
            float: 北向资金净流入金额(亿元)
        """
        cache_key = 'north_flow'
        
        # 检查缓存
        if self._check_cache(cache_key):
            self.logger.debug("从缓存获取北向资金数据")
            return self.data_cache[cache_key]
        
        self.logger.info("获取北向资金流入数据")
        
        try:
            # 获取最新交易日
            today = self._get_latest_trade_date()
            
            # 尝试获取当天数据
            north_data = self.ts_api.moneyflow_hsgt(trade_date=today)
            
            # 如果当天数据为空，尝试获取前一天
            if north_data is None or north_data.empty:
                yesterday = self._get_prev_trade_date(today)
                north_data = self.ts_api.moneyflow_hsgt(trade_date=yesterday)
            
            if north_data is not None and not north_data.empty:
                # 计算北向资金
                north_money = north_data['north_money'].sum() / 100000000  # 转换为亿元
                self.logger.info(f"北向资金净流入: {north_money:.2f}亿元")
                
                # 更新缓存
                self._update_cache(cache_key, north_money)
                
                return north_money
            else:
                self.logger.warning("未能获取北向资金数据")
        
        except Exception as e:
            self.logger.error(f"获取北向资金数据失败: {str(e)}")
        
        # 使用备份数据或默认值
        backup_data = self._load_from_disk(cache_key)
        if backup_data is not None:
            self.logger.info(f"使用备份北向资金数据: {backup_data:.2f}亿元")
            return backup_data
        
        # 无法获取数据时，返回0
        self.logger.warning("无法获取北向资金数据，使用默认值0")
        return 0.0
    
    def analyze_hot_sectors(self) -> Dict:
        """分析当前热门行业
        
        综合考虑涨跌幅、成交量、技术指标等因素识别热门行业
        
        Returns:
            Dict: 热门行业分析结果
        """
        cache_key = 'hot_sectors_result'
        
        # 检查缓存
        if self._check_cache(cache_key):
            self.logger.info("从缓存获取热门行业分析结果")
            return self.data_cache[cache_key]
        
        self.logger.info("开始分析热门行业...")
        
        try:
            # 获取行业列表
            sectors = self.get_sector_list()
            
            if not sectors:
                self.logger.error("无法获取行业列表数据")
                return {
                    'status': 'error',
                    'message': '无法获取行业列表数据',
                    'data': {}
                }
            
            # 获取北向资金
            north_flow = self.get_north_flow()
            
            # 分析每个行业
            hot_sectors = []
            sectors_with_incomplete_data = []
            
            for sector in sectors:
                try:
                    sector_code = sector['code']
                    sector_name = sector['name']
                    
                    # 获取行业历史数据
                    hist_data = self.get_sector_history(sector_code, sector_name)
                    
                    if hist_data.empty:
                        self.logger.warning(f"行业 {sector_name} 没有历史数据，跳过分析")
                        continue
                    
                    # 检查数据质量
                    is_real_data = True
                    if '是真实数据' in hist_data.columns:
                        is_real_data = hist_data['是真实数据'].all()
                    
                    if not is_real_data:
                        sectors_with_incomplete_data.append(sector_name)
                    
                    # 计算技术指标
                    if '收盘' not in hist_data.columns:
                        self.logger.warning(f"行业 {sector_name} 历史数据缺少收盘价列，跳过分析")
                        continue
                    
                    close_prices = hist_data['收盘'].astype(float).values
                    
                    # 1. MACD指标
                    macd, macdsignal, macdhist = ta.MACD(
                        close_prices,
                        fastperiod=self.technical_params['macd_fast'],
                        slowperiod=self.technical_params['macd_slow'],
                        signalperiod=self.technical_params['macd_signal']
                    )
                    
                    # 2. RSI指标
                    rsi = ta.RSI(close_prices, timeperiod=self.technical_params['rsi_period'])
                    
                    # 3. 均线
                    ma_data = {}
                    for period in self.technical_params['price_ma']:
                        ma_data[f'MA{period}'] = ta.MA(close_prices, timeperiod=period)
                    
                    # 4. 成交量分析
                    volume = 0
                    volume_change = 0
                    if '成交量' in hist_data.columns:
                        volumes = hist_data['成交量'].astype(float).values
                        if len(volumes) > 0:
                            volume = volumes[-1]
                            if len(volumes) > 1:
                                volume_change = (volume / volumes[-2] - 1) * 100 if volumes[-2] > 0 else 0
                    
                    # 计算行业热度得分
                    
                    # 1. 涨跌幅分数 (40%)
                    change_pct = float(sector.get('change_pct', 0))
                    change_score = min(max(change_pct * 10, 0), 100)  # 转换为0-100分
                    
                    # 2. 成交量分数 (20%)
                    volume_score = min(volume / 10000000 * 5, 100)  # 转换为0-100分
                    
                    # 3. 技术指标分数 (30%)
                    tech_score = 0
                    
                    # MACD金叉加分
                    if len(macd) > 1 and macd[-1] > macdsignal[-1] and macd[-2] <= macdsignal[-2]:
                        tech_score += 30
                    
                    # MACD值由负转正加分
                    if len(macd) > 1 and macd[-1] > 0 and macd[-2] <= 0:
                        tech_score += 20
                    
                    # RSI位于上升区间加分
                    if len(rsi) > 0 and 40 <= rsi[-1] <= 70:
                        tech_score += 15
                    
                    # 价格站上多条均线加分
                    ma_count = 0
                    for period in self.technical_params['price_ma']:
                        ma_values = ma_data[f'MA{period}']
                        if len(ma_values) > 0 and len(close_prices) > 0 and close_prices[-1] > ma_values[-1]:
                            ma_count += 1
                    
                    tech_score += min(ma_count * 5, 20)  # 最多加20分
                    
                    # 将技术分数限制在0-100之间
                    tech_score = min(tech_score, 100)
                    
                    # 4. 数据质量分数 (10%)
                    quality_score = 100 if is_real_data else 50
                    
                    # 计算综合得分
                    hot_score = (
                        change_score * 0.4 +
                        volume_score * 0.2 +
                        tech_score * 0.3 +
                        quality_score * 0.1
                    )
                    
                    # 生成分析原因
                    analysis_reason = self._generate_analysis_reason(
                        change_pct, volume_change, 
                        macd[-1] if len(macd) > 0 else 0, 
                        macdsignal[-1] if len(macdsignal) > 0 else 0,
                        rsi[-1] if len(rsi) > 0 else 0
                    )
                    
                    # 添加到热门行业列表
                    hot_sectors.append({
                        'code': sector_code,
                        'name': sector_name,
                        'hot_score': hot_score,
                        'change_pct': change_pct,
                        'volume': volume,
                        'macd': float(macd[-1]) if len(macd) > 0 else 0,
                        'rsi': float(rsi[-1]) if len(rsi) > 0 else 0,
                        'analysis_reason': analysis_reason,
                        'is_real_data': is_real_data
                    })
                
                except Exception as e:
                    self.logger.error(f"分析行业 {sector.get('name', sector_code)} 时出错: {str(e)}")
            
            # 按热度分数排序
            hot_sectors.sort(key=lambda x: x['hot_score'], reverse=True)
            
            # 限制返回数量
            top_sectors = hot_sectors[:self.top_n]
            
            # 优先返回有真实数据的行业
            real_data_sectors = [s for s in top_sectors if s.get('is_real_data', False)]
            
            if len(real_data_sectors) >= self.top_n:
                top_sectors = real_data_sectors[:self.top_n]
            
            # 组织返回结果
            result = {
                'status': 'success',
                'message': 'success',
                'data': {
                    'hot_sectors': top_sectors,
                    'north_flow': north_flow,
                    'incomplete_data_count': len(sectors_with_incomplete_data),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_source': 'Tushare真实数据'
                }
            }
            
            # 更新缓存
            self._update_cache(cache_key, result)
            
            return result
        
        except Exception as e:
            self.logger.error(f"分析热门行业失败: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'data': {}
            }
    
    def _generate_analysis_reason(self, change_pct: float, volume_change: float, 
                                 macd: float, macd_signal: float, rsi: float) -> str:
        """生成行业分析原因"""
        reasons = []
        
        # 涨跌幅分析
        if change_pct > 3:
            reasons.append("强势上涨")
        elif change_pct > 1:
            reasons.append("稳步上涨")
        elif change_pct < -3:
            reasons.append("大幅回调")
        elif change_pct < -1:
            reasons.append("小幅回调")
        else:
            reasons.append("窄幅波动")
        
        # 成交量分析
        if volume_change > 30:
            reasons.append("成交量大幅放大")
        elif volume_change > 10:
            reasons.append("成交量温和放大")
        elif volume_change < -30:
            reasons.append("成交量大幅萎缩")
        
        # MACD分析
        if macd > 0 and macd > macd_signal:
            reasons.append("MACD金叉形成")
        elif macd < 0 and macd < macd_signal:
            reasons.append("MACD死叉形成")
        
        # RSI分析
        if rsi > 70:
            reasons.append("RSI超买")
        elif rsi < 30:
            reasons.append("RSI超卖")
        elif 50 < rsi < 70:
            reasons.append("RSI走强")
        elif 30 < rsi < 50:
            reasons.append("RSI企稳回升")
        
        return "，".join(reasons)
    
    def generate_sector_report(self) -> Dict:
        """生成行业分析报告
        
        全面分析行业情况，包括热门行业、市场趋势等
        
        Returns:
            Dict: 行业分析报告
        """
        self.logger.info("开始生成行业分析报告...")
        
        try:
            # 获取热门行业
            hot_sectors_result = self.analyze_hot_sectors()
            if hot_sectors_result['status'] != 'success':
                return hot_sectors_result
            
            hot_sectors = hot_sectors_result['data']['hot_sectors']
            north_flow = hot_sectors_result['data']['north_flow']
            
            # 获取所有行业
            all_sectors = self.get_sector_list()
            
            # 计算市场整体情况
            up_sectors = sum(1 for s in all_sectors if s['change_pct'] > 0)
            down_sectors = sum(1 for s in all_sectors if s['change_pct'] < 0)
            flat_sectors = len(all_sectors) - up_sectors - down_sectors
            
            avg_change = np.mean([s['change_pct'] for s in all_sectors])
            
            # 判断市场趋势
            market_trend = "中性"
            if avg_change > 1.5:
                market_trend = "强势上涨"
            elif avg_change > 0.5:
                market_trend = "温和上涨"
            elif avg_change < -1.5:
                market_trend = "明显下跌"
            elif avg_change < -0.5:
                market_trend = "小幅下跌"
            
            # 生成报告
            report = {
                'status': 'success',
                'data': {
                    'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'market_summary': {
                        'avg_change': avg_change,
                        'up_sectors': up_sectors,
                        'down_sectors': down_sectors,
                        'flat_sectors': flat_sectors,
                        'market_trend': market_trend,
                        'north_flow': north_flow
                    },
                    'hot_sectors': hot_sectors,
                    'sector_distribution': {
                        'up_ratio': up_sectors / len(all_sectors) if len(all_sectors) > 0 else 0,
                        'down_ratio': down_sectors / len(all_sectors) if len(all_sectors) > 0 else 0,
                        'flat_ratio': flat_sectors / len(all_sectors) if len(all_sectors) > 0 else 0
                    },
                    'analysis_conclusion': self._generate_market_conclusion(avg_change, up_sectors, down_sectors, north_flow)
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成行业分析报告失败: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'data': {}
            }
    
    def _generate_market_conclusion(self, avg_change: float, up_sectors: int, down_sectors: int, north_flow: float) -> str:
        """生成市场结论"""
        conclusion = ""
        
        # 市场趋势
        if avg_change > 1.5:
            conclusion += "市场整体呈强势上涨态势，"
        elif avg_change > 0.5:
            conclusion += "市场整体呈温和上涨态势，"
        elif avg_change < -1.5:
            conclusion += "市场整体呈明显下跌态势，"
        elif avg_change < -0.5:
            conclusion += "市场整体呈小幅下跌态势，"
        else:
            conclusion += "市场整体呈窄幅震荡态势，"
        
        # 行业涨跌
        if up_sectors > down_sectors * 2:
            conclusion += "绝大多数行业上涨。"
        elif up_sectors > down_sectors:
            conclusion += "上涨行业占优。"
        elif down_sectors > up_sectors * 2:
            conclusion += "绝大多数行业下跌。"
        elif down_sectors > up_sectors:
            conclusion += "下跌行业占优。"
        else:
            conclusion += "行业涨跌互现。"
        
        # 北向资金
        if north_flow > 30:
            conclusion += " 北向资金大幅流入，市场情绪乐观。"
        elif north_flow > 10:
            conclusion += " 北向资金适度流入，市场情绪偏积极。"
        elif north_flow < -30:
            conclusion += " 北向资金大幅流出，市场情绪谨慎。"
        elif north_flow < -10:
            conclusion += " 北向资金适度流出，市场情绪偏谨慎。"
        
        return conclusion
    
# 如果直接运行此文件，执行简单测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 初始化分析器
    analyzer = AdvancedSectorAnalyzer()
    
    # 获取行业列表
    sectors = analyzer.get_sector_list()
    print(f"获取到 {len(sectors)} 个行业")
    
    # 分析热门行业
    result = analyzer.analyze_hot_sectors()
    if result['status'] == 'success':
        hot_sectors = result['data']['hot_sectors']
        print("\n热门行业排名:")
        for i, sector in enumerate(hot_sectors, 1):
            print(f"{i}. {sector['name']} (热度: {sector['hot_score']:.2f}) - {sector['analysis_reason']}")
    else:
        print(f"分析失败: {result['message']}")
    
    # 生成行业报告
    report = analyzer.generate_sector_report()
    if report['status'] == 'success':
        market_summary = report['data']['market_summary']
        print(f"\n市场概况:")
        print(f"平均涨跌幅: {market_summary['avg_change']:.2f}%")
        print(f"上涨行业: {market_summary['up_sectors']}，下跌行业: {market_summary['down_sectors']}，平稳行业: {market_summary['flat_sectors']}")
        print(f"北向资金: {market_summary['north_flow']:.2f}亿元")
        print(f"\n分析结论: {report['data']['analysis_conclusion']}") 