#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
热门行业分析方法修复
"""

import os
import sys
import re

def apply_fix():
    """应用修复"""
    file_path = 'enhanced_sector_analyzer.py'
    
    if not os.path.exists(file_path):
        print(f"找不到文件: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找get_hot_sectors方法的结果构建部分
    pattern = r'(result\s*=\s*\{\s*\'status\'\s*:\s*\'success\'\s*,\s*\'data\'\s*:\s*\{.*?\'hot_sectors\'\s*:\s*hot_sectors\s*,)'
    
    if not re.search(pattern, content, re.DOTALL):
        print("无法找到要修改的模式")
        return False
    
    # 添加market_trend字段
    replacement = r'\1\n                # 添加市场趋势信息\n                \'market_trend\': market_data.get(\'trend\', \'neutral\'),\n                \'market_chg_pct\': market_data.get(\'change_percent\', 0.0),'
    
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 查找市场数据获取部分，确保存在market_data变量
    market_data_pattern = r'def get_hot_sectors.*?hot_sectors\s*=\s*\['
    
    market_data_code = """
            # 获取市场整体趋势数据
            market_data = {}
            try:
                index_data = self.pro.index_daily(ts_code='000001.SH', start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
                if index_data is not None and not index_data.empty:
                    # 计算大盘趋势
                    latest = index_data.iloc[0]
                    prev = index_data.iloc[min(5, len(index_data)-1)]
                    change_percent = (latest['close'] - prev['close']) / prev['close'] * 100
                    
                    # 确定趋势
                    if change_percent > 5:
                        trend = 'strong_bull'
                    elif change_percent > 2:
                        trend = 'bull'
                    elif change_percent < -5:
                        trend = 'strong_bear'
                    elif change_percent < -2:
                        trend = 'bear'
                    else:
                        trend = 'neutral'
                        
                    market_data = {
                        'trend': trend,
                        'change_percent': change_percent,
                        'latest_close': latest['close'],
                        'prev_close': prev['close']
                    }
            except Exception as e:
                self.logger.warning(f"获取市场趋势数据失败: {e}")
                
            # 获取热门行业
            hot_sectors = [
"""
    
    if 'market_data = {}' not in content:
        updated_content = re.sub(market_data_pattern, lambda m: m.group(0).replace('hot_sectors = [', market_data_code), updated_content, flags=re.DOTALL)
    
    # 保存修改后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"已成功修复 {file_path}")
    return True

if __name__ == "__main__":
    apply_fix() 