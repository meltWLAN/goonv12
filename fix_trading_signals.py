#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析交易信号修复工具
解决交易信号缺失问题
"""

import os
import sys
import logging
import inspect
import traceback
import json
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_signals_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradingSignalsFix")

class TradingSignalsFixer:
    """交易信号修复工具"""
    
    def __init__(self):
        """初始化修复工具"""
        # 尝试导入增强版行业分析器
        try:
            from enhance_sector_analyzer import EnhancedSectorAnalyzer
            self.enhanced_analyzer_cls = EnhancedSectorAnalyzer
            logger.info("成功导入增强版行业分析器")
        except ImportError as e:
            logger.error(f"导入增强版行业分析器失败: {str(e)}")
            sys.exit(1)

    def fix_trading_signals(self):
        """修复交易信号方法"""
        logger.info("修复交易信号方法")
        
        try:
            # 获取增强版分析器代码
            source = inspect.getsource(self.enhanced_analyzer_cls)
            
            # 检查是否有交易信号相关方法
            has_calculate_signals = '_calculate_trading_signals' in source
            
            if not has_calculate_signals:
                logger.error("增强版行业分析器中缺少交易信号计算方法")
                return False
            
            # 判断是否需要修复
            source_analyze = inspect.getsource(self.enhanced_analyzer_cls.analyze_enhanced_hot_sectors)
            signals_added = "trading_signals" in source_analyze and "enhanced_analysis['trading_signals']" in source_analyze
            
            if signals_added:
                logger.info("交易信号已经正确添加到分析结果中")
                return True
            
            # 修复analyze_enhanced_hot_sectors方法
            original_analyze_method = self.enhanced_analyzer_cls.analyze_enhanced_hot_sectors
            
            def patched_analyze_hot_sectors(self):
                """修复版热门行业分析方法"""
                # 调用原始方法获取结果
                result = original_analyze_method(self)
                
                if result['status'] != 'success':
                    return result
                
                # 确保每个行业都有交易信号
                for i, sector in enumerate(result['data']['hot_sectors']):
                    if 'trading_signals' not in sector or not sector['trading_signals']:
                        # 获取行业历史数据
                        sector_name = sector['name']
                        sector_data = self.integrator._get_sector_history(sector_name)
                        
                        if sector_data is not None and not sector_data.empty:
                            # 计算指标
                            sector_data_with_indicators = self._calculate_momentum_indicators(sector_data)
                            # 计算交易信号
                            trading_signals = self._calculate_trading_signals(sector_data_with_indicators)
                            
                            # 添加交易信号
                            result['data']['hot_sectors'][i]['trading_signals'] = trading_signals
                            
                            # 添加入场/出场区间
                            entry_zones, exit_zones = self._calculate_entry_exit_zones(
                                sector_data_with_indicators, 
                                sector['trend_stability_score']
                            )
                            
                            # 添加到交易信号中
                            result['data']['hot_sectors'][i]['trading_signals']['entry_zones'] = entry_zones
                            result['data']['hot_sectors'][i]['trading_signals']['exit_zones'] = exit_zones
                            
                            # 添加风险评估
                            risk_level, position_advice = self._calculate_risk_position(
                                sector_data_with_indicators,
                                sector['trend_stability_score'],
                                sector['relative_strength_score']
                            )
                            
                            # 添加到交易信号中
                            result['data']['hot_sectors'][i]['trading_signals']['risk_level'] = risk_level
                            result['data']['hot_sectors'][i]['trading_signals']['position_advice'] = position_advice
                            
                            # 更新分析理由
                            signal_desc = ""
                            if trading_signals['buy_signals']:
                                signal_desc += f"买入信号: {trading_signals['buy_signals'][0]}; "
                            if trading_signals['sell_signals']:
                                signal_desc += f"卖出信号: {trading_signals['sell_signals'][0]}; "
                            
                            result['data']['hot_sectors'][i]['analysis_reason'] += f" {signal_desc}风险级别: {risk_level}."
                
                return result
            
            # 添加入场/出场区间计算方法
            def calculate_entry_exit_zones(self, data, trend_score):
                """计算入场和出场区间"""
                entry_zones = []
                exit_zones = []
                
                # 获取最近的价格
                last_price = data['收盘'].iloc[-1]
                max_price = data['最高'].iloc[-20:].max()
                min_price = data['最低'].iloc[-20:].min()
                
                # 计算支撑位和阻力位
                support_level = min_price * 0.99
                resistance_level = max_price * 1.01
                
                # 计算移动平均线
                ma20 = data['收盘'].rolling(window=20).mean().iloc[-1]
                ma50 = data['收盘'].rolling(window=50).mean().iloc[-1]
                
                # 判断趋势
                is_uptrend = trend_score > 60
                is_downtrend = trend_score < 40
                
                # 确定入场区间
                if is_uptrend:
                    # 上升趋势，在回调到支撑位附近入场
                    entry_price = max(support_level, ma20 * 0.97)
                    entry_zones.append({
                        'price': round(entry_price, 2),
                        'desc': '支撑位回调入场'
                    })
                    
                    # 突破阻力位入场
                    entry_zones.append({
                        'price': round(resistance_level * 1.02, 2),
                        'desc': '突破阻力位入场'
                    })
                    
                elif is_downtrend:
                    # 下降趋势，在反弹确认后入场
                    entry_price = min_price * 1.05
                    entry_zones.append({
                        'price': round(entry_price, 2),
                        'desc': '反弹确认入场'
                    })
                else:
                    # 震荡行情，在支撑位附近入场
                    entry_price = support_level * 1.01
                    entry_zones.append({
                        'price': round(entry_price, 2),
                        'desc': '支撑位附近入场'
                    })
                
                # 确定出场区间
                if is_uptrend:
                    # 上升趋势，目标价位出场
                    exit_price = last_price * 1.10
                    exit_zones.append({
                        'price': round(exit_price, 2),
                        'desc': '目标价位出场'
                    })
                    
                    # 止损位
                    exit_zones.append({
                        'price': round(support_level * 0.95, 2),
                        'desc': '止损出场'
                    })
                    
                elif is_downtrend:
                    # 下降趋势，反弹高点出场
                    exit_price = max(last_price * 1.05, ma20)
                    exit_zones.append({
                        'price': round(exit_price, 2),
                        'desc': '反弹高点出场'
                    })
                else:
                    # 震荡行情，阻力位附近出场
                    exit_price = resistance_level * 0.99
                    exit_zones.append({
                        'price': round(exit_price, 2),
                        'desc': '阻力位附近出场'
                    })
                
                return entry_zones, exit_zones
            
            # 添加风险和仓位建议计算方法
            def calculate_risk_position(self, data, trend_score, relative_strength):
                """计算风险等级和仓位建议"""
                # 分析近期波动率
                returns = data['收盘'].pct_change().iloc[-20:]
                volatility = returns.std() * 100
                
                # 判断趋势强度
                is_strong_trend = trend_score > 80
                is_weak_trend = trend_score < 40
                
                # 判断相对强度
                is_strong_relative = relative_strength > 60
                is_weak_relative = relative_strength < 40
                
                # 计算风险等级
                risk_level = "中等"
                
                if volatility > 2.5:
                    risk_level = "高"
                elif volatility < 1.0:
                    risk_level = "低"
                
                # 如果趋势很弱，提高风险等级
                if is_weak_trend and risk_level != "高":
                    risk_level = "中高"
                
                # 如果相对强度弱，提高风险等级
                if is_weak_relative and risk_level != "高":
                    risk_level = "中高"
                
                # 计算建议仓位
                position_advice = 0.5  # 默认中等仓位
                
                if risk_level == "低":
                    position_advice = 0.7
                elif risk_level == "中等":
                    position_advice = 0.5
                elif risk_level == "中高":
                    position_advice = 0.3
                elif risk_level == "高":
                    position_advice = 0.2
                
                # 如果趋势强且相对强度强，增加仓位
                if is_strong_trend and is_strong_relative:
                    position_advice = min(0.8, position_advice + 0.1)
                
                # 如果趋势弱且相对强度弱，减少仓位
                if is_weak_trend and is_weak_relative:
                    position_advice = max(0.1, position_advice - 0.1)
                
                return risk_level, position_advice
            
            # 替换和添加方法
            self.enhanced_analyzer_cls.analyze_enhanced_hot_sectors = patched_analyze_hot_sectors
            self.enhanced_analyzer_cls._calculate_entry_exit_zones = calculate_entry_exit_zones
            self.enhanced_analyzer_cls._calculate_risk_position = calculate_risk_position
            
            logger.info("成功修复交易信号方法")
            
            # 验证预测方法是否需要修复
            source_predict = inspect.getsource(self.enhanced_analyzer_cls.predict_hot_sectors_enhanced)
            signals_in_predict = "trading_signals" in source_predict
            
            if not signals_in_predict:
                logger.info("修复预测方法的交易信号集成")
                
                # 获取原始预测方法
                original_predict_method = self.enhanced_analyzer_cls.predict_hot_sectors_enhanced
                
                def patched_predict_method(self):
                    """修复版预测方法"""
                    # 调用原始方法
                    result = original_predict_method(self)
                    
                    if result['status'] != 'success':
                        return result
                    
                    # 确保每个预测行业都有交易信号
                    for i, sector in enumerate(result['data']['predicted_sectors']):
                        sector_name = sector['name']
                        
                        # 获取行业历史数据
                        sector_data = self.integrator._get_sector_history(sector_name)
                        
                        if sector_data is not None and not sector_data.empty:
                            # 计算指标
                            sector_data_with_indicators = self._calculate_momentum_indicators(sector_data)
                            
                            # 计算交易信号
                            trading_signals = self._calculate_trading_signals(sector_data_with_indicators)
                            
                            # 添加交易信号
                            result['data']['predicted_sectors'][i]['trading_signals'] = trading_signals
                            
                            # 获取或计算趋势稳定性得分
                            trend_score = sector.get('trend_stability', 50)
                            if isinstance(trend_score, str):
                                try:
                                    trend_score = float(trend_score.split()[0])
                                except:
                                    trend_score = 50
                            
                            # 获取或设置相对强度得分
                            rel_strength = sector.get('relative_strength', 50)
                            if isinstance(rel_strength, str):
                                try:
                                    rel_strength = float(rel_strength.split()[0])
                                except:
                                    rel_strength = 50
                            
                            # 添加入场/出场区间
                            entry_zones, exit_zones = self._calculate_entry_exit_zones(
                                sector_data_with_indicators, 
                                trend_score
                            )
                            
                            # 添加到交易信号中
                            result['data']['predicted_sectors'][i]['trading_signals']['entry_zones'] = entry_zones
                            result['data']['predicted_sectors'][i]['trading_signals']['exit_zones'] = exit_zones
                            
                            # 添加风险评估
                            risk_level, position_advice = self._calculate_risk_position(
                                sector_data_with_indicators,
                                trend_score,
                                rel_strength
                            )
                            
                            # 添加到交易信号中
                            result['data']['predicted_sectors'][i]['trading_signals']['risk_level'] = risk_level
                            result['data']['predicted_sectors'][i]['trading_signals']['position_advice'] = position_advice
                    
                    return result
                
                # 替换预测方法
                self.enhanced_analyzer_cls.predict_hot_sectors_enhanced = patched_predict_method
                logger.info("成功修复预测方法")
            
            return True
            
        except Exception as e:
            logger.error(f"修复交易信号方法失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def verify_fix(self):
        """验证修复效果"""
        logger.info("验证修复效果")
        
        try:
            # 创建测试实例
            test_analyzer = self.enhanced_analyzer_cls(top_n=3)
            
            # 测试热门行业分析
            result = test_analyzer.analyze_enhanced_hot_sectors()
            
            if result['status'] != 'success':
                logger.error(f"获取热门行业失败: {result.get('message', '未知错误')}")
                return False
            
            # 检查是否有交易信号
            has_signals = all('trading_signals' in sector for sector in result['data']['hot_sectors'])
            
            if not has_signals:
                logger.error("热门行业分析中缺少交易信号")
                return False
            
            # 检查入场/出场区间
            first_sector = result['data']['hot_sectors'][0]
            has_entry_exit = ('entry_zones' in first_sector['trading_signals'] and 
                             'exit_zones' in first_sector['trading_signals'])
            
            if not has_entry_exit:
                logger.error("缺少入场/出场区间")
                return False
            
            # 检查风险评估
            has_risk = ('risk_level' in first_sector['trading_signals'] and 
                       'position_advice' in first_sector['trading_signals'])
            
            if not has_risk:
                logger.error("缺少风险评估")
                return False
            
            logger.info("热门行业分析交易信号验证通过")
            
            # 测试行业预测
            predict_result = test_analyzer.predict_hot_sectors_enhanced()
            
            if predict_result['status'] != 'success':
                logger.error(f"获取行业预测失败: {predict_result.get('message', '未知错误')}")
                return False
            
            # 检查预测中是否有交易信号
            predict_has_signals = all('trading_signals' in sector for sector in predict_result['data']['predicted_sectors'])
            
            if not predict_has_signals:
                logger.error("行业预测中缺少交易信号")
                return False
            
            logger.info("行业预测交易信号验证通过")
            
            # 打印示例结果
            logger.info("\n*** 示例交易信号 ***")
            signals = first_sector['trading_signals']
            logger.info(f"行业: {first_sector['name']}")
            logger.info(f"买入信号: {signals.get('buy_signals', [])}")
            logger.info(f"卖出信号: {signals.get('sell_signals', [])}")
            logger.info(f"入场区间: {signals.get('entry_zones', [])}")
            logger.info(f"出场区间: {signals.get('exit_zones', [])}")
            logger.info(f"风险级别: {signals.get('risk_level', 'N/A')}")
            logger.info(f"仓位建议: {int(signals.get('position_advice', 0) * 100)}%")
            
            return True
            
        except Exception as e:
            logger.error(f"验证修复效果失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

def main():
    """主函数"""
    print("\n===== 行业分析交易信号修复工具 =====\n")
    
    # 初始化修复工具
    fixer = TradingSignalsFixer()
    
    # 修复交易信号
    print("1. 修复交易信号功能...")
    if fixer.fix_trading_signals():
        print("✅ 成功修复交易信号功能")
    else:
        print("❌ 修复交易信号功能失败")
    
    # 验证修复效果
    print("\n2. 验证修复效果...")
    if fixer.verify_fix():
        print("✅ 验证通过，交易信号功能正常工作")
        
        print("\n🎉 修复完成！行业分析模块现在具备完整的交易信号功能")
        print("建议运行以下命令进行全面验证:")
        print("python verify_enhanced_sectors.py")
    else:
        print("❌ 验证失败")
        print("\n请查看日志文件了解详情，并手动修复问题")

if __name__ == "__main__":
    main() 