#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级行业分析模块安装脚本
帮助用户设置和配置高级行业分析模块
"""

import os
import sys
import shutil
import logging
import subprocess
import platform
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("setup_advanced_sector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SetupAdvancedSector")

def check_prerequisites():
    """检查安装先决条件"""
    logger.info("检查安装先决条件...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
        logger.error(f"Python版本不满足要求: 当前 {python_version.major}.{python_version.minor}.{python_version.micro}，需要 3.6+")
        return False
    
    logger.info(f"Python版本检查通过: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的包
    required_packages = ['tushare', 'pandas', 'numpy', 'talib']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"包 {package} 已安装")
        except ImportError:
            logger.warning(f"包 {package} 未安装")
            missing_packages.append(package)
    
    # 如果有缺失的包，提供安装命令
    if missing_packages:
        if 'talib' in missing_packages:
            logger.warning("TA-Lib需要特殊安装，请参考: https://github.com/mrjbq7/ta-lib")
            missing_packages.remove('talib')
        
        if missing_packages:
            install_cmd = f"pip install {' '.join(missing_packages)}"
            logger.info(f"请运行以下命令安装缺失的包: {install_cmd}")
        
        return False
    
    return True

def backup_existing_files():
    """备份可能存在的原有文件"""
    logger.info("备份可能存在的原有文件...")
    
    files_to_backup = [
        'advanced_sector_analyzer.py',
        'advanced_sector_integration.py'
    ]
    
    backup_dir = f"backup_sector_modules_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    for file in files_to_backup:
        if os.path.exists(file):
            backup_path = os.path.join(backup_dir, file)
            shutil.copy2(file, backup_path)
            logger.info(f"已备份文件 {file} 到 {backup_path}")
    
    return backup_dir

def create_config_directory():
    """创建配置和缓存目录"""
    logger.info("创建必要的配置和缓存目录...")
    
    dirs = [
        'data_cache',
        'data_cache/advanced_sectors',
        'config'
    ]
    
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"创建目录: {directory}")
        else:
            logger.info(f"目录已存在: {directory}")
    
    # 创建API密钥配置文件
    config_file = 'config/api_keys.txt'
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            f.write("# API密钥配置文件\n")
            f.write("# 格式: 键=值\n")
            f.write("TUSHARE_TOKEN=0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10\n")
        logger.info(f"创建默认API配置文件: {config_file}")
    else:
        logger.info(f"API配置文件已存在: {config_file}")

def setup_integration():
    """设置集成点"""
    logger.info("设置模块集成点...")
    
    # 检查stock_analysis_gui.py是否存在
    if os.path.exists('stock_analysis_gui.py'):
        logger.info("发现stock_analysis_gui.py，尝试设置集成...")
        
        # 检查是否需要替换
        with open('stock_analysis_gui.py', 'r') as f:
            content = f.read()
        
        # 如果已经有高级分析模块集成，则不需要修改
        if 'from advanced_sector_integration import' in content:
            logger.info("GUI中已存在高级行业分析模块集成，无需修改")
        else:
            # 简单的添加导入语句，但这可能不够，具体集成需要更复杂的修改
            logger.warning("GUI文件需要手动修改以集成高级行业分析模块")
            logger.info("请在合适位置添加: from advanced_sector_integration import AdvancedSectorIntegrator")
            logger.info("然后将AdvancedSectorIntegrator实例传递给适当的组件")
    else:
        logger.warning("未找到stock_analysis_gui.py，无法设置自动集成")
        logger.info("请手动集成高级行业分析模块到您的系统中")

def test_installation():
    """测试安装是否成功"""
    logger.info("测试安装...")
    
    try:
        # 检查高级行业分析模块是否可导入
        result = subprocess.run([sys.executable, '-c', 
                                'try: import advanced_sector_analyzer; print("导入成功"); exit(0)\n'
                                'except Exception as e: print(f"导入失败: {e}"); exit(1)'], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("高级行业分析模块导入测试通过")
        else:
            logger.error(f"高级行业分析模块导入测试失败: {result.stdout} {result.stderr}")
            return False
        
        # 测试集成模块
        if os.path.exists('advanced_sector_integration.py'):
            logger.info("运行集成测试...")
            result = subprocess.run([sys.executable, 'advanced_sector_integration.py'], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("集成测试成功")
                logger.info(result.stdout)
            else:
                logger.warning(f"集成测试出现警告或错误: {result.stderr}")
                logger.info(result.stdout)
        
        return True
        
    except Exception as e:
        logger.error(f"测试安装时发生错误: {str(e)}")
        return False

def setup_tushare_token():
    """设置Tushare API Token"""
    logger.info("配置Tushare API Token...")
    
    config_file = 'config/api_keys.txt'
    current_token = None
    
    # 读取当前token
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                if line.startswith('TUSHARE_TOKEN='):
                    current_token = line.strip().split('=')[1]
                    break
    
    print("\n===== Tushare API Token配置 =====")
    print(f"当前Token: {current_token}")
    print("Tushare API需要有效的token才能访问数据")
    print("1. 保留当前token")
    print("2. 设置新token")
    choice = input("请选择 [1/2]: ").strip()
    
    if choice == '2':
        new_token = input("请输入您的Tushare token: ").strip()
        if new_token:
            # 更新配置文件
            lines = []
            with open(config_file, 'r') as f:
                lines = f.readlines()
            
            with open(config_file, 'w') as f:
                for line in lines:
                    if line.startswith('TUSHARE_TOKEN='):
                        f.write(f"TUSHARE_TOKEN={new_token}\n")
                    else:
                        f.write(line)
            
            logger.info(f"已更新Tushare token: {new_token}")
            print(f"Token已更新为: {new_token}")
        else:
            logger.warning("未输入新token，保留原token")
            print("保留原token")
    else:
        logger.info("保留原token")
        print("保留原token")

def main():
    """主安装过程"""
    print("\n====== 高级行业分析模块安装 ======\n")
    
    # 检查先决条件
    if not check_prerequisites():
        print("\n警告: 一些先决条件未满足，请解决上述问题后再继续")
        choice = input("是否继续安装? [y/N]: ").strip().lower()
        if choice != 'y':
            print("安装已取消")
            return
    
    # 备份现有文件
    backup_dir = backup_existing_files()
    print(f"\n已备份现有文件到: {backup_dir}")
    
    # 创建配置目录
    create_config_directory()
    
    # 设置Tushare Token
    setup_tushare_token()
    
    # 设置集成点
    setup_integration()
    
    # 测试安装
    if test_installation():
        print("\n安装测试成功!")
    else:
        print("\n安装测试部分失败，请查看日志文件以获取详细信息")
    
    print("\n====== 高级行业分析模块安装完成 ======")
    print("\n要使用高级行业分析模块，请在您的代码中导入:")
    print("from advanced_sector_analyzer import AdvancedSectorAnalyzer")
    print("analyzer = AdvancedSectorAnalyzer()")
    print("result = analyzer.analyze_hot_sectors()")
    print("\n如需与现有系统集成，请使用:")
    print("from advanced_sector_integration import AdvancedSectorIntegrator")
    print("integrator = AdvancedSectorIntegrator()")
    print("result = integrator.get_hot_sectors()")

if __name__ == "__main__":
    main() 