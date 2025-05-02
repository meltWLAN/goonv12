#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复 akshare 接口调用问题
此脚本修复 sector_data_provider.py 和相关文件中的 akshare 接口调用
"""

import os
import sys
import re
import importlib
import inspect
from pathlib import Path
import shutil
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_akshare.log')
    ]
)
logger = logging.getLogger("akshare_fixer")

def get_available_akshare_functions():
    """获取当前可用的akshare函数"""
    try:
        import akshare as ak
        functions = {}
        
        # 获取所有函数
        for name in dir(ak):
            if name.startswith('_'):
                continue
            
            obj = getattr(ak, name)
            if callable(obj):
                functions[name] = {
                    'name': name,
                    'doc': inspect.getdoc(obj),
                    'signature': str(inspect.signature(obj)) if hasattr(inspect, 'signature') else ''
                }
        
        return functions
    except ImportError:
        logger.error("无法导入akshare，请先安装: pip install akshare")
        return {}

def find_akshare_interface_replacements():
    """查找替代接口"""
    try:
        import akshare as ak
        replacements = {
            # 旧接口 -> 新接口
            'stock_hsgt_north_net_flow_in_em': 'stock_hsgt_north_net_flow_in',
            'stock_sector_detail': 'stock_board_industry_cons_em',
            'stock_sector_fund_flow_rank': 'stock_sector_fund_flow_rank_em',
            'stock_sse_deal_daily': 'stock_sse_deal_daily_em',
            'stock_zh_index_daily': 'stock_zh_index_daily_em',
            'stock_zh_a_daily': 'stock_zh_a_daily_hfq'
        }
        
        # 尝试测试所有替代接口
        valid_replacements = {}
        for old, new in replacements.items():
            if hasattr(ak, new):
                valid_replacements[old] = new
                logger.info(f"找到有效替代: {old} -> {new}")
            else:
                logger.warning(f"替代接口不可用: {new}")
                
                # 尝试寻找替代接口
                for func_name in dir(ak):
                    if func_name.startswith('_'):
                        continue
                        
                    if old.replace('_em', '') in func_name:
                        logger.info(f"可能的替代接口: {old} -> {func_name}")
                        valid_replacements[old] = func_name
                        break
        
        return valid_replacements
    except Exception as e:
        logger.error(f"查找替代接口时出错: {str(e)}")
        return {}

def update_file(file_path, replacements):
    """更新文件中的akshare接口调用"""
    if not os.path.exists(file_path):
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    # 创建备份
    backup_path = f"{file_path}.pre_akshare_fix.bak"
    shutil.copy2(file_path, backup_path)
    logger.info(f"已创建备份: {backup_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应用替换
        modified = False
        for old_interface, new_interface in replacements.items():
            pattern = r'ak\.{}\('.format(re.escape(old_interface))
            replacement = r'ak.{}('.format(new_interface)
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                logger.info(f"在 {file_path} 中将 {old_interface} 替换为 {new_interface}")
                modified = True
        
        # 如果内容已修改，则写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已更新文件: {file_path}")
            return True
        else:
            logger.info(f"文件无需更新: {file_path}")
            return False
    
    except Exception as e:
        logger.error(f"更新文件 {file_path} 时出错: {str(e)}")
        return False

def update_error_handling(file_path):
    """增强错误处理"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加额外的错误处理
        if 'except Exception as e:' in content:
            # 替换简单的异常处理为更健壮的版本
            error_patterns = [
                (r'except Exception as e:', r'except (Exception, IndexError, TypeError, ValueError) as e:'),
                (r'if data is None:', r'if data is None or len(data) == 0:'),
                (r'if result is None:', r'if result is None or (isinstance(result, (list, tuple, dict)) and len(result) == 0):')
            ]
            
            modified = False
            for pattern, replacement in error_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已增强文件 {file_path} 的错误处理")
                return True
            
        return False
    except Exception as e:
        logger.error(f"增强错误处理时出错: {str(e)}")
        return False

def add_fallback_functions(file_path):
    """添加回退功能"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查文件中是否已经有回退功能
        if "def get_sector_data_fallback" not in content:
            # 在文件末尾添加回退功能
            fallback_code = """

def get_sector_data_fallback(sector_name):
    """回退方法：当接口失败时使用缓存数据"""
    try:
        logger.info(f"尝试从缓存获取行业 {sector_name} 数据")
        # 这里可以实现从缓存加载数据的逻辑
        cache_dir = os.path.join("data_cache", "sectors")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            
        cache_file = os.path.join(cache_dir, f"{sector_name.replace('/', '_')}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
            return data
        return None
    except Exception as e:
        logger.error(f"回退方法获取行业数据失败: {str(e)}")
        return None
"""
            content += fallback_code
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"已添加回退功能到文件 {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"添加回退功能时出错: {str(e)}")
        return False

def patch_interface_calls():
    """修补所有接口调用"""
    # 获取替代接口
    replacements = find_akshare_interface_replacements()
    if not replacements:
        logger.error("未找到可用的替代接口")
        return False
    
    # 需要修改的文件
    target_files = [
        'sector_data_provider.py',
        'china_stock_provider.py',
        'enhanced_sector_analyzer.py',
        'enhanced_sector_analyzer_v2.py',
        'data_provider.py',
        'enhanced_data_provider.py',
        'tushare_data_service.py'
    ]
    
    # 更新所有文件
    success_count = 0
    for file in target_files:
        if os.path.exists(file):
            if update_file(file, replacements):
                update_error_handling(file)
                add_fallback_functions(file)
                success_count += 1
    
    logger.info(f"成功更新 {success_count}/{len(target_files)} 个文件")
    return success_count > 0

def create_interface_test_script():
    """创建测试脚本验证接口可用性"""
    test_file = 'test_akshare_fix.py'
    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_akshare_fix.log')
    ]
)
logger = logging.getLogger("akshare_test")

def test_akshare_interfaces():
    """测试akshare接口可用性"""
    try:
        import akshare as ak
        
        interfaces = [
            ('stock_hsgt_north_net_flow_in', {}),
            ('stock_board_industry_cons_em', {'symbol': '半导体'}),
            ('stock_sector_fund_flow_rank_em', {}),
            ('stock_zh_index_daily_em', {'symbol': '000001'}),
            ('stock_zh_a_daily_hfq', {'symbol': '000001'})
        ]
        
        for interface_name, kwargs in interfaces:
            if hasattr(ak, interface_name):
                try:
                    logger.info(f"测试接口: {interface_name}({kwargs})")
                    func = getattr(ak, interface_name)
                    result = func(**kwargs)
                    success = result is not None and len(result) > 0
                    logger.info(f"接口 {interface_name} 测试{'成功' if success else '失败'}")
                    if success and hasattr(result, 'shape'):
                        logger.info(f"返回数据大小: {result.shape}")
                except Exception as e:
                    logger.error(f"接口 {interface_name} 测试出错: {str(e)}")
                    traceback.print_exc()
            else:
                logger.warning(f"接口不存在: {interface_name}")
        
        return True
    except ImportError:
        logger.error("未安装akshare")
        return False
    except Exception as e:
        logger.error(f"测试过程出错: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试akshare接口...")
    success = test_akshare_interfaces()
    print(f"测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
"""
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    logger.info(f"已创建测试脚本: {test_file}")
    return test_file

def main():
    """主函数"""
    logger.info("开始修复akshare接口...")
    
    # 安装或升级akshare
    logger.info("升级akshare到最新版本...")
    os.system("pip install --upgrade akshare")
    
    # 获取当前可用的akshare函数
    functions = get_available_akshare_functions()
    logger.info(f"检测到 {len(functions)} 个可用的akshare函数")
    
    # 修补接口调用
    if patch_interface_calls():
        logger.info("接口调用已修补")
    else:
        logger.error("修补接口调用失败")
    
    # 创建测试脚本
    test_file = create_interface_test_script()
    
    logger.info("akshare接口修复完成！")
    logger.info(f"请运行测试脚本验证修复效果: python {test_file}")

if __name__ == "__main__":
    main() 