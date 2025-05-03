#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复增强回测功能
- 检查和修复缩进错误
- 添加缺失的方法
"""

import os
import sys
import re
import importlib

def check_enhanced_backtesting():
    """检查增强回测模块是否可以加载"""
    try:
        # 尝试导入模块
        import enhanced_backtesting
        print("✅ 增强回测模块可以成功导入")
        
        # 尝试创建回测器实例
        try:
            backtester = enhanced_backtesting.EnhancedBacktester()
            print("✅ 可以成功创建EnhancedBacktester实例")
            return True
        except Exception as e:
            print(f"❌ 创建EnhancedBacktester实例失败: {e}")
            return False
    except ImportError as e:
        print(f"❌ 导入增强回测模块失败: {e}")
        return False
    except SyntaxError as e:
        print(f"❌ 增强回测模块存在语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def fix_indentation_errors():
    """修复缩进错误"""
    file_path = 'enhanced_backtesting.py'
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 文件 {file_path} 不存在")
        return False
    
    # 备份文件
    backup_path = f"{file_path}.bak"
    try:
        with open(file_path, 'r', encoding='utf-8') as src_file:
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                backup_file.write(src_file.read())
        print(f"✅ 已备份文件到 {backup_path}")
    except Exception as e:
        print(f"❌ 备份文件失败: {e}")
        return False
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False
    
    # 修复缩进问题
    # 1. 查找"def backtest_kdj_strategy"行的错误缩进
    pattern_kdj = r'^def backtest_kdj_strategy\('
    fixed_content = re.sub(pattern_kdj, '    def backtest_kdj_strategy(', content, flags=re.MULTILINE)
    
    # 2. 添加缺失的_get_volatility_percentile方法
    pattern_class_end = r'(def update_trailing_stop.*?\n    .*?\n\n)'
    
    volatility_method = '''
    def _get_volatility_percentile(self) -> float:
        """获取当前市场波动率分位数
        
        如果未计算波动率分位数，返回默认值0.5
        
        Returns:
            波动率分位数 (0-1)
        """
        # 如果已经设置了市场波动率分位数，直接返回
        if hasattr(self, 'market_volatility_percentile'):
            return self.market_volatility_percentile
            
        # 默认返回中等波动率
        return 0.5
        
'''
    
    if '_get_volatility_percentile' not in fixed_content:
        fixed_content = re.sub(pattern_class_end, r'\1' + volatility_method, fixed_content, flags=re.DOTALL)
    
    # 保存修复后的文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ 已保存修复后的文件")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return False
    
    # 验证修复
    try:
        import py_compile
        py_compile.compile(file_path)
        print("✅ 修复后的文件通过了语法检查")
        return True
    except Exception as e:
        print(f"❌ 修复后的文件语法检查失败: {e}")
        return False

def main():
    """主函数"""
    print("==== 开始修复增强回测功能 ====")
    
    # 首先检查是否可以加载
    if check_enhanced_backtesting():
        print("✅ 增强回测模块可以正常工作，不需要修复")
        return
    
    # 尝试修复缩进错误
    print("\n正在修复缩进错误...")
    if fix_indentation_errors():
        print("✅ 修复完成，正在重新检查...")
        
        # 重新加载模块
        if 'enhanced_backtesting' in sys.modules:
            del sys.modules['enhanced_backtesting']
        
        # 重新检查
        if check_enhanced_backtesting():
            print("\n🎉 增强回测功能已成功修复！")
        else:
            print("\n❓ 修复可能不完整，请手动检查文件")
    else:
        print("\n❌ 修复失败，请手动检查文件")

if __name__ == "__main__":
    main() 