#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复logger未定义问题
"""

import os

def fix_logger_issue():
    """修复logger未定义问题"""
    print("正在修复logger未定义问题...")
    
    # 寻找并修改 visual_stock_system.py 文件
    filename = 'visual_stock_system.py'
    
    if not os.path.exists(filename):
        print(f"找不到文件 {filename}")
        return
        
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查文件是否已包含logger定义
    if 'import logging' not in content:
        lines = content.split('\n')
        
        # 寻找导入语句的最后一行
        import_section_end = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_section_end = i
        
        # 在导入部分后添加logger定义
        logger_setup = [
            "import logging",
            "# 配置日志",
            "logger = logging.getLogger('VisualStockSystem')"
        ]
        
        # 在导入部分后插入logger定义
        new_lines = lines[:import_section_end + 1] + logger_setup + lines[import_section_end + 1:]
        new_content = '\n'.join(new_lines)
    else:
        # 如果已经有import logging，但没有logger定义
        if 'logger = ' not in content:
            lines = content.split('\n')
            
            # 找到import logging的位置
            logging_import_line = -1
            for i, line in enumerate(lines):
                if 'import logging' in line:
                    logging_import_line = i
                    break
            
            # 在import logging后添加logger定义
            if logging_import_line >= 0:
                logger_def = "logger = logging.getLogger('VisualStockSystem')"
                new_lines = lines[:logging_import_line + 1] + [logger_def] + lines[logging_import_line + 1:]
                new_content = '\n'.join(new_lines)
            else:
                # 如果找不到import logging，在文件开头添加
                logger_setup = [
                    "import logging",
                    "# 配置日志",
                    "logger = logging.getLogger('VisualStockSystem')"
                ]
                new_content = '\n'.join(logger_setup) + '\n' + content
        else:
            # 已经存在logger定义，不需要修改
            print("logger已经定义，无需修改")
            return
    
    # 将logger.debug替换为统一的日志处理
    if 'logger.debug("数据点数不足，无法计算动量指标，将使用默认值")' in new_content:
        # 文件中已经有修复后的代码
        pass
    else:
        # 替换原始的打印语句
        new_content = new_content.replace(
            'print("数据点数不足，无法计算动量指标")',
            'logger.debug("数据点数不足，无法计算动量指标，将使用默认值")'
        )
    
    # 保存修改后的文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"已修复 {filename} 中的logger未定义问题")

if __name__ == "__main__":
    print("开始修复logger未定义问题...")
    fix_logger_issue()
    print("修复完成，请重新启动应用程序尝试") 