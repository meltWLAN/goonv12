#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复 matplotlib 中文字体问题
通过修改 matplotlib 配置并注入自定义字体处理逻辑
"""

import os
import sys
import logging
import shutil
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_matplotlib.log')
    ]
)
logger = logging.getLogger("font_fixer")

def detect_system_chinese_fonts():
    """检测系统中的中文字体"""
    logger.info("检测系统中的中文字体...")
    
    # 创建临时Python脚本检测字体
    temp_script = 'detect_fonts.py'
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write("""
import matplotlib.font_manager as fm
import json

fonts = []
for font in fm.fontManager.ttflist:
    fonts.append({
        'name': font.name,
        'family': font.family_name,
        'path': font.fname,
        'style': font.style_name
    })

with open('detected_fonts.json', 'w', encoding='utf-8') as f:
    json.dump(fonts, f, ensure_ascii=False, indent=2)
print(f"检测到 {len(fonts)} 个字体")
""")
    
    # 运行脚本
    result = subprocess.run([sys.executable, temp_script], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          text=True)
    
    # 清理临时文件
    os.remove(temp_script)
    
    if result.returncode != 0:
        logger.error(f"字体检测失败: {result.stderr}")
        return []
    
    # 加载检测结果
    if os.path.exists('detected_fonts.json'):
        import json
        with open('detected_fonts.json', 'r', encoding='utf-8') as f:
            fonts = json.load(f)
        
        # 清理文件
        os.remove('detected_fonts.json')
        
        # 过滤中文字体
        chinese_fonts = []
        for font in fonts:
            name = font['name'].lower()
            if any(keyword in name for keyword in ['chinese', 'cn', 'ming', 'hei', 'sans', 'song', 'kai', 'pingfang', 'heiti', 'simhei', 'simsun']):
                chinese_fonts.append(font)
        
        logger.info(f"检测到 {len(chinese_fonts)} 个可能的中文字体")
        return chinese_fonts
    
    return []

def modify_font_config():
    """修改matplotlib字体配置"""
    logger.info("修改matplotlib字体配置...")
    
    try:
        import matplotlib
        import matplotlib.font_manager as fm
        
        # 检测系统中的中文字体
        chinese_fonts = detect_system_chinese_fonts()
        available_chinese_font = None
        
        if chinese_fonts:
            # 选择第一个可用的中文字体
            available_chinese_font = chinese_fonts[0]['name']
            logger.info(f"选择中文字体: {available_chinese_font}")
        else:
            logger.warning("未检测到中文字体，将使用默认字体")
            available_chinese_font = 'sans-serif'
        
        # 修改matplotlib配置
        mpl_configdir = matplotlib.get_configdir()
        if not os.path.exists(mpl_configdir):
            os.makedirs(mpl_configdir)
        
        mpl_config = os.path.join(mpl_configdir, 'matplotlibrc')
        with open(mpl_config, 'w', encoding='utf-8') as f:
            f.write(f"""
# Matplotlib配置文件
# 修复中文字体显示问题

font.family         : sans-serif
font.sans-serif     : {available_chinese_font}, DejaVu Sans, Bitstream Vera Sans, Arial, sans-serif
axes.unicode_minus  : False
""")
        
        logger.info(f"已创建matplotlib配置文件: {mpl_config}")
        
        # 清理字体缓存
        font_cache = os.path.join(mpl_configdir, 'fontlist-v*')
        for cache_file in Path(mpl_configdir).glob('fontlist-v*'):
            cache_file.unlink()
            logger.info(f"已删除字体缓存: {cache_file}")
        
        return True
    except Exception as e:
        logger.error(f"修改字体配置失败: {str(e)}")
        return False

def inject_font_handling():
    """注入字体处理逻辑到绘图代码"""
    logger.info("注入字体处理逻辑...")
    
    target_files = [
        'sector_visualization.py',
        'visual_stock_system.py',
        'visualize_stock_data.py'
    ]
    
    font_handling_code = """
# 自动设置中文字体
def set_chinese_font():
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import os
    import platform
    
    # 尝试多种中文字体
    font_names = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Heiti SC', 'STHeiti', 'SimSun', 'Hiragino Sans GB']
    
    # 替代方案：使用默认字体并禁用unicode minus
    plt.rcParams['axes.unicode_minus'] = False
    
    # 尝试设置中文字体
    for font_name in font_names:
        try:
            plt.rcParams['font.sans-serif'] = [font_name, 'sans-serif']
            # 简单测试
            fig = plt.figure(figsize=(1, 1))
            plt.title('测试')
            plt.close(fig)
            print(f"成功设置中文字体: {font_name}")
            return True
        except:
            print(f"设置字体 {font_name} 失败")
    
    print("警告: 未能设置中文字体，将使用默认字体")
    return False

# 调用字体设置函数
set_chinese_font()
"""
    
    success_count = 0
    for file in target_files:
        if not os.path.exists(file):
            logger.warning(f"文件不存在: {file}")
            continue
        
        # 备份文件
        backup_file = f"{file}.font_orig.bak"
        shutil.copy2(file, backup_file)
        
        # 读取文件内容
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已注入字体处理逻辑
        if "set_chinese_font" in content:
            logger.info(f"文件 {file} 已包含字体处理逻辑")
            continue
        
        # 注入字体处理逻辑
        # 在导入语句之后注入
        import_end = content.find('\n\n', content.find('import'))
        if import_end != -1:
            new_content = content[:import_end+2] + font_handling_code + content[import_end+2:]
            
            # 写入文件
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"已向文件 {file} 注入字体处理逻辑")
            success_count += 1
    
    logger.info(f"成功向 {success_count}/{len(target_files)} 个文件注入字体处理逻辑")
    return success_count > 0

def fix_unicode_symbols():
    """修复Unicode字符问题"""
    logger.info("修复Unicode字符问题...")
    
    target_files = [
        'sector_visualization.py',
        'visual_stock_system.py',
        'enhanced_sector_analyzer.py'
    ]
    
    replacements = [
        ('⭐', '*'),
        ('↑', '^'),
        ('↓', 'v'),
        ('•', '-'),
        ('…', '...')
    ]
    
    success_count = 0
    for file in target_files:
        if not os.path.exists(file):
            logger.warning(f"文件不存在: {file}")
            continue
        
        # 备份文件
        backup_file = f"{file}.unicode_orig.bak"
        shutil.copy2(file, backup_file)
        
        # 读取文件内容
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换Unicode字符
        modified = False
        for unicode_char, ascii_char in replacements:
            if unicode_char in content:
                content = content.replace(unicode_char, ascii_char)
                modified = True
                logger.info(f"已将 {unicode_char} 替换为 {ascii_char} 在文件 {file} 中")
        
        if modified:
            # 写入文件
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"已修复文件 {file} 中的Unicode字符")
            success_count += 1
    
    logger.info(f"成功修复 {success_count}/{len(target_files)} 个文件中的Unicode字符")
    return success_count > 0

def create_font_test_script():
    """创建字体测试脚本"""
    test_file = 'test_font.py'
    
    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import os
import platform
import matplotlib.font_manager as fm

# 输出系统信息
print(f"Python版本: {platform.python_version()}")
print(f"系统: {platform.system()} {platform.release()}")
print(f"Matplotlib版本: {plt.__version__}")

# 显示可用字体
print("\\n可用字体:")
fonts = [f.name for f in fm.fontManager.ttflist]
chinese_fonts = [f for f in fonts if any(keyword in f for keyword in 
                ['SimHei', 'Microsoft YaHei', 'PingFang', 'Heiti', 'STHeiti', 'SimSun'])]
print(f"检测到的中文字体: {chinese_fonts}")

# 测试绘图
x = np.linspace(0, 2*np.pi, 100)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

# 测试1：标准文本
ax1.plot(x, np.sin(x))
ax1.set_title('正弦函数测试 (Sine Function Test)')
ax1.set_xlabel('角度值 (Angle)')
ax1.set_ylabel('振幅 (Amplitude)')

# 测试2：包含特殊字符
ax2.plot(x, np.cos(x))
ax2.set_title('余弦函数与特殊符号 ± × ÷ °C ←→')
ax2.set_xlabel('测试Unicode符号: ★☆♠♣♥♦♪♫')
ax2.text(np.pi, 0, '中文文本测试 OK?', fontsize=14)

plt.tight_layout()
plt.savefig('font_test_result.png')
print("\\n测试图形已保存为 font_test_result.png")

# 在终端显示字体设置
print("\\nMatplotlib字体设置:")
print(f"当前字体家族: {plt.rcParams['font.family']}")
print(f"无衬线字体: {plt.rcParams['font.sans-serif']}")
print(f"Unicode减号处理: {'禁用' if not plt.rcParams['axes.unicode_minus'] else '启用'}")

print("\\n字体测试完成")
"""
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    logger.info(f"已创建字体测试脚本: {test_file}")
    return test_file

def main():
    """主函数"""
    logger.info("开始修复matplotlib字体问题...")
    
    # 修改字体配置
    if modify_font_config():
        logger.info("字体配置已修改")
    else:
        logger.error("修改字体配置失败")
    
    # 注入字体处理逻辑
    if inject_font_handling():
        logger.info("字体处理逻辑已注入")
    else:
        logger.warning("注入字体处理逻辑失败或不需要")
    
    # 修复Unicode字符
    if fix_unicode_symbols():
        logger.info("Unicode字符已修复")
    else:
        logger.warning("修复Unicode字符失败或不需要")
    
    # 创建字体测试脚本
    test_file = create_font_test_script()
    
    logger.info("matplotlib字体问题修复完成！")
    logger.info(f"请运行测试脚本验证修复效果: python {test_file}")
    logger.info("建议重启应用程序以应用更改")

if __name__ == "__main__":
    main() 