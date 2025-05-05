#!/bin/bash

# 清理热门行业相关的所有配置文件、缓存和日志
echo "开始清理热门行业相关文件..."

# 清理缓存文件
if [ -d "data_cache" ]; then
    echo "清理缓存目录..."
    find data_cache -name "*sector*" -type f -delete
    find data_cache -name "*hot*" -type f -delete
    echo "缓存清理完成"
fi

# 清理日志文件
echo "清理日志文件..."
find . -name "*sector*.log" -type f -delete
find . -name "*enhanced_sector*.log" -type f -delete
echo "日志清理完成"

# 清理测试文件
echo "清理测试数据..."
find . -name "*hot_sectors_diagnostic*.json" -type f -delete
find . -name "sector_diagnosis_*.json" -type f -delete
echo "测试数据清理完成"

# 清理备份文件
echo "清理备份文件..."
find . -name "*sector*.bak" -type f -delete
echo "备份文件清理完成"

# 清理集成文件
echo "清理集成文件..."
rm -f integration_status.json 2>/dev/null

echo "清理完成！所有热门行业相关的配置文件、缓存和日志已被移除。" 