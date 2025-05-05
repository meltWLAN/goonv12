#!/bin/bash
# 安装行业分析模块依赖包

echo "正在安装系统依赖..."

# 检查是否已安装pip
if ! command -v pip &> /dev/null; then
    echo "未找到pip，请先安装Python和pip"
    exit 1
fi

# 创建一个临时目录存放日志
mkdir -p ./logs
log_file="./logs/install_log_$(date +%Y%m%d_%H%M%S).txt"

echo "安装基础依赖包..."
pip install numpy pandas matplotlib -q || {
    echo "安装基础依赖包失败"
    exit 1
}

echo "安装tushare..."
pip install tushare -q || {
    echo "安装tushare失败，请检查网络连接"
    echo "详细错误信息已记录到 $log_file"
    exit 1
} 2>> "$log_file"

echo "安装talib依赖..."
pip install ta-lib -q || {
    echo "尝试替代安装方式..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS安装方式
        brew install ta-lib || {
            echo "通过brew安装ta-lib失败"
            exit 1
        }
        pip install ta-lib -q || {
            echo "安装ta-lib Python包失败"
            exit 1
        }
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux安装方式
        sudo apt-get update
        sudo apt-get install -y ta-lib || {
            echo "通过apt安装ta-lib失败"
            exit 1
        }
        pip install ta-lib -q || {
            echo "安装ta-lib Python包失败"
            exit 1
        }
    else
        echo "未知操作系统，请手动安装ta-lib"
        exit 1
    fi
}

echo "安装其他必要依赖..."
pip install requests pandas-ta tqdm scikit-learn statsmodels -q || {
    echo "安装其他依赖包失败"
    exit 1
}

echo "依赖安装完成！"
echo "系统已准备就绪，可以运行行业分析模块了。" 