#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
综合修复脚本
修复系统中的所有问题：
1. akshare接口调用问题
2. matplotlib字体问题
3. Unicode字符问题
4. 数据源配置问题
"""

import os
import sys
import logging
import shutil
import subprocess
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_all_issues.log')
    ]
)
logger = logging.getLogger("system_fixer")

def run_fix_script(script_name):
    """运行修复脚本"""
    logger.info(f"运行修复脚本 {script_name}...")
    
    start_time = time.time()
    result = subprocess.run([sys.executable, script_name], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           text=True)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        logger.info(f"脚本 {script_name} 运行成功（用时 {elapsed:.2f} 秒）")
        return True
    else:
        logger.error(f"脚本 {script_name} 运行失败（用时 {elapsed:.2f} 秒）")
        logger.error(f"错误信息: {result.stderr}")
        return False

def optimize_caching():
    """优化缓存配置"""
    logger.info("优化缓存配置...")
    
    config_file = 'data_source_config.yaml'
    if not os.path.exists(config_file):
        logger.warning(f"配置文件 {config_file} 不存在")
        return False
    
    try:
        import yaml
        
        # 备份配置文件
        backup_file = f"{config_file}.orig.bak"
        shutil.copy2(config_file, backup_file)
        
        # 读取配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 优化缓存设置
        if 'cache' in config:
            config['cache']['enabled'] = True
            config['cache']['max_size'] = 2000
            config['cache']['max_age'] = 86400  # 1天
            config['cache']['cleanup_interval'] = 7200  # 2小时
            
            if 'data_sources' in config:
                # 降低akshare优先级
                if 'akshare' in config['data_sources']:
                    config['data_sources']['akshare']['priority'] = 2
                
                # 提高本地数据源优先级
                if 'local' in config['data_sources']:
                    config['data_sources']['local']['priority'] = 1
            
            # 写入配置
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"已优化缓存配置: {config_file}")
            return True
        else:
            logger.warning("配置文件中没有缓存设置")
            return False
    except Exception as e:
        logger.error(f"优化缓存配置失败: {str(e)}")
        return False

def create_dummy_data():
    """创建模拟数据以防接口失败"""
    logger.info("创建模拟数据...")
    
    # 创建缓存目录
    cache_dir = os.path.join("data_cache", "sectors")
    os.makedirs(cache_dir, exist_ok=True)
    
    # 主要行业列表
    sectors = [
        "电子", "计算机", "汽车", "机械设备", "电气设备", 
        "医药生物", "家用电器", "传媒", "通信", "非银金融"
    ]
    
    import json
    import numpy as np
    from datetime import datetime, timedelta
    
    # 创建模拟数据
    success_count = 0
    for sector in sectors:
        cache_file = os.path.join(cache_dir, f"{sector}.json")
        
        # 仅在文件不存在时创建
        if not os.path.exists(cache_file):
            # 创建30天的模拟数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            dates = []
            date = start_date
            while date <= end_date:
                dates.append(date.strftime("%Y-%m-%d"))
                date += timedelta(days=1)
            
            # 生成模拟价格数据
            base_price = np.random.uniform(1000, 5000)
            prices = []
            price = base_price
            for _ in range(len(dates)):
                price = price * (1 + np.random.uniform(-0.02, 0.02))
                prices.append(float(f"{price:.2f}"))
            
            # 创建数据结构
            data = {
                "sector": sector,
                "dates": dates,
                "prices": prices,
                "source": "dummy_data",
                "is_simulated": True,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存到文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已创建行业 {sector} 的模拟数据: {cache_file}")
            success_count += 1
    
    logger.info(f"成功创建 {success_count}/{len(sectors)} 个行业的模拟数据")
    return success_count > 0

def test_system():
    """测试系统功能"""
    logger.info("测试系统功能...")
    
    # 创建测试脚本
    test_file = 'system_test.py'
    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import traceback
import importlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system_test.log')
    ]
)
logger = logging.getLogger("system_test")

def test_module(module_name):
    """测试模块能否正常导入"""
    try:
        module = importlib.import_module(module_name)
        logger.info(f"模块 {module_name} 导入成功")
        return True
    except Exception as e:
        logger.error(f"模块 {module_name} 导入失败: {str(e)}")
        traceback.print_exc()
        return False

def test_system_components():
    """测试系统组件"""
    # 核心模块列表
    core_modules = [
        'sector_data_provider',
        'enhanced_sector_analyzer',
        'stock_review',
        'visual_stock_system'
    ]
    
    success_count = 0
    for module in core_modules:
        if test_module(module):
            success_count += 1
    
    logger.info(f"成功导入 {success_count}/{len(core_modules)} 个核心模块")
    return success_count == len(core_modules)

if __name__ == "__main__":
    print("开始测试系统功能...")
    success = test_system_components()
    print(f"系统测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
"""
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    logger.info(f"已创建系统测试脚本: {test_file}")
    
    # 运行测试脚本
    success = run_fix_script(test_file)
    return success

def main():
    """主函数"""
    logger.info("开始综合修复...")
    
    # 判断修复脚本是否存在
    required_scripts = [
        'fix_akshare_interfaces.py',
        'fix_matplotlib_fonts.py'
    ]
    
    missing_scripts = [script for script in required_scripts if not os.path.exists(script)]
    if missing_scripts:
        logger.error(f"缺少以下修复脚本: {', '.join(missing_scripts)}")
        return
    
    # 步骤1: 运行akshare接口修复脚本
    logger.info("步骤1: 修复akshare接口...")
    if run_fix_script('fix_akshare_interfaces.py'):
        logger.info("akshare接口修复成功")
    else:
        logger.warning("akshare接口修复失败，继续执行...")
    
    # 步骤2: 运行matplotlib字体修复脚本
    logger.info("步骤2: 修复matplotlib字体...")
    if run_fix_script('fix_matplotlib_fonts.py'):
        logger.info("matplotlib字体修复成功")
    else:
        logger.warning("matplotlib字体修复失败，继续执行...")
    
    # 步骤3: 优化缓存配置
    logger.info("步骤3: 优化缓存配置...")
    if optimize_caching():
        logger.info("缓存配置优化成功")
    else:
        logger.warning("缓存配置优化失败，继续执行...")
    
    # 步骤4: 创建模拟数据
    logger.info("步骤4: 创建模拟数据...")
    if create_dummy_data():
        logger.info("模拟数据创建成功")
    else:
        logger.warning("模拟数据创建失败，继续执行...")
    
    # 步骤5: 测试系统
    logger.info("步骤5: 测试系统功能...")
    if test_system():
        logger.info("系统测试成功")
    else:
        logger.warning("系统测试失败")
    
    logger.info("综合修复完成！")
    logger.info("请重新启动应用程序以应用所有更改")
    logger.info("推荐运行命令: python stock_analyzer_app.py")

if __name__ == "__main__":
    main() 