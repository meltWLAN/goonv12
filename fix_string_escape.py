#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复stock_analyzer_app.py中的转义字符串问题
"""

import os
import sys
import re
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_escape.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("FixEscapeScript")

def fix_escape_chars(file_path):
    """修复文件中的转义字符串问题"""
    logger.info(f"开始修复 {file_path} 中的转义字符串问题...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份文件
    with open(f"{file_path}.escape.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复"\\n"为"\n"
    content = content.replace('\\\\n', '\\n')
    
    # 将修改后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"成功修复 {file_path} 中的转义字符串问题")
    return True

if __name__ == "__main__":
    logger.info("开始修复转义字符串问题...")
    
    # 修复stock_analyzer_app.py文件
    if fix_escape_chars("stock_analyzer_app.py"):
        logger.info("转义字符串问题修复完成!")
    else:
        logger.error("转义字符串问题修复失败!")
        sys.exit(1) 