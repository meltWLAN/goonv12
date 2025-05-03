#!/bin/bash

# 股票分析系统启动脚本
# 这个脚本设置所有必要的环境变量并启动系统

# 设置Qt环境变量
export QT_MAC_WANTS_LAYER=1
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_ENABLE_HIGHDPI_SCALING=1
export PYTHONIOENCODING=utf-8

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查是否有Python虚拟环境
if [ -d "venv" ]; then
    echo "使用虚拟环境..."
    source venv/bin/activate
fi

# 启动系统
echo "正在启动股票分析系统..."
python app.py

# 如果app.py启动失败，尝试直接启动GUI
if [ $? -ne 0 ]; then
    echo "尝试直接启动GUI..."
    python stock_analysis_gui.py
fi

echo "股票分析系统已退出" 