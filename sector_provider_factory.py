#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
行业数据提供器工厂
用于统一管理不同的行业数据提供器(Tushare、AKShare等)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("SectorProviderFactory")

# 全局实例
_tushare_provider = None
_akshare_provider = None

def get_provider(provider_type='auto', tushare_token=None):
    """获取行业数据提供器
    
    Args:
        provider_type: 提供器类型 ('tushare', 'akshare', 'auto')
        tushare_token: Tushare API Token
        
    Returns:
        行业数据提供器实例
    """
    global _tushare_provider, _akshare_provider
    
    # 如果指定使用Tushare
    if provider_type.lower() == 'tushare':
        if _tushare_provider is None:
            try:
                from tushare_sector_provider import get_sector_provider
                _tushare_provider = get_sector_provider()
                logger.info("已初始化Tushare行业数据提供器")
            except ImportError:
                logger.error("无法导入Tushare行业数据提供器模块")
                return None
        return _tushare_provider
    
    # 如果指定使用AKShare
    elif provider_type.lower() == 'akshare':
        if _akshare_provider is None:
            try:
                from akshare_sector_provider import get_sector_provider
                _akshare_provider = get_sector_provider()
                logger.info("已初始化AKShare行业数据提供器")
            except ImportError:
                logger.error("无法导入AKShare行业数据提供器模块")
                return None
        return _akshare_provider
    
    # 如果是自动选择（尝试优先使用AKShare，失败则尝试Tushare）
    elif provider_type.lower() == 'auto':
        # 优先尝试AKShare
        try:
            if _akshare_provider is None:
                from akshare_sector_provider import get_sector_provider
                _akshare_provider = get_sector_provider()
                logger.info("已初始化AKShare行业数据提供器")
            
            # 验证AKShare能否正常工作
            test_ok = _test_provider(_akshare_provider)
            if test_ok:
                logger.info("AKShare行业数据提供器测试通过，将使用AKShare")
                return _akshare_provider
            else:
                logger.warning("AKShare行业数据提供器测试失败，尝试使用Tushare")
        except ImportError:
            logger.warning("无法导入AKShare行业数据提供器模块，尝试使用Tushare")
        
        # 如果AKShare不可用，尝试Tushare
        try:
            if _tushare_provider is None:
                from tushare_sector_provider import get_sector_provider
                _tushare_provider = get_sector_provider()
                logger.info("已初始化Tushare行业数据提供器")
            
            # 验证Tushare能否正常工作
            test_ok = _test_provider(_tushare_provider)
            if test_ok:
                logger.info("Tushare行业数据提供器测试通过，将使用Tushare")
                return _tushare_provider
            else:
                logger.error("Tushare行业数据提供器测试失败")
                return None
        except ImportError:
            logger.error("无法导入Tushare行业数据提供器模块")
            return None
    
    else:
        logger.error(f"不支持的提供器类型: {provider_type}")
        return None

def _test_provider(provider):
    """测试提供器是否能正常工作
    
    Args:
        provider: 行业数据提供器实例
        
    Returns:
        是否通过测试
    """
    try:
        # 获取行业列表
        sectors = provider.get_sector_list()
        if sectors and len(sectors) > 0:
            # 尝试获取第一个行业的历史数据
            sector_code = sectors[0]['code']
            history = provider.get_sector_history(sector_code, days=10)
            
            # 如果能获取历史数据，测试通过
            if history is not None and not history.empty:
                return True
            else:
                logger.warning(f"提供器无法获取行业 {sector_code} 的历史数据")
                # 尝试获取板块历史数据
                for sector in sectors:
                    history = provider.get_sector_history(sector['code'], days=10)
                    if history is not None and not history.empty:
                        return True
                return False
        else:
            logger.warning("提供器无法获取行业列表")
            return False
    except Exception as e:
        logger.error(f"测试提供器时出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试
    print("测试行业数据提供器工厂...")
    
    # 测试自动选择
    provider = get_provider(provider_type='auto')
    if provider:
        print("自动选择的提供器类型:", provider.__class__.__name__)
        
        # 获取行业列表
        sectors = provider.get_sector_list()
        print(f"获取到 {len(sectors)} 个行业")
        
        # 测试获取第一个行业的历史数据
        if sectors:
            test_sector = sectors[0]
            print(f"测试获取行业 {test_sector['name']} 历史数据:")
            history = provider.get_sector_history(test_sector['code'], days=10)
            if history is not None:
                print(f"获取到 {len(history)} 条历史数据")
            else:
                print("获取历史数据失败")
    else:
        print("无法获取有效的行业数据提供器") 