#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
热门行业分析命令行工具
用于在命令行直接分析和查看热门行业
"""

import sys
import argparse
import time
from datetime import datetime
import pandas as pd

# 尝试导入必要的组件
try:
    from tushare_sector_provider import get_sector_provider
    from sector_analyzer import SectorAnalyzer
    HAS_OPTIMIZED = True
except ImportError:
    HAS_OPTIMIZED = False
    try:
        from optimized_sector_analyzer import OptimizedSectorAnalyzer as SectorAnalyzer
    except ImportError:
        print("错误: 未找到行业分析器模块，请确保已正确安装")
        sys.exit(1)

# 设置彩色输出
try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # 创建替代的颜色类
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()

def color_text(text, color_code, is_bold=False):
    """为文本添加颜色"""
    if not HAS_COLOR:
        return text
    bold = Style.BRIGHT if is_bold else ""
    return f"{bold}{color_code}{text}{Style.RESET_ALL}"

def format_change_pct(pct):
    """格式化涨跌幅，添加颜色"""
    if pct > 0:
        return color_text(f"+{pct:.2f}%", Fore.RED, True)
    elif pct < 0:
        return color_text(f"{pct:.2f}%", Fore.GREEN, True)
    else:
        return color_text(f"{pct:.2f}%", Fore.WHITE)

def print_header(text):
    """打印带有装饰的标题"""
    width = 60
    print("\n" + "=" * width)
    print(color_text(text.center(width), Fore.CYAN, True))
    print("=" * width)

def analyze_hot_sectors(token=None, top_n=15, show_details=True, save_result=False):
    """分析热门行业"""
    print_header("热门行业分析")
    
    start_time = time.time()
    
    # 初始化行业分析器
    try:
        # 优先尝试使用优化版行业分析器
        if HAS_OPTIMIZED:
            print("使用优化版行业分析器")
            sector_analyzer = SectorAnalyzer(top_n=top_n, token=token)
        else:
            print("使用标准版行业分析器")
            sector_analyzer = SectorAnalyzer(top_n=top_n)
        
        # 获取热门行业
        print("正在分析热门行业...")
        result = sector_analyzer.analyze_hot_sectors()
        
        if result['status'] != 'success':
            print(color_text(f"分析失败: {result['message']}", Fore.RED))
            return
        
        end_time = time.time()
        print(f"分析完成，耗时: {end_time - start_time:.2f}秒")
        
        # 打印分析结果
        hot_sectors = result['data']['hot_sectors']
        north_flow = result['data'].get('north_flow', 0)
        
        print("\n" + color_text("【市场概览】", Fore.YELLOW, True))
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"北向资金流入: {format_change_pct(north_flow)}")
        
        # 检查真实数据和模拟数据的数量
        real_data_count = sum(1 for s in hot_sectors if not s.get('is_mock_data', False))
        mock_data_count = len(hot_sectors) - real_data_count
        
        if mock_data_count > 0:
            print(color_text(f"⚠️ 警告: 当前分析包含 {mock_data_count} 个模拟数据，{real_data_count} 个真实数据", Fore.YELLOW))
            print(color_text("模拟数据用于在无法获取真实数据时保持系统运行，结果仅供参考", Fore.YELLOW))
        else:
            print(color_text("✅ 所有数据均为真实数据", Fore.GREEN))
        
        # 打印热门行业排名
        print("\n" + color_text("【热门行业排名】", Fore.YELLOW, True))
        print(f"{'排名':4} {'行业名称':10} {'热度':8} {'涨跌幅':10} {'成交量(亿)':10} {'数据来源':8}")
        print("-" * 60)
        
        for i, sector in enumerate(hot_sectors, 1):
            # 获取属性，处理可能不存在的键
            name = sector['name']
            hot_score = sector.get('hot_score', 0)
            change_pct = sector.get('change_pct', 0)
            volume = sector.get('volume', 0)
            is_mock = sector.get('is_mock_data', False)
            
            # 格式化输出
            source_tag = color_text("[模拟]", Fore.YELLOW) if is_mock else color_text("[真实]", Fore.GREEN)
            
            print(f"{i:2}   {name:10} {hot_score:8.2f} {format_change_pct(change_pct):10} "
                  f"{volume:10.2f} {source_tag:8}")
        
        # 打印详细分析（可选）
        if show_details and hot_sectors:
            print("\n" + color_text("【详细分析】", Fore.YELLOW, True))
            for i, sector in enumerate(hot_sectors[:5], 1):  # 只显示前5个的详细分析
                print(f"\n{i}. {color_text(sector['name'], Fore.CYAN, True)}:")
                print(f"   热度得分: {sector.get('hot_score', 0):.2f}")
                print(f"   涨跌幅: {format_change_pct(sector.get('change_pct', 0))}")
                
                if 'analysis_reason' in sector:
                    print(f"   分析: {sector['analysis_reason']}")
                
                # 标记数据来源
                source = color_text("模拟数据", Fore.YELLOW) if sector.get('is_mock_data', False) else color_text("真实数据", Fore.GREEN)
                print(f"   数据来源: {source}")
                
                # 技术指标
                if 'macd' in sector:
                    macd_color = Fore.RED if sector['macd'] > 0 else Fore.GREEN
                    print(f"   MACD: {color_text(f'{sector['macd']:.4f}', macd_color)}")
                
                if 'volatility' in sector:
                    print(f"   波动率: {sector['volatility']:.2f}%")
                    
                print("-" * 40)
        
        # 保存结果（可选）
        if save_result:
            save_path = f"hot_sectors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            try:
                # 转换为DataFrame
                df = pd.DataFrame(hot_sectors)
                df.to_csv(save_path, index=False, encoding='utf-8-sig')
                print(f"\n分析结果已保存到: {save_path}")
            except Exception as e:
                print(f"保存结果失败: {e}")
        
        return hot_sectors
    
    except Exception as e:
        print(color_text(f"分析过程中出错: {e}", Fore.RED))
        import traceback
        print(traceback.format_exc())
        return None

def predict_hot_sectors(token=None, top_n=5):
    """预测未来热门行业"""
    print_header("热门行业走势预测")
    
    # 初始化行业分析器
    try:
        if HAS_OPTIMIZED:
            sector_analyzer = SectorAnalyzer(top_n=top_n, token=token)
        else:
            sector_analyzer = SectorAnalyzer(top_n=top_n)
        
        # 获取预测结果
        print("正在预测热门行业走势...")
        result = sector_analyzer.predict_next_hot_sectors()
        
        if result['status'] != 'success':
            print(color_text(f"预测失败: {result['message']}", Fore.RED))
            return
        
        # 打印预测结果
        predictions = result['data']['predicted_sectors']
        
        print("\n" + color_text("【行业预测结果】", Fore.YELLOW, True))
        print(f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"预测周期: {result['data'].get('prediction_period', '未来7天')}")
        
        print(f"\n{'排名':4} {'行业名称':10} {'预测评分':8} {'预测理由':30}")
        print("-" * 60)
        
        for i, pred in enumerate(predictions, 1):
            name = pred['name']
            
            # 获取预测评分，可能用不同的字段名
            score = 0
            for score_field in ['prediction_score', 'technical_score', 'score']:
                if score_field in pred:
                    score = pred[score_field]
                    break
            
            # 获取预测理由
            reason = pred.get('reason', '')[:30]  # 截断过长的理由
            
            print(f"{i:2}   {name:10} {score:8.2f} {reason:30}")
        
        # 输出结论
        if predictions:
            print("\n" + color_text("【预测结论】", Fore.YELLOW, True))
            top_sector = predictions[0]['name']
            print(f"预计 {top_sector} 将在近期表现较好，建议重点关注")
            
            if len(predictions) > 1:
                other_sectors = ", ".join([s['name'] for s in predictions[1:3]])
                print(f"同时可以关注: {other_sectors}")
            
            print("\n" + color_text("⚠️ 声明：预测仅供参考，投资有风险，入市需谨慎", Fore.RED))
        
        return predictions
    
    except Exception as e:
        print(color_text(f"预测过程中出错: {e}", Fore.RED))
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="热门行业分析命令行工具")
    parser.add_argument("--analyze", action="store_true", help="分析当前热门行业")
    parser.add_argument("--predict", action="store_true", help="预测未来热门行业")
    parser.add_argument("--token", type=str, help="Tushare API token")
    parser.add_argument("--top", type=int, default=10, help="显示的行业数量")
    parser.add_argument("--save", action="store_true", help="保存分析结果到CSV文件")
    parser.add_argument("--details", action="store_true", help="显示详细分析信息")
    
    args = parser.parse_args()
    
    # 如果没有指定操作，默认进行分析
    if not args.analyze and not args.predict:
        args.analyze = True
    
    # 执行行业分析
    if args.analyze:
        analyze_hot_sectors(token=args.token, top_n=args.top, 
                           show_details=args.details, save_result=args.save)
    
    # 执行行业预测
    if args.predict:
        predict_hot_sectors(token=args.token, top_n=args.top)
    
    print("\n感谢使用热门行业分析工具！")

if __name__ == "__main__":
    main() 