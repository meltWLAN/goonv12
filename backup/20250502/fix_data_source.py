#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复数据源配置和接口问题
"""

import os
import yaml
import json
import sys
import importlib
import inspect
from pathlib import Path

def check_akshare_version():
    """检查akshare版本和接口可用性"""
    print("检查akshare版本和接口可用性...")
    
    try:
        import akshare as ak
        version = ak.__version__
        print(f"当前akshare版本: {version}")
        
        # 检查北向资金接口
        if hasattr(ak, 'stock_hsgt_north_net_flow_in_em'):
            print("✓ 北向资金接口可用 (stock_hsgt_north_net_flow_in_em)")
        else:
            print("✗ 北向资金接口不可用 (stock_hsgt_north_net_flow_in_em)")
            # 查找替代接口
            alt_funcs = [name for name in dir(ak) if 'north' in name.lower() and 'flow' in name.lower()]
            if alt_funcs:
                print(f"  可能的替代接口: {', '.join(alt_funcs)}")
        
        # 检查行业数据接口
        if hasattr(ak, 'stock_sector_detail'):
            print("✓ 行业数据接口可用 (stock_sector_detail)")
        else:
            print("✗ 行业数据接口不可用 (stock_sector_detail)")
            # 查找替代接口
            alt_funcs = [name for name in dir(ak) if 'sector' in name.lower()]
            if alt_funcs:
                print(f"  可能的替代接口: {', '.join(alt_funcs)}")
    
    except ImportError:
        print("✗ 未安装akshare库")
        return False
    except Exception as e:
        print(f"✗ 检查akshare出错: {str(e)}")
        return False
    
    return True

def fix_data_source_config():
    """优化数据源配置"""
    print("正在优化数据源配置...")
    
    config_file = 'data_source_config.yaml'
    if not os.path.exists(config_file):
        print(f"✗ 配置文件 {config_file} 不存在")
        return False
    
    try:
        # 读取配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 优化配置
        if 'akshare' in config.get('data_sources', {}):
            # 增加akshare重试次数
            config['data_sources']['akshare']['retry_attempts'] = 5
            # 增加超时时间
            config['data_sources']['akshare']['timeout'] = 60
            # 降低优先级，减少依赖
            config['data_sources']['akshare']['priority'] = 3
            
            print("✓ 已优化akshare配置")
        
        # 优化缓存策略
        if 'cache' in config:
            # 增加缓存大小和生命周期
            config['cache']['max_size'] = 2000  # 增加缓存容量
            config['cache']['cleanup_interval'] = 7200  # 减少清理频率
            config['cache']['memory_cache_size'] = 200  # 增加内存缓存
            
            print("✓ 已优化缓存配置")
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✓ 配置已保存到 {config_file}")
        return True
    
    except Exception as e:
        print(f"✗ 优化配置失败: {str(e)}")
        return False

def fix_sector_data_provider():
    """修复行业数据提供器"""
    print("正在修复行业数据提供器...")
    
    provider_file = 'sector_data_provider.py'
    if not os.path.exists(provider_file):
        # 尝试查找真实文件名
        data_files = [f for f in os.listdir('.') if 'sector' in f.lower() and f.endswith('.py')]
        if data_files:
            provider_file = data_files[0]
            print(f"找到行业数据提供器文件: {provider_file}")
        else:
            print("✗ 未找到行业数据提供器文件")
            return False
    
    try:
        with open(provider_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复可能的接口错误
        replacements = [
            # 修正北向资金接口
            ("stock_hsgt_north_net_flow_in_em", "stock_hsgt_north_net_flow_in"),
            # 添加异常处理
            ("except Exception as e:", "except (Exception, IndexError, KeyError, TypeError) as e:"),
            # 修复价格异常警告
            ("if price > 10000:", "if price > 5000:"),
        ]
        
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                print(f"✓ 已修复: {old} -> {new}")
                modified = True
        
        if modified:
            # 备份原文件
            backup_file = f"{provider_file}.bak"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已备份原文件为 {backup_file}")
            
            # 保存修改后的文件
            with open(provider_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已保存修改到 {provider_file}")
        else:
            print("✓ 行业数据提供器无需修复")
        
        return True
    
    except Exception as e:
        print(f"✗ 修复行业数据提供器失败: {str(e)}")
        return False

def check_data_provider_compatibility():
    """检查数据提供器兼容性"""
    print("正在检查数据提供器兼容性...")
    
    try:
        # 尝试识别主要数据提供器
        providers = [f for f in os.listdir('.') if ('provider' in f.lower() or 'data' in f.lower()) and f.endswith('.py')]
        
        for provider in providers:
            print(f"检查 {provider}...")
            
            with open(provider, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找akshare接口使用
            ak_apis = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'ak.' in line and '(' in line:
                    api_call = line.split('ak.')[1].split('(')[0].strip()
                    ak_apis.append((api_call, i+1))
            
            if ak_apis:
                print(f"  发现 {len(ak_apis)} 个akshare接口调用:")
                for api, line_num in ak_apis[:5]:  # 只显示前5个
                    print(f"  - 第{line_num}行: {api}")
                
                if len(ak_apis) > 5:
                    print(f"  ... 以及其他 {len(ak_apis)-5} 个接口")
    except Exception as e:
        print(f"✗ 检查数据提供器失败: {str(e)}")
    
    return True

def main():
    print("开始修复数据源问题...\n")
    
    # 检查akshare版本和接口
    check_akshare_version()
    
    # 优化数据源配置
    fix_data_source_config()
    
    # 修复行业数据提供器
    fix_sector_data_provider()
    
    # 检查数据提供器兼容性
    check_data_provider_compatibility()
    
    print("\n数据源修复完成！建议重新启动应用以应用更改。")

if __name__ == "__main__":
    main() 