from datetime import datetime
import pandas as pd
import numpy as np
import akshare as ak
import talib as ta
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging
import time
import threading

class SectorAnalyzer:
    def __init__(self, top_n=10):
        """初始化行业分析器
        
        Args:
            top_n: 返回的热门行业数量
        """
        self.top_n = top_n
        self._cache = {}
        self._cache_expiry = 1800  # 缓存30分钟
        self.logger = logging.getLogger('SectorAnalyzer')
        self.cache_lock = threading.Lock()
        self.north_flow = 0.0
        self._last_update = 0
        
    def get_sector_list(self) -> List[Dict]:
        """获取所有行业板块列表"""
        cache_key = 'sector_list'
        
        # 首先检查缓存是否有效
        current_time = time.time()
        with self.cache_lock:
            if cache_key in self._cache and current_time - self._cache[cache_key]['timestamp'] < self._cache_expiry:
                print("从缓存获取行业列表数据")
                return self._cache[cache_key]['data']
        
        # 如果缓存无效，尝试从API获取数据
        max_retries = 3
        retry_delay = 2  # 初始重试延迟（秒）
        
        # 添加备用数据源
        for attempt in range(max_retries):
            try:
                print(f"尝试从API获取行业列表数据 (尝试 {attempt+1}/{max_retries})")
                
                # 获取申万一级行业列表
                try:
                    df = ak.stock_board_industry_name_em()
                except Exception as e:
                    print(f"主接口获取失败，尝试备用接口: {str(e)}")
                    try:
                        from akshare import stock_board_industry_cons_em
                        df = stock_board_industry_cons_em(symbol="沪深京行业分类")  # 备用数据源
                    except Exception as e2:
                        print(f"备用接口也失败: {str(e2)}")
                        raise ValueError("无法获取行业数据")
                
                if df is None or df.empty:
                    raise ValueError("获取到的行业数据为空")
                
                # 检查必要的列是否存在
                required_columns = ['板块名称', '最新价', '涨跌幅']
                volume_columns = ['成交金额', '成交额', '总成交额', '成交量', '成交股数', 'amount', 'volume', 'AMOUNT', 'VOLUME']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                # 检查成交量相关列
                volume_col = '换手率'
                if '换手率' not in df.columns:
                    available_columns = df.columns.tolist()
                    print(f"换手率字段不存在，可用字段：{available_columns}")
                    volume_col = '涨跌幅'  # 使用涨跌幅作为备用字段
                
                if missing_columns:
                    raise ValueError(f"行业数据缺少必要列: {', '.join(missing_columns)}")
                
                # 整理数据格式
                sectors = []
                for _, row in df.iterrows():
                    try:
                        # 处理成交量计算逻辑
                        volume_value = 0.0
                        if '总市值' in df.columns and volume_col in df.columns:
                            try:
                                # 尝试将换手率*总市值/100作为估算值
                                volume_value = float(row[volume_col]) * float(row['总市值']) / 100
                            except (ValueError, TypeError):
                                volume_value = float(row[volume_col]) if volume_col == '涨跌幅' else 0.0
                        
                        sector = {
                            'code': row['板块代码'] if '板块代码' in df.columns else '',
                            'name': row['板块名称'],
                            'level': '二级行业',
                            'standard_code': f'EM_{row["板块代码"]}' if '板块代码' in df.columns else '',
                            'price': float(row['最新价']),
                            'change_pct': float(row['涨跌幅']),
                            'volume': volume_value/100000000 if volume_value > 0 else 0.0,  # 转换为亿元
                            'source': '东方财富'
                        }
                        sectors.append(sector)
                    except (ValueError, TypeError) as e:
                        print(f"处理行业数据行时出错: {str(e)}, 行数据: {row}")
                        continue
                
                if not sectors:
                    raise ValueError("处理后的行业数据为空")
                
                # 更新缓存
                with self.cache_lock:
                    self._cache[cache_key] = {
                        'data': sectors,
                        'timestamp': current_time
                    }
                
                print(f"成功获取行业列表数据，共{len(sectors)}个行业")
                return sectors
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"第{attempt + 1}次获取行业数据失败，等待重试: {e}")
                    time.sleep(2 ** attempt)
                else:
                    print(f"获取行业数据最终失败: {e}")
                    raise e
        
        # 所有尝试都失败，返回空DataFrame
        return pd.DataFrame()

    def analyze_hot_sectors(self) -> Dict:
        """分析当前热门行业
        综合考虑涨跌幅、成交量、资金流向等因素"""
        try:
            sectors = self.get_sector_list()
            if not sectors:
                return {'status': 'error', 'message': '获取行业数据失败'}
            
            # 计算行业热度得分
            # 按标准化行业名称分组计算平均值
            sector_groups = {}
            for sector in sectors:
                name = sector['name']
                if name not in sector_groups:
                    sector_groups[name] = {
                        'total_volume': sector['volume'],
                        'avg_change': sector['change_pct'],
                        'count': 1
                    }
                else:
                    sector_groups[name]['total_volume'] += sector['volume']
                    sector_groups[name]['avg_change'] += sector['change_pct']
                    sector_groups[name]['count'] += 1
            
            # 计算每个行业的平均值
            for name in sector_groups:
                count = sector_groups[name]['count']
                sector_groups[name]['avg_volume'] = sector_groups[name]['total_volume'] / count
                sector_groups[name]['avg_change'] = sector_groups[name]['avg_change'] / count
            
            # 计算所有行业的平均成交量
            total_volume_avg = np.mean([g['avg_volume'] for g in sector_groups.values()])
            
            # 为每个行业计算热度得分
            for sector in sectors:
                name = sector['name']
                # 基础分（根据行业平均涨跌幅）
                base_score = sector_groups[name]['avg_change'] * 2
                
                # 成交量得分（相对于所有行业平均成交量）
                volume_score = (sector_groups[name]['avg_volume'] / total_volume_avg - 1) * 30 if total_volume_avg > 0 else 0
                
                # 计算综合得分
                sector['hot_score'] = base_score + volume_score
            
            # 按热度得分排序
            hot_sectors = sorted(sectors, key=lambda x: x['hot_score'], reverse=True)
            
            # 获取北向资金流向数据
            try:
                north_flow = ak.stock_hsgt_north_net_flow_in_em()
                total_north_flow = north_flow['value'].iloc[-1] if not north_flow.empty else 0.0
            except Exception as e:
                print(f"获取北向资金数据失败: {str(e)}")
                total_north_flow = 0.0
            
            # 获取行业资金流向数据
            try:
                sector_flow = ak.stock_sector_fund_flow_rank(indicator="今日")
                # 整合资金流向数据
                for sector in hot_sectors:
                    flow_data = sector_flow[sector_flow['名称'] == sector['name']]
                    if not flow_data.empty:
                        try:
                            fund_flow_str = flow_data.iloc[0]['净额']
                            # 处理亿元单位
                            if isinstance(fund_flow_str, str) and '亿' in fund_flow_str:
                                fund_flow_str = fund_flow_str.replace('亿', '')
                            sector['fund_flow'] = float(fund_flow_str)
                        except (ValueError, TypeError):
                            sector['fund_flow'] = 0.0
                    else:
                        sector['fund_flow'] = 0.0
            except Exception as e:
                print(f"获取行业资金流向数据失败: {str(e)}")
                for sector in hot_sectors:
                    sector['fund_flow'] = 0.0
            
            # 获取上涨下跌家数
            try:
                for sector in hot_sectors:
                    sector['up_down_ratio'] = "0/0"  # 默认值
            except Exception as e:
                print(f"获取上涨下跌家数失败: {str(e)}")
            
            return {
                'status': 'success',
                'data': {
                    'hot_sectors': hot_sectors[:self.top_n],  # 返回前N个热门行业
                    'total_sectors': len(sectors),
                    'north_flow': total_north_flow,
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            print(f"分析热门行业失败：{str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def predict_next_hot_sectors(self) -> Dict:
        """预测下一阶段可能的热门行业
        基于行业轮动规律和市场情绪指标
        """
        try:
            # 获取当前热门行业
            current_hot = self.analyze_hot_sectors()
            if current_hot['status'] != 'success':
                return current_hot
            
            # 获取行业列表
            sectors = self.get_sector_list()
            predictions = []
            
            for sector in sectors:
                try:
                    # 获取行业指数历史数据
                    hist_data = None
                    try:
                        hist_data = ak.stock_board_industry_hist_em(
                            symbol=sector['name'], 
                            start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
                        )
                    except Exception as e:
                        print(f"获取行业{sector['name']}历史数据失败: {str(e)}")
                        continue
                    
                    if hist_data is None or hist_data.empty:
                        continue
                    
                    # 计算技术指标
                    close_prices = hist_data['收盘'].values
                    volumes = hist_data['成交量'].values if '成交量' in hist_data.columns else np.ones_like(close_prices)
                    
                    # MACD指标
                    macd, signal, hist = ta.MACD(close_prices)
                    
                    # RSI指标
                    rsi = ta.RSI(close_prices)
                    
                    # 布林带
                    upper, middle, lower = ta.BBANDS(close_prices)
                    
                    # 计算预测分数
                    technical_score = 0
                    
                    # MACD金叉判断
                    if len(hist) > 1 and hist[-1] > 0 and hist[-2] <= 0:
                        technical_score += 30
                    
                    # RSI位置判断
                    if len(rsi) > 0 and 30 <= rsi[-1] <= 50:
                        technical_score += 20
                    
                    # 布林带位置判断
                    if len(middle) > 0 and len(close_prices) > 0 and close_prices[-1] < middle[-1]:
                        technical_score += 15
                    
                    # 成交量趋势判断
                    volume_ma = np.mean(volumes[-5:]) if len(volumes) >= 5 else 0
                    if volume_ma > np.mean(volumes) and len(volumes) > 0:
                        technical_score += 15
                    
                    # 添加预测结果
                    if technical_score > 40:
                        predictions.append({
                            'code': sector.get('code', ''),
                            'name': sector['name'],
                            'technical_score': technical_score,
                            'current_price': sector['price'],
                            'reason': self._generate_prediction_reason(
                                technical_score, 
                                hist[-1] if len(hist) > 0 else 0, 
                                rsi[-1] if len(rsi) > 0 else 0, 
                                close_prices[-1] if len(close_prices) > 0 else 0, 
                                middle[-1] if len(middle) > 0 else 0
                            )
                        })
                        
                except Exception as e:
                    print(f"处理行业{sector['name']}预测数据时发生错误：{str(e)}")
                    continue
            
            # 按预测分数排序
            predictions = sorted(predictions, key=lambda x: x['technical_score'], reverse=True)
            
            return {
                'status': 'success',
                'data': {
                    'predicted_sectors': predictions[:self.top_n],  # 返回预测分数最高的N个行业
                    'prediction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'prediction_period': '未来3-5个交易日'
                }
            }
            
        except Exception as e:
            print(f"预测热门行业失败：{str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _generate_prediction_reason(self, technical_score: float, macd_hist: float, rsi: float, price: float, ma20: float) -> str:
        """生成预测理由"""
        reasons = []
        
        if macd_hist > 0:
            reasons.append("MACD金叉形成，上涨动能增强")
        
        if 30 <= rsi <= 50:
            reasons.append("RSI处于低位回升阶段，具有上涨空间")
        
        if price < ma20:
            reasons.append("当前价格处于20日均线下方，存在修复机会")
        
        if not reasons:
            reasons.append("技术指标综合表现良好")
        
        return "，".join(reasons)

    def generate_sector_report(self):
        """生成行业分析报告"""
        try:
            hot_sectors = self.analyze_hot_sectors()
            if hot_sectors['status'] != 'success':
                return hot_sectors
                
            predicted_sectors = self.predict_next_hot_sectors()
            if predicted_sectors['status'] != 'success':
                return predicted_sectors
                
            # 计算行业整体健康指数
            sectors = self.get_sector_list()
            if not sectors:
                return {'status': 'error', 'message': '获取行业数据失败'}
                
            # 计算行业整体指标
            avg_change = np.mean([s['change_pct'] for s in sectors])
            up_sectors = sum(1 for s in sectors if s['change_pct'] > 0)
            down_sectors = sum(1 for s in sectors if s['change_pct'] < 0)
            up_down_ratio = up_sectors / down_sectors if down_sectors > 0 else float('inf')
            
            # 生成报告
            report = {
                'status': 'success',
                'data': {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'market_sentiment': '看多' if avg_change > 0 else '看空',
                    'sector_health_index': avg_change,
                    'up_down_ratio': up_down_ratio,
                    'hot_sectors': hot_sectors['data']['hot_sectors'],
                    'predicted_sectors': predicted_sectors['data']['predicted_sectors'],
                    'north_flow': hot_sectors['data']['north_flow']
                }
            }
            
            return report
            
        except Exception as e:
            print(f"生成行业报告失败：{str(e)}")
            return {'status': 'error', 'message': str(e)}