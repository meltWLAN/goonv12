#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复evolving_backtester_integration.py文件中的run_backtest函数
使其能够正确处理AdvancedBacktestResult对象
"""

import os
import sys
import logging
import traceback
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FixIntegration')

def fix_integration_file():
    """修复evolving_backtester_integration.py文件中的run_backtest函数"""
    
    logger.info("开始修复evolving_backtester_integration.py")
    
    # 备份原始文件
    backup_name = f'evolving_backtester_integration.py.bak'
    try:
        if os.path.exists('evolving_backtester_integration.py'):
            shutil.copy('evolving_backtester_integration.py', backup_name)
            logger.info(f"备份原始文件到 {backup_name}")
    except Exception as e:
        logger.error(f"备份文件失败: {str(e)}")
        return False
    
    try:
        # 读取文件内容
        with open('evolving_backtester_integration.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找需要修改的部分 - 结果处理代码
        target_code = '''        # 执行回测
        if strategy == "MACD金叉策略":
            result = backtester.backtest_macd_strategy(stock_data, stock_code)
        elif strategy == "KDJ金叉策略":
            result = backtester.backtest_kdj_strategy(stock_data, stock_code)
        elif strategy == "双均线策略":
            result = backtester.backtest_ma_strategy(stock_data, stock_code)
        else:
            result = backtester.backtest_macd_strategy(stock_data, stock_code)
            
        # 处理结果
        result_dict = {}
        
        # 对于高级回测结果，提取指标
        if isinstance(result, AdvancedBacktestResult):'''
        
        # 新的处理代码，正确处理AdvancedBacktestResult
        new_code = '''        # 执行回测
        if strategy == "MACD金叉策略":
            result = backtester.backtest_macd_strategy(stock_data, stock_code)
        elif strategy == "KDJ金叉策略":
            result = backtester.backtest_kdj_strategy(stock_data, stock_code)
        elif strategy == "双均线策略":
            result = backtester.backtest_ma_strategy(stock_data, stock_code)
        else:
            result = backtester.backtest_macd_strategy(stock_data, stock_code)
            
        # 处理结果
        result_dict = {}
        
        # 对于高级回测结果，提取指标
        if isinstance(result, AdvancedBacktestResult):'''
    
        # 找到旧的普通回测器结果处理代码
        old_result_code = '''        else:
            # 普通回测器结果处理
            days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
            annual_factor = 365 / max(days, 1)
            
            result_dict = {
                'initial_capital': initial_capital,
                'final_capital': backtester.current_capital,
                'total_return': ((backtester.current_capital/initial_capital)-1)*100,
                'annual_return': ((backtester.current_capital/initial_capital)**annual_factor-1)*100,
                'max_drawdown': getattr(backtester, 'max_drawdown', 0) * 100,
                'sharpe_ratio': getattr(backtester, 'sharpe_ratio', 0),
                'trade_count': getattr(backtester, 'trade_count', 0),
                'win_rate': getattr(backtester, 'win_rate', 0) * 100,
                'profit_ratio': getattr(backtester, 'profit_ratio', 0),
                'avg_holding_period': getattr(backtester, 'avg_holding_period', 0),
                'strategy': strategy,
                'mode': mode
            }'''
    
        # 新的普通回测器结果处理代码，增加对AdvancedBacktestResult的处理
        new_result_code = '''        else:
            # 普通回测器结果处理
            days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
            annual_factor = 365 / max(days, 1)
            
            # 检查结果是否为None
            if result is None:
                return {
                    "error": f"回测失败: 回测结果为空",
                    "success": False,
                    "stock_code": stock_code,
                    "strategy": strategy
                }
            
            # 处理AdvancedBacktestResult类型的结果
            if isinstance(result, AdvancedBacktestResult):
                # 使用对象属性
                result_dict = {
                    'initial_capital': result.initial_capital,
                    'final_capital': result.final_capital,
                    'total_return': result.total_profit,  # 使用计算属性
                    'annual_return': ((result.final_capital/result.initial_capital)**annual_factor-1)*100,
                    'max_drawdown': getattr(result, 'max_drawdown', 0) * 100,
                    'sharpe_ratio': getattr(result, 'sharpe_ratio', 0),
                    'trade_count': result.trade_count,  # 使用计算属性
                    'win_rate': result.win_rate if result.win_rate is not None else 0,
                    'profit_factor': result.profit_factor if result.profit_factor is not None else 0,
                    'total_trades': result.total_trades,
                    'winning_trades': result.winning_trades if result.winning_trades is not None else 0,
                    'losing_trades': result.losing_trades if result.losing_trades is not None else 0,
                    'strategy': strategy,
                    'mode': mode
                }
            else:
                # 传统回测器结果处理
                result_dict = {
                    'initial_capital': initial_capital,
                    'final_capital': backtester.current_capital,
                    'total_return': ((backtester.current_capital/initial_capital)-1)*100,
                    'annual_return': ((backtester.current_capital/initial_capital)**annual_factor-1)*100,
                    'max_drawdown': getattr(backtester, 'max_drawdown', 0) * 100,
                    'sharpe_ratio': getattr(backtester, 'sharpe_ratio', 0),
                    'trade_count': getattr(backtester, 'trade_count', 0),
                    'win_rate': getattr(backtester, 'win_rate', 0) * 100,
                    'profit_ratio': getattr(backtester, 'profit_ratio', 0),
                    'avg_holding_period': getattr(backtester, 'avg_holding_period', 0),
                    'strategy': strategy,
                    'mode': mode
                }'''
            
        # 更新内容
        content = content.replace(old_result_code, new_result_code)
        
        # 修复日志记录错误：确保正确访问total_return
        old_log_code = '''        # 记录回测完成
        logger.info(f"回测完成: {stock_code}, 最终资金: {backtester.current_capital:.2f}, " +
                   f"总收益率: {result_dict['total_return']:.2f}%, " +
                   f"胜率: {result_dict.get('win_rate', 0):.2f}%")'''
                   
        new_log_code = '''        # 记录回测完成
        logger.info(f"回测完成: {stock_code}, 最终资金: {result_dict.get('final_capital', 0):.2f}, " +
                   f"总收益率: {result_dict.get('total_return', 0):.2f}%, " +
                   f"胜率: {result_dict.get('win_rate', 0):.2f}%")'''
        
        content = content.replace(old_log_code, new_log_code)
        
        # 写入修改后的内容
        with open('evolving_backtester_integration.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功修复evolving_backtester_integration.py文件")
        return True
    
    except Exception as e:
        logger.error(f"修复失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import shutil
    
    if fix_integration_file():
        print("修复成功: evolving_backtester_integration.py文件已经更新")
    else:
        print("修复失败: 查看日志了解详情")
        sys.exit(1) 