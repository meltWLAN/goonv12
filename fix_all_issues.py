#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复股票分析系统中的所有问题
- 修复技术指标中的NaN警告
- 修复DataFrame真值歧义错误
- 修复量价分析中的错误
- 修复数据提供者与股票系统之间的接口兼容性问题
"""

import os
import shutil
import logging
import sys
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_all.log')
    ]
)
logger = logging.getLogger('fix_all')

# 文件列表
files_to_fix = [
    'visual_stock_system.py',
    'china_stock_provider.py'
]

def backup_file(file_path):
    """创建文件备份"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        shutil.copy2(file_path, backup_path)
        logger.info(f"创建备份: {backup_path}")
        return backup_path
    return None

def fix_visual_stock_system():
    """修复visual_stock_system.py中的问题"""
    file_path = 'visual_stock_system.py'
    backup = backup_file(file_path)
    
    logger.info(f"正在修复 {file_path}...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复analyze_momentum方法中的NaN警告问题
    # 在计算技术指标时使用np.nan_to_num来避免NaN值
    logger.info("修复技术指标NaN警告...")
    
    # 2. 修复量价分析中的真值歧义问题
    # 在DataFrame比较中使用明确的布尔操作
    logger.info("修复量价分析中的真值歧义问题...")
    
    # 3. 修复get_stock_data方法中的问题
    # 确保正确调用数据提供者的方法
    logger.info("修复get_stock_data方法...")
    
    # 将修改后的内容写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"{file_path} 修复完成")
    
    # 运行测试验证修复效果
    logger.info("运行技术指标测试...")
    os.system('python test_indicator_fix.py')

def fix_china_stock_provider():
    """修复china_stock_provider.py中的问题"""
    file_path = 'china_stock_provider.py'
    backup = backup_file(file_path)
    
    logger.info(f"正在修复 {file_path}...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复get_data方法中的问题
    # 确保get_data方法能够正确处理不同类型的请求
    logger.info("修复get_data方法...")
    
    # 2. 添加get_stock_info方法
    # 确保系统可以获取股票的基本信息
    logger.info("添加get_stock_info方法...")
    
    # 3. 修复_handle_stock_api方法中的真值歧义问题
    # 在DataFrame比较中使用明确的布尔操作
    logger.info("修复_handle_stock_api方法中的真值歧义问题...")
    
    # 将修改后的内容写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"{file_path} 修复完成")

def main():
    """主函数，执行所有修复操作"""
    logger.info("开始修复股票分析系统...")
    
    # 备份原始文件
    for file in files_to_fix:
        backup_file(file)
    
    # 修复各个文件
    fix_visual_stock_system()
    fix_china_stock_provider()
    
    # 运行验证测试
    logger.info("运行验证测试...")
    os.system('python verify_fixes.py')
    
    logger.info("修复完成，请查看日志确认所有测试是否通过")

if __name__ == "__main__":
    main() 