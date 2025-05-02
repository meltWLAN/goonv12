#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LazyStockAnalyzer全系统整合脚本
将高效分析器整合到所有相关模块中
"""

import os
import sys
import logging
import json
import re
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integration_log.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LazyAnalyzerFullIntegration")

# 模块路径
MODULE_PATHS = {
    'smart_review_core': './smart_review_core.py',
    'strategy_optimization_engine': './strategy_optimization_engine.py', 
    'enhanced_backtesting': './enhanced_backtesting.py',
    'volume_price_strategy': './volume_price_strategy.py',
    'smart_review_main': './smart_review_main.py',
}

def create_backup(file_path):
    """创建文件备份"""
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        logger.info(f"已创建备份: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return None

def integrate_strategy_optimization_engine():
    """整合LazyStockAnalyzer到策略优化引擎"""
    logger.info("开始整合LazyStockAnalyzer到StrategyOptimizationEngine...")
    file_path = MODULE_PATHS['strategy_optimization_engine']
    
    # 创建备份
    if not create_backup(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已整合
        if 'LazyStockAnalyzer' in content and 'self.lazy_analyzer' in content:
            logger.info("StrategyOptimizationEngine已整合LazyStockAnalyzer")
            return True
        
        # 添加导入
        if 'from lazy_analyzer import LazyStockAnalyzer' not in content:
            import_pos = content.find('from volume_price_strategy import VolumePriceStrategy')
            if import_pos > -1:
                content = content[:import_pos] + 'from lazy_analyzer import LazyStockAnalyzer\n' + content[import_pos:]
        
        # 在初始化方法中添加LazyStockAnalyzer
        init_method = re.search(r'def __init__\(self, token=None, data_dir=\'./strategy_data\'\):(.*?)# 加载策略配置', 
                               content, re.DOTALL)
        if init_method:
            init_code = init_method.group(1)
            if 'self.lazy_analyzer' not in init_code:
                new_init_code = init_code.replace(
                    'self.backtester = EnhancedBacktester(initial_capital=100000.0)',
                    'self.backtester = EnhancedBacktester(initial_capital=100000.0)\n        \n'
                    '        # 初始化LazyStockAnalyzer\n'
                    '        self.lazy_analyzer = LazyStockAnalyzer(required_indicators=[\n'
                    '            \'ma\', \'ema\', \'macd\', \'rsi\', \'kdj\', \'volume_ratio\', \'trend_direction\'\n'
                    '        ])'
                )
                content = content.replace(init_code, new_init_code)
        
        # 添加辅助方法来获取策略所需指标
        if '_get_strategy_required_indicators' not in content:
            backtest_pos = content.find('def backtest_strategy(self')
            if backtest_pos > -1:
                # 在backtest_strategy方法前添加辅助方法
                helper_method = '''
    def _get_strategy_required_indicators(self, strategy_id):
        """获取策略所需的技术指标
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            所需指标列表
        """
        if strategy_id == 'volume_price':
            return ['volume_ratio', 'trend_direction', 'macd', 'rsi']
        elif strategy_id == 'moving_average_crossover':
            return ['ma', 'ema']
        elif strategy_id == 'rsi_strategy':
            return ['rsi']
        else:
            return 'all'  # 默认全量计算
    
'''
                content = content[:backtest_pos] + helper_method + content[backtest_pos:]
        
        # 修改backtest_strategy方法，使用LazyStockAnalyzer
        backtest_method = re.search(r'def backtest_strategy\(self, strategy_id, symbol, start_date=None, end_date=None, parameters=None\):(.*?)# 添加回测元数据', 
                                   content, re.DOTALL)
        if backtest_method:
            backtest_code = backtest_method.group(1)
            if 'self.lazy_analyzer' not in backtest_code:
                new_backtest_code = backtest_code.replace(
                    'df = self.data_provider.get_stock_daily_data(symbol, start_date=start_date, end_date=end_date)',
                    'df = self.data_provider.get_stock_daily_data(symbol, start_date=start_date, end_date=end_date)\n'
                    '            \n'
                    '            # 使用LazyStockAnalyzer预处理数据\n'
                    '            required_indicators = self._get_strategy_required_indicators(strategy_id)\n'
                    '            analysis_result = self.lazy_analyzer.analyze(df)\n'
                    '            \n'
                    '            # 合并分析结果到原始数据\n'
                    '            for key, value in analysis_result.items():\n'
                    '                if key not in [\'date\', \'open\', \'high\', \'low\', \'close\', \'volume\']:\n'
                    '                    df[key] = value'
                )
                content = content.replace(backtest_code, new_backtest_code)
        
        # 保存修改
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功整合LazyStockAnalyzer到StrategyOptimizationEngine")
        return True
    
    except Exception as e:
        logger.error(f"整合StrategyOptimizationEngine时出错: {str(e)}")
        return False

def integrate_enhanced_backtester():
    """整合LazyStockAnalyzer到增强回测器"""
    logger.info("开始整合LazyStockAnalyzer到EnhancedBacktester...")
    file_path = MODULE_PATHS['enhanced_backtesting']
    
    # 创建备份
    if not create_backup(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已整合
        if 'LazyStockAnalyzer' in content and '_prepare_data_with_indicators' in content:
            logger.info("EnhancedBacktester已整合LazyStockAnalyzer")
            return True
        
        # 添加导入
        if 'from lazy_analyzer import LazyStockAnalyzer' not in content:
            import_match = re.search(r'import numpy as np(.*?)class EnhancedBacktester', content, re.DOTALL)
            if import_match:
                import_section = import_match.group(1)
                content = content.replace(
                    import_section,
                    import_section + '\nfrom lazy_analyzer import LazyStockAnalyzer\n'
                )
        
        # 在初始化方法中添加LazyStockAnalyzer
        init_method = re.search(r'def __init__\(self, initial_capital=100000.0\):(.*?)def ', content, re.DOTALL)
        if init_method:
            init_code = init_method.group(1)
            if 'self.lazy_analyzer' not in init_code:
                new_init_code = init_code.replace(
                    'self.trades = []',
                    'self.trades = []\n        \n'
                    '        # 初始化LazyStockAnalyzer\n'
                    '        self.lazy_analyzer = LazyStockAnalyzer(required_indicators=[\n'
                    '            \'ma\', \'ema\', \'macd\', \'rsi\', \'kdj\', \'volume_ratio\', \'trend_direction\'\n'
                    '        ])'
                )
                content = content.replace(init_code, new_init_code)
        
        # 添加辅助方法来预处理数据
        if '_prepare_data_with_indicators' not in content:
            # 找到第一个回测方法的位置
            backtest_pos = content.find('def backtest_')
            if backtest_pos > -1:
                # 在第一个回测方法前添加辅助方法
                helper_method = '''
    def _prepare_data_with_indicators(self, data, strategy_type):
        """使用LazyStockAnalyzer高效计算策略所需指标
        
        Args:
            data: 股票数据DataFrame
            strategy_type: 策略类型
            
        Returns:
            处理后的数据
        """
        if strategy_type == 'volume_price':
            required = ['volume_ratio', 'trend_direction', 'macd']
        elif strategy_type == 'ma_crossover':
            required = ['ma', 'ema']
        elif strategy_type == 'rsi_strategy':
            required = ['rsi']
        else:
            required = 'all'  # 默认全量计算
            
        analysis_result = self.lazy_analyzer.analyze(data)
        
        # 合并分析结果到原始数据
        for key, value in analysis_result.items():
            if key not in ['date', 'open', 'high', 'low', 'close', 'volume']:
                if isinstance(value, (int, float)):
                    data[key] = value
                
        return data
        
'''
                content = content[:backtest_pos] + helper_method + content[backtest_pos:]
        
        # 修改回测方法，使用LazyStockAnalyzer
        # 替换所有回测方法中的数据处理部分
        backtest_methods = [
            'backtest_volume_price_strategy',
            'backtest_ma_crossover_strategy',
            'backtest_rsi_strategy'
        ]
        
        for method in backtest_methods:
            method_pattern = f'def {method}\\(self, data=None, symbol=None'
            if method_pattern in content:
                method_match = re.search(f'def {method}\\(.*?\\):(.*?)result = {{', content, re.DOTALL)
                if method_match:
                    method_code = method_match.group(1)
                    if 'self._prepare_data_with_indicators' not in method_code:
                        strategy_type = method.replace('backtest_', '').replace('_strategy', '')
                        new_method_code = method_code.replace(
                            'try:',
                            f'try:\n            # 使用LazyStockAnalyzer预处理数据\n            data = self._prepare_data_with_indicators(data, \'{strategy_type}\')'
                        )
                        content = content.replace(method_code, new_method_code)
        
        # 保存修改
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功整合LazyStockAnalyzer到EnhancedBacktester")
        return True
    
    except Exception as e:
        logger.error(f"整合EnhancedBacktester时出错: {str(e)}")
        return False

def integrate_volume_price_strategy():
    """整合LazyStockAnalyzer到量价策略"""
    logger.info("开始整合LazyStockAnalyzer到VolumePriceStrategy...")
    file_path = MODULE_PATHS['volume_price_strategy']
    
    # 创建备份
    if not create_backup(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已整合
        if 'LazyStockAnalyzer' in content and 'analyzer = LazyStockAnalyzer' in content:
            logger.info("VolumePriceStrategy已整合LazyStockAnalyzer")
            return True
        
        # 添加导入
        if 'from lazy_analyzer import LazyStockAnalyzer' not in content:
            import_match = re.search(r'import numpy as np(.*?)class VolumePriceStrategy', content, re.DOTALL)
            if import_match:
                import_section = import_match.group(1)
                content = content.replace(
                    import_section,
                    import_section + '\nfrom lazy_analyzer import LazyStockAnalyzer\n'
                )
        
        # 修改analyze方法，使用LazyStockAnalyzer
        analyze_method = re.search(r'def analyze\(self, data\):(.*?)return result', content, re.DOTALL)
        if analyze_method:
            analyze_code = analyze_method.group(1)
            if 'LazyStockAnalyzer' not in analyze_code:
                # 查找原来的指标计算逻辑
                volume_calc = re.search(r'# 计算成交量相关指标(.*?)# 计算', analyze_code, re.DOTALL)
                if volume_calc:
                    orig_volume_calc = volume_calc.group(0)
                    # 使用LazyStockAnalyzer替换
                    new_volume_calc = '''        # 使用LazyStockAnalyzer高效计算技术指标
        required_indicators = ['volume_ratio', 'ma', 'ema', 'trend_direction', 'rsi', 'macd']
        analyzer = LazyStockAnalyzer(required_indicators=required_indicators)
        analysis = analyzer.analyze(data)
        
        # 使用分析结果
        volume_ratio = analysis.get('volume_ratio', 1.0)
        trend_direction = analysis.get('trend_direction', 0)
        
        # 计算'''
                    analyze_code = analyze_code.replace(orig_volume_calc, new_volume_calc)
                
                # 更新结果组装部分
                result_assembly = re.search(r'result = {(.*?)}', analyze_code, re.DOTALL)
                if result_assembly:
                    orig_result = result_assembly.group(1)
                    new_result = '''
            'volume_ratio': volume_ratio,
            'trend': 'uptrend' if trend_direction > 0 else 'downtrend' if trend_direction < 0 else 'sideways',
            'macd_hist': analysis.get('macd_hist', 0),
            'rsi': analysis.get('rsi', 50),
            'strategy_score': strategy_score
        '''
                    analyze_code = analyze_code.replace(orig_result, new_result)
                
                content = content.replace(analyze_method.group(1), analyze_code)
        
        # 保存修改
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功整合LazyStockAnalyzer到VolumePriceStrategy")
        return True
    
    except Exception as e:
        logger.error(f"整合VolumePriceStrategy时出错: {str(e)}")
        return False

def integrate_smart_review_main():
    """整合LazyStockAnalyzer到智能复盘主程序"""
    logger.info("开始整合LazyStockAnalyzer到SmartReviewMain...")
    file_path = MODULE_PATHS['smart_review_main']
    
    # 创建备份
    if not create_backup(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已整合
        if '--lazy-mode' in content and 'lazy_mode=' in content:
            logger.info("SmartReviewMain已整合LazyStockAnalyzer")
            return True
        
        # 添加命令行参数
        parse_args_method = re.search(r'def parse_arguments\(\):(.*?)return parser\.parse_args\(\)', content, re.DOTALL)
        if parse_args_method:
            args_code = parse_args_method.group(1)
            if '--lazy-mode' not in args_code:
                new_args_code = args_code + '''
    # LazyStockAnalyzer模式
    parser.add_argument('--lazy-mode', dest='lazy_mode', action='store_true', 
                        help='使用LazyStockAnalyzer的按需计算模式(默认)')
    parser.add_argument('--no-lazy-mode', dest='lazy_mode', action='store_false',
                        help='使用全量计算模式')
    parser.set_defaults(lazy_mode=True)
'''
                content = content.replace(args_code, new_args_code)
        
        # 修改SmartReviewCore的初始化
        init_core = re.search(r'review_core = SmartReviewCore\(token=token, data_dir=args\.data_dir\)', content)
        if init_core:
            old_init = init_core.group(0)
            new_init = 'review_core = SmartReviewCore(token=token, data_dir=args.data_dir, lazy_mode=args.lazy_mode)'
            content = content.replace(old_init, new_init)
        
        # 保存修改
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功整合LazyStockAnalyzer到SmartReviewMain")
        return True
    
    except Exception as e:
        logger.error(f"整合SmartReviewMain时出错: {str(e)}")
        return False

def update_integration_status(results):
    """更新整合状态"""
    status_file = 'lazy_analyzer_integration_status.json'
    
    status = {
        'integration_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0',
        'modules': results,
        'overall_status': all(results.values())
    }
    
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=4)
        logger.info(f"整合状态已保存到 {status_file}")
    except Exception as e:
        logger.error(f"保存整合状态时出错: {str(e)}")

def run_integration():
    """运行整合过程"""
    logger.info("===== 开始LazyStockAnalyzer全系统整合 =====")
    
    # 执行整合
    results = {
        'strategy_optimization_engine': integrate_strategy_optimization_engine(),
        'enhanced_backtester': integrate_enhanced_backtester(),
        'volume_price_strategy': integrate_volume_price_strategy(),
        'smart_review_main': integrate_smart_review_main()
    }
    
    # 更新整合状态
    update_integration_status(results)
    
    # 输出结果
    logger.info("===== LazyStockAnalyzer全系统整合完成 =====")
    succeeded = sum(1 for s in results.values() if s)
    failed = sum(1 for s in results.values() if not s)
    logger.info(f"整合结果: 成功: {succeeded}, 失败: {failed}")
    
    for module, status in results.items():
        logger.info(f"{module}: {'成功' if status else '失败'}")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_integration()
    sys.exit(0 if success else 1) 