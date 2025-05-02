#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tushare行业数据提供者
使用Tushare的接口获取行业数据和技术指标
作为sector_data_provider.py的替代或备用数据源
"""

import pandas as pd
import numpy as np
import tushare as ts
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

class TushareSectorProvider:
    """Tushare行业数据提供者"""
    
    def __init__(self, token: str = None, cache_dir: str = './data_cache'):
        """初始化
        
        Args:
            token: Tushare API token
            cache_dir: 缓存目录
        """
        self.logger = logging.getLogger('TushareSectorProvider')
        self.token = token or os.environ.get('TUSHARE_TOKEN') or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        self.cache_dir = cache_dir
        self.industry_map = {}  # 行业映射表
        self.cache_timeout = 86400  # 缓存过期时间(秒)
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, 'sectors'), exist_ok=True)
        
        # 初始化Tushare
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        # 初始化行业映射
        self._init_industry_map()
    
    def _init_industry_map(self):
        """初始化行业映射"""
        try:
            # 从缓存加载行业映射
            cache_file = os.path.join(self.cache_dir, 'industry_map.csv')
            if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < self.cache_timeout:
                self.industry_map = pd.read_csv(cache_file, index_col=0).to_dict()['industry']
                self.logger.info("从缓存加载行业映射成功")
                return
                
            # 获取行业分类数据
            df_industry = self.pro.index_classify(level='L1', src='SW')
            df_stocks = pd.DataFrame()
            
            # 获取每个行业的成分股
            for index_code in df_industry['index_code']:
                df_cons = self.pro.index_member(index_code=index_code)
                if df_cons is not None and not df_cons.empty:
                    df_stocks = pd.concat([df_stocks, df_cons])
            
            # 构建股票->行业的映射
            if not df_stocks.empty:
                # 获取行业名称
                df_stocks = df_stocks.merge(df_industry, on='index_code', how='left')
                # 构建映射
                self.industry_map = dict(zip(df_stocks['con_code'], df_stocks['name']))
                # 保存到缓存
                pd.DataFrame({'industry': self.industry_map}).to_csv(cache_file)
                self.logger.info(f"行业映射初始化成功，共{len(self.industry_map)}只股票")
            else:
                self.logger.warning("获取行业分类数据失败")
        
        except Exception as e:
            self.logger.error(f"初始化行业映射失败: {str(e)}")
    
    def get_sector_list(self) -> List[str]:
        """获取行业列表
        
        Returns:
            行业列表
        """
        try:
            df = self.pro.index_classify(level='L1', src='SW')
            return df['name'].tolist() if df is not None and not df.empty else []
        except Exception as e:
            self.logger.error(f"获取行业列表失败: {str(e)}")
            return []
    
    def get_sector_stocks(self, sector_name: str) -> List[str]:
        """获取行业成分股
        
        Args:
            sector_name: 行业名称
            
        Returns:
            行业成分股代码列表
        """
        try:
            # 反向查找行业代码
            df = self.pro.index_classify(level='L1', src='SW')
            if df is None or df.empty:
                return []
                
            sector_code = df[df['name'] == sector_name]['index_code'].values
            if len(sector_code) == 0:
                return []
                
            # 获取成分股
            df_cons = self.pro.index_member(index_code=sector_code[0])
            return df_cons['con_code'].tolist() if df_cons is not None and not df_cons.empty else []
        
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}成分股失败: {str(e)}")
            return []
    
    def get_sector_technical_indicator(self, sector_name: str, indicator: str, 
                                      days: int = 30) -> pd.DataFrame:
        """获取行业技术指标
        
        Args:
            sector_name: 行业名称
            indicator: 技术指标名称，例如'macd'、'kdj_k'等
            days: 历史天数
            
        Returns:
            行业技术指标数据
        """
        try:
            # 获取行业成分股
            stocks = self.get_sector_stocks(sector_name)
            if not stocks:
                return pd.DataFrame()
                
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            # 获取每只股票的技术指标
            df_all = pd.DataFrame()
            for stock in stocks[:30]:  # 限制股票数量，避免API调用次数过多
                try:
                    # 使用stk_factor接口获取技术指标
                    fields = f'ts_code,trade_date,close,{indicator}'
                    df = self.pro.stk_factor(ts_code=stock, start_date=start_date, 
                                          end_date=end_date, fields=fields)
                    
                    if df is not None and not df.empty:
                        df_all = pd.concat([df_all, df])
                    
                    # 避免API限制
                    time.sleep(0.1)
                
                except Exception as e:
                    self.logger.warning(f"获取股票{stock}技术指标失败: {str(e)}")
                    continue
            
            # 如果数据为空，返回空DataFrame
            if df_all.empty:
                return pd.DataFrame()
                
            # 按日期分组计算行业指标均值
            df_sector = df_all.groupby('trade_date').agg({
                'close': 'mean',
                indicator: 'mean'
            }).reset_index()
            
            # 只保留最近days天的数据
            df_sector = df_sector.sort_values('trade_date', ascending=False).head(days)
            
            return df_sector
        
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}技术指标失败: {str(e)}")
            return pd.DataFrame()
    
    def get_hot_sectors(self, top_n: int = 10, 
                       indicators: List[str] = None) -> Dict:
        """获取热门行业
        
        通过各种技术指标综合评分，找出最热门的行业
        
        Args:
            top_n: 返回热门行业数量
            indicators: 使用的技术指标列表，默认为['macd', 'kdj_k', 'rsi_6']
            
        Returns:
            热门行业数据，包含分数和排名
        """
        try:
            # 默认使用的技术指标
            if indicators is None:
                indicators = ['macd', 'kdj_k', 'rsi_6']
                
            # 获取行业列表
            sectors = self.get_sector_list()
            if not sectors:
                return {'status': 'error', 'message': '获取行业列表失败'}
                
            # 计算每个行业的技术指标得分
            sector_scores = []
            for sector in sectors:
                try:
                    score = 0
                    analysis = []
                    
                    # 计算MACD指标得分
                    if 'macd' in indicators:
                        df_macd = self.get_sector_technical_indicator(sector, 'macd', days=10)
                        if not df_macd.empty:
                            # MACD由负转正是买入信号
                            macd_values = df_macd['macd'].values
                            if len(macd_values) >= 2:
                                if macd_values[0] > 0 and macd_values[1] < 0:
                                    score += 30
                                    analysis.append("MACD金叉")
                                elif macd_values[0] > 0:
                                    score += 20
                                    analysis.append("MACD为正")
                                elif macd_values[0] > macd_values[1]:
                                    score += 10
                                    analysis.append("MACD上升")
                    
                    # 计算KDJ指标得分
                    if 'kdj_k' in indicators:
                        df_kdj = self.get_sector_technical_indicator(sector, 'kdj_k', days=10)
                        if not df_kdj.empty:
                            # KDJ K值大于80表示超买，小于20表示超卖
                            kdj_values = df_kdj['kdj_k'].values
                            if len(kdj_values) >= 1:
                                if kdj_values[0] > 80:
                                    score += 10  # 较高但可能有回调风险
                                    analysis.append("KDJ超买区")
                                elif 50 < kdj_values[0] < 80:
                                    score += 25
                                    analysis.append("KDJ强势区")
                                elif 20 < kdj_values[0] < 50:
                                    score += 15
                                    analysis.append("KDJ中性区")
                                elif kdj_values[0] < 20:
                                    score += 5  # 超卖可能有反弹机会
                                    analysis.append("KDJ超卖区")
                    
                    # 计算RSI指标得分
                    if 'rsi_6' in indicators:
                        df_rsi = self.get_sector_technical_indicator(sector, 'rsi_6', days=10)
                        if not df_rsi.empty:
                            # RSI大于70表示超买，小于30表示超卖
                            rsi_values = df_rsi['rsi_6'].values
                            if len(rsi_values) >= 1:
                                if rsi_values[0] > 70:
                                    score += 15
                                    analysis.append("RSI超买区")
                                elif 50 < rsi_values[0] < 70:
                                    score += 25
                                    analysis.append("RSI强势区")
                                elif 30 < rsi_values[0] < 50:
                                    score += 10
                                    analysis.append("RSI弱势区")
                                elif rsi_values[0] < 30:
                                    score += 5
                                    analysis.append("RSI超卖区")
                    
                    # 添加到结果中
                    sector_scores.append({
                        'name': sector,
                        'score': score,
                        'analysis': '，'.join(analysis) if analysis else '无明显信号'
                    })
                    
                except Exception as e:
                    self.logger.warning(f"计算行业{sector}热度得分时发生错误: {str(e)}")
                    # 出错不影响其他行业，继续计算
                    continue
            
            # 按分数排序
            sorted_sectors = sorted(sector_scores, key=lambda x: x['score'], reverse=True)
            
            # 获取热门行业的热度等级
            hot_sectors = []
            for i, sector in enumerate(sorted_sectors[:top_n]):
                # 根据分数确定热度等级
                if sector['score'] >= 70:
                    hot_level = '热门'
                elif sector['score'] >= 50:
                    hot_level = '较热'
                elif sector['score'] >= 30:
                    hot_level = '中性'
                else:
                    hot_level = '冷门'
                
                hot_sectors.append({
                    'name': sector['name'],
                    'hot_score': sector['score'],
                    'hot_level': hot_level,
                    'rank': i + 1,
                    'analysis_reason': sector['analysis']
                })
            
            return {
                'status': 'success',
                'data': {
                    'hot_sectors': hot_sectors,
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取热门行业失败: {str(e)}")
            return {'status': 'error', 'message': f"获取热门行业失败: {str(e)}"}
    
    def get_sector_historical_data(self, sector_name: str, 
                                 days: int = 30) -> pd.DataFrame:
        """获取行业历史数据
        
        从行业成分股平均计算得到行业指数
        
        Args:
            sector_name: 行业名称
            days: 历史天数
            
        Returns:
            行业历史数据
        """
        try:
            # 获取行业成分股
            stocks = self.get_sector_stocks(sector_name)
            if not stocks:
                return pd.DataFrame()
                
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            # 获取每只股票的历史数据
            df_all = pd.DataFrame()
            for stock in stocks[:20]:  # 限制股票数量，避免API调用次数过多
                try:
                    # 使用日线行情接口获取历史数据
                    df = self.pro.daily(ts_code=stock, start_date=start_date, 
                                     end_date=end_date)
                    
                    if df is not None and not df.empty:
                        df_all = pd.concat([df_all, df])
                    
                    # 避免API限制
                    time.sleep(0.1)
                
                except Exception as e:
                    self.logger.warning(f"获取股票{stock}历史数据失败: {str(e)}")
                    continue
            
            # 如果数据为空，返回空DataFrame
            if df_all.empty:
                return pd.DataFrame()
                
            # 按日期分组计算行业指数
            df_sector = df_all.groupby('trade_date').agg({
                'open': 'mean',
                'high': 'mean',
                'low': 'mean',
                'close': 'mean',
                'vol': 'sum',
                'amount': 'sum'
            }).reset_index()
            
            # 重命名列名以匹配系统使用习惯
            df_sector = df_sector.rename(columns={
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            # 只保留最近days天的数据
            df_sector = df_sector.sort_values('date', ascending=False).head(days)
            df_sector = df_sector.sort_values('date')  # 按日期升序排序
            
            # 添加行业名称列
            df_sector['sector'] = sector_name
            
            return df_sector
            
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}历史数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_sector_prediction(self, sector_name: str) -> Dict:
        """获取行业预测数据
        
        使用技术指标预测行业走势
        
        Args:
            sector_name: 行业名称
            
        Returns:
            行业预测数据
        """
        try:
            # 获取各项技术指标
            indicators = ['macd', 'kdj_k', 'kdj_d', 'kdj_j', 'rsi_6', 'rsi_12', 'rsi_24']
            indicator_data = {}
            
            for indicator in indicators:
                df = self.get_sector_technical_indicator(sector_name, indicator, days=10)
                if not df.empty:
                    indicator_data[indicator] = df[indicator].values
            
            # 如果没有获取到任何指标数据，返回空结果
            if not indicator_data:
                return {
                    'status': 'error', 
                    'message': f'无法获取行业{sector_name}的技术指标数据'
                }
            
            # 分析走势
            prediction = self._analyze_trend(indicator_data)
            
            # 获取行业历史数据
            df_history = self.get_sector_historical_data(sector_name, days=10)
            if not df_history.empty:
                # 计算最新价格和涨跌幅
                latest_price = df_history['close'].values[-1]
                chg_pct = ((df_history['close'].values[-1] / df_history['close'].values[0]) - 1) * 100
                
                prediction.update({
                    'latest_price': round(latest_price, 2),
                    'chg_pct': round(chg_pct, 2)
                })
            
            return {
                'status': 'success',
                'data': {
                    'sector': sector_name,
                    'prediction': prediction,
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取行业{sector_name}预测数据失败: {str(e)}")
            return {'status': 'error', 'message': f"获取行业预测失败: {str(e)}"}
    
    def _analyze_trend(self, indicator_data: Dict) -> Dict:
        """分析行业走势
        
        根据多个技术指标综合判断行业走势
        
        Args:
            indicator_data: 技术指标数据
            
        Returns:
            走势分析结果
        """
        # 初始化得分
        bull_score = 0
        bear_score = 0
        analysis = []
        
        # 分析MACD
        if 'macd' in indicator_data and len(indicator_data['macd']) >= 2:
            macd = indicator_data['macd']
            if macd[-1] > 0 and macd[-2] < 0:  # 金叉
                bull_score += 30
                analysis.append("MACD金叉，买入信号")
            elif macd[-1] < 0 and macd[-2] > 0:  # 死叉
                bear_score += 30
                analysis.append("MACD死叉，卖出信号")
            elif macd[-1] > 0:  # MACD为正
                bull_score += 15
                analysis.append("MACD为正，多头市场")
            elif macd[-1] < 0:  # MACD为负
                bear_score += 15
                analysis.append("MACD为负，空头市场")
        
        # 分析KDJ
        if all(k in indicator_data for k in ['kdj_k', 'kdj_d']) and len(indicator_data['kdj_k']) >= 2:
            k = indicator_data['kdj_k']
            d = indicator_data['kdj_d']
            
            if k[-1] > d[-1] and k[-2] < d[-2]:  # KDJ金叉
                bull_score += 25
                analysis.append("KDJ金叉，买入信号")
            elif k[-1] < d[-1] and k[-2] > d[-2]:  # KDJ死叉
                bear_score += 25
                analysis.append("KDJ死叉，卖出信号")
            
            if k[-1] > 80:  # 超买区
                bear_score += 15
                analysis.append("KDJ超买区，注意回调风险")
            elif k[-1] < 20:  # 超卖区
                bull_score += 15
                analysis.append("KDJ超卖区，可能有反弹机会")
        
        # 分析RSI
        if 'rsi_6' in indicator_data and len(indicator_data['rsi_6']) >= 1:
            rsi = indicator_data['rsi_6']
            
            if rsi[-1] > 70:  # 超买区
                bear_score += 20
                analysis.append("RSI超买区，注意回调风险")
            elif rsi[-1] < 30:  # 超卖区
                bull_score += 20
                analysis.append("RSI超卖区，可能有反弹机会")
            elif 50 < rsi[-1] < 70:  # 强势区
                bull_score += 10
                analysis.append("RSI处于强势区")
            elif 30 < rsi[-1] < 50:  # 弱势区
                bear_score += 10
                analysis.append("RSI处于弱势区")
        
        # 根据得分判断走势
        if bull_score > bear_score + 20:
            trend = "强烈看多"
        elif bull_score > bear_score:
            trend = "看多"
        elif bear_score > bull_score + 20:
            trend = "强烈看空"
        elif bear_score > bull_score:
            trend = "看空"
        else:
            trend = "中性"
        
        return {
            'trend': trend,
            'bull_score': bull_score,
            'bear_score': bear_score,
            'analysis': '；'.join(analysis) if analysis else '无明显信号'
        }

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 使用示例
    provider = TushareSectorProvider()
    
    # 获取行业列表
    sectors = provider.get_sector_list()
    print(f"行业列表: {sectors[:5]}...")
    
    # 获取行业成分股
    if sectors:
        stocks = provider.get_sector_stocks(sectors[0])
        print(f"行业 {sectors[0]} 成分股: {stocks[:5]}...")
    
    # 获取热门行业
    hot_sectors = provider.get_hot_sectors(top_n=5)
    print("热门行业:")
    print(hot_sectors) 