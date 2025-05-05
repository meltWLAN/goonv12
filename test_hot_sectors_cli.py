#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试热门行业分析CLI工具
"""

import sys
import os

def main():
    # 设置Tushare Token
    token = "0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10"
    
    # 运行热门行业分析CLI
    print("运行热门行业分析CLI...")
    os.system(f"python hot_sector_cli.py --analyze --predict --token {token} --details")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 