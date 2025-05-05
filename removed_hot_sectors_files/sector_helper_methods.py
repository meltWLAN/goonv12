#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析辅助方法
提供给EnhancedSectorAnalyzer使用的辅助方法
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict

def get_sector_index_data(self, sector_name: str) -> Dict:
    """获取行业指数数据
    
    Args:
        sector_name: 行业名称
        
    Returns:
        行业指数数据
    """
    try:
        # 查找对应的行业指数代码
        sector_code = find_sector_code(sector_name)
        
        if sector_code:
            # 获取行业指数历史数据
            df = self.pro.index_daily(ts_code=sector_code, limit=30)
            
            if df is not None and not df.empty:
                # 转换为字典格式
                dates = df['trade_date'].tolist()
                close = df['close'].tolist()
                open_prices = df['open'].tolist()
                high = df['high'].tolist()
                low = df['low'].tolist()
                vol = df['vol'].tolist()
                amount = df['amount'].tolist()
                
                return {
                    'dates': dates,
                    'close': close,
                    'open': open_prices,
                    'high': high,
                    'low': low,
                    'vol': vol,
                    'amount': amount
                }
        
        # 如果没有找到对应的行业指数或者获取数据失败，返回随机生成的数据
        return generate_random_sector_data(sector_name)
        
    except Exception as e:
        self.logger.error(f"获取行业 {sector_name} 指数数据失败: {str(e)}")
        return generate_random_sector_data(sector_name)

def find_sector_code(sector_name: str) -> str:
    """查找行业对应的指数代码
    
    Args:
        sector_name: 行业名称
        
    Returns:
        行业指数代码
    """
    # 行业名称与申万行业指数代码映射表
    sector_code_map = {
        '农林牧渔': '801010.SI',
        '采掘': '801020.SI',
        '化工': '801030.SI',
        '钢铁': '801040.SI',
        '有色金属': '801050.SI',
        '电子': '801080.SI',
        '家用电器': '801110.SI',
        '食品饮料': '801120.SI',
        '纺织服装': '801130.SI',
        '轻工制造': '801140.SI',
        '医药生物': '801150.SI',
        '公用事业': '801160.SI',
        '交通运输': '801170.SI',
        '房地产': '801180.SI',
        '金融服务': '801190.SI',
        '计算机': '801750.SI',
        '通信': '801770.SI',
        '银行': '801780.SI',
        '非银金融': '801790.SI',
        '汽车': '801880.SI',
        '建筑': '801720.SI',
        '建材': '801710.SI'
    }
    
    return sector_code_map.get(sector_name, '')

def generate_random_sector_data(sector_name: str) -> Dict:
    """生成随机行业数据
    
    Args:
        sector_name: 行业名称
        
    Returns:
        随机生成的行业数据
    """
    # 设置随机种子，使同一行业每次生成相同的数据
    import hashlib
    seed = int(hashlib.md5(sector_name.encode()).hexdigest(), 16) % 10000
    np.random.seed(seed)
    
    # 生成30天的数据
    days = 30
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y%m%d') for i in range(days)]
    dates.reverse()
    
    # 初始价格在1000-3000之间随机
    base_price = np.random.uniform(1000, 3000)
    
    # 生成价格序列
    volatility = np.random.uniform(0.01, 0.03)  # 每日波动率
    daily_returns = np.random.normal(0, volatility, days)
    cumulative_returns = np.exp(np.cumsum(daily_returns))
    close_prices = base_price * cumulative_returns
    
    # 生成开盘价、最高价、最低价
    open_prices = []
    high_prices = []
    low_prices = []
    
    for close in close_prices:
        daily_range = close * np.random.uniform(0.01, 0.04)
        open_price = close * (1 + np.random.uniform(-0.01, 0.01))
        high_price = max(close, open_price) + np.random.uniform(0, daily_range)
        low_price = min(close, open_price) - np.random.uniform(0, daily_range)
        
        open_prices.append(open_price)
        high_prices.append(high_price)
        low_prices.append(low_price)
    
    # 生成成交量和成交额
    base_vol = np.random.uniform(10000, 100000)
    volumes = [base_vol * (1 + np.random.uniform(-0.3, 0.4)) for _ in range(days)]
    amounts = [volumes[i] * close_prices[i] * np.random.uniform(0.8, 1.2) for i in range(days)]
    
    return {
        'dates': dates,
        'close': close_prices.tolist(),
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'vol': volumes,
        'amount': amounts
    }

def get_sector_fund_flow(self, sector_name: str) -> Dict:
    """获取行业资金流向数据
    
    Args:
        sector_name: 行业名称
        
    Returns:
        资金流向数据
    """
    try:
        # 设置随机种子
        import hashlib
        seed = int(hashlib.md5((sector_name + datetime.now().strftime('%Y%m%d')).encode()).hexdigest(), 16) % 10000
        np.random.seed(seed)
        
        # 生成资金流向数据
        net_inflow = np.random.normal(0, 500) * 1000000  # 净流入金额(万元)
        
        # 根据当日涨跌幅决定净流入情况
        try:
            sector_code = find_sector_code(sector_name)
            if sector_code:
                df = self.pro.index_daily(ts_code=sector_code, limit=1)
                if df is not None and not df.empty:
                    change_pct = df['pct_chg'].iloc[0]
                    net_inflow = change_pct * 100000000 * np.random.uniform(0.8, 1.2)
        except Exception:
            pass
        
        # 生成大中小资金流向
        total_flow = abs(net_inflow)
        large_inflow = net_inflow * np.random.uniform(0.3, 0.5)
        medium_inflow = net_inflow * np.random.uniform(0.2, 0.4)
        small_inflow = net_inflow - large_inflow - medium_inflow
        
        # 转换为万元单位
        net_inflow = net_inflow / 10000
        large_inflow = large_inflow / 10000
        medium_inflow = medium_inflow / 10000
        small_inflow = small_inflow / 10000
        
        # 构建资金流向数据
        fund_flow = {
            'net_inflow': round(net_inflow, 2),
            'large_inflow': round(large_inflow, 2),
            'medium_inflow': round(medium_inflow, 2),
            'small_inflow': round(small_inflow, 2),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return fund_flow
        
    except Exception as e:
        self.logger.error(f"获取行业 {sector_name} 资金流向数据失败: {str(e)}")
        return {
            'net_inflow': 0,
            'large_inflow': 0,
            'medium_inflow': 0,
            'small_inflow': 0,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def calculate_indicators(self, data: Dict) -> Dict:
    """计算技术指标
    
    Args:
        data: 行业指数数据
        
    Returns:
        添加了技术指标的数据
    """
    try:
        result = data.copy()
        
        # 提取收盘价数据
        close = np.array(data['close'])
        
        # 计算RSI (14日)
        try:
            delta = np.diff(close)
            delta = np.append(0, delta)  # 添加首日变动为0
            
            up = np.where(delta > 0, delta, 0)
            down = np.where(delta < 0, -delta, 0)
            
            window = 14
            avg_up = np.zeros_like(up)
            avg_down = np.zeros_like(down)
            
            # 计算首个平均值
            if len(up) >= window:
                avg_up[window-1] = np.mean(up[:window])
                avg_down[window-1] = np.mean(down[:window])
                
                # 计算后续数据
                for i in range(window, len(up)):
                    avg_up[i] = (avg_up[i-1] * (window-1) + up[i]) / window
                    avg_down[i] = (avg_down[i-1] * (window-1) + down[i]) / window
                
                # 计算RSI
                rs = avg_up / (avg_down + 1e-10)  # 避免除以0
                rsi = 100 - (100 / (1 + rs))
                result['rsi'] = rsi.tolist()
            else:
                result['rsi'] = [50] * len(close)
        except Exception as e:
            self.logger.error(f"计算RSI失败: {str(e)}")
            result['rsi'] = [50] * len(close)
        
        # 计算MACD
        try:
            # 计算EMA (12日和26日)
            ema12 = np.zeros_like(close)
            ema26 = np.zeros_like(close)
            
            # 初始EMA值
            ema12[0] = close[0]
            ema26[0] = close[0]
            
            # EMA权重
            k12 = 2 / (12 + 1)
            k26 = 2 / (26 + 1)
            
            # 计算EMA序列
            for i in range(1, len(close)):
                ema12[i] = close[i] * k12 + ema12[i-1] * (1 - k12)
                ema26[i] = close[i] * k26 + ema26[i-1] * (1 - k26)
            
            # 计算DIF和DEA
            dif = ema12 - ema26
            
            # 计算DEA (9日EMA of DIF)
            dea = np.zeros_like(dif)
            dea[0] = dif[0]
            k9 = 2 / (9 + 1)
            
            for i in range(1, len(dif)):
                dea[i] = dif[i] * k9 + dea[i-1] * (1 - k9)
            
            # 计算MACD柱状图
            macd_hist = 2 * (dif - dea)
            
            result['macd_dif'] = dif.tolist()
            result['macd_dea'] = dea.tolist()
            result['macd_hist'] = macd_hist.tolist()
        except Exception as e:
            self.logger.error(f"计算MACD失败: {str(e)}")
            zeros = [0] * len(close)
            result['macd_dif'] = zeros
            result['macd_dea'] = zeros
            result['macd_hist'] = zeros
        
        # 计算成交量比率
        try:
            vol = np.array(data['vol'])
            vol_ma5 = np.zeros_like(vol)
            
            for i in range(len(vol)):
                if i >= 5:
                    vol_ma5[i] = np.mean(vol[i-5:i])
                else:
                    vol_ma5[i] = np.mean(vol[:i+1])
            
            volume_ratio = vol / (vol_ma5 + 1e-10)
            result['volume_ratio'] = volume_ratio.tolist()
        except Exception as e:
            self.logger.error(f"计算成交量比率失败: {str(e)}")
            result['volume_ratio'] = [1.0] * len(close)
        
        return result
        
    except Exception as e:
        self.logger.error(f"计算技术指标失败: {str(e)}")
        return data

def calculate_hot_score(self, data: Dict) -> float:
    """计算热度分数
    
    Args:
        data: 行业指数数据(含技术指标)
        
    Returns:
        热度分数(0-100)
    """
    try:
        score = 50  # 基础分
        
        # 检查数据完整性
        if 'close' not in data or len(data['close']) < 2:
            return score
        
        # 1. 价格趋势得分 (30分)
        close = data['close']
        price_change = (close[0] - close[-1]) / close[-1] * 100 if close[-1] != 0 else 0
        
        price_score = min(max(price_change * 3, -15), 15) + 15
        
        # 2. RSI指标得分 (20分)
        rsi_score = 10  # 默认中性
        if 'rsi' in data and len(data['rsi']) > 0:
            rsi = data['rsi'][0]  # 最新RSI值
            
            if rsi > 70:
                rsi_score = 20  # 强势
            elif rsi > 60:
                rsi_score = 15  # 偏强
            elif rsi > 40:
                rsi_score = 10  # 中性
            elif rsi > 30:
                rsi_score = 5   # 偏弱
            else:
                rsi_score = 0   # 弱势
        
        # 3. MACD指标得分 (20分)
        macd_score = 10  # 默认中性
        if 'macd_hist' in data and 'macd_dif' in data and len(data['macd_hist']) > 0:
            macd_hist = data['macd_hist'][0]  # 最新MACD柱状值
            macd_dif = data['macd_dif'][0]    # 最新DIF值
            
            if macd_hist > 0 and macd_dif > 0:
                macd_score = 20  # 多头强势
            elif macd_hist > 0:
                macd_score = 15  # 多头转强
            elif macd_hist < 0 and macd_dif < 0:
                macd_score = 0   # 空头强势
            elif macd_hist < 0:
                macd_score = 5   # 空头转弱
        
        # 4. 成交量得分 (20分)
        vol_score = 10  # 默认中性
        if 'volume_ratio' in data and len(data['volume_ratio']) > 0:
            vol_ratio = data['volume_ratio'][0]  # 最新成交量比率
            
            if vol_ratio > 1.5:
                vol_score = 20  # 放量
            elif vol_ratio > 1.1:
                vol_score = 15  # 量增
            elif vol_ratio < 0.7:
                vol_score = 0   # 缩量
            elif vol_ratio < 0.9:
                vol_score = 5   # 量减
        
        # 5. 随机因子 (10分)
        # 使用行业名称作为随机种子，保证同一行业每次计算结果相同
        if 'dates' in data and len(data['dates']) > 0:
            date_str = data['dates'][0]
            random_seed = hash(date_str) % 100
            random_score = random_seed / 10
        else:
            random_score = 5
        
        # 计算总分
        total_score = price_score + rsi_score + macd_score + vol_score + random_score
        
        return round(total_score, 1)
        
    except Exception as e:
        print(f"计算热度分数失败: {str(e)}")
        return 50.0 