#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业分析器集成模块
将增强版行业分析器集成到现有系统中
"""

import os
import sys
import importlib
import logging
import inspect
import datetime
import traceback
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sector_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SectorAnalyzerIntegration")

def patch_sector_analyzer():
    """
    修补原有行业分析器，使其使用增强版功能
    
    Returns:
        bool: 是否成功修补
    """
    try:
        # 导入模块
        import sector_analyzer
        from enhance_sector_analyzer import EnhancedSectorAnalyzer
        
        logger.info("开始修补行业分析器...")
        
        # 获取原始类引用
        SectorAnalyzer = sector_analyzer.SectorAnalyzer
        
        # 保存原始方法引用
        original_analyze_hot_sectors = SectorAnalyzer.analyze_hot_sectors
        original_predict_next_hot_sectors = SectorAnalyzer.predict_next_hot_sectors
        
        # 创建增强版封装方法
        def enhanced_analyze_hot_sectors(self):
            """增强版热门行业分析方法"""
            logger.info("调用增强版热门行业分析")
            try:
                # 初始化增强版分析器
                enhanced_analyzer = EnhancedSectorAnalyzer(top_n=self.top_n)
                # 调用增强版分析
                result = enhanced_analyzer.analyze_enhanced_hot_sectors()
                return result
            except Exception as e:
                logger.error(f"增强版热门行业分析失败: {str(e)}")
                logger.info("回退到原始行业分析")
                # 失败时回退到原始方法
                return original_analyze_hot_sectors(self)
        
        def enhanced_predict_next_hot_sectors(self):
            """增强版热门行业预测方法"""
            logger.info("调用增强版热门行业预测")
            try:
                # 初始化增强版分析器
                enhanced_analyzer = EnhancedSectorAnalyzer(top_n=self.top_n)
                # 调用增强版预测
                result = enhanced_analyzer.predict_hot_sectors_enhanced()
                return result
            except Exception as e:
                logger.error(f"增强版热门行业预测失败: {str(e)}")
                logger.info("回退到原始行业预测")
                # 失败时回退到原始方法
                return original_predict_next_hot_sectors(self)
        
        # 替换方法
        SectorAnalyzer.analyze_hot_sectors = enhanced_analyze_hot_sectors
        SectorAnalyzer.predict_next_hot_sectors = enhanced_predict_next_hot_sectors
        
        # 添加标识属性
        SectorAnalyzer.is_enhanced = True
        SectorAnalyzer.enhancement_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info("成功修补行业分析器，启用增强功能")
        return True
        
    except Exception as e:
        logger.error(f"修补行业分析器失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_integration_status():
    """
    检查集成状态
    
    Returns:
        dict: 集成状态信息
    """
    status = {
        "integration_success": False,
        "enhanced_analyze": False,
        "enhanced_predict": False,
        "details": ""
    }
    
    try:
        # 导入模块
        import sector_analyzer
        
        # 获取类引用
        SectorAnalyzer = sector_analyzer.SectorAnalyzer
        
        # 检查是否已集成
        if hasattr(SectorAnalyzer, 'is_enhanced') and SectorAnalyzer.is_enhanced:
            status["integration_success"] = True
            status["details"] = f"已集成增强功能，集成时间: {SectorAnalyzer.enhancement_time}"
            
            # 获取方法源代码检查是否为增强版
            analyze_code = inspect.getsource(SectorAnalyzer.analyze_hot_sectors)
            predict_code = inspect.getsource(SectorAnalyzer.predict_next_hot_sectors)
            
            status["enhanced_analyze"] = "enhanced_analyzer" in analyze_code
            status["enhanced_predict"] = "enhanced_analyzer" in predict_code
        else:
            status["details"] = "未集成增强功能"
            
    except Exception as e:
        status["details"] = f"检查集成状态失败: {str(e)}"
    
    return status

def update_dependencies():
    """
    确保所有依赖正确安装
    
    Returns:
        bool: 是否成功更新依赖
    """
    try:
        import importlib
        
        required_packages = {
            'pandas': 'pandas',
            'numpy': 'numpy',
            'matplotlib': 'matplotlib',
            'tushare': 'tushare'
        }
        
        missing_packages = []
        
        # 检查每个依赖包
        for package, import_name in required_packages.items():
            try:
                importlib.import_module(import_name)
                logger.info(f"依赖包 {package} 已安装")
            except ImportError:
                missing_packages.append(package)
        
        # 如果有缺失的包，尝试安装
        if missing_packages:
            logger.warning(f"以下依赖包缺失: {', '.join(missing_packages)}")
            logger.info("尝试安装缺失的依赖包...")
            
            # 检查pip是否可用
            try:
                import pip
                for package in missing_packages:
                    logger.info(f"安装 {package}...")
                    pip.main(['install', package])
            except Exception as e:
                logger.error(f"安装依赖包失败: {str(e)}")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"更新依赖失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n===== 行业分析器集成工具 =====\n")
    
    # 更新依赖
    print("检查并更新依赖...")
    if update_dependencies():
        print("依赖检查完成")
    else:
        print("依赖检查失败，请手动安装缺失的依赖包")
    
    # 修补行业分析器
    print("\n开始集成增强版行业分析器...")
    if patch_sector_analyzer():
        print("集成成功！行业分析器已启用增强功能")
        
        # 检查集成状态
        status = check_integration_status()
        print(f"\n集成状态: {'成功' if status['integration_success'] else '失败'}")
        print(f"增强版热门行业分析: {'已启用' if status['enhanced_analyze'] else '未启用'}")
        print(f"增强版行业预测: {'已启用' if status['enhanced_predict'] else '未启用'}")
        print(f"详情: {status['details']}")
        
        # 使用建议
        print("\n使用建议:")
        print("1. 直接通过原有接口使用增强功能:")
        print("   from sector_analyzer import SectorAnalyzer")
        print("   analyzer = SectorAnalyzer()")
        print("   hot_sectors = analyzer.analyze_hot_sectors()")
        print("   predictions = analyzer.predict_next_hot_sectors()")
    else:
        print("集成失败，请查看日志了解详情")

if __name__ == "__main__":
    main() 