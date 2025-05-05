#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AKShare行业数据提供器
使用AKShare库获取真实的申万行业和概念板块数据
"""

import os
import sys
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import pickle
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("akshare_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AKShareSectorProvider")

# 导入AKShare库
try:
    import akshare as ak
    logger.info(f"AKShare版本: {ak.__version__}")
except ImportError:
    logger.error("AKShare库未安装，正在安装...")
    import os
    os.system("pip install akshare -U")
    try:
        import akshare as ak
        logger.info(f"AKShare版本: {ak.__version__}")
    except ImportError:
        logger.error("AKShare安装失败，请手动安装")
        raise

class AKShareSectorProvider:
    """AKShare行业数据提供器，使用AKShare获取申万行业和概念板块数据"""
    
    def __init__(self, cache_dir='data_cache/akshare_sectors', cache_expiry=1800):
        """初始化AKShare行业数据提供器
        
        Args:
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
        
        # 加载本地缓存
        self._load_cache_from_disk()
        
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
        try:
            self._rate_limit()
            sw_index = ak.sw_index_first_info()
            
            if sw_index is not None and not sw_index.empty:
                logger.info(f"获取到 {len(sw_index)} 个申万一级行业")
                
                for _, row in sw_index.iterrows():
                    sectors.append({
                        'code': row['行业代码'],
                        'name': row['行业名称'], 
                        'type': 'SW',
                        'description': f'申万一级行业-{row["行业名称"]}',
                        'stock_count': row['成份个数']
                    })
        except Exception as e:
            logger.error(f"获取申万行业列表失败: {str(e)}")
        
        # 获取概念板块
        try:
            self._rate_limit()
            concepts = ak.stock_board_concept_name_em()
            
            if concepts is not None and not concepts.empty:
                logger.info(f"获取到 {len(concepts)} 个概念板块")
                # 只取前30个概念板块，避免太多
                for _, row in concepts.head(30).iterrows():
                    sectors.append({
                        'code': row['板块代码'],
                        'name': row['板块名称'],
                        'type': 'CN',
                        'description': f'概念板块-{row["板块名称"]}'
                    })
        except Exception as e:
            logger.error(f"获取概念板块列表失败: {str(e)}")
        
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
            return data
        
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # 初始化结果
        hist_data = None
        
        # 如果是申万行业指数
        if sector_code.endswith('.SI'):
            try:
                self._rate_limit()
                logger.info(f"获取申万行业 {sector_code} 历史数据")
                # 提取行业代码（去掉.SI后缀）
                industry_code = sector_code.replace('.SI', '')
                
                # 使用sw_index_hist_sw_min函数获取申万行业历史数据
                # 也可以尝试sw_index_daily_indicator或sw_index_spot_hist
                try:
                    index_data = ak.sw_index_spot_hist(symbol=industry_code)
                    logger.info(f"使用sw_index_spot_hist获取 {industry_code} 历史数据")
                except Exception as e1:
                    logger.warning(f"使用sw_index_spot_hist获取 {industry_code} 历史数据失败: {str(e1)}")
                    try:
                        index_data = ak.index_hist_sw(symbol=industry_code)
                        logger.info(f"使用index_hist_sw获取 {industry_code} 历史数据")
                    except Exception as e2:
                        logger.warning(f"使用index_hist_sw获取 {industry_code} 历史数据失败: {str(e2)}")
                        # 作为最终尝试
                        logger.info(f"尝试使用index_value_hist_funddb获取申万行业 {industry_code} 历史数据")
                        index_data = ak.index_value_hist_funddb(symbol=f"801{industry_code}", indicator="日频")
                
                if index_data is not None and not index_data.empty:
                    # 标准化列名
                    rename_cols = {}
                    
                    # 处理不同的数据结构
                    if '日期' in index_data.columns:
                        rename_cols['日期'] = '日期'
                    elif 'date' in index_data.columns:
                        rename_cols['date'] = '日期'
                    
                    if '开盘' in index_data.columns:
                        rename_cols['开盘'] = '开盘'
                    elif 'open' in index_data.columns:
                        rename_cols['open'] = '开盘'
                        
                    if '收盘' in index_data.columns:
                        rename_cols['收盘'] = '收盘'
                    elif 'close' in index_data.columns:
                        rename_cols['close'] = '收盘'
                    
                    if '最高' in index_data.columns:
                        rename_cols['最高'] = '最高'
                    elif 'high' in index_data.columns:
                        rename_cols['high'] = '最高'
                    
                    if '最低' in index_data.columns:
                        rename_cols['最低'] = '最低'
                    elif 'low' in index_data.columns:
                        rename_cols['low'] = '最低'
                    
                    if '成交量' in index_data.columns:
                        rename_cols['成交量'] = '成交量'
                    elif 'volume' in index_data.columns:
                        rename_cols['volume'] = '成交量'
                    
                    # 转换列名
                    hist_data = index_data.rename(columns=rename_cols)
                    
                    # 确保必要的列存在
                    required_cols = ['日期', '开盘', '收盘', '最高', '最低']
                    missing_cols = [col for col in required_cols if col not in hist_data.columns]
                    
                    if not missing_cols:
                        # 设置日期为索引
                        if '日期' in hist_data.columns:
                            hist_data['日期'] = pd.to_datetime(hist_data['日期'])
                            hist_data = hist_data.set_index('日期')
                        
                        # 按日期升序排序
                        hist_data = hist_data.sort_index()
                        
                        # 添加标记列
                        hist_data['数据来源'] = 'akshare'
                        hist_data['是真实数据'] = True
                    else:
                        logger.warning(f"申万行业历史数据缺少必要列: {missing_cols}，原始列: {index_data.columns.tolist()}")
                else:
                    logger.warning(f"获取申万行业 {industry_code} 历史数据为空或None")
            except Exception as e:
                logger.error(f"获取申万行业历史数据失败: {str(e)}")
        
        # 如果是概念板块
        elif sector_code.startswith('BK'):
            try:
                self._rate_limit()
                logger.info(f"获取概念板块 {sector_code} 历史数据")
                
                # 首先获取概念板块名称
                concepts = ak.stock_board_concept_name_em()
                if concepts is not None and not concepts.empty:
                    concept_name = concepts[concepts['板块代码'] == sector_code]['板块名称'].values
                    if len(concept_name) > 0:
                        concept_name = concept_name[0]
                        
                        # 获取概念板块历史数据
                        board_data = ak.stock_board_concept_hist_em(
                            symbol=concept_name,
                            start_date=start_date,
                            end_date=end_date,
                            period="daily"
                        )
                        
                        if board_data is not None and not board_data.empty:
                            # 转换列名和格式
                            hist_data = board_data.rename(columns={
                                '日期': '日期',
                                '开盘': '开盘',
                                '收盘': '收盘',
                                '最高': '最高',
                                '最低': '最低',
                                '成交量': '成交量',
                                '成交额': '成交额',
                                '涨跌幅': '涨跌幅'
                            })
                            
                            # 设置日期为索引
                            hist_data['日期'] = pd.to_datetime(hist_data['日期'])
                            hist_data = hist_data.set_index('日期')
                            
                            # 按日期升序排序
                            hist_data = hist_data.sort_index()
                            
                            # 添加标记列
                            hist_data['数据来源'] = 'akshare'
                            hist_data['是真实数据'] = True
            except Exception as e:
                logger.error(f"获取概念板块历史数据失败: {str(e)}")
        
        # 如果获取到了数据，保存到缓存
        if hist_data is not None and not hist_data.empty:
            self._save_to_cache(cache_key, hist_data)
            return hist_data
        
        logger.warning(f"无法获取行业 {sector_code} 的历史数据")
        return None
    
    def get_concept_details(self, concept_code: str) -> Optional[pd.DataFrame]:
        """获取概念板块详细信息和成分股
        
        Args:
            concept_code: 概念板块代码
            
        Returns:
            DataFrame包含概念板块成分股
        """
        if not concept_code.startswith('BK'):
            logger.error(f"无效的概念板块代码: {concept_code}，应以BK开头")
            return None
            
        cache_key = f'concept_detail_{concept_code}'
        hit, data = self._get_from_cache(cache_key)
        if hit:
            return data
            
        try:
            self._rate_limit()
            
            # 首先获取概念板块名称
            concepts = ak.stock_board_concept_name_em()
            if concepts is not None and not concepts.empty:
                concept_name = concepts[concepts['板块代码'] == concept_code]['板块名称'].values
                if len(concept_name) > 0:
                    concept_name = concept_name[0]
                    
                    # 获取概念板块成分股
                    stocks = ak.stock_board_concept_cons_em(symbol=concept_name)
                    
                    if stocks is not None and not stocks.empty:
                        logger.info(f"获取到概念板块 {concept_name} 的 {len(stocks)} 只成分股")
                        # 保存到缓存
                        self._save_to_cache(cache_key, stocks)
                        return stocks
            
            logger.warning(f"概念板块 {concept_code} 没有成分股数据")
            return None
        except Exception as e:
            logger.error(f"获取概念板块详情失败: {str(e)}")
            return None
    
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
        
        try:
            self._rate_limit()
            # 获取交易日历
            calendar = ak.tool_trade_date_hist_sina()
            
            if calendar is not None and not calendar.empty:
                # 获取最新交易日
                latest_day = calendar.iloc[-1]['trade_date']
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

def get_sector_provider(cache_dir='data_cache/akshare_sectors', cache_expiry=1800):
    """获取AKShareSectorProvider单例
    
    Args:
        cache_dir: 缓存目录
        cache_expiry: 缓存过期时间(秒)
        
    Returns:
        AKShareSectorProvider实例
    """
    global _instance
    if _instance is None:
        _instance = AKShareSectorProvider(cache_dir, cache_expiry)
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
    concept_sectors = [s for s in sectors if s['type'] == 'CN']
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