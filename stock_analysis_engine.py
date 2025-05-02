import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
from tushare_data_service import TushareDataService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StockAnalysisEngine")

class StockAnalysisEngine:
    """股票分析引擎，整合基本面分析和技术分析"""
    
    def __init__(self, tushare_token=None):
        """初始化分析引擎"""
        self.data_service = TushareDataService(token=tushare_token)
        logger.info("股票分析引擎初始化完成")
    
    # ===================== 基本面分析 =====================
    
    def calculate_financial_indicators(self, ts_code):
        """计算财务指标"""
        try:
            # 获取财务数据
            income = self.data_service.get_income_statement(ts_code)
            balance = self.data_service.get_balance_sheet(ts_code)
            cashflow = self.data_service.get_cash_flow(ts_code)
            
            if income.empty or balance.empty or cashflow.empty:
                logger.warning(f"财务数据不完整: {ts_code}")
                return pd.DataFrame()
            
            # 获取最新交易日数据，用于计算市值
            daily_basic = self.data_service.get_daily_basic(ts_code)
            if daily_basic.empty:
                logger.warning(f"无法获取市场数据: {ts_code}")
                return pd.DataFrame()
            
            # 合并期末日期相同的数据
            income = income.sort_values('end_date', ascending=False)
            balance = balance.sort_values('end_date', ascending=False)
            cashflow = cashflow.sort_values('end_date', ascending=False)
            
            # 提取关键财务数据
            fin_data = {}
            
            # 从利润表提取数据
            if not income.empty:
                fin_data['revenue'] = income['revenue'].iloc[0]  # 营业收入
                fin_data['net_profit'] = income['n_income'].iloc[0]  # 净利润
                fin_data['operate_profit'] = income['operate_profit'].iloc[0]  # 营业利润
                fin_data['total_profit'] = income['total_profit'].iloc[0]  # 利润总额
                fin_data['fin_exp'] = income['fin_exp'].iloc[0] if 'fin_exp' in income.columns else 0  # 财务费用
            
            # 从资产负债表提取数据
            if not balance.empty:
                fin_data['total_assets'] = balance['total_assets'].iloc[0]  # 总资产
                fin_data['total_liab'] = balance['total_liab'].iloc[0]  # 总负债
                fin_data['total_equity'] = balance['total_hldr_eqy_exc_min_int'].iloc[0]  # 股东权益
                fin_data['total_share'] = balance['total_share'].iloc[0] if 'total_share' in balance.columns else 0  # 总股本
            
            # 从现金流量表提取数据
            if not cashflow.empty:
                fin_data['op_cashflow'] = cashflow['n_cashflow_act'].iloc[0]  # 经营活动现金流
                fin_data['inv_cashflow'] = cashflow['n_cashflow_inv_act'].iloc[0] if 'n_cashflow_inv_act' in cashflow.columns else 0  # 投资活动现金流
                fin_data['fin_cashflow'] = cashflow['n_cash_flows_fnc_act'].iloc[0] if 'n_cash_flows_fnc_act' in cashflow.columns else 0  # 筹资活动现金流
            
            # 从行情数据获取市场相关数据
            if not daily_basic.empty:
                market_data = daily_basic.iloc[0]
                fin_data['close'] = market_data['close']  # 最新收盘价
                fin_data['pe'] = market_data['pe'] if 'pe' in market_data else 0  # 市盈率
                fin_data['pb'] = market_data['pb'] if 'pb' in market_data else 0  # 市净率
                fin_data['total_mv'] = market_data['total_mv'] if 'total_mv' in market_data else 0  # 总市值
                fin_data['circ_mv'] = market_data['circ_mv'] if 'circ_mv' in market_data else 0  # 流通市值
            
            # 计算财务指标
            indicators = {}
            
            # 偿债能力指标
            indicators['debt_to_assets'] = fin_data['total_liab'] / fin_data['total_assets'] if fin_data['total_assets'] else 0  # 资产负债率
            
            # 盈利能力指标
            indicators['roe'] = fin_data['net_profit'] / fin_data['total_equity'] if fin_data['total_equity'] else 0  # 净资产收益率
            indicators['roa'] = fin_data['net_profit'] / fin_data['total_assets'] if fin_data['total_assets'] else 0  # 总资产收益率
            indicators['profit_margin'] = fin_data['net_profit'] / fin_data['revenue'] if fin_data['revenue'] else 0  # 净利率
            indicators['gross_margin'] = (fin_data['revenue'] - fin_data['operate_profit']) / fin_data['revenue'] if fin_data['revenue'] else 0  # 毛利率
            
            # 经营能力指标
            indicators['asset_turnover'] = fin_data['revenue'] / fin_data['total_assets'] if fin_data['total_assets'] else 0  # 总资产周转率
            
            # 现金流指标
            indicators['cf_to_profit'] = fin_data['op_cashflow'] / fin_data['net_profit'] if fin_data['net_profit'] else 0  # 经营现金流/净利润
            indicators['cf_to_revenue'] = fin_data['op_cashflow'] / fin_data['revenue'] if fin_data['revenue'] else 0  # 经营现金流/营业收入
            
            # 估值指标
            indicators['pe'] = fin_data.get('pe', 0)  # 市盈率
            indicators['pb'] = fin_data.get('pb', 0)  # 市净率
            indicators['ps'] = fin_data['total_mv'] / fin_data['revenue'] if fin_data['revenue'] else 0  # 市销率
            
            # 整合为DataFrame
            result = pd.DataFrame([indicators])
            result['ts_code'] = ts_code
            result['end_date'] = income['end_date'].iloc[0] if not income.empty else None
            
            logger.info(f"计算财务指标成功: {ts_code}")
            return result
            
        except Exception as e:
            logger.error(f"计算财务指标失败: {ts_code}, 错误: {str(e)}")
            return pd.DataFrame()
    
    def analyze_growth(self, ts_code, periods=4):
        """分析增长性"""
        try:
            # 获取近几期财务数据
            income_list = []
            
            # 获取最近的几期财报
            for i in range(periods):
                year = datetime.now().year - (i // 4)
                quarter = 4 - (i % 4)
                if quarter == 0:
                    year -= 1
                    quarter = 4
                period = f"{year}{quarter:02d}31"
                
                income = self.data_service.get_income_statement(ts_code, period)
                if not income.empty:
                    income_list.append(income)
            
            if not income_list:
                logger.warning(f"无法获取历史财务数据: {ts_code}")
                return pd.DataFrame()
            
            # 合并财务数据
            income_df = pd.concat(income_list)
            income_df = income_df.sort_values('end_date', ascending=False)
            
            # 计算同比增长率
            growth = {}
            for i in range(len(income_df) - 4):
                current = income_df.iloc[i]
                prev_year = income_df.iloc[i + 4] if i + 4 < len(income_df) else None
                
                if prev_year is not None:
                    # 营收增长率
                    if prev_year['revenue'] and prev_year['revenue'] > 0:
                        growth_rate = (current['revenue'] - prev_year['revenue']) / prev_year['revenue']
                        growth[f"revenue_growth_{current['end_date']}"] = growth_rate
                    
                    # 净利润增长率
                    if prev_year['n_income'] and prev_year['n_income'] > 0:
                        growth_rate = (current['n_income'] - prev_year['n_income']) / prev_year['n_income']
                        growth[f"profit_growth_{current['end_date']}"] = growth_rate
            
            # 计算平均增长率
            revenue_growths = [v for k, v in growth.items() if 'revenue_growth' in k]
            profit_growths = [v for k, v in growth.items() if 'profit_growth' in k]
            
            result = {
                'ts_code': ts_code,
                'avg_revenue_growth': np.mean(revenue_growths) if revenue_growths else None,
                'avg_profit_growth': np.mean(profit_growths) if profit_growths else None,
                'latest_revenue_growth': revenue_growths[0] if revenue_growths else None,
                'latest_profit_growth': profit_growths[0] if profit_growths else None,
            }
            
            logger.info(f"分析增长性成功: {ts_code}")
            return pd.DataFrame([result])
            
        except Exception as e:
            logger.error(f"分析增长性失败: {ts_code}, 错误: {str(e)}")
            return pd.DataFrame()
    
    def calculate_quality_score(self, ts_code):
        """计算公司质量评分 (0-100)"""
        try:
            # 获取财务指标
            fin_indicators = self.calculate_financial_indicators(ts_code)
            if fin_indicators.empty:
                return 0
            
            # 获取增长性分析
            growth = self.analyze_growth(ts_code)
            
            # 计算评分
            score = 0
            
            # 1. 盈利能力 (30分)
            # ROE评分 (15分)
            roe = fin_indicators['roe'].iloc[0]
            if roe >= 0.20:  # ROE >= 20%
                score += 15
            elif roe >= 0.15:  # 15% <= ROE < 20%
                score += 12
            elif roe >= 0.10:  # 10% <= ROE < 15%
                score += 9
            elif roe >= 0.05:  # 5% <= ROE < 10%
                score += 6
            elif roe > 0:  # 0 < ROE < 5%
                score += 3
            
            # 净利率评分 (15分)
            profit_margin = fin_indicators['profit_margin'].iloc[0]
            if profit_margin >= 0.20:  # 净利率 >= 20%
                score += 15
            elif profit_margin >= 0.15:  # 15% <= 净利率 < 20%
                score += 12
            elif profit_margin >= 0.10:  # 10% <= 净利率 < 15%
                score += 9
            elif profit_margin >= 0.05:  # 5% <= 净利率 < 10%
                score += 6
            elif profit_margin > 0:  # 0 < 净利率 < 5%
                score += 3
            
            # 2. 财务健康度 (30分)
            # 资产负债率评分 (15分)
            debt_ratio = fin_indicators['debt_to_assets'].iloc[0]
            if debt_ratio <= 0.30:  # 负债率 <= 30%
                score += 15
            elif debt_ratio <= 0.40:  # 30% < 负债率 <= 40%
                score += 12
            elif debt_ratio <= 0.50:  # 40% < 负债率 <= 50%
                score += 9
            elif debt_ratio <= 0.60:  # 50% < 负债率 <= 60%
                score += 6
            elif debt_ratio <= 0.70:  # 60% < 负债率 <= 70%
                score += 3
            
            # 现金流质量评分 (15分)
            cf_ratio = fin_indicators['cf_to_profit'].iloc[0]
            if cf_ratio >= 1.2:  # 现金流/净利润 >= 1.2
                score += 15
            elif cf_ratio >= 1.0:  # 1.0 <= 现金流/净利润 < 1.2
                score += 12
            elif cf_ratio >= 0.8:  # 0.8 <= 现金流/净利润 < 1.0
                score += 9
            elif cf_ratio >= 0.6:  # 0.6 <= 现金流/净利润 < 0.8
                score += 6
            elif cf_ratio > 0:  # 0 < 现金流/净利润 < 0.6
                score += 3
            
            # 3. 增长性 (40分)
            if not growth.empty:
                # 营收增长率评分 (20分)
                rev_growth = growth['latest_revenue_growth'].iloc[0]
                if rev_growth >= 0.30:  # 增长率 >= 30%
                    score += 20
                elif rev_growth >= 0.20:  # 20% <= 增长率 < 30%
                    score += 16
                elif rev_growth >= 0.10:  # 10% <= 增长率 < 20%
                    score += 12
                elif rev_growth >= 0.05:  # 5% <= 增长率 < 10%
                    score += 8
                elif rev_growth > 0:  # 0 < 增长率 < 5%
                    score += 4
                
                # 净利润增长率评分 (20分)
                profit_growth = growth['latest_profit_growth'].iloc[0]
                if profit_growth >= 0.30:  # 增长率 >= 30%
                    score += 20
                elif profit_growth >= 0.20:  # 20% <= 增长率 < 30%
                    score += 16
                elif profit_growth >= 0.10:  # 10% <= 增长率 < 20%
                    score += 12
                elif profit_growth >= 0.05:  # 5% <= 增长率 < 10%
                    score += 8
                elif profit_growth > 0:  # 0 < 增长率 < 5%
                    score += 4
            
            logger.info(f"计算质量评分成功: {ts_code}, 得分: {score}")
            return score
            
        except Exception as e:
            logger.error(f"计算质量评分失败: {ts_code}, 错误: {str(e)}")
            return 0
    
    # ===================== 技术分析 =====================
    
    def analyze_technical_indicators(self, ts_code, start_date=None, end_date=None):
        """计算并分析技术指标"""
        try:
            # 获取日线数据
            daily = self.data_service.get_stock_daily(ts_code, start_date, end_date)
            if daily.empty:
                logger.warning(f"无法获取日线数据: {ts_code}")
                return pd.DataFrame()
            
            # 计算技术指标
            data = self.data_service.calculate_all_indicators(daily)
            
            # 分析趋势
            trend = self._analyze_trend(data)
            
            # 分析MACD
            macd_signal = self._analyze_macd(data)
            
            # 分析KDJ
            kdj_signal = self._analyze_kdj(data)
            
            # 分析布林带
            boll_signal = self._analyze_boll(data)
            
            # 分析RSI
            rsi_signal = self._analyze_rsi(data)
            
            # 汇总信号
            signals = {
                'ts_code': ts_code,
                'date': data['trade_date'].iloc[0],
                'close': data['close'].iloc[0],
                'trend': trend,
                'macd': macd_signal,
                'kdj': kdj_signal,
                'boll': boll_signal,
                'rsi': rsi_signal
            }
            
            # 综合评分 (-100 到 100)
            score = 0
            
            # 趋势权重 40%
            if trend == 'strong_up':
                score += 40
            elif trend == 'up':
                score += 20
            elif trend == 'down':
                score -= 20
            elif trend == 'strong_down':
                score -= 40
            
            # MACD权重 15%
            if macd_signal == 'buy':
                score += 15
            elif macd_signal == 'sell':
                score -= 15
            
            # KDJ权重 15%
            if kdj_signal == 'buy':
                score += 15
            elif kdj_signal == 'sell':
                score -= 15
            
            # 布林带权重 15%
            if boll_signal == 'buy':
                score += 15
            elif boll_signal == 'sell':
                score -= 15
            
            # RSI权重 15%
            if rsi_signal == 'buy':
                score += 15
            elif rsi_signal == 'sell':
                score -= 15
            
            signals['tech_score'] = score
            
            logger.info(f"技术分析完成: {ts_code}, 评分: {score}")
            return pd.DataFrame([signals])
            
        except Exception as e:
            logger.error(f"技术分析失败: {ts_code}, 错误: {str(e)}")
            return pd.DataFrame()
    
    def _analyze_trend(self, data):
        """分析价格趋势"""
        try:
            # 确认数据非空且包含必要列
            if data.empty or not all(col in data.columns for col in ['close', 'ma5', 'ma20', 'ma60']):
                return 'neutral'
            
            # 获取最新价格和均线数据
            close = data['close'].iloc[0]
            ma5 = data['ma5'].iloc[0]
            ma20 = data['ma20'].iloc[0]
            ma60 = data['ma60'].iloc[0]
            
            # 判断趋势
            if pd.notna(ma5) and pd.notna(ma20) and pd.notna(ma60):
                if close > ma5 > ma20 > ma60:
                    return 'strong_up'  # 强势上涨
                elif close > ma20 and ma5 > ma20:
                    return 'up'  # 上涨
                elif close < ma5 < ma20 < ma60:
                    return 'strong_down'  # 强势下跌
                elif close < ma20 and ma5 < ma20:
                    return 'down'  # 下跌
            
            return 'neutral'  # 中性
            
        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return 'neutral'
    
    def _analyze_macd(self, data):
        """分析MACD信号"""
        try:
            # 确认数据非空且包含必要列
            if data.empty or not all(col in data.columns for col in ['macd', 'macd_dif', 'macd_dea']):
                return 'neutral'
            
            # 获取MACD数据
            if len(data) < 2:
                return 'neutral'
                
            macd_current = data['macd'].iloc[0]
            macd_prev = data['macd'].iloc[1]
            dif_current = data['macd_dif'].iloc[0]
            dea_current = data['macd_dea'].iloc[0]
            
            # 判断MACD信号
            if pd.notna(macd_current) and pd.notna(macd_prev):
                # 金叉：DIF从下向上穿越DEA
                if macd_current > 0 and macd_prev <= 0:
                    return 'buy'
                # 死叉：DIF从上向下穿越DEA
                elif macd_current < 0 and macd_prev >= 0:
                    return 'sell'
                # DIF > DEA，多头趋势
                elif dif_current > dea_current:
                    return 'hold_long'
                # DIF < DEA，空头趋势
                elif dif_current < dea_current:
                    return 'hold_short'
            
            return 'neutral'
            
        except Exception as e:
            logger.error(f"MACD分析失败: {str(e)}")
            return 'neutral'
    
    def _analyze_kdj(self, data):
        """分析KDJ信号"""
        try:
            # 确认数据非空且包含必要列
            if data.empty or not all(col in data.columns for col in ['kdj_k', 'kdj_d', 'kdj_j']):
                return 'neutral'
            
            # 获取KDJ数据
            if len(data) < 2:
                return 'neutral'
                
            k_current = data['kdj_k'].iloc[0]
            k_prev = data['kdj_k'].iloc[1]
            d_current = data['kdj_d'].iloc[0]
            d_prev = data['kdj_d'].iloc[1]
            
            # 判断KDJ信号
            if pd.notna(k_current) and pd.notna(d_current) and pd.notna(k_prev) and pd.notna(d_prev):
                # 金叉：K线从下向上穿越D线
                if k_current > d_current and k_prev <= d_prev:
                    return 'buy'
                # 死叉：K线从上向下穿越D线
                elif k_current < d_current and k_prev >= d_prev:
                    return 'sell'
                # K > D，多头趋势
                elif k_current > d_current:
                    return 'hold_long'
                # K < D，空头趋势
                elif k_current < d_current:
                    return 'hold_short'
                
                # 超买超卖判断
                if k_current > 80 and d_current > 80:
                    return 'overbought'
                elif k_current < 20 and d_current < 20:
                    return 'oversold'
            
            return 'neutral'
            
        except Exception as e:
            logger.error(f"KDJ分析失败: {str(e)}")
            return 'neutral'
    
    def _analyze_boll(self, data):
        """分析布林带信号"""
        try:
            # 确认数据非空且包含必要列
            if data.empty or not all(col in data.columns for col in ['close', 'boll_upper', 'boll_mid', 'boll_lower']):
                return 'neutral'
            
            # 获取布林带数据
            close = data['close'].iloc[0]
            upper = data['boll_upper'].iloc[0]
            mid = data['boll_mid'].iloc[0]
            lower = data['boll_lower'].iloc[0]
            
            # 判断布林带信号
            if pd.notna(close) and pd.notna(upper) and pd.notna(mid) and pd.notna(lower):
                # 价格接近下轨，可能买入
                if close <= lower * 1.02:
                    return 'buy'
                # 价格接近上轨，可能卖出
                elif close >= upper * 0.98:
                    return 'sell'
                # 价格高于中轨，偏多头
                elif close > mid:
                    return 'hold_long'
                # 价格低于中轨，偏空头
                elif close < mid:
                    return 'hold_short'
            
            return 'neutral'
            
        except Exception as e:
            logger.error(f"布林带分析失败: {str(e)}")
            return 'neutral'
    
    def _analyze_rsi(self, data):
        """分析RSI信号"""
        try:
            # 确认数据非空且包含必要列
            if data.empty or not all(col in data.columns for col in ['rsi_6', 'rsi_12', 'rsi_24']):
                return 'neutral'
            
            # 获取RSI数据
            rsi6 = data['rsi_6'].iloc[0]
            rsi12 = data['rsi_12'].iloc[0]
            
            # 判断RSI信号
            if pd.notna(rsi6) and pd.notna(rsi12):
                # 超卖区域
                if rsi6 < 20:
                    return 'buy'
                # 超买区域
                elif rsi6 > 80:
                    return 'sell'
                # RSI6上穿RSI12，买入信号
                elif len(data) > 1 and pd.notna(data['rsi_6'].iloc[1]) and pd.notna(data['rsi_12'].iloc[1]):
                    if rsi6 > rsi12 and data['rsi_6'].iloc[1] <= data['rsi_12'].iloc[1]:
                        return 'buy'
                    # RSI6下穿RSI12，卖出信号
                    elif rsi6 < rsi12 and data['rsi_6'].iloc[1] >= data['rsi_12'].iloc[1]:
                        return 'sell'
                # RSI6 > RSI12，多头趋势
                elif rsi6 > rsi12:
                    return 'hold_long'
                # RSI6 < RSI12，空头趋势
                elif rsi6 < rsi12:
                    return 'hold_short'
            
            return 'neutral'
            
        except Exception as e:
            logger.error(f"RSI分析失败: {str(e)}")
            return 'neutral'
    
    # ===================== 综合分析 =====================
    
    def analyze_stock(self, ts_code):
        """综合分析股票"""
        try:
            # 获取公司基本信息
            company_info = self.data_service.get_company_info(ts_code)
            if company_info.empty:
                logger.warning(f"无法获取公司信息: {ts_code}")
                return None
            
            # 基本面分析
            quality_score = self.calculate_quality_score(ts_code)
            
            # 技术分析
            tech_analysis = self.analyze_technical_indicators(ts_code)
            tech_score = tech_analysis['tech_score'].iloc[0] if not tech_analysis.empty else 0
            
            # 计算综合评分 (0-100)
            # 基本面权重60%，技术面权重40%
            # 技术面评分从-100~100转换到0~100
            tech_score_normalized = (tech_score + 100) / 2
            composite_score = quality_score * 0.6 + tech_score_normalized * 0.4
            
            # 生成投资建议
            if composite_score >= 80:
                advice = "强烈推荐"
                reason = "公司基本面优秀，技术形态强势"
            elif composite_score >= 70:
                advice = "建议买入"
                reason = "综合表现良好，具有投资价值"
            elif composite_score >= 60:
                advice = "谨慎买入"
                reason = "有一定投资价值，但存在部分风险"
            elif composite_score >= 40:
                advice = "持有观望"
                reason = "暂无明确方向，需进一步观察"
            elif composite_score >= 30:
                advice = "减持"
                reason = "整体表现不佳，投资风险较大"
            else:
                advice = "建议规避"
                reason = "基本面和技术面均较差，不推荐投资"
            
            # 汇总分析结果
            result = {
                'ts_code': ts_code,
                'name': company_info['name'].iloc[0] if 'name' in company_info.columns else "",
                'industry': company_info['industry'].iloc[0] if 'industry' in company_info.columns else "",
                'quality_score': quality_score,
                'tech_score': tech_score,
                'composite_score': composite_score,
                'advice': advice,
                'reason': reason,
                'analysis_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            logger.info(f"综合分析完成: {ts_code}, 评分: {composite_score:.2f}, 建议: {advice}")
            return result
            
        except Exception as e:
            logger.error(f"综合分析失败: {ts_code}, 错误: {str(e)}")
            return None
    
    def analyze_batch(self, ts_codes, top_n=10):
        """批量分析多只股票并返回评分最高的N只"""
        results = []
        
        for ts_code in ts_codes:
            try:
                result = self.analyze_stock(ts_code)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"分析失败: {ts_code}, 错误: {str(e)}")
        
        # 按综合评分排序
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # 返回评分最高的N只
        return results[:top_n]


# 使用示例
if __name__ == "__main__":
    # 初始化分析引擎
    engine = StockAnalysisEngine()
    
    # 选择一只股票进行分析
    ts_code = '000001.SZ'
    
    # 综合分析
    result = engine.analyze_stock(ts_code)
    if result:
        print(f"分析结果 - {result['name']}({result['ts_code']}):")
        print(f"行业: {result['industry']}")
        print(f"基本面评分: {result['quality_score']:.2f}/100")
        print(f"技术面评分: {result['tech_score']:.2f}/100")
        print(f"综合评分: {result['composite_score']:.2f}/100")
        print(f"投资建议: {result['advice']} - {result['reason']}")
        print(f"分析日期: {result['analysis_date']}") 