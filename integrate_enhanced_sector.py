#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版行业分析器集成模块
整合增强版行业分析器到系统中
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='enhanced_sector_integration.log',
    filemode='a'
)
logger = logging.getLogger('EnhancedSectorIntegration')

class EnhancedSectorIntegrator:
    """增强版行业分析器集成器"""
    
    def __init__(self, cache_dir: str = './data_cache'):
        """初始化
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加载行业代码映射
        self.sector_code_map = self._load_sector_code_map()
        
        # 检查增强版分析器可用性
        self.use_fixed_version = False
        self.enhanced_available = self._check_enhanced_analyzer()
        
        if self.enhanced_available:
            # 根据检查结果选择正确的分析器
            if self.use_fixed_version:
                from enhanced_sector_analyzer_fixed import EnhancedSectorAnalyzer
            else:
                from enhanced_sector_analyzer import EnhancedSectorAnalyzer
                
            self.analyzer = EnhancedSectorAnalyzer(cache_dir=self.cache_dir)
            
            from sector_technical_analysis import SectorTechnicalAnalyzer
            self.tech_analyzer = SectorTechnicalAnalyzer(cache_dir=self.cache_dir)
            
            logger.info("增强版行业分析器已成功集成")
        else:
            logger.warning("增强版行业分析器不可用，将回退到简化版分析器")
    
    def _load_sector_code_map(self) -> Dict[str, str]:
        """加载行业代码映射"""
        map_file = os.path.join(self.cache_dir, 'sector_code_map.json')
        if os.path.exists(map_file):
            try:
                with open(map_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载行业代码映射失败: {e}")
        return {}
    
    def _check_enhanced_analyzer(self) -> bool:
        """检查增强版分析器是否可用"""
        try:
            # 首先尝试导入修复版分析器
            try:
                from enhanced_sector_analyzer_fixed import EnhancedSectorAnalyzer
                self.use_fixed_version = True
                logger.info("使用修复版增强型行业分析器")
                return True
            except ImportError:
                self.use_fixed_version = False
                logger.info("未找到修复版增强型行业分析器，尝试使用原始版本")
            
            # 尝试导入原始版分析器
            from enhanced_sector_analyzer import EnhancedSectorAnalyzer
            # 尝试导入行业技术分析模块
            from sector_technical_analysis import SectorTechnicalAnalyzer
            
            logger.info("使用原始版增强型行业分析器")
            return True
        except ImportError as e:
            logger.error(f"增强版行业分析器导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"增强版行业分析器检查失败: {e}")
            return False
    
    def get_hot_sectors(self, top_n: int = 10) -> Dict:
        """获取热门行业
        
        Args:
            top_n: 返回的热门行业数量
            
        Returns:
            热门行业分析结果
        """
        if not self.enhanced_available:
            return self._fallback_to_simple('hot_sectors')
        
        try:
            # 使用增强版分析器获取热门行业
            result = self.analyzer.get_hot_sectors(top_n=top_n)
            
            # 添加增强版标记
            if result['status'] == 'success':
                result['data']['source'] = 'enhanced'
                
                # 确保存在market_trend字段
                if 'market_trend' not in result['data']:
                    # 默认添加一个中性的趋势
                    result['data']['market_trend'] = 'neutral'
                    result['data']['market_chg_pct'] = 0.0
            
            return result
        except Exception as e:
            logger.error(f"增强版获取热门行业失败: {e}")
            return self._fallback_to_simple('hot_sectors')
    
    def get_sector_code(self, sector_name: str) -> str:
        """获取行业代码
        
        Args:
            sector_name: 行业名称
            
        Returns:
            行业代码
        """
        # 从映射中获取
        if sector_name in self.sector_code_map:
            return self.sector_code_map[sector_name]
        
        # 如果没有映射，尝试从行业列表中获取
        try:
            sector_list = self.analyzer.get_sector_list()
            if sector_list['status'] == 'success':
                for sector in sector_list['data']['sectors']:
                    if sector['name'] == sector_name:
                        return sector['index_code']
        except Exception:
            pass
        
        # 返回默认代码
        return f"DEFAULT_{hash(sector_name) % 1000:03d}"
    
    def get_sector_technical(self, sector_name: str, sector_code: str = '') -> Dict:
        """获取行业技术分析
        
        Args:
            sector_name: 行业名称
            sector_code: 行业指数代码 (可选)
            
        Returns:
            行业技术分析结果
        """
        if not self.enhanced_available:
            return self._fallback_to_simple('technical', sector_name)
        
        try:
            # 如果没有提供行业代码，尝试获取
            if not sector_code:
                sector_code = self.get_sector_code(sector_name)
            
            # 如果还是没有行业代码，返回错误
            if not sector_code:
                logger.error(f"无法获取行业 {sector_name} 的指数代码")
                return {
                    'status': 'error',
                    'message': f"无法获取行业 {sector_name} 的指数代码"
                }
            
            # 检查缓存中是否有技术分析数据
            cache_path = os.path.join(self.cache_dir, f"sector_tech_{sector_code}.json")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        tech_result = json.load(f)
                        if tech_result['status'] == 'success':
                            tech_result['data']['source'] = 'enhanced'
                            return tech_result
                except Exception as e:
                    logger.error(f"读取技术分析缓存失败: {e}")
            
            # 使用技术分析器进行分析
            result = self.tech_analyzer.analyze_sector(sector_code, sector_name)
            
            # 添加增强版标记
            if result['status'] == 'success':
                result['data']['source'] = 'enhanced'
            
            return result
        except Exception as e:
            logger.error(f"增强版行业技术分析失败: {e}")
            return self._fallback_to_simple('technical', sector_name)
    
    def get_sector_stocks(self, sector_name: str) -> Dict:
        """获取行业成分股
        
        Args:
            sector_name: 行业名称
            
        Returns:
            行业成分股列表
        """
        if not self.enhanced_available:
            return self._fallback_to_simple('stocks', sector_name)
        
        try:
            # 使用增强版分析器获取行业成分股
            result = self.analyzer.get_sector_stocks(sector_name)
            
            # 添加增强版标记
            if result['status'] == 'success':
                result['data']['source'] = 'enhanced'
            
            return result
        except Exception as e:
            logger.error(f"增强版获取行业成分股失败: {e}")
            return self._fallback_to_simple('stocks', sector_name)
    
    def _fallback_to_simple(self, request_type: str, sector_name: str = '') -> Dict:
        """回退到简化版分析器
        
        Args:
            request_type: 请求类型 ('hot_sectors', 'technical', 'stocks')
            sector_name: 行业名称 (可选)
            
        Returns:
            简化版分析器的结果
        """
        try:
            # 导入简化版分析器
            from fix_sector_analyzer import SimpleSectorAnalyzer
            simple_analyzer = SimpleSectorAnalyzer()
            
            if request_type == 'hot_sectors':
                return simple_analyzer.get_hot_sectors()
            elif request_type == 'technical' and sector_name:
                return simple_analyzer.get_sector_technical_analysis(sector_name)
            elif request_type == 'stocks' and sector_name:
                # 简化版可能没有这个功能，返回一个基本结果
                return {
                    'status': 'success',
                    'data': {
                        'sector': sector_name,
                        'stocks': [],
                        'total': 0,
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'simple'
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': f"未知的请求类型: {request_type}"
                }
        except Exception as e:
            logger.error(f"回退到简化版分析器失败: {e}")
            return {
                'status': 'error',
                'message': f"无法处理请求: {e}"
            }
    
    def get_unified_analysis(self) -> Dict:
        """获取统一格式的行业分析结果
        
        返回一个标准化格式的行业分析结果，包含热门行业和技术分析
        """
        # 获取热门行业
        hot_sectors_result = self.get_hot_sectors()
        
        if hot_sectors_result['status'] != 'success':
            return hot_sectors_result
        
        hot_sectors = hot_sectors_result['data']['hot_sectors']
        
        # 获取第一个热门行业的技术分析
        if hot_sectors and len(hot_sectors) > 0:
            top_sector = hot_sectors[0]
            sector_code = top_sector.get('code', '')
            tech_result = self.get_sector_technical(top_sector['name'], sector_code)
            
            if tech_result['status'] == 'success':
                hot_sectors_result['data']['technical_analysis'] = tech_result['data']
        
        # 添加数据源标记
        hot_sectors_result['data']['analyzer_version'] = 'enhanced' if self.enhanced_available else 'simple'
        
        return hot_sectors_result
    
    def generate_investment_report(self) -> Dict:
        """生成行业投资报告
        
        返回全面的行业分析和投资建议报告
        """
        if not self.enhanced_available:
            return {
                'status': 'error',
                'message': '增强版行业分析器不可用，无法生成投资报告'
            }
        
        try:
            # 获取热门行业
            hot_sectors_result = self.analyzer.get_hot_sectors(top_n=20)
            
            if hot_sectors_result['status'] != 'success':
                return hot_sectors_result
            
            hot_sectors = hot_sectors_result['data']['hot_sectors']
            
            # 对前5个热门行业进行技术分析
            top_sectors = hot_sectors[:5]
            for sector in top_sectors:
                sector_code = sector.get('code', '') or self.get_sector_code(sector['name'])
                tech_result = self.get_sector_technical(sector['name'], sector_code)
                if tech_result['status'] == 'success':
                    sector['technical'] = tech_result['data']
            
            # 从市场概览中提取市场趋势
            market_trend = hot_sectors_result['data'].get('market_trend', 'neutral')
            market_chg_pct = hot_sectors_result['data'].get('market_chg_pct', 0.0)
            market_status = hot_sectors_result['data'].get('market_status', '正常')
            market_comment = self._get_market_comment(market_trend)
            
            # 生成建议
            recommendations = self._generate_recommendations(top_sectors)
            
            # 提取风险因素
            risk_factors = []
            for rec in recommendations:
                if 'risk_factors' in rec:
                    for risk in rec.get('risk_factors', []):
                        if risk not in risk_factors:
                            risk_factors.append(risk)
            
            # 生成报告
            report = {
                'status': 'success',
                'data': {
                    'title': '行业投资分析报告',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'market_trend': market_trend,
                    'market_chg_pct': market_chg_pct,
                    'market_status': market_status,
                    'market_comment': market_comment,
                    'hot_sectors': top_sectors,
                    'recommendations': recommendations,
                    'risk_factors': risk_factors,
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'enhanced'
                }
            }
            
            return report
        except Exception as e:
            logger.error(f"生成行业投资报告失败: {e}")
            return {
                'status': 'error',
                'message': f"生成行业投资报告失败: {str(e)}"
            }
    
    def _get_market_comment(self, market_trend: str) -> str:
        """获取市场评论"""
        if market_trend == 'strong_bull':
            return '市场呈强烈上涨态势，投资者情绪高涨，可适当提高仓位'
        elif market_trend == 'bull':
            return '市场处于上升趋势，投资热情回升，可积极关注热门行业机会'
        elif market_trend == 'strong_bear':
            return '市场呈明显下跌态势，投资者避险情绪浓厚，建议降低仓位观望'
        elif market_trend == 'bear':
            return '市场处于下行趋势，投资氛围谨慎，建议控制风险'
        else:
            return '市场保持震荡，投资者情绪中性，可选择性布局绩优板块'
    
    def _generate_recommendations(self, top_sectors: List[Dict]) -> List[Dict]:
        """生成投资建议"""
        recommendations = []
        
        for i, sector in enumerate(top_sectors):
            # 只对有技术分析的行业生成建议
            if 'technical' not in sector:
                continue
            
            tech = sector['technical']
            
            # 获取交易信号
            trade_action = tech.get('trade_signal', {}).get('action', '观望')
            trade_strength = tech.get('trade_signal', {}).get('strength', '中等')
            trade_description = tech.get('trade_signal', {}).get('description', '')
            
            # 生成理由文本
            reason = trade_description
            if not reason:
                if 'bullish' in trade_action.lower() or '买入' in trade_action or '看多' in trade_action:
                    reason = f"{sector['name']}行业技术指标走强，热度{sector.get('hot_level', '中等')}，建议关注"
                elif 'bearish' in trade_action.lower() or '卖出' in trade_action or '看空' in trade_action:
                    reason = f"{sector['name']}行业技术指标走弱，可能面临调整，建议谨慎"
                else:
                    reason = f"{sector['name']}行业技术面中性，可持续观察"
            
            recommendation = {
                'sector': sector['name'],
                'rating': '★★★★★' if i == 0 else '★★★★' if i == 1 else '★★★' if i <= 3 else '★★',
                'investment_advice': trade_action,
                'action': trade_action,  # 添加action字段，与analyze_sectors方法兼容
                'reason': reason,  # 添加reason字段，与analyze_sectors方法兼容
                'strength': trade_strength,
                'key_points': [
                    f"行业热度: {sector.get('hot_level', '未知')}",
                    f"技术评分: {tech.get('tech_score', 0)}/100",
                    f"趋势: {tech.get('trend_analysis', {}).get('trend', '未知')}"
                ],
                'risk_factors': self._get_risk_factors(sector, tech)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_risk_factors(self, sector: Dict, tech: Dict) -> List[str]:
        """获取风险因素"""
        risks = []
        
        # 基于技术分析添加风险因素
        if tech.get('indicators', {}).get('rsi', {}).get('signal') in ['严重超买', '超买']:
            risks.append(f"{sector['name']}行业RSI过高，存在超买风险")
        
        if '下降' in tech.get('trend_analysis', {}).get('trend', ''):
            risks.append(f"{sector['name']}行业处于下降趋势，注意调整风险")
        
        # 根据行业状态添加风险
        if sector.get('industry_status') == '快速下跌期':
            risks.append(f"{sector['name']}行业正处于快速下跌阶段，短期风险较大")
        
        # 如果没有找到风险因素，添加一个通用的
        if not risks:
            risks.append(f"市场波动可能影响{sector['name']}行业短期表现")
        
        return risks

# 测试代码
if __name__ == "__main__":
    print("增强版行业分析器集成测试")
    integrator = EnhancedSectorIntegrator()
    
    print(f"增强版分析器可用: {integrator.enhanced_available}")
    
    # 获取热门行业
    print("\n获取热门行业...")
    hot_result = integrator.get_hot_sectors(top_n=5)
    if hot_result['status'] == 'success':
        print(f"数据源: {hot_result['data'].get('source', '未知')}")
        print("\n热门行业:")
        for i, sector in enumerate(hot_result['data']['hot_sectors'], 1):
            print(f"{i}. {sector['name']} - 热度: {sector.get('hot_score', 0)}, 信号: {sector.get('trade_signal', '未知')}")
    
    # 生成投资报告
    if integrator.enhanced_available:
        print("\n生成投资报告...")
        report = integrator.generate_investment_report()
        if report['status'] == 'success':
            print(f"\n{report['data']['title']} ({report['data']['date']})")
            print(f"市场概况: {report['data']['market_comment']}")
            print("\n投资建议:")
            for rec in report['data']['recommendations']:
                print(f"{rec['rating']} {rec['sector']}: {rec['investment_advice']}") 