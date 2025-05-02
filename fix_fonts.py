#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import matplotlib
import matplotlib.font_manager as fm
import shutil
import glob

def fix_matplotlib_fonts():
    """Fix matplotlib font configuration for Chinese characters"""
    print("Fixing matplotlib font configuration...")
    
    # Get matplotlib config directory
    mpl_configdir = matplotlib.get_configdir()
    os.makedirs(mpl_configdir, exist_ok=True)
    
    # Create matplotlibrc file with font configuration
    mpl_config = os.path.join(mpl_configdir, 'matplotlibrc')
    
    config_content = """
# Matplotlib configuration for Chinese fonts
font.family         : sans-serif
font.sans-serif     : DejaVu Sans, Arial, Helvetica, sans-serif
axes.unicode_minus  : False
"""
    
    with open(mpl_config, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"Created matplotlib configuration file: {mpl_config}")
    
    # Clear font cache
    font_cache_pattern = os.path.join(mpl_configdir, 'fontlist-v*')
    for cache_file in glob.glob(font_cache_pattern):
        if os.path.isfile(cache_file):
            os.remove(cache_file)
            print(f"Removed font cache: {cache_file}")
    
    # Inject font handling into visualization files
    target_files = [
        'sector_visualization.py',
        'visual_stock_system.py',
        'visualize_stock_data.py'
    ]
    
    font_handling_code = """
# Fix Chinese font display
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

"""
    
    for file_path in target_files:
        if os.path.exists(file_path):
            # Create backup
            backup_path = f"{file_path}.font.bak"
            shutil.copy2(file_path, backup_path)
            print(f"Created backup: {backup_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add font handling code after imports
            import_end = content.find('\n\n', content.find('import'))
            if import_end != -1:
                content = content[:import_end+2] + font_handling_code + content[import_end+2:]
                
                # Write modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Added font handling code to: {file_path}")
    
    # Replace Unicode stars with ASCII stars
    unicode_replacements = [
        ('⭐', '*'),
        ('★', '*'),
        ('↑', '^'),
        ('↓', 'v')
    ]
    
    for file_path in target_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            for unicode_char, ascii_char in unicode_replacements:
                if unicode_char in content:
                    content = content.replace(unicode_char, ascii_char)
                    modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Replaced Unicode characters in: {file_path}")
    
    print("Font configuration fixed successfully")

if __name__ == "__main__":
    fix_matplotlib_fonts() 