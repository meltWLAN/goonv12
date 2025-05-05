#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tushare行业数据缓存工具
从Tushare获取行业数据并缓存到本地
"""

import os
import sys
import time
import json
import pickle
import logging
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tushare_cache.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TushareCache")

class TushareSectorCache:
    """Tushare行业数据缓存工具"""
    
    def __init__(self, token=None, cache_dir='data_cache/advanced_sectors'):
        """初始化缓存工具
        
        Args:
            token: Tushare API token
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        
        # 创建缓存目录
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"创建缓存目录: {self.cache_dir}")
        
        # 初始化Tushare API
        self.token = token or self._load_token()
        self.ts_api = None
        if self.token:
            self._init_tushare_api()
    
    def _load_token(self):
        """从配置文件加载Token"""
        config_path = 'config/api_keys.txt'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('TUSHARE_TOKEN='):
                            token = line.strip().split('=')[1]
                            logger.info(f"从配置文件加载Token: {token[:4]}...{token[-4:]}")
                            return token
            except Exception as e:
                logger.error(f"读取Token配置失败: {str(e)}")
        
        # 尝试从环境变量获取
        env_token = os.environ.get('TUSHARE_TOKEN')
        if env_token:
            logger.info(f"从环境变量加载Token: {env_token[:4]}...{env_token[-4:]}")
            return env_token
            
        # 使用默认Token
        default_token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        logger.warning(f"未找到有效Token，使用默认Token")
        return default_token
    
    def _init_tushare_api(self):
        """初始化Tushare API"""
        try:
            ts.set_token(self.token)
            self.ts_api = ts.pro_api()
            
            # 验证API连接
            test_data = self.ts_api.trade_cal(exchange='SSE', start_date='20230101', end_date='20230110')
            if test_data is not None and not test_data.empty:
                logger.info(f"Tushare API初始化成功，Token: {self.token[:4]}...{self.token[-4:]}")
                return True
            else:
                logger.error("Tushare API返回空数据，请检查网络连接")
                return False
        except Exception as e:
            logger.error(f"Tushare API初始化失败: {str(e)}")
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
    
    def _get_latest_trade_date(self):
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
            logger.error(f"获取最新交易日失败: {str(e)}")
            return datetime.now().strftime('%Y%m%d')
    
    def cache_sector_list(self):
        """缓存行业列表数据"""
        logger.info("开始缓存行业列表数据...")
        
        if not self.ts_api:
            logger.error("Tushare API未初始化")
            return False
        
        sectors = []
        cached = False
        
        # 尝试获取申万一级行业
        try:
            logger.info("尝试获取申万一级行业分类")
            sw_sectors = self.ts_api.index_classify(level='L1', src='SW')
            
            if sw_sectors is not None and not sw_sectors.empty:
                logger.info(f"成功获取申万一级行业，共 {len(sw_sectors)} 个")
                
                # 获取最新交易日
                latest_trade_date = self._get_latest_trade_date()
                
                # 处理每个行业
                for _, row in sw_sectors.iterrows():
                    industry_code = row['index_code']
                    industry_name = row['industry_name']
                    
                    # 创建行业信息字典
                    sector = {
                        'code': industry_code,
                        'name': industry_name,
                        'level': '申万一级',
                        'price': 0,
                        'change_pct': 0,
                        'volume': 0,
                        'trade_date': latest_trade_date,
                        'source': '申万',
                        'is_real_data': True
                    }
                    
                    sectors.append(sector)
                
                # 保存到缓存
                cached = self._save_to_cache('sector_list', sectors)
            else:
                logger.warning("无法获取申万一级行业分类")
                
                # 尝试获取概念板块
                logger.info("尝试获取概念板块")
                concept_sectors = self.ts_api.concept()
                
                if concept_sectors is not None and not concept_sectors.empty:
                    logger.info(f"成功获取概念板块，共 {len(concept_sectors)} 个")
                    
                    # 获取最新交易日
                    latest_trade_date = self._get_latest_trade_date()
                    
                    # 处理每个概念板块
                    for _, row in concept_sectors.head(20).iterrows():  # 取前20个概念板块
                        code = row['ts_code'] if 'ts_code' in row else row['code']
                        name = row['name']
                        
                        # 创建行业信息字典
                        sector = {
                            'code': code,
                            'name': name,
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
                    cached = self._save_to_cache('sector_list', sectors)
                else:
                    logger.warning("无法获取行业/概念板块数据")
        except Exception as e:
            logger.error(f"获取行业列表失败: {str(e)}")
        
        if cached:
            logger.info(f"成功缓存 {len(sectors)} 个行业数据")
            return True
        else:
            logger.error("行业列表缓存失败")
            return False
    
    def cache_sector_history(self, max_sectors=10):
        """缓存行业历史数据
        
        Args:
            max_sectors: 最多缓存的行业数量
        """
        logger.info(f"开始缓存行业历史数据，最多 {max_sectors} 个行业...")
        
        if not self.ts_api:
            logger.error("Tushare API未初始化")
            return False
        
        # 加载行业列表
        try:
            sector_list_path = os.path.join(self.cache_dir, "sector_list.pkl")
            if not os.path.exists(sector_list_path):
                logger.warning("行业列表缓存不存在，先缓存行业列表")
                if not self.cache_sector_list():
                    return False
            
            with open(sector_list_path, 'rb') as f:
                sectors = pickle.load(f)
                
            if not sectors:
                logger.error("行业列表为空")
                return False
                
            logger.info(f"从缓存加载 {len(sectors)} 个行业")
            
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            # 限制行业数量
            if len(sectors) > max_sectors:
                sectors = sectors[:max_sectors]
                logger.info(f"限制为前 {max_sectors} 个行业")
            
            success_count = 0
            for sector in sectors:
                sector_code = sector['code']
                sector_name = sector['name']
                
                logger.info(f"获取行业 {sector_name} 历史数据")
                success = False
                
                # 尝试直接获取行业指数数据
                try:
                    history_data = self.ts_api.index_daily(ts_code=sector_code, start_date=start_date, end_date=end_date)
                    
                    if history_data is not None and not history_data.empty:
                        # 对列名进行标准化
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
                        
                        # 添加标记
                        history_data['是真实数据'] = True
                        
                        # 按日期升序排序
                        if '日期' in history_data.columns:
                            history_data = history_data.sort_values('日期')
                        
                        # 保存到缓存
                        cache_key = f"history_{sector_code}"
                        if self._save_to_cache(cache_key, history_data):
                            logger.info(f"成功缓存行业 {sector_name} 历史数据，共 {len(history_data)} 条记录")
                            success = True
                            success_count += 1
                        else:
                            logger.error(f"保存行业 {sector_name} 历史数据失败")
                    else:
                        logger.warning(f"行业 {sector_name} 没有返回历史数据")
                        
                        # 尝试获取成分股历史数据
                        if sector['level'] == '概念板块':
                            logger.info(f"尝试获取 {sector_name} 成分股")
                            try:
                                # 获取成分股
                                if 'ts_code' in sector:
                                    concept_stocks = self.ts_api.concept_detail(concept_id=sector['ts_code'].split('.')[0])
                                else:
                                    concept_stocks = self.ts_api.concept_detail(concept_id=sector['code'])
                                
                                if concept_stocks is not None and not concept_stocks.empty:
                                    logger.info(f"获取到 {len(concept_stocks)} 个成分股")
                                    
                                    # 获取前5个成分股的历史数据
                                    stock_dfs = []
                                    for _, stock in concept_stocks.head(5).iterrows():
                                        ts_code = stock['ts_code']
                                        try:
                                            stock_data = self.ts_api.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                                            if stock_data is not None and not stock_data.empty:
                                                stock_dfs.append(stock_data)
                                                time.sleep(0.3)  # 避免请求过快
                                        except Exception as e:
                                            logger.warning(f"获取股票 {ts_code} 数据失败: {str(e)}")
                                    
                                    if stock_dfs:
                                        # 合并成分股数据
                                        all_data = pd.concat(stock_dfs)
                                        
                                        # 按日期分组计算
                                        composite_data = all_data.groupby('trade_date').agg({
                                            'open': 'mean',
                                            'high': 'mean',
                                            'low': 'mean',
                                            'close': 'mean',
                                            'vol': 'sum',
                                            'amount': 'sum'
                                        }).reset_index()
                                        
                                        # 计算涨跌幅
                                        composite_data['pct_chg'] = composite_data['close'].pct_change() * 100
                                        
                                        # 对列名进行标准化
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
                                        composite_data = composite_data.rename(columns={k: v for k, v in column_map.items() if k in composite_data.columns})
                                        
                                        # 添加标记
                                        composite_data['是真实数据'] = True
                                        composite_data['是合成数据'] = True
                                        
                                        # 按日期升序排序
                                        if '日期' in composite_data.columns:
                                            composite_data = composite_data.sort_values('日期')
                                        
                                        # 保存到缓存
                                        cache_key = f"history_{sector_code}"
                                        if self._save_to_cache(cache_key, composite_data):
                                            logger.info(f"通过成分股合成行业 {sector_name} 历史数据，共 {len(composite_data)} 条记录")
                                            success = True
                                            success_count += 1
                                        else:
                                            logger.error(f"保存合成行业 {sector_name} 历史数据失败")
                            except Exception as e:
                                logger.error(f"处理概念板块 {sector_name} 成分股失败: {str(e)}")
                except Exception as e:
                    logger.error(f"获取行业 {sector_name} 历史数据失败: {str(e)}")
                
                # 避免请求过快
                time.sleep(0.5)
            
            logger.info(f"行业历史数据缓存完成，成功 {success_count}/{len(sectors)} 个行业")
            return success_count > 0
        
        except Exception as e:
            logger.error(f"缓存行业历史数据失败: {str(e)}")
            return False
    
    def cache_north_flow(self):
        """缓存北向资金数据"""
        logger.info("开始缓存北向资金数据...")
        
        if not self.ts_api:
            logger.error("Tushare API未初始化")
            return False
        
        try:
            # 获取最新交易日
            today = self._get_latest_trade_date()
            yesterday = (datetime.strptime(today, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
            
            # 尝试获取当天和前一天的北向资金数据
            north_data = None
            for date in [today, yesterday]:
                try:
                    data = self.ts_api.moneyflow_hsgt(trade_date=date)
                    if data is not None and not data.empty:
                        north_data = data
                        break
                except Exception as e:
                    logger.warning(f"获取日期 {date} 的北向资金数据失败: {str(e)}")
                    time.sleep(0.5)
            
            if north_data is not None and not north_data.empty:
                # 计算北向资金
                north_money = north_data['north_money'].sum() / 100000000  # 转换为亿元
                logger.info(f"北向资金净流入: {north_money:.2f}亿元")
                
                # 保存到缓存
                if self._save_to_cache('north_flow', north_money):
                    logger.info("成功缓存北向资金数据")
                    return True
                else:
                    logger.error("保存北向资金数据失败")
                    return False
            else:
                logger.warning("无法获取北向资金数据")
                return False
        
        except Exception as e:
            logger.error(f"缓存北向资金数据失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("\n====== Tushare行业数据缓存工具 ======\n")
    
    # 创建缓存工具
    cache_tool = TushareSectorCache()
    
    # 缓存行业列表
    print("\n1. 缓存行业列表...")
    if cache_tool.cache_sector_list():
        print("行业列表缓存成功")
    else:
        print("行业列表缓存失败")
    
    # 缓存行业历史数据
    print("\n2. 缓存行业历史数据...")
    if cache_tool.cache_sector_history():
        print("行业历史数据缓存成功")
    else:
        print("行业历史数据缓存失败")
    
    # 缓存北向资金数据
    print("\n3. 缓存北向资金数据...")
    if cache_tool.cache_north_flow():
        print("北向资金数据缓存成功")
    else:
        print("北向资金数据缓存失败")
    
    print("\n缓存完成！现在可以运行股票分析系统，它将使用缓存的真实数据。")
    print("运行命令: python stock_analyzer_app.py")

if __name__ == "__main__":
    main() 