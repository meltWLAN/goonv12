#!/bin/bash

# 股票分析系统启动脚本

echo "正在启动股票分析系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3。请确保已安装Python 3.8或更高版本。"
    exit 1
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "使用虚拟环境..."
    source venv/bin/activate
fi

# 启动应用
python3 app.py

# 退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "系统异常退出，退出代码: $EXIT_CODE"
    exit $EXIT_CODE
fi 