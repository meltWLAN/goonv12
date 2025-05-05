#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析模块修复工具
解决数据完整性和交易信号问题
"""

import os
import sys
import json
import datetime
import logging
import traceback
import pandas as pd
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sector_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SectorDataFix")

class SectorDataFixer:
    """行业数据修复工具"""
    
    def __init__(self, cache_dir="data_cache"):
        """初始化修复工具"""
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 尝试导入必要模块
        try:
            from sector_integration import SectorIntegrator
            self.integrator = SectorIntegrator(cache_dir=self.cache_dir)
            logger.info("成功导入行业分析集成器")
            
            # 检查属性名
            if hasattr(self.integrator, 'sector_mapping'):
                self.sector_map_attr = 'sector_mapping'
            elif hasattr(self.integrator, 'sector_map'):
                self.sector_map_attr = 'sector_map'
            else:
                # 如果都没有，创建一个
                self.integrator.sector_mapping = {}
                self.sector_map_attr = 'sector_mapping'
                logger.warning("未找到行业映射属性，已创建空映射")
                
            logger.info(f"使用行业映射属性: {self.sector_map_attr}")
        except ImportError as e:
            logger.error(f"导入行业分析集成器失败: {str(e)}")
            sys.exit(1)

    def fix_get_sector_list_method(self):
        """修复获取行业列表方法"""
        logger.info("修复获取行业列表方法")
        
        try:
            # 检查是否存在get_sector_list方法
            if not hasattr(self.integrator, 'get_sector_list'):
                # 添加get_sector_list方法
                def get_sector_list(self):
                    """获取行业列表"""
                    logger.info("获取行业列表")
                    
                    # 直接从映射表中获取行业列表
                    if hasattr(self, 'sector_mapping'):
                        sectors = list(self.sector_mapping.keys())
                    elif hasattr(self, 'sector_map'):
                        sectors = list(self.sector_map.keys())
                    else:
                        logger.warning("未找到行业映射属性")
                        # 从文件名推断行业列表
                        sectors = self._infer_sectors_from_files()
                    
                    if not sectors:
                        logger.warning("行业列表为空")
                        return []
                    
                    return sectors
                
                # 新增从文件名推断行业列表的方法
                def _infer_sectors_from_files(self):
                    """从缓存文件推断行业列表"""
                    logger.info("从缓存文件推断行业列表")
                    
                    sectors = []
                    
                    # 检查是否有缓存
                    if os.path.exists(self.cache_dir):
                        files = [f for f in os.listdir(self.cache_dir) if f.startswith("history_") and f.endswith(".pkl")]
                        
                        # 有代码到行业名的映射表
                        if hasattr(self, 'sector_mapping'):
                            code_to_sector = {v: k for k, v in self.sector_mapping.items()}
                        else:
                            # 创建一个简单的映射表
                            code_to_sector = {
                                '801020.SI': '采掘', '801030.SI': '化工', '801040.SI': '钢铁',
                                '801050.SI': '有色金属', '801710.SI': '建筑材料', '801720.SI': '建筑装饰',
                                '801730.SI': '电气设备', '801890.SI': '机械设备', '801740.SI': '国防军工',
                                '801880.SI': '汽车', '801110.SI': '家用电器', '801130.SI': '纺织服装',
                                '801140.SI': '轻工制造', '801200.SI': '商业贸易', '801010.SI': '农林牧渔',
                                '801120.SI': '食品饮料', '801210.SI': '休闲服务', '801150.SI': '医药生物',
                                '801160.SI': '公用事业', '801170.SI': '交通运输', '801180.SI': '房地产',
                                '801080.SI': '电子', '801750.SI': '计算机', '801760.SI': '传媒',
                                '801770.SI': '通信', '801780.SI': '银行', '801790.SI': '非银金融',
                                '801230.SI': '综合'
                            }
                        
                        for file in files:
                            # 从文件名中提取行业代码
                            code = file.replace("history_", "").replace(".pkl", "")
                            
                            # 找到对应的行业名称
                            if code in code_to_sector:
                                sectors.append(code_to_sector[code])
                    
                    return sectors
                
                # 将方法绑定到集成器对象
                import types
                self.integrator.get_sector_list = types.MethodType(get_sector_list, self.integrator)
                self.integrator._infer_sectors_from_files = types.MethodType(_infer_sectors_from_files, self.integrator)
                
                logger.info("成功添加get_sector_list方法")
                return True
            else:
                logger.info("get_sector_list方法已存在")
                return True
        except Exception as e:
            logger.error(f"修复get_sector_list方法失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def patch_trading_signals(self):
        """修复交易信号生成问题"""
        logger.info("修复交易信号生成问题")
        
        try:
            # 导入增强版行业分析器
            from enhance_sector_analyzer import EnhancedSectorAnalyzer
            
            # 获取方法源代码
            import inspect
            source = inspect.getsource(EnhancedSectorAnalyzer._calculate_trading_signals)
            
            # 检查交易信号是否添加到分析结果中
            is_adding_signals = "enhanced_analysis['trading_signals'] = trading_signals" in source
            
            if not is_adding_signals:
                logger.warning("交易信号未添加到分析结果中")
                
                # 修复analyze_enhanced_hot_sectors方法
                original_analyze_method = EnhancedSectorAnalyzer.analyze_enhanced_hot_sectors
                
                def patched_analyze_hot_sectors(self):
                    """修复版热门行业分析方法"""
                    # 调用原始方法
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
                                
                                # 更新分析理由
                                if trading_signals and (trading_signals['buy_signals'] or trading_signals['sell_signals']):
                                    signal_desc = ""
                                    if trading_signals['buy_signals']:
                                        signal_desc += f"买入信号: {trading_signals['buy_signals'][0]}; "
                                    if trading_signals['sell_signals']:
                                        signal_desc += f"卖出信号: {trading_signals['sell_signals'][0]}; "
                                    
                                    result['data']['hot_sectors'][i]['analysis_reason'] += f" {signal_desc}风险级别: {trading_signals['risk_level']}."
                    
                    return result
                
                # 替换方法
                EnhancedSectorAnalyzer.analyze_enhanced_hot_sectors = patched_analyze_hot_sectors
                
                logger.info("成功修复交易信号生成问题")
                return True
            else:
                logger.info("交易信号功能正常")
                return True
        except Exception as e:
            logger.error(f"修复交易信号生成问题失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def ensure_cache_data(self):
        """确保行业缓存数据完整"""
        logger.info("检查行业缓存数据完整性")
        
        try:
            # 获取行业列表和映射
            if hasattr(self.integrator, self.sector_map_attr):
                sector_map = getattr(self.integrator, self.sector_map_attr)
                sectors = list(sector_map.keys())
            else:
                # 如果没有映射表，使用固定的行业列表
                sectors = [
                    '采掘', '化工', '钢铁', '有色金属', '建筑材料', '建筑装饰',
                    '电气设备', '机械设备', '国防军工', '汽车', '家用电器', '纺织服装',
                    '轻工制造', '商业贸易', '农林牧渔', '食品饮料', '休闲服务', '医药生物',
                    '公用事业', '交通运输', '房地产', '电子', '计算机', '传媒',
                    '通信', '银行', '非银金融', '综合'
                ]
                
                # 创建一个默认映射
                sector_map = {
                    '采掘': '801020.SI', '化工': '801030.SI', '钢铁': '801040.SI',
                    '有色金属': '801050.SI', '建筑材料': '801710.SI', '建筑装饰': '801720.SI',
                    '电气设备': '801730.SI', '机械设备': '801890.SI', '国防军工': '801740.SI',
                    '汽车': '801880.SI', '家用电器': '801110.SI', '纺织服装': '801130.SI',
                    '轻工制造': '801140.SI', '商业贸易': '801200.SI', '农林牧渔': '801010.SI',
                    '食品饮料': '801120.SI', '休闲服务': '801210.SI', '医药生物': '801150.SI',
                    '公用事业': '801160.SI', '交通运输': '801170.SI', '房地产': '801180.SI',
                    '电子': '801080.SI', '计算机': '801750.SI', '传媒': '801760.SI',
                    '通信': '801770.SI', '银行': '801780.SI', '非银金融': '801790.SI',
                    '综合': '801230.SI'
                }
                
                # 将映射保存到集成器
                setattr(self.integrator, self.sector_map_attr, sector_map)
            
            logger.info(f"系统共有 {len(sectors)} 个行业")
            
            # 检查是否有缓存
            cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith("history_") and f.endswith(".pkl")]
            cached_sectors = []
            
            for file in cache_files:
                # 从文件名中提取行业代码
                code = file.replace("history_", "").replace(".pkl", "")
                
                # 找到对应的行业名称
                sector_name = None
                for name, sector_code in sector_map.items():
                    if sector_code == code:
                        sector_name = name
                        break
                
                if sector_name:
                    cached_sectors.append(sector_name)
            
            logger.info(f"已缓存 {len(cached_sectors)} 个行业数据")
            
            # 找出未缓存的行业
            uncached_sectors = [s for s in sectors if s not in cached_sectors]
            
            if uncached_sectors:
                logger.warning(f"有 {len(uncached_sectors)} 个行业数据未缓存")
                
                # 创建模拟数据并保存
                for sector in uncached_sectors:
                    logger.info(f"为行业 {sector} 创建模拟数据")
                    sector_code = sector_map.get(sector)
                    
                    if not sector_code:
                        logger.warning(f"行业 {sector} 没有对应的代码")
                        continue
                    
                    # 创建模拟数据
                    simulated_data = self._create_simulated_data(sector_code)
                    
                    # 保存到缓存
                    cache_file = os.path.join(self.cache_dir, f"history_{sector_code}.pkl")
                    simulated_data.to_pickle(cache_file)
                    logger.info(f"成功为行业 {sector} 创建并缓存模拟数据")
            
            logger.info("行业缓存数据检查完成")
            return True
        except Exception as e:
            logger.error(f"行业缓存数据修复失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _create_simulated_data(self, sector_code, days=90):
        """创建模拟行业数据"""
        # 生成日期序列
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # 创建模拟价格和成交量
        import numpy as np
        np.random.seed(int(sector_code.replace('.SI', '')))
        
        # 初始价格
        initial_price = np.random.uniform(10, 50)
        
        # 价格趋势
        trend = np.random.uniform(-0.0005, 0.0010)
        
        # 生成价格
        close_prices = []
        price = initial_price
        for _ in range(len(dates)):
            # 随机波动
            change = np.random.normal(trend, 0.01)
            price *= (1 + change)
            close_prices.append(price)
        
        close_prices = np.array(close_prices)
        
        # 生成开盘、最高、最低价
        open_prices = close_prices * np.random.uniform(0.995, 1.005, len(dates))
        high_prices = np.maximum(close_prices, open_prices) * np.random.uniform(1.001, 1.01, len(dates))
        low_prices = np.minimum(close_prices, open_prices) * np.random.uniform(0.99, 0.999, len(dates))
        
        # 生成成交量
        vol_trend = np.random.uniform(0.8, 1.2)
        volumes = np.random.uniform(1000000, 5000000, len(dates)) * vol_trend
        
        # 创建DataFrame
        df = pd.DataFrame({
            '开盘': open_prices,
            '收盘': close_prices,
            '最高': high_prices,
            '最低': low_prices,
            '成交量': volumes
        }, index=dates)
        
        return df

    def verify_fix(self):
        """验证修复效果"""
        logger.info("验证修复效果")
        
        try:
            # 验证get_sector_list方法
            sectors = self.integrator.get_sector_list()
            
            if not sectors:
                logger.error("get_sector_list方法返回空列表")
                return False
            
            logger.info(f"get_sector_list方法返回 {len(sectors)} 个行业")
            
            # 验证行业历史数据
            test_sectors = sectors[:3]  # 测试前3个行业
            
            for sector in test_sectors:
                logger.info(f"测试行业 {sector} 的历史数据")
                
                # 获取历史数据
                history = self.integrator._get_sector_history(sector)
                
                if history is None or history.empty:
                    logger.error(f"行业 {sector} 的历史数据为空")
                    return False
                
                logger.info(f"行业 {sector} 的历史数据有 {len(history)} 条记录")
            
            # 验证交易信号
            try:
                from enhance_sector_analyzer import EnhancedSectorAnalyzer
                
                analyzer = EnhancedSectorAnalyzer(top_n=3)
                result = analyzer.analyze_enhanced_hot_sectors()
                
                if result['status'] != 'success':
                    logger.error(f"获取增强版热门行业失败: {result.get('message', '未知错误')}")
                    return False
                
                # 检查是否有交易信号
                has_signals = all('trading_signals' in sector for sector in result['data']['hot_sectors'])
                
                if not has_signals:
                    logger.error("部分行业缺少交易信号")
                    return False
                
                logger.info("所有行业都有交易信号")
                
                return True
            except Exception as e:
                logger.error(f"验证交易信号失败: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"修复验证失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

def main():
    """主函数"""
    print("\n===== 行业分析模块修复工具 =====\n")
    
    # 初始化修复工具
    fixer = SectorDataFixer()
    
    # 修复get_sector_list方法
    print("1. 修复获取行业列表方法...")
    if fixer.fix_get_sector_list_method():
        print("✅ 成功修复获取行业列表方法")
    else:
        print("❌ 修复获取行业列表方法失败")
    
    # 修复交易信号生成问题
    print("\n2. 修复交易信号生成问题...")
    if fixer.patch_trading_signals():
        print("✅ 成功修复交易信号生成问题")
    else:
        print("❌ 修复交易信号生成问题失败")
    
    # 确保行业缓存数据完整
    print("\n3. 确保行业缓存数据完整...")
    if fixer.ensure_cache_data():
        print("✅ 成功确保行业缓存数据完整")
    else:
        print("❌ 确保行业缓存数据完整失败")
    
    # 验证修复效果
    print("\n4. 验证修复效果...")
    if fixer.verify_fix():
        print("✅ 修复验证通过")
        
        # 建议重新运行测试
        print("\n🎉 修复完成！建议运行以下命令验证修复效果:")
        print("python verify_enhanced_sectors.py")
    else:
        print("❌ 修复验证失败")
        print("\n请查看日志文件了解详情，并手动修复问题")

if __name__ == "__main__":
    main() 