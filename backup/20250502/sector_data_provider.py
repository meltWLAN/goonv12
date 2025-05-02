import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Any, Optional, Union

class SectorDataProvider:
    """
    行业数据提供器
    
    提供多种数据源获取行业数据，并在实时数据获取失败时提供模拟数据
    作为行业分析的数据层，提供更可靠的数据获取机制
    """
    
    def __init__(self, cache_dir="./cache"):
        """
        初始化行业数据提供器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger('SectorDataProvider')
        
        # 缓存设置
        self._cache = {}
        self._cache_expiry = 1800  # 缓存30分钟
        
        # 加载历史数据缓存
        self.history_cache_file = os.path.join(self.cache_dir, "sector_history_cache.json")
        self.load_history_cache()
        
        # 加载行业名称映射
        self.industry_name_map = self._load_industry_name_map()
    
    def load_history_cache(self):
        """加载历史数据缓存"""
        try:
            if os.path.exists(self.history_cache_file):
                with open(self.history_cache_file, 'r', encoding='utf-8') as f:
                    self._history_cache = json.load(f)
                self.logger.info(f"成功加载历史数据缓存，包含{len(self._history_cache)}个行业")
            else:
                self._history_cache = {}
                self.logger.info("历史数据缓存文件不存在，创建新缓存")
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"加载历史数据缓存失败: {e}")
            self._history_cache = {}
    
    def save_history_cache(self):
        """保存历史数据缓存"""
        try:
            with open(self.history_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._history_cache, f, ensure_ascii=False, indent=2)
            self.logger.info("成功保存历史数据缓存")
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"保存历史数据缓存失败: {e}")
    
    def get_sector_history(self, sector_name: str, days: int = 90) -> pd.DataFrame:
        """
        获取行业历史数据，支持多数据源和模拟数据
        
        Args:
            sector_name: 行业名称
            days: 获取天数
            
        Returns:
            行业历史数据DataFrame
        """
        try:
            # 检查缓存
            cache_key = f"{sector_name}_{days}"
            if cache_key in self._cache and time.time() - self._cache[cache_key]['timestamp'] < self._cache_expiry:
                self.logger.info(f"从缓存获取{sector_name}历史数据")
                return self._cache[cache_key]['data']
            
            # 尝试从实时数据源获取
            df = self._get_history_from_realtime(sector_name, days)
            
            # 如果实时数据获取失败，尝试从历史缓存获取
            if df is None or df.empty:
                df = self._get_history_from_cache(sector_name, days)
            
            # 如果历史缓存也没有，生成模拟数据
            if df is None or df.empty:
                df = self._generate_mock_history(sector_name, days)
                self.logger.warning(f"使用模拟数据作为{sector_name}的历史数据")
            
            # 更新缓存
            self._cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }
            
            # 更新历史缓存
            if not df.empty and sector_name not in self._history_cache:
                # 只保存最近的数据到历史缓存
                recent_data = df.tail(30).to_dict('records')
                self._history_cache[sector_name] = recent_data
                self.save_history_cache()
            
            return df
        
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"获取{sector_name}历史数据失败: {e}")
            # 出错时返回模拟数据
            return self._generate_mock_history(sector_name, days)
    
    def _get_history_from_realtime(self, sector_name: str, days: int) -> Optional[pd.DataFrame]:
        """
        从实时数据源获取历史数据
        
        Args:
            sector_name: 行业名称
            days: 获取天数
            
        Returns:
            行业历史数据DataFrame或None
        """
        try:
            import akshare as ak
            
            # 定义数据源配置
            self.data_sources = [
                {'name': '东方财富', 'retry': 3},
                {'name': '申万行业', 'retry': 2},
                {'name': '概念板块', 'retry': 2}
            ] if not hasattr(self, 'data_sources') else self.data_sources
            
            # 尝试从东方财富获取数据
            try:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                df = ak.stock_board_industry_hist_em(symbol=sector_name, start_date=start_date)
                if df is not None and not df.empty:
                    df['成交量'] = df['成交量'].astype(float)
                    volume_value = df['成交量'].iloc[-1]
                if df is not None and not df.empty and '收盘' in df.columns:
                    return df
                else:
                    self.logger.warning(f'东方财富返回无效数据格式: {sector_name}')
                    return None
            except (Exception, IndexError, KeyError, TypeError) as e:
                self.logger.warning(f"从东方财富获取{sector_name}历史数据失败: {e}")
            
            # 尝试从申万行业指数获取数据
            try:
                sw_code = self._get_sw_industry_code(sector_name)
                if sw_code:
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    try:
                        # 获取申万行业成分股
                        cons_df = ak.sw_index_cons(index_code=sw_code)
                        # 获取行业指数数据
                        df = ak.sw_index_daily(index_code=sw_code)
                        if df is not None and not df.empty:
                            df = df[df['date'] >= start_date]
                            df = df.rename(columns={'date': '日期', 'close': '收盘', 'open': '开盘', 
                                                  'high': '最高', 'low': '最低', 'volume': '成交量'})
                            return df
                    except AttributeError:
                        self.logger.error('检测到旧版akshare，请升级至最新版本：pip install --upgrade akshare')
                    except (Exception, IndexError, KeyError, TypeError) as e:
                        self.logger.error(f'申万指数接口异常: {str(e)}')
            except (Exception, IndexError, KeyError, TypeError) as e:
                self.logger.warning(f"从申万行业指数获取{sector_name}历史数据失败: {e}")
            
            # 尝试从概念板块获取数据
            try:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                try:
                    df = ak.stock_board_concept_hist_em(symbol=sector_name, start_date=start_date)
                    if df is not None and not df.empty and '收盘' in df.columns:
                        return df
                    else:
                        self.logger.warning(f'概念板块返回无效数据: {sector_name}')
                        return None
                except (Exception, IndexError, KeyError, TypeError) as e:
                    self.logger.error(f'获取概念板块数据异常: {str(e)}')
                    return None
            except (Exception, IndexError, KeyError, TypeError) as e:
                self.logger.warning(f"从概念板块获取{sector_name}历史数据失败: {e}")
            
            return None
        
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"从实时数据源获取{sector_name}历史数据失败: {e}")
            return None
    
    def _get_history_from_cache(self, sector_name: str, days: int) -> Optional[pd.DataFrame]:
        """
        从历史缓存获取数据
        
        Args:
            sector_name: 行业名称
            days: 获取天数
            
        Returns:
            行业历史数据DataFrame或None
        """
        try:
            if sector_name in self._history_cache:
                cached_data = self._history_cache[sector_name]
                if cached_data:
                    df = pd.DataFrame(cached_data)
                    # 确保日期列存在
                    if '日期' not in df.columns and 'date' in df.columns:
                        df = df.rename(columns={'date': '日期'})
                    return df
            return None
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"从历史缓存获取{sector_name}数据失败: {e}")
            return None
    
    def _generate_mock_history(self, sector_name: str, days: int) -> pd.DataFrame:
        """
        生成模拟历史数据
        
        Args:
            sector_name: 行业名称
            days: 生成天数
            
        Returns:
            模拟的行业历史数据DataFrame
        """
        try:
            # 生成日期序列
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
            date_strings = [d.strftime('%Y-%m-%d') for d in date_range]
            
            # 生成基础价格和波动
            base_price = 1000 + np.random.randint(-200, 200)  # 基础价格在800-1200之间
            volatility = np.random.uniform(0.005, 0.02)  # 每日波动率
            trend = np.random.uniform(-0.001, 0.002)  # 整体趋势
            
            # 生成价格序列
            prices = []
            current_price = base_price
            for i in range(len(date_range)):
                # 添加随机波动和趋势
                change = current_price * (np.random.normal(trend, volatility))
                current_price += change
                prices.append(max(current_price, 100))  # 确保价格不会太低
            
            # 生成其他数据
            opens = [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices]
            highs = [max(o, c) * (1 + np.random.uniform(0, 0.02)) for o, c in zip(opens, prices)]
            lows = [min(o, c) * (1 - np.random.uniform(0, 0.02)) for o, c in zip(opens, prices)]
            volumes = [np.random.randint(10000, 1000000) for _ in range(len(date_range))]
            
            # 创建DataFrame
            data = {
                '日期': date_strings,
                '开盘': opens,
                '收盘': prices,
                '最高': highs,
                '最低': lows,
                '成交量': volumes
            }
            
            df = pd.DataFrame(data)
            return df
        
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"生成{sector_name}模拟历史数据失败: {e}")
            # 创建一个最小的有效DataFrame
            return pd.DataFrame({
                '日期': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)],
                '开盘': [1000] * days,
                '收盘': [1000] * days,
                '最高': [1050] * days,
                '最低': [950] * days,
                '成交量': [100000] * days
            })
    
    def _get_sw_industry_code(self, industry_name: str) -> str:
        """
        获取申万行业代码
        
        Args:
            industry_name: 行业名称
            
        Returns:
            申万行业代码
        """
        # 申万行业代码映射表 - 与全市场分析模块保持一致的行业分类标准
        sw_industry_map = {
            # 申万一级行业
            "农林牧渔": "801010",
            "采掘": "801020",
            "化工": "801030",
            "钢铁": "801040",
            "有色金属": "801050",
            "电子": "801080",
            "家用电器": "801110",
            "食品饮料": "801120",
            "纺织服装": "801130",
            "医药生物": "801150",
            "公用事业": "801160",
            "交通运输": "801170",
            "房地产": "801180",
            "银行": "801190",
            "非银金融": "801200",
            "综合": "801230",
            "建筑材料": "801710",
            "建筑装饰": "801720",
            "电气设备": "801730",
            "机械设备": "801740",
            "国防军工": "801750",
            "计算机": "801760",
            "传媒": "801770",
            "通信": "801780",
            "社会服务": "801790",
            "汽车": "801880",
            
            # 细分行业和概念
            "电力设备": "801730",
            "石油石化": "801020",
            "煤炭": "801020",
            "环保": "801160",
            "美容护理": "801130",
            "商贸零售": "801200",
            "消费电子": "801080",
            "半导体": "801080",
            "软件服务": "801760",
            "新能源": "801730",
            "人工智能": "801760",
            "互联网": "801760",
            "医疗服务": "801150",
            "医疗器械": "801150",
            "基础化学": "801030",
            "电子元件": "801080",
            "通信设备": "801780",
            "光伏": "801730",
            "风电": "801730",
            "储能": "801730",
            "新能源车": "801880",
            "锂电池": "801730",
            "云计算": "801760",
            "大数据": "801760",
            "物联网": "801780",
            "生物医药": "801150",
            "军工": "801750",
            "航空航天": "801750",
            "稀土永磁": "801050",
            "智能驾驶": "801880",
            "智能家居": "801110"
        }
        
        # 直接匹配
        if industry_name in sw_industry_map:
            return sw_industry_map[industry_name]
        
        # 部分匹配
        for key, code in sw_industry_map.items():
            if key in industry_name or industry_name in key:
                return code
        
        # 如果无法匹配，记录日志
        self.logger.warning(f"无法匹配行业代码: {industry_name}")
        return ""
    
    def get_sector_data(self, sector_name: str = None) -> List[Dict]:
        """
        获取行业实时数据，支持多数据源和模拟数据，增强异常处理和数据一致性检查
        
        Args:
            sector_name: 行业名称，如果为None则获取所有行业
            
        Returns:
            行业实时数据列表
        """
        try:
            # 检查缓存
            cache_key = f"sector_data_{sector_name if sector_name else 'all'}"
            if cache_key in self._cache and time.time() - self._cache[cache_key]['timestamp'] < self._cache_expiry:
                self.logger.info(f"从缓存获取行业数据")
                return self._cache[cache_key]['data']
            
            # 尝试从实时数据源获取
            sectors = self._get_sectors_from_realtime(sector_name)
            
            # 数据一致性检查
            if sectors:
                sectors = self._validate_sector_data(sectors)
                
                # 如果数据一致性检查后数据为空，则使用历史数据或模拟数据
                if not sectors:
                    self.logger.warning("数据一致性检查后数据为空，尝试使用历史数据")
            
            # 如果实时数据获取失败，尝试从历史数据中获取
            if not sectors:
                sectors = self._get_sectors_from_history(sector_name)
                if sectors:
                    self.logger.info(f"使用历史数据作为行业实时数据")
            
            # 如果历史数据也没有，生成模拟数据
            if not sectors:
                sectors = self._generate_mock_sectors(sector_name)
                self.logger.warning(f"使用模拟数据作为行业实时数据")
            
            # 更新缓存
            self._cache[cache_key] = {
                'data': sectors,
                'timestamp': time.time()
            }
            
            # 更新历史数据
            self._update_sector_history(sectors)
            
            return sectors
        
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"获取行业数据失败: {e}")
            # 出错时返回模拟数据
            return self._generate_mock_sectors(sector_name)
    
    def _validate_sector_data(self, sectors: List[Dict]) -> List[Dict]:
        """
        验证行业数据的一致性和有效性
        
        Args:
            sectors: 行业数据列表
            
        Returns:
            验证后的行业数据列表
        """
        try:
            if not sectors:
                return []
                
            valid_sectors = []
            for sector in sectors:
                # 检查必要字段是否存在
                required_fields = ['name', 'price', 'change_pct']
                if not all(field in sector for field in required_fields):
                    self.logger.warning(f"行业数据缺少必要字段: {sector.get('name', '未知行业')}")
                    continue
                    
                # 检查数值字段是否有效
                try:
                    price = float(sector['price'])
                    change_pct = float(sector['change_pct'])
                    
                    # 检查价格是否在合理范围内
                    if price <= 0 or price > 10000:
                        self.logger.warning(f"行业{sector['name']}价格异常: {price}")
                        # 修正异常价格
                        sector['price'] = 1000.0
                    
                    # 检查涨跌幅是否在合理范围内
                    if abs(change_pct) > 15:
                        self.logger.warning(f"行业{sector['name']}涨跌幅异常: {change_pct}%")
                        # 修正异常涨跌幅
                        sector['change_pct'] = np.sign(change_pct) * 10.0
                        
                    valid_sectors.append(sector)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"行业{sector.get('name', '未知行业')}数据格式错误: {e}")
                    continue
            
            # 检查数据集整体一致性
            if valid_sectors:
                # 计算涨跌幅的平均值和标准差
                change_pcts = [s['change_pct'] for s in valid_sectors]
                mean_change = np.mean(change_pcts)
                std_change = np.std(change_pcts)
                
                # 标记异常值
                for sector in valid_sectors:
                    # 如果涨跌幅偏离均值超过3个标准差，标记为异常
                    if abs(sector['change_pct'] - mean_change) > 3 * std_change:
                        sector['is_outlier'] = True
                        self.logger.warning(f"行业{sector['name']}涨跌幅为异常值: {sector['change_pct']}%")
                    else:
                        sector['is_outlier'] = False
            
            return valid_sectors
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"验证行业数据失败: {e}")
            return sectors  # 出错时返回原始数据
    
    def _get_sectors_from_history(self, sector_name: str = None) -> List[Dict]:
        """
        从历史数据中获取行业数据
        
        Args:
            sector_name: 行业名称，如果为None则获取所有行业
            
        Returns:
            行业数据列表
        """
        try:
            if not hasattr(self, '_history_cache'):
                return []
                
            result = []
            
            # 如果指定了行业名称，只获取该行业的数据
            if sector_name and sector_name in self._history_cache:
                hist_data = self._history_cache[sector_name]
                if hist_data:
                    # 使用最近的历史数据
                    latest_data = hist_data[-1] if isinstance(hist_data, list) else hist_data
                    # 构建行业数据
                    sector = {
                        'code': latest_data.get('code', ''),
                        'name': sector_name,
                        'price': latest_data.get('收盘', latest_data.get('close', 1000.0)),
                        'change_pct': 0.0,  # 默认涨跌幅为0
                        'volume': latest_data.get('成交量', latest_data.get('volume', 0.0)),
                        'source': '历史数据'
                    }
                    result.append(sector)
            # 获取所有行业的数据
            elif not sector_name:
                for name, hist_data in self._history_cache.items():
                    if hist_data:
                        # 使用最近的历史数据
                        latest_data = hist_data[-1] if isinstance(hist_data, list) else hist_data
                        # 构建行业数据
                        sector = {
                            'code': latest_data.get('code', ''),
                            'name': name,
                            'price': latest_data.get('收盘', latest_data.get('close', 1000.0)),
                            'change_pct': 0.0,  # 默认涨跌幅为0
                            'volume': latest_data.get('成交量', latest_data.get('volume', 0.0)),
                            'source': '历史数据'
                        }
                        result.append(sector)
            
            return result
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"从历史数据获取行业数据失败: {e}")
            return []
    
    def _update_sector_history(self, sectors: List[Dict]) -> None:
        """
        更新行业历史数据
        
        Args:
            sectors: 行业数据列表
        """
        try:
            if not sectors:
                return
                
            for sector in sectors:
                name = sector['name']
                # 只保存来自实时数据源的数据
                if sector.get('source', '') != '模拟数据':
                    # 构建历史数据记录
                    record = {
                        'code': sector.get('code', ''),
                        '日期': datetime.now().strftime('%Y-%m-%d'),
                        '收盘': sector['price'],
                        '涨跌幅': sector['change_pct'],
                        '成交量': sector.get('volume', 0.0)
                    }
                    
                    # 更新历史缓存
                    if name not in self._history_cache:
                        self._history_cache[name] = [record]
                    else:
                        # 检查是否已存在今日数据
                        today = datetime.now().strftime('%Y-%m-%d')
                        existing_records = self._history_cache[name]
                        if isinstance(existing_records, list):
                            # 检查是否已有今日数据
                            has_today = False
                            for i, rec in enumerate(existing_records):
                                if rec.get('日期', '') == today:
                                    # 更新今日数据
                                    existing_records[i] = record
                                    has_today = True
                                    break
                            
                            # 如果没有今日数据，添加新记录
                            if not has_today:
                                existing_records.append(record)
                                # 只保留最近30条记录
                                if len(existing_records) > 30:
                                    existing_records = existing_records[-30:]
                                self._history_cache[name] = existing_records
                        else:
                            # 如果不是列表，重新初始化
                            self._history_cache[name] = [record]
            
            # 保存历史缓存
            self.save_history_cache()
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"更新行业历史数据失败: {e}")

    
    def _load_industry_name_map(self) -> Dict:
        """加载行业名称映射配置"""
        mapping_file = os.path.join(self.cache_dir, "industry_name_mapping.json")
        try:
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning("行业名称映射文件不存在")
                return {}
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"加载行业名称映射失败: {e}")
            return {}
    
    def _standardize_industry_name(self, name: str) -> str:
        """标准化行业名称，确保在不同模块中使用统一的行业分类标准"""
        if not name:
            return name
            
        # 直接从映射表中查找
        if name in self.industry_name_map:
            return self.industry_name_map[name]
            
        # 尝试部分匹配
        for key, value in self.industry_name_map.items():
            if key in name or name in key:
                self.logger.info(f"行业名称部分匹配: {name} -> {value}")
                return value
                
        # 如果没有匹配到，返回原名称
        return name
    
    def _get_sectors_from_realtime(self, sector_name: str = None) -> List[Dict]:
        """
        从实时数据源获取行业数据（统一使用东方财富二级行业分类）
        """
        try:
            import akshare as ak
            df = ak.stock_board_industry_name_em()
            
            # 直接使用东方财富的细分行业数据
            result_sectors = []
            for _, row in df.iterrows():
                try:
                    # 处理成交量计算逻辑
                    volume_value = 0.0
                    if '总市值' in df.columns and '换手率' in df.columns:
                        try:
                            volume_value = float(row['换手率']) * float(row['总市值']) / 100
                        except (ValueError, TypeError):
                            volume_value = 0.0
                    
                    # 标准化行业名称
                    original_name = row['板块名称']
                    industry_name = self._standardize_industry_name(original_name)
                    
                    # 记录行业名称映射情况
                    if original_name != industry_name:
                        self.logger.info(f"行业名称标准化: {original_name} -> {industry_name}")
                    
                    sector = {
                        'code': row['板块代码'] if '板块代码' in df.columns else '',
                        'name': industry_name,  # 使用标准化后的行业名称
                        'original_name': original_name,  # 保留原始名称以便追踪
                        'level': '细分行业',
                        'standard_code': f'EM_{row["板块代码"]}' if '板块代码' in df.columns else '',
                        'price': float(row['最新价']),
                        'change_pct': float(row['涨跌幅']),
                        'volume': volume_value/100000000 if volume_value > 0 else 0.0,  # 转换为亿元
                        'source': '东方财富'
                    }
                    result_sectors.append(sector)
                except (ValueError, TypeError) as e:
                    self.logger.error(f"处理行业数据行时出错: {e}, 行数据: {row}")
                    continue
            
            if not result_sectors:
                self.logger.error("获取行业数据失败或数据为空")
                return []
            
            self.logger.info(f"从东方财富获取到{len(result_sectors)}个行业数据")
            return result_sectors
            
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"从东方财富获取行业数据失败: {e}")
            return []
        
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"从实时数据源获取行业数据失败: {e}")
            return []
    
    def _optimize_cache_strategy(self):
        """优化缓存策略"""
        try:
            # 动态调整缓存过期时间
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 15:  # 交易时段
                self._cache_expiry = 300  # 5分钟
            else:
                self._cache_expiry = 1800  # 30分钟
            
            # 清理过期缓存
            current_time = time.time()
            expired_keys = [k for k, v in self._cache.items() 
                          if current_time - v['timestamp'] > self._cache_expiry]
            for k in expired_keys:
                del self._cache[k]
                
            # 压缩历史缓存
            if len(self._history_cache) > 1000:
                sorted_items = sorted(self._history_cache.items(), 
                                    key=lambda x: x[1]['last_access'])
                self._history_cache = dict(sorted_items[-1000:])
                
            return True
            
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"优化缓存策略时出错: {str(e)}")
            return False
    
    def _preload_common_sectors(self):
        """预加载常用行业数据"""
        try:
            common_sectors = self._get_most_active_sectors()
            for sector in common_sectors:
                if sector not in self._cache:
                    self.get_sector_history(sector, days=30)
            return True
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"预加载行业数据时出错: {str(e)}")
            return False
    
    def _get_most_active_sectors(self) -> List[str]:
        """获取最活跃的行业列表"""
        try:
            # 这里可以根据成交量、关注度等指标来确定最活跃的行业
            return ['科技', '医药', '金融', '消费', '新能源']
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"获取活跃行业列表时出错: {str(e)}")
            return []
    
    def _generate_mock_sectors(self, sector_name: str = None) -> List[Dict]:
        """
        生成模拟行业数据，包含更多维度的指标
        
        Args:
            sector_name: 行业名称，如果为None则生成多个行业
            
        Returns:
            模拟的行业数据列表，包含更丰富的指标
        """
        try:
            # 默认行业列表 - 与全市场分析模块保持一致的行业分类
            default_sectors = [
                "电子", "计算机", "通信", "医药生物", "食品饮料", 
                "家用电器", "汽车", "银行", "非银金融", "房地产",
                "建筑装饰", "建筑材料", "电气设备", "机械设备", "国防军工",
                "传媒", "社会服务", "纺织服装", "农林牧渔", "钢铁",
                "有色金属", "化工", "煤炭", "石油石化", "环保",
                "新能源", "半导体", "人工智能", "消费电子", "互联网",
                "光伏", "风电", "储能", "新能源车", "锂电池",
                "云计算", "大数据", "物联网", "生物医药", "军工"
            ]
            
            # 如果指定了行业名称，则只生成该行业的数据
            if sector_name:
                sectors = [sector_name]
            else:
                sectors = default_sectors
            
            # 生成市场整体趋势，用于保持数据的一致性
            market_trend = np.random.normal(0, 1.0)  # 市场整体涨跌趋势
            north_flow_direction = 1 if np.random.random() > 0.5 else -1  # 北向资金流向
            
            result = []
            for name in sectors:
                # 生成随机价格和涨跌幅，考虑市场整体趋势
                price = np.random.uniform(800, 1500)
                # 涨跌幅受市场整体趋势影响，但有自己的随机性
                change_pct = market_trend + np.random.normal(0, 2.0)  
                volume = np.random.uniform(5, 50)  # 5-50亿元
                
                # 生成北向资金流入数据
                north_flow = np.random.uniform(0, 5) * north_flow_direction
                if change_pct > 0 and north_flow_direction > 0:
                    # 正相关：行业上涨且北向资金流入
                    north_flow = abs(north_flow) * (1 + change_pct/10)
                elif change_pct < 0 and north_flow_direction < 0:
                    # 正相关：行业下跌且北向资金流出
                    north_flow = -abs(north_flow) * (1 + abs(change_pct)/10)
                
                # 生成机构持仓变化数据
                inst_holding = np.random.uniform(10, 60)  # 机构持仓比例(10%-60%)
                inst_change = np.random.normal(0, 2.0)  # 机构持仓变化百分比
                if change_pct > 1.5:
                    # 大幅上涨的行业，机构可能增持
                    inst_change = abs(inst_change)
                elif change_pct < -1.5:
                    # 大幅下跌的行业，机构可能减持
                    inst_change = -abs(inst_change)
                
                # 生成上涨下跌家数
                total_stocks = np.random.randint(30, 100)
                if change_pct > 0:
                    up_count = int(total_stocks * (0.5 + change_pct/20))
                else:
                    up_count = int(total_stocks * (0.5 + change_pct/20))
                up_count = max(0, min(up_count, total_stocks))
                down_count = total_stocks - up_count
                
                # 生成行业热度评分
                hot_score = change_pct * 3  # 基础分
                hot_score += (volume / 25 - 1) * 25  # 成交量得分
                hot_score += north_flow * 5  # 北向资金得分
                hot_score += inst_change * 3  # 机构持仓变化得分
                
                # 热度等级
                if hot_score > 50:
                    hot_level = '极热'
                elif hot_score > 30:
                    hot_level = '热门'
                elif hot_score > 10:
                    hot_level = '温和'
                else:
                    hot_level = '冷淡'
                
                sector = {
                    'code': f"BK{np.random.randint(100000, 999999)}",
                    'name': name,
                    'price': price,
                    'change_pct': change_pct,
                    'volume': volume,
                    'north_flow': north_flow,
                    'institution_holding': inst_holding,
                    'institution_change': inst_change,
                    'up_count': up_count,
                    'down_count': down_count,
                    'up_down_ratio': f"{up_count}/{down_count}",
                    'total_stocks': total_stocks,
                    'hot_score': hot_score,
                    'hot_level': hot_level,
                    'source': '模拟数据',
                    'reliability': 0.6  # 模拟数据可靠性较低
                }
                result.append(sector)
            
            return result
        
        except (Exception, IndexError, KeyError, TypeError) as e:
            self.logger.error(f"生成模拟行业数据失败: {e}")
            # 返回一个最小的有效数据
            if sector_name:
                return [{
                    'code': 'BK000000',
                    'name': sector_name,
                    'price': 1000.0,
                    'change_pct': 0.0,
                    'volume': 10.0,
                    'north_flow': 0.0,
                    'institution_holding': 30.0,
                    'institution_change': 0.0,
                    'up_count': 15,
                    'down_count': 15,
                    'up_down_ratio': '15/15',
                    'total_stocks': 30,
                    'hot_score': 0.0,
                    'hot_level': '冷淡',
                    'source': '模拟数据',
                    'reliability': 0.6
                }]
            else:
                return [{
                    'code': 'BK000000',
                    'name': '默认行业',
                    'price': 1000.0,
                    'change_pct': 0.0,
                    'volume': 10.0,
                    'north_flow': 0.0,
                    'institution_holding': 30.0,
                    'institution_change': 0.0,
                    'up_count': 15,
                    'down_count': 15,
                    'up_down_ratio': '15/15',
                    'total_stocks': 30,
                    'hot_score': 0.0,
                    'hot_level': '冷淡',
                    'source': '模拟数据',
                    'reliability': 0.6
                }]
        
    
    def get_industry_data(self, industry_code: str, retries=3) -> dict:
        """获取行业数据，带有重试机制和错误处理"""
        for attempt in range(retries):
            try:
                data = ak.stock_board_industry_hist_em(symbol=industry_code, 
                                                     start_date=self._get_date_str(30),
                                                     end_date=self._get_date_str(0))
                
                # 数据完整性校验
                if data.empty or '收盘' not in data.columns:
                    raise ValueError(f"行业{industry_code}数据不完整")
                
                # 计算关键指标
                data['MA20'] = data['收盘'].rolling(20).mean()
                data['Volatility'] = data['收盘'].pct_change().std() * np.sqrt(252)
                
                return {
                    'industry': industry_code,
                    'data': data.to_dict(orient='records'),
                    'metadata': {
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'data_points': len(data),
                        'status': 'success'
                    }
                }
            
            except (Exception, IndexError, KeyError, TypeError) as e:
                self.logger.error(f"获取行业数据失败（尝试{attempt+1}/{retries}）: {str(e)}")
                time.sleep(2 ** attempt)  # 指数退避
                
                # 最后一次尝试仍然失败时返回错误信息
                if attempt == retries - 1:
                    return {
                        'industry': industry_code,
                        'error': str(e),
                        'metadata': {
                            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'error'
                        }
                    }

    # 删除未完成的方法定义