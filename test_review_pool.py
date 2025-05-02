#!/usr/bin/env python
# coding: utf-8

import os
import sys
import logging
from PyQt5.QtWidgets import QApplication

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestReviewPool')

def main():
    """测试复盘池功能"""
    # 创建QApplication实例，避免PyQt相关错误
    app = QApplication(sys.argv)
    
    try:
        from enhanced_stock_review import EnhancedStockReview
        
        logger.info("正在初始化增强版复盘模块...")
        esr = EnhancedStockReview()
        
        # 检查复盘池数据是否加载
        logger.info(f"复盘池数据加载状态: {esr.enhanced_review_data is not None}")
        logger.info(f"复盘池股票数量: {len(esr.enhanced_review_data.get('stocks', []))}")
        
        # 尝试获取复盘池数据
        stocks = esr.get_enhanced_review_pool()
        logger.info(f"获取到的复盘池股票数量: {len(stocks)}")
        
        # 列出复盘池文件状态
        pool_file = esr.enhanced_review_file
        if os.path.exists(pool_file):
            logger.info(f"复盘池文件 {pool_file} 存在，大小: {os.path.getsize(pool_file)} 字节")
        else:
            logger.warning(f"复盘池文件 {pool_file} 不存在")
        
        logger.info("测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试复盘池时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 