import sys
import argparse
import os
import traceback
from PyQt5.QtWidgets import QApplication
from stock_analyzer_app import StockAnalyzerApp
from visual_stock_system import VisualStockSystem
from stock_selector import main as run_stock_selector
from single_stock_analyzer import SingleStockAnalyzer
from stock_review import StockReview

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票分析系统')
    parser.add_argument('--cli', action='store_true', help='在命令行模式下运行')
    parser.add_argument('--scan', action='store_true', help='扫描市场并推荐股票')
    parser.add_argument('--analyze', type=str, help='分析单只股票，例如：000001.SZ')
    parser.add_argument('--top', type=int, default=15, help='推荐股票数量')
    parser.add_argument('--token', type=str, help='API令牌')
    parser.add_argument('--review', action='store_true', help='运行复盘模块')
    parser.add_argument('--add-to-review', action='store_true', help='将扫描结果添加到复盘股票池')
    parser.add_argument('--backtest-review', action='store_true', help='回测复盘股票池')
    return parser.parse_args()

def analyze_single_stock(stock_code, token=None):
    """分析单只股票"""
    try:
        # 使用SingleStockAnalyzer而不是直接使用VisualStockSystem
        analyzer = SingleStockAnalyzer(token)
        result = analyzer.get_detailed_analysis(stock_code)
        
        # 如果SingleStockAnalyzer失败，尝试使用VisualStockSystem作为备选
        if result['status'] != 'success':
            print(f"使用单股分析器失败，正在尝试备选方式分析...")
            system = VisualStockSystem(token, headless=True)
            analysis, _ = system.analyze_stock(stock_code)
            if analysis:
                result = {
                    'status': 'success',
                    'data': {
                        'name': analysis['name'],
                        'last_price': analysis['close'],
                        'trend_analysis': analysis['trend_analysis'],
                        'volume_analysis': analysis['volume_analysis'],
                        'technical_indicators': analysis['technical_indicators'],
                        'trading_advice': analysis.get('trading_advice', {}).get('action', '观望')
                    }
                }
            else:
                return False
        
        if result['status'] == 'success':
            print(f"\n===== {result['data']['name']} ({stock_code}) 分析结果 =====")
            print(f"当前价格: {result['data']['last_price']}")
            print(f"趋势分析: {result['data']['trend_analysis']['trend']} (强度: {result['data']['trend_analysis']['strength']}%)")
            print(f"量价分析: {result['data']['volume_analysis']['status']} (量比: {result['data']['volume_analysis']['ratio']})")
            
            # 技术指标格式化 - 修复格式化错误
            macd_value = 0
            if isinstance(result['data']['technical_indicators'], dict):
                if isinstance(result['data']['technical_indicators']['macd'], dict):
                    macd_value = result['data']['technical_indicators']['macd'].get('hist', 0)
                else:
                    macd_value = result['data']['technical_indicators']['macd']
            else:
                macd_value = result['data']['technical_indicators'].get('macd', {}).get('hist', 0)
                
            rsi_value = result['data']['trend_analysis'].get('rsi_value', 50)
            
            print(f"技术指标: MACD={macd_value:.3f}, RSI={rsi_value:.2f}")
            print(f"交易建议: {result['data']['trading_advice']}")
            return True
        else:
            print(f"分析失败: {result['message']}")
            return False
    except Exception as e:
        print(f"分析股票时发生错误: {str(e)}")
        traceback.print_exc()
        return False

def run_gui_mode(args):
    """运行GUI模式"""
    try:
        app = QApplication(sys.argv)
        window = StockAnalyzerApp()
        print('成功创建主窗口实例')
        window.show()
        print('主窗口已触发显示事件')
        return app.exec()
    except Exception as e:
        print(f'GUI初始化失败: {str(e)}')
        traceback.print_exc()
        return 1

def main():
    """主函数"""
    # 设置工作目录为脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 获取API令牌
    token = args.token or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
    
    # 根据参数决定运行模式
    if args.cli:
        print("以命令行模式运行股票分析系统")
        if args.analyze:
            return 0 if analyze_single_stock(args.analyze, token) else 1
        elif args.scan:
            print("扫描市场并推荐股票...")
            # 创建可视化股票系统实例
            system = VisualStockSystem(token, headless=True)
            from stock_selector import get_all_stocks, filter_stocks
            
            # 获取所有股票
            stocks = get_all_stocks()
            if stocks.empty:
                print("无法获取股票列表，程序终止")
                return 1
            
            print(f"开始扫描分析 {len(stocks)} 只股票，请耐心等待...")
            print("=" * 50)
            
            # 筛选出最符合条件的股票
            top_stocks = filter_stocks(system, stocks, args.top)
            
            print("=" * 50)
            
            if not top_stocks:
                print("未找到符合条件的股票，请调整筛选参数")
                return 1
            
            # 打印推荐结果
            print("\n===== 推荐股票 =====")
            if hasattr(system, 'print_recommendations'):
                system.print_recommendations(top_stocks)
            else:
                # 如果方法不存在，提供默认实现
                print("推荐股票列表:")
                for idx, stock in enumerate(top_stocks, 1):
                    print(f"{idx}. {stock.get('name', 'N/A')}({stock.get('symbol', 'N/A')}): {stock.get('price', 0):.2f}元")
                    print(f"   趋势: {stock.get('trend', 'N/A')}, 评分: {stock.get('total_score', 0):.2f}")
                    print(f"   推荐理由: {stock.get('recommendation', 'N/A')}")
            
            # 如果需要添加到复盘股票池
            if args.add_to_review:
                review_system = StockReview(token)
                count = review_system.add_recommendations_to_pool(top_stocks)
                print(f"已添加 {count} 只强烈推荐买入的股票到复盘池")
            
            return 0
        elif args.review:
            # 运行复盘模块
            print("运行股票复盘模块...")
            from stock_review import main as run_stock_review
            run_stock_review()
            return 0
        elif args.backtest_review:
            # 回测复盘股票池
            print("回测复盘股票池...")
            review_system = StockReview(token)
            results = review_system.backtest_review_pool()
            if results:
                print("\n===== 回测结果 =====")
                print(f"总收益率: {results['total_return']}%")
                print(f"年化收益率: {results['annual_return']}%")
                print(f"最大回撤: {results['max_drawdown']}%")
                print(f"夏普比率: {results['sharpe_ratio']}")
            return 0
        else:
            print("请指定要执行的操作: --scan, --analyze STOCK_CODE, --review 或 --backtest-review")
            return 1
    else:
        # 默认运行GUI模式
        print("以GUI模式运行股票分析系统")
        return run_gui_mode(args)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        traceback.print_exc()
        sys.exit(1)