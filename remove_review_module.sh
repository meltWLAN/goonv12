#!/bin/bash

# 创建备份目录
BACKUP_DIR="./backup_review_module_$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 复盘相关文件列表
REVIEW_FILES=(
    "./test_review_pool.py"
    "./enhanced_stock_review_20250426105053.py.bak"
    "./smart_review_data/smart_review_pool.json"
    "./cache/review_pool.json"
    "./fix_stock_review_simple.py"
    "./enhanced_stock_review.py"
    "./test_stock_review_fix.py"
    "./stock_review.py"
    "./fix_review_pool.log"
    "./stock_review_fix_test.log"
    "./fix_stock_review.py"
    "./enhanced_review_pool.json"
    "./enhanced_stock_review_fix.py"
    "./fix_review_pool.py"
    "./review_pool.json"
    "./review_pool_ui.py"
    "./show_review_pool.py"
    "./enhanced_stock_review.log"
)

# 备份并删除复盘相关文件
echo "正在备份并删除复盘相关文件..."
for file in "${REVIEW_FILES[@]}"; do
    if [ -f "$file" ]; then
        # 创建目标目录
        dir=$(dirname "$file")
        mkdir -p "$BACKUP_DIR/$dir"
        
        # 复制文件到备份目录
        cp "$file" "$BACKUP_DIR/$file"
        echo "已备份: $file"
        
        # 删除原文件
        rm "$file"
        echo "已删除: $file"
    fi
done

# 清理__pycache__中的复盘相关.pyc文件
echo "正在清理__pycache__中的复盘相关文件..."
find ./__pycache__ -name "*stock_review*" -o -name "*review*" | while read file; do
    cp "$file" "$BACKUP_DIR/__pycache__/"
    rm "$file"
    echo "已删除: $file"
done

echo "复盘模块清理完成！所有文件已备份到: $BACKUP_DIR"
echo "您可以通过执行以下命令恢复文件(如果需要):"
echo "cp -r $BACKUP_DIR/* ./" 