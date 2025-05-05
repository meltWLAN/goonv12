#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tushare行业数据提供器
专注于申万行业分类和概念板块，提供高效可靠的数据服务
"""

import os
import sys
import time
import json
import pickle
import logging
import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tushare_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TushareSectorProvider")

class TushareSectorProvider:
    """Tushare行业数据提供器，专注于申万行业和概念板块"""
    
    # 申万一级行业映射 (名称: 代码)
    SW_INDUSTRY_MAP = {
        '农林牧渔': '801010.SI', '采掘': '801020.SI', '化工': '801030.SI', 
        '钢铁': '801040.SI', '有色金属': '801050.SI', '电子': '801080.SI',
        '家用电器': '801110.SI', '食品饮料': '801120.SI', '纺织服装': '801130.SI',
        '轻工制造': '801140.SI', '医药生物': '801150.SI', '公用事业': '801160.SI',
        '交通运输': '801170.SI', '房地产': '801180.SI', '商业贸易': '801200.SI',
        '休闲服务': '801210.SI', '综合': '801230.SI', '建筑材料': '801710.SI',
        '建筑装饰': '801720.SI', '电气设备': '801730.SI', '国防军工': '801740.SI',
        '计算机': '801750.SI', '传媒': '801760.SI', '通信': '801770.SI',
        '银行': '801780.SI', '非银金融': '801790.SI', '汽车': '801880.SI',
        '机械设备': '801890.SI'
    }
    
    def __init__(self, token=None, cache_dir='data_cache/sectors', cache_expiry=1800):
        """初始化Tushare行业数据提供器
        
        Args:
            token: Tushare API Token，默认从环境变量或配置文件读取
            cache_dir: 缓存目录
            cache_expiry: 缓存过期时间(秒)，默认30分钟
        """
        self.cache_dir = cache_dir
        self.cache_expiry = cache_expiry
        self._cache = {}
        self._last_api_call = 0
        self.api_call_interval = 0.5  # API调用间隔(秒)
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化Tushare API
        self.token = token or self._get_token()
        self.pro = None
        self.is_pro_available = False
        self._init_tushare_api()
        
        # 加载本地缓存
        self._load_cache_from_disk()
        
    def _get_token(self) -> str:
        """从环境变量或配置文件获取Tushare API Token"""
        # 使用固定的Token
        default_token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        
        # 尝试从环境变量获取
        token = os.environ.get('TUSHARE_TOKEN')
        if token:
            logger.info(f"从环境变量获取Token: {token[:4]}...{token[-4:]}")
            return token
            
        # 尝试从配置文件获取
        try:
            config_files = [
                'config/api_keys.txt',
                'config/tushare_token.txt',
                '.tushare_token'
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    token_found = False
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            # 跳过注释和空行
                            if not line or line.startswith('#'):
                                continue
                            
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip().upper()
                                value = value.strip()
                                if key in ['TUSHARE_TOKEN', 'TOKEN']:
                                    token = value
                                    token_found = True
                                    logger.info(f"从配置文件 {config_file} 获取Token: {token[:4]}...{token[-4:]}")
                                    return token
                            else:
                                # 可能是单行token
                                potential_token = line.strip()
                                if len(potential_token) > 20:  # 简单判断是否为token
                                    token = potential_token
                                    token_found = True
                                    logger.info(f"从配置文件 {config_file} 获取Token: {token[:4]}...{token[-4:]}")
                                    return token
                    
                    if not token_found:
                        logger.warning(f"配置文件 {config_file} 中没有找到有效的Token")
        except Exception as e:
            logger.warning(f"读取配置文件出错: {str(e)}")
        
        # 使用默认Token
        logger.info(f"使用默认Token: {default_token[:4]}...{default_token[-4:]}")
        return default_token
    
    def _init_tushare_api(self) -> None:
        """初始化Tushare API"""
        try:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            
            # 验证Token有效性
            test_data = self.pro.trade_cal(exchange='SSE', start_date='20230101', end_date='20230110')
            if test_data is not None and not test_data.empty:
                self.is_pro_available = True
                logger.info(f"Tushare API 初始化成功")
            else:
                self.is_pro_available = False
                logger.error(f"Tushare API 返回空数据，可能无法访问或权限不足")
        except Exception as e:
            self.is_pro_available = False
            logger.error(f"Tushare API 初始化失败: {str(e)}")
    
    def _rate_limit(self) -> None:
        """API访问速率限制"""
        now = time.time()
        elapsed = now - self._last_api_call
        if elapsed < self.api_call_interval:
            time.sleep(self.api_call_interval - elapsed)
        self._last_api_call = time.time()
    
    def _save_to_cache(self, key: str, data: any) -> None:
        """保存数据到内存缓存和磁盘"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # 保存到磁盘
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.pkl")
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"数据已保存到磁盘: {key}")
        except Exception as e:
            logger.error(f"保存缓存到磁盘失败: {str(e)}")
    
    def _get_from_cache(self, key: str) -> Tuple[bool, any]:
        """从缓存获取数据
        
        Returns:
            (是否命中缓存, 数据)
        """
        current_time = time.time()
        
        # 检查内存缓存
        if key in self._cache:
            cache_item = self._cache[key]
            if current_time - cache_item['timestamp'] < self.cache_expiry:
                logger.debug(f"从内存缓存获取: {key}")
                return True, cache_item['data']
        
        # 检查磁盘缓存
        file_path = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(file_path):
            try:
                # 检查文件修改时间
                mod_time = os.path.getmtime(file_path)
                if current_time - mod_time < self.cache_expiry:
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                    
                    # 更新内存缓存
                    self._cache[key] = {
                        'data': data,
                        'timestamp': mod_time
                    }
                    
                    logger.debug(f"从磁盘缓存获取: {key}")
                    return True, data
            except Exception as e:
                logger.error(f"读取磁盘缓存失败: {str(e)}")
        
        return False, None
    
    def _load_cache_from_disk(self) -> None:
        """启动时加载磁盘缓存到内存"""
        if not os.path.exists(self.cache_dir):
            return
            
        try:
            files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
            if not files:
                return
                
            logger.info(f"加载磁盘缓存，共 {len(files)} 个文件")
            for file in files:
                key = file.replace('.pkl', '')
                file_path = os.path.join(self.cache_dir, file)
                mod_time = os.path.getmtime(file_path)
                
                try:
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                    
                    self._cache[key] = {
                        'data': data,
                        'timestamp': mod_time
                    }
                except Exception as e:
                    logger.error(f"加载缓存文件 {file} 失败: {str(e)}")
            
            logger.info(f"成功加载 {len(self._cache)} 个缓存项")
        except Exception as e:
            logger.error(f"加载缓存目录失败: {str(e)}")
    
    def get_sector_list(self) -> List[Dict]:
        """获取行业列表，包括申万行业和热门概念板块
        
        Returns:
            行业列表 [{'code': 代码, 'name': 名称, 'type': 类型}]
        """
        cache_key = 'sector_list'
        hit, data = self._get_from_cache(cache_key)
        if hit:
            return data
        
        sectors = []
        
        # 添加申万行业
        for name, code in self.SW_INDUSTRY_MAP.items():
            sectors.append({
                'code': code,
                'name': name, 
                'type': 'SW',
                'description': f'申万一级行业-{name}'
            })
        
        # 如果Tushare可用，获取概念板块
        if self.is_pro_available:
            try:
                self._rate_limit()
                concepts = self.pro.concept()
                
                if concepts is not None and not concepts.empty:
                    logger.info(f"获取到 {len(concepts)} 个概念板块")
                    # 只取前30个概念板块，避免太多
                    for _, row in concepts.head(30).iterrows():
                        sectors.append({
                            'code': row['code'],
                            'name': row['name'],
                            'type': 'TS',
                            'description': f'概念板块-{row["name"]}'
                        })
            except Exception as e:
                logger.error(f"获取概念板块失败: {str(e)}")
        
        # 保存到缓存
        self._save_to_cache(cache_key, sectors)
        return sectors
    
    def get_sector_history(self, sector_code: str, days: int = 90) -> Optional[pd.DataFrame]:
        """获取行业历史数据
        
        Args:
            sector_code: 行业代码
            days: 获取历史天数
            
        Returns:
            DataFrame包含行业历史数据 (日期索引, OHLCV数据)
        """
        cache_key = f'history_{sector_code}'
        hit, data = self._get_from_cache(cache_key)
        if hit:
            # 确保缓存的数据是真实数据
            if data.get('是真实数据', pd.Series([True] * len(data))).iloc[-1]:
                return data
            else:
                logger.warning(f"缓存中的行业 {sector_code} 数据不是真实数据，尝试重新获取")
        
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # 初始化结果
        hist_data = None
        
        # 如果是申万行业指数
        if sector_code.endswith('.SI') and sector_code.startswith('8'):
            if self.is_pro_available:
                try:
                    self._rate_limit()
                    logger.info(f"获取申万行业 {sector_code} 历史数据")
                    index_data = self.pro.index_daily(
                        ts_code=sector_code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if index_data is not None and not index_data.empty:
                        # 转换列名和格式
                        hist_data = index_data.rename(columns={
                            'trade_date': '日期',
                            'open': '开盘',
                            'high': '最高',
                            'low': '最低',
                            'close': '收盘',
                            'vol': '成交量',
                            'amount': '成交额',
                            'pct_chg': '涨跌幅'
                        })
                        
                        # 设置日期为索引
                        hist_data['日期'] = pd.to_datetime(hist_data['日期'])
                        hist_data = hist_data.set_index('日期')
                        
                        # 按日期升序排序
                        hist_data = hist_data.sort_index()
                        
                        # 添加一个标记列表示数据来源
                        hist_data['数据来源'] = 'tushare'
                        hist_data['是真实数据'] = True
                except Exception as e:
                    logger.error(f"获取申万行业历史数据失败: {str(e)}")
        
        # 如果是概念板块或者申万行业获取失败
        if hist_data is None or hist_data.empty:
            # 对于概念板块，尝试通过成分股合成指数
            try:
                if sector_code.startswith('TS'):
                    self._rate_limit()
                    logger.info(f"尝试获取概念板块 {sector_code} 的成分股")
                    
                    # 获取成分股
                    concept_stocks = self.pro.concept_detail(id=sector_code)
                    
                    if concept_stocks is not None and not concept_stocks.empty:
                        # 取前10个成分股代表整个板块
                        stock_codes = concept_stocks['ts_code'].tolist()[:10]
                        logger.info(f"使用 {len(stock_codes)} 只股票合成板块指数")
                        
                        # 获取每只股票的历史数据
                        stock_data_list = []
                        for code in stock_codes:
                            try:
                                self._rate_limit()
                                daily_data = self.pro.daily(
                                    ts_code=code,
                                    start_date=start_date,
                                    end_date=end_date
                                )
                                
                                if daily_data is not None and not daily_data.empty:
                                    stock_data_list.append(daily_data)
                            except Exception as e:
                                logger.warning(f"获取股票 {code} 历史数据失败: {str(e)}")
                        
                        # 如果获取到了股票数据
                        if stock_data_list:
                            # 合并所有股票数据
                            all_stock_data = pd.concat(stock_data_list)
                            
                            # 按日期分组计算均值
                            grouped = all_stock_data.groupby('trade_date').agg({
                                'open': 'mean',
                                'high': 'mean',
                                'low': 'mean',
                                'close': 'mean',
                                'vol': 'sum',
                                'amount': 'sum'
                            })
                            
                            # 重命名列
                            hist_data = grouped.rename(columns={
                                'open': '开盘',
                                'high': '最高',
                                'low': '最低',
                                'close': '收盘',
                                'vol': '成交量',
                                'amount': '成交额'
                            })
                            
                            # 转换日期并设为索引
                            hist_data.index = pd.to_datetime(hist_data.index)
                            
                            # 按日期升序排序
                            hist_data = hist_data.sort_index()
                            
                            # 添加来源标记
                            hist_data['数据来源'] = 'concept_stocks'
                            hist_data['是真实数据'] = True
                            
                            # 计算涨跌幅
                            hist_data['涨跌幅'] = hist_data['收盘'].pct_change() * 100
            except Exception as e:
                logger.error(f"通过成分股合成板块指数失败: {str(e)}")
        
        # 如果仍然没有数据，尝试使用模拟数据
        if hist_data is None or hist_data.empty:
            logger.warning(f"无法获取行业 {sector_code} 的真实数据，将使用模拟数据")
            try:
                hist_data = self._generate_mock_data(sector_code, days)
                # 标记为模拟数据
                if '是真实数据' not in hist_data.columns:
                    hist_data['是真实数据'] = False
            except Exception as e:
                logger.error(f"生成模拟数据也失败: {str(e)}")
                return None
        
        # 确保数据完整性
        if hist_data is not None and not hist_data.empty:
            # 保存到缓存
            self._save_to_cache(cache_key, hist_data)
            return hist_data
        
        return None
    
    def get_concept_details(self, concept_code: str) -> Optional[pd.DataFrame]:
        """获取概念板块详细信息和成分股
        
        Args:
            concept_code: 概念板块代码 (以TS开头)
            
        Returns:
            DataFrame包含概念板块成分股
        """
        if not concept_code.startswith('TS'):
            logger.error(f"无效的概念板块代码: {concept_code}，应以TS开头")
            return None
            
        cache_key = f'concept_detail_{concept_code}'
        hit, data = self._get_from_cache(cache_key)
        if hit:
            return data
            
        if not self.is_pro_available:
            logger.error("Tushare API不可用，无法获取概念板块详情")
            return None
            
        try:
            self._rate_limit()
            stocks = self.pro.concept_detail(id=concept_code)
            
            if stocks is not None and not stocks.empty:
                logger.info(f"获取到概念板块 {concept_code} 的 {len(stocks)} 只成分股")
                # 保存到缓存
                self._save_to_cache(cache_key, stocks)
                return stocks
            else:
                logger.warning(f"概念板块 {concept_code} 没有成分股数据")
                return None
        except Exception as e:
            logger.error(f"获取概念板块详情失败: {str(e)}")
            return None
    
    def _generate_mock_data(self, sector_code: str, days: int = 90) -> pd.DataFrame:
        """生成模拟行业数据 - 在无法获取真实数据时作为备选
        
        Args:
            sector_code: 行业代码
            days: 天数
            
        Returns:
            DataFrame模拟数据
        """
        logger.warning(f"无法获取行业 {sector_code} 的真实数据，生成模拟数据作为备选")
        
        # 创建日期范围
        end_date = datetime.now()
        dates = [(end_date - timedelta(days=i)).strftime('%Y%m%d') for i in range(days)]
        dates.reverse()  # 按日期升序排列
        
        # 设置基础价格
        base_price = 1000.0 + hash(sector_code) % 3000
        
        # 生成数据结构
        data = {
            '日期': pd.to_datetime(dates),
            '开盘': [],
            '最高': [],
            '最低': [],
            '收盘': [],
            '成交量': [],
            '成交额': [],
            '是模拟数据': [True] * len(dates)
        }
        
        # 生成价格序列
        price = base_price
        for i in range(len(dates)):
            # 生成随机变动
            change_pct = np.random.normal(0, 0.015)  # 正态分布的变动
            price = price * (1 + change_pct)
            
            # 生成其他价格
            open_price = price * (1 + np.random.normal(0, 0.005))
            high_price = max(price, open_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(price, open_price) * (1 - abs(np.random.normal(0, 0.005)))
            
            # 生成成交量和成交额
            volume = abs(change_pct) * 1000000 * (1 + np.random.normal(0, 0.3))
            amount = volume * price
            
            # 添加到数据中
            data['开盘'].append(open_price)
            data['最高'].append(high_price)
            data['最低'].append(low_price)
            data['收盘'].append(price)
            data['成交量'].append(volume)
            data['成交额'].append(amount)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        df.set_index('日期', inplace=True)
        
        logger.warning(f"已生成行业 {sector_code} 的模拟数据，共 {len(df)} 条记录")
        return df
    
    def get_latest_trading_day(self) -> str:
        """获取最近的交易日
        
        Returns:
            交易日期字符串 (YYYYMMDD)
        """
        cache_key = 'latest_trading_day'
        hit, data = self._get_from_cache(cache_key)
        if hit:
            # 如果缓存时间不超过1天，直接返回
            if time.time() - self._cache[cache_key]['timestamp'] < 86400:
                return data
        
        # 默认返回当前日期
        latest_day = datetime.now().strftime('%Y%m%d')
        
        if self.is_pro_available:
            try:
                self._rate_limit()
                # 获取最近10天的交易日历
                today = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
                
                calendar = self.pro.trade_cal(
                    exchange='SSE',
                    start_date=start_date,
                    end_date=today
                )
                
                if calendar is not None and not calendar.empty:
                    # 筛选交易日
                    trade_days = calendar[calendar['is_open'] == 1]['cal_date'].tolist()
                    if trade_days:
                        latest_day = trade_days[-1]
            except Exception as e:
                logger.error(f"获取最新交易日失败: {str(e)}")
        
        # 保存到缓存
        self._save_to_cache(cache_key, latest_day)
        return latest_day

    def clear_cache(self, older_than_days=None):
        """清除缓存
        
        Args:
            older_than_days: 只清除几天前的缓存，None表示清除所有
        """
        if older_than_days is None:
            # 清除所有内存缓存
            self._cache.clear()
            
            # 清除所有磁盘缓存
            if os.path.exists(self.cache_dir):
                for file in os.listdir(self.cache_dir):
                    if file.endswith('.pkl'):
                        try:
                            os.remove(os.path.join(self.cache_dir, file))
                        except Exception as e:
                            logger.error(f"删除缓存文件 {file} 失败: {str(e)}")
            
            logger.info("已清除所有缓存")
        else:
            # 计算截止时间
            cutoff_time = time.time() - older_than_days * 86400
            
            # 清除旧的内存缓存
            keys_to_remove = []
            for key, value in self._cache.items():
                if value['timestamp'] < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
            
            # 清除旧的磁盘缓存
            if os.path.exists(self.cache_dir):
                for file in os.listdir(self.cache_dir):
                    if file.endswith('.pkl'):
                        file_path = os.path.join(self.cache_dir, file)
                        try:
                            if os.path.getmtime(file_path) < cutoff_time:
                                os.remove(file_path)
                        except Exception as e:
                            logger.error(f"删除缓存文件 {file} 失败: {str(e)}")
            
            logger.info(f"已清除 {len(keys_to_remove)} 个超过 {older_than_days} 天的缓存项")

# 单例模式提供全局访问点
_instance = None

def get_sector_provider(token=None, cache_dir='data_cache/sectors', cache_expiry=1800):
    """获取TushareSectorProvider单例
    
    Args:
        token: Tushare API Token
        cache_dir: 缓存目录
        cache_expiry: 缓存过期时间(秒)
        
    Returns:
        TushareSectorProvider实例
    """
    global _instance
    if _instance is None:
        _instance = TushareSectorProvider(token, cache_dir, cache_expiry)
    return _instance

if __name__ == "__main__":
    # 简单测试
    provider = get_sector_provider()
    
    # 测试获取行业列表
    print("\n测试获取行业列表:")
    sectors = provider.get_sector_list()
    print(f"共获取到 {len(sectors)} 个行业")
    for i, sector in enumerate(sectors[:5]):  # 只显示前5个
        print(f"{i+1}. {sector['name']} ({sector['code']}) - {sector['type']}")
    
    # 测试获取行业历史数据
    if sectors:
        test_sector = sectors[0]
        print(f"\n测试获取行业 {test_sector['name']} 历史数据:")
        history = provider.get_sector_history(test_sector['code'], days=30)
        if history is not None:
            print(f"获取到 {len(history)} 条历史数据")
            print(history.head())
        else:
            print("获取历史数据失败")
    
    # 测试获取概念板块详情
    concept_sectors = [s for s in sectors if s['type'] == 'TS']
    if concept_sectors:
        test_concept = concept_sectors[0]
        print(f"\n测试获取概念板块 {test_concept['name']} 详情:")
        details = provider.get_concept_details(test_concept['code'])
        if details is not None:
            print(f"获取到 {len(details)} 只成分股")
            print(details.head())
        else:
            print("获取概念板块详情失败")
    
    print("\n测试完成！") 