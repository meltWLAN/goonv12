#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复evolving_backtester_integration.py中的图表生成功能
主要处理可能为None的值，确保在绘图时不会出错
"""

import os
import sys
import logging
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FixVisualization')

def fix_visualization():
    """修复图表生成功能"""
    
    logger.info("开始修复evolving_backtester_integration.py中的图表生成功能")
    
    # 备份原始文件
    backup_name = f'evolving_backtester_integration.py.viz.bak'
    try:
        if os.path.exists('evolving_backtester_integration.py'):
            import shutil
            shutil.copy('evolving_backtester_integration.py', backup_name)
            logger.info(f"备份原始文件到 {backup_name}")
    except Exception as e:
        logger.error(f"备份文件失败: {str(e)}")
        return False
    
    try:
        # 读取文件内容
        with open('evolving_backtester_integration.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复风险指标绘图代码
        old_risk_code = '''    plt.subplot(2, 2, 2)
    plt.title('风险指标')
    risk_metrics = ['max_drawdown', 'sharpe_ratio']
    risk_values = [result_data.get(m, 0) for m in risk_metrics]
    plt.bar(['最大回撤 (%)', '夏普比率'], risk_values, color=['#F44336', '#FF9800'])'''
        
        new_risk_code = '''    plt.subplot(2, 2, 2)
    plt.title('风险指标')
    # 安全获取风险指标，确保值不为None
    max_drawdown = result_data.get('max_drawdown', 0)
    if max_drawdown is None:
        max_drawdown = 0
    
    sharpe_ratio = result_data.get('sharpe_ratio', 0)
    if sharpe_ratio is None:
        sharpe_ratio = 0
    
    risk_values = [max_drawdown, sharpe_ratio]
    plt.bar(['最大回撤 (%)', '夏普比率'], risk_values, color=['#F44336', '#FF9800'])'''
        
        # 修复交易统计绘图代码
        old_trade_code = '''    plt.subplot(2, 2, 3)
    plt.title('交易统计')
    trade_metrics = ['win_rate', 'profit_ratio']
    trade_values = [result_data.get('win_rate', 0), result_data.get('profit_ratio', 0)]
    plt.bar(['胜率 (%)', '盈亏比'], trade_values, color=['#9C27B0', '#FFEB3B'])'''
        
        new_trade_code = '''    plt.subplot(2, 2, 3)
    plt.title('交易统计')
    # 安全获取交易指标，确保值不为None
    win_rate = result_data.get('win_rate', 0)
    if win_rate is None:
        win_rate = 0
    
    profit_ratio = result_data.get('profit_ratio', result_data.get('profit_factor', 0))
    if profit_ratio is None:
        profit_ratio = 0
    
    trade_values = [win_rate, profit_ratio]
    plt.bar(['胜率 (%)', '盈亏比'], trade_values, color=['#9C27B0', '#FFEB3B'])'''
        
        # 修复收益率绘图代码
        old_returns_code = '''    plt.subplot(2, 2, 1)
    plt.title('收益指标')
    metrics = ['total_return', 'annual_return']
    values = [result_data.get(m, 0) for m in metrics]
    plt.bar(['总收益率', '年化收益率'], values, color=['#2196F3', '#4CAF50'])'''
        
        new_returns_code = '''    plt.subplot(2, 2, 1)
    plt.title('收益指标')
    # 安全获取收益指标，确保值不为None
    total_return = result_data.get('total_return', 0)
    if total_return is None:
        total_return = 0
    
    annual_return = result_data.get('annual_return', 0)
    if annual_return is None:
        annual_return = 0
    
    values = [total_return, annual_return]
    plt.bar(['总收益率', '年化收益率'], values, color=['#2196F3', '#4CAF50'])'''
        
        # 修复模型指标绘图代码
        old_model_code = '''            plt.bar(['入场模型', '出场模型'], model_metrics, color=['#2196F3', '#4CAF50'])'''
        
        new_model_code = '''            # 确保没有None值
            if None in model_metrics:
                model_metrics = [0 if m is None else m for m in model_metrics]
            plt.bar(['入场模型', '出场模型'], model_metrics, color=['#2196F3', '#4CAF50'])'''
        
        # 进行替换
        content = content.replace(old_risk_code, new_risk_code)
        content = content.replace(old_trade_code, new_trade_code)
        content = content.replace(old_returns_code, new_returns_code)
        content = content.replace(old_model_code, new_model_code)
        
        # 在图表生成函数开头添加安全检查
        old_visualization_start = '''def visualize_backtest_results(result_data, stock_code, strategy, save_path="backtest_charts"):
    """生成回测结果的可视化图表'''
        
        new_visualization_start = '''def visualize_backtest_results(result_data, stock_code, strategy, save_path="backtest_charts"):
    """生成回测结果的可视化图表'''
        
        visualization_check = '''
    # 检查result_data是否为None或为空
    if result_data is None or not isinstance(result_data, dict) or not result_data:
        logger.warning(f"无法生成图表：结果数据为空或格式不正确")
        return []
        
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    '''
        
        visualization_impl_start = '''    """
    
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)'''
        
        # 添加安全检查到函数开头
        new_visualization_impl = new_visualization_start + visualization_check + visualization_impl_start[4:]
        content = content.replace(old_visualization_start + visualization_impl_start, new_visualization_impl)
        
        # 写入修改后的内容
        with open('evolving_backtester_integration.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("成功修复图表生成功能")
        return True
        
    except Exception as e:
        logger.error(f"修复失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_visualization():
        print("修复成功: 图表生成功能已更新")
    else:
        print("修复失败: 查看日志了解详情")
        sys.exit(1) 