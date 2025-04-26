"""
应用修复到VisualStockSystem模块

此脚本将visual_stock_system_fixes.py中的修复应用到VisualStockSystem类，
并验证修复后的功能是否正常工作。
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApplyFixes')

def main():
    """主函数"""
    try:
        # 检查visual_stock_system.py是否存在
        if not os.path.exists('visual_stock_system.py'):
            logger.error("找不到visual_stock_system.py文件")
            return False
            
        # 检查visual_stock_system_fixes.py是否存在
        if not os.path.exists('visual_stock_system_fixes.py'):
            logger.error("找不到visual_stock_system_fixes.py文件")
            return False
            
        # 导入VisualStockSystem类
        sys.path.append('.')
        from visual_stock_system import VisualStockSystem
        from visual_stock_system_fixes import apply_fixes
        
        # 应用修复
        logger.info("开始应用修复...")
        FixedVisualStockSystem = apply_fixes(VisualStockSystem)
        
        # 测试修复后的功能
        test_fixes(FixedVisualStockSystem)
        
        return True
    except Exception as e:
        logger.error(f"应用修复过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
def test_fixes(FixedClass):
    """测试修复后的功能是否正常工作"""
    logger.info("开始测试修复后的功能...")
    
    # 创建实例
    system = FixedClass()
    
    # 测试1: analyze_momentum处理NaN值
    logger.info("测试1: 测试analyze_momentum修复...")
    df = pd.DataFrame({
        'close': [100, 101, np.nan, 103, 104, 105, 106, 107, 108, 109, 110,
                 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121]
    })
    try:
        result = system.analyze_momentum(df)
        logger.info(f"动量分析结果: {result}")
        if isinstance(result, dict) and 'direction' in result:
            logger.info("✓ analyze_momentum修复成功")
        else:
            logger.warning("✗ analyze_momentum修复可能不完整")
    except Exception as e:
        logger.error(f"测试analyze_momentum时出错: {str(e)}")
    
    # 测试2: get_stock_data参数验证
    logger.info("测试2: 测试get_stock_data修复...")
    try:
        # 测试有效参数
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        df = system.get_stock_data("000001.SZ", start_date, end_date)
        if df is not None and not df.empty:
            logger.info(f"✓ get_stock_data成功获取数据，共{len(df)}行")
        else:
            logger.warning("✗ get_stock_data未能获取数据")
    except Exception as e:
        if "格式错误" in str(e) or "无法识别" in str(e):
            logger.info("✓ get_stock_data正确验证了输入参数")
        else:
            logger.error(f"测试get_stock_data时出错: {str(e)}")
    
    # 测试3: get_stock_name缓存机制
    logger.info("测试3: 测试get_stock_name修复...")
    try:
        # 第一次调用
        name1 = system.get_stock_name("000001.SZ")
        logger.info(f"股票名称: {name1}")
        
        # 第二次调用应该使用缓存
        import time
        start = time.time()
        name2 = system.get_stock_name("000001.SZ")
        end = time.time()
        
        if end - start < 0.01:  # 如果非常快，说明使用了缓存
            logger.info(f"✓ get_stock_name缓存机制正常工作")
        else:
            logger.warning(f"✗ get_stock_name缓存可能不工作")
            
        if name1 == name2:
            logger.info(f"✓ get_stock_name返回结果一致")
        else:
            logger.warning(f"✗ get_stock_name返回的结果不一致")
    except Exception as e:
        logger.error(f"测试get_stock_name时出错: {str(e)}")
    
    logger.info("测试完成")

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("修复应用成功")
    else:
        logger.error("修复应用失败")
        sys.exit(1) 