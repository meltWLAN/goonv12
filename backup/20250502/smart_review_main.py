#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from datetime import datetime, timedelta
import logging
import traceback

from smart_review_core import SmartReviewCore
from strategy_optimization_engine import StrategyOptimizationEngine

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("smart_review_system.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmartReviewSystem")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='智能复盘系统')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 分析子命令
    analyze_parser = subparsers.add_parser('analyze', help='分析复盘池中的股票')
    analyze_parser.add_argument('--min-score', type=int, default=0, help='最低分数阈值')
    
    # 添加股票子命令
    add_parser = subparsers.add_parser('add', help='添加股票到复盘池')
    add_parser.add_argument('symbol', help='股票代码，例如：000001.SZ')
    add_parser.add_argument('--name', help='股票名称')
    add_parser.add_argument('--tags', help='标签，用逗号分隔')
    add_parser.add_argument('--notes', help='备注')
    
    # 显示股票子命令
    show_parser = subparsers.add_parser('show', help='显示复盘池中的股票')
    show_parser.add_argument('--status', choices=['watching', 'bought', 'half_bought', 'half_sold', 'sold'], 
                              help='按状态筛选')
    show_parser.add_argument('--min-score', type=int, default=0, help='最低分数阈值')
    show_parser.add_argument('--symbol', help='指定股票代码')
    
    # 更新股票状态子命令
    update_parser = subparsers.add_parser('update', help='更新股票状态')
    update_parser.add_argument('symbol', help='股票代码')
    update_parser.add_argument('status', choices=['watching', 'bought', 'half_bought', 'half_sold', 'sold'], 
                              help='新状态')
    update_parser.add_argument('--price', type=float, help='交易价格')
    update_parser.add_argument('--notes', help='备注')
    
    # 获取推荐子命令
    recommend_parser = subparsers.add_parser('recommend', help='获取推荐股票')
    recommend_parser.add_argument('--count', type=int, default=5, help='推荐数量')
    recommend_parser.add_argument('--min-score', type=int, default=70, help='最低分数阈值')
    
    # 回测子命令
    backtest_parser = subparsers.add_parser('backtest', help='回测策略')
    backtest_parser.add_argument('strategy', help='策略ID')
    backtest_parser.add_argument('symbol', help='股票代码')
    backtest_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    backtest_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    
    # 参数优化子命令
    optimize_parser = subparsers.add_parser('optimize', help='优化策略参数')
    optimize_parser.add_argument('strategy', help='策略ID')
    optimize_parser.add_argument('symbol', help='股票代码')
    optimize_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    optimize_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    
    # 查看策略子命令
    strategy_parser = subparsers.add_parser('strategies', help='查看可用策略')
    
    # 绩效统计子命令
    performance_parser = subparsers.add_parser('performance', help='查看交易绩效')
    
    # 交易历史子命令
    history_parser = subparsers.add_parser('history', help='查看交易历史')
    history_parser.add_argument('--symbol', help='按股票代码筛选')
    
    # 批量添加子命令
    batch_add_parser = subparsers.add_parser('batch-add', help='批量添加股票到复盘池')
    batch_add_parser.add_argument('file', help='包含股票代码的文件路径')
    
    # 批量回测子命令
    batch_backtest_parser = subparsers.add_parser('batch-backtest', help='批量回测策略')
    batch_backtest_parser.add_argument('strategy', help='策略ID')
    batch_backtest_parser.add_argument('--symbols', help='股票代码，用逗号分隔')
    batch_backtest_parser.add_argument('--file', help='包含股票代码的文件路径')
    batch_backtest_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    batch_backtest_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    
    # 共同参数
    parser.add_argument('--token', help='API令牌')
    parser.add_argument('--data-dir', default='./smart_review_data', help='数据目录')
    
    
    # LazyStockAnalyzer模式
    parser.add_argument('--lazy-mode', dest='lazy_mode', action='store_true', 
                        help='使用LazyStockAnalyzer的按需计算模式(默认)')
    parser.add_argument('--no-lazy-mode', dest='lazy_mode', action='store_false',
                        help='使用全量计算模式')
    parser.set_defaults(lazy_mode=True)
return parser.parse_args()

def print_stock_info(stock):
    """打印股票信息"""
    print(f"\n{stock['name']} ({stock['symbol']})")
    print(f"状态: {stock['status']}")
    print(f"智能评分: {stock.get('smart_score', 'N/A')}")
    print(f"添加日期: {stock.get('date_added', 'N/A')}")
    
    if 'analysis' in stock and stock['analysis']:
        analysis = stock['analysis']
        print("\n分析信息:")
        print(f"趋势: {analysis.get('trend', 'N/A')}")
        print(f"成交量比率: {analysis.get('volume_ratio', 'N/A')}")
        print(f"MACD直方图: {analysis.get('macd_hist', 'N/A')}")
        print(f"RSI: {analysis.get('rsi', 'N/A')}")
        print(f"推荐: {analysis.get('recommendation', 'N/A')}")
        print(f"最新价格: {analysis.get('last_price', 'N/A')}")
        print(f"最后分析日期: {analysis.get('last_date', 'N/A')}")
    
    if stock.get('trade_history'):
        print("\n交易历史:")
        for trade in stock['trade_history']:
            print(f"[{trade.get('date', 'N/A')}] {trade.get('status_from', 'N/A')} -> {trade.get('status_to', 'N/A')}, 价格: {trade.get('price', 'N/A')}")
            if trade.get('notes'):
                print(f"  备注: {trade['notes']}")
    
    if stock.get('tags'):
        print(f"\n标签: {', '.join(stock['tags'])}")
    
    if stock.get('notes'):
        print(f"\n备注:\n{stock['notes']}")
    
    print('-' * 50)

def print_strategy_info(strategy):
    """打印策略信息"""
    print(f"\n{strategy['name']} ({strategy['id']})")
    print(f"描述: {strategy['description']}")
    print('-' * 50)

def print_performance_metrics(metrics):
    """打印绩效指标"""
    print("\n===== 绩效统计 =====")
    print(f"总交易次数: {metrics.get('trade_count', 0)}")
    print(f"胜率: {metrics.get('win_rate', 0)}%")
    print(f"总收益率: {metrics.get('total_profit', 0)}%")
    print(f"平均收益率: {metrics.get('avg_profit', 0)}%")
    print(f"最大盈利: {metrics.get('max_profit', 0)}%")
    print(f"最大亏损: {metrics.get('min_profit', 0)}%")
    print(f"最大回撤: {metrics.get('max_drawdown', 0)}%")
    print(f"夏普比率: {metrics.get('sharpe_ratio', 0)}")
    print('-' * 50)

def print_trade_history(trade):
    """打印交易历史"""
    print(f"\n{trade['name']} ({trade['symbol']})")
    print(f"买入日期: {trade.get('buy_date', 'N/A')}")
    print(f"买入价格: {trade.get('buy_price', 'N/A')}")
    print(f"卖出日期: {trade.get('sell_date', 'N/A')}")
    print(f"卖出价格: {trade.get('sell_price', 'N/A')}")
    print(f"盈利率: {trade.get('profit_percent', 'N/A')}%")
    print(f"持有天数: {trade.get('holding_days', 'N/A')}")
    
    if trade.get('tags'):
        print(f"标签: {', '.join(trade['tags'])}")
    
    if trade.get('notes'):
        print(f"备注: {trade['notes']}")
    
    print('-' * 50)

def print_optimization_result(result):
    """打印优化结果"""
    print("\n===== 策略优化结果 =====")
    print(f"策略: {result['strategy_name']} ({result['strategy_id']})")
    print(f"股票: {result['symbol']}")
    print(f"时间范围: {result['start_date']} 至 {result['end_date']}")
    print(f"优化时间: {result['optimization_time']}")
    
    print("\n最佳参数组合:")
    for param, value in result['best_parameters'].items():
        print(f"  {param}: {value}")
    
    print("\n最佳性能指标:")
    performance = result['best_performance']
    print(f"  总收益率: {performance['total_return']}%")
    print(f"  夏普比率: {performance['sharpe_ratio']}")
    print(f"  最大回撤: {performance['max_drawdown']}%")
    print(f"  胜率: {performance['win_rate']}%")
    print(f"  交易次数: {performance['trade_count']}")
    
    print("\n前10个参数组合:")
    for i, result_item in enumerate(result['all_results'], 1):
        print(f"\n组合 {i}:")
        print(f"  参数: {result_item['parameters']}")
        print(f"  总收益率: {result_item['total_return']}%")
        print(f"  夏普比率: {result_item['sharpe_ratio']}")
        print(f"  最大回撤: {result_item['max_drawdown']}%")
    
    print('-' * 50)

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # 获取API令牌
        token = args.token or '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        
        # 初始化系统组件
        review_core = SmartReviewCore(token=token, data_dir=args.data_dir, lazy_mode=args.lazy_mode)
        strategy_engine = StrategyOptimizationEngine(token=token, data_dir=os.path.join(args.data_dir, 'strategy_data'))
        
        # 根据子命令执行相应操作
        if args.command == 'analyze':
            logger.info("分析复盘池中的股票")
            results = review_core.analyze_all_stocks_in_pool()
            
            print(f"\n分析完成，成功: {results['success_count']}，失败: {results['fail_count']}")
            print(f"分数上升: {results['improved_count']}，分数下降: {results['declined_count']}")
            
            print("\n分析结果:")
            for stock in results['stocks']:
                if stock['smart_score'] >= args.min_score:
                    print(f"{stock['name']} ({stock['symbol']}) - 评分: {stock['smart_score']} ({'+' if stock['score_change'] > 0 else ''}{stock['score_change']})")
                    print(f"  推荐: {stock['recommendation']}")
        
        elif args.command == 'add':
            logger.info(f"添加股票 {args.symbol} 到复盘池")
            
            # 准备股票信息
            stock_info = {
                'symbol': args.symbol,
                'name': args.name,
                'notes': args.notes
            }
            
            if args.tags:
                stock_info['tags'] = args.tags.split(',')
            
            # 如果没有提供名称，尝试获取
            if not args.name:
                try:
                    stock_data = review_core.data_provider.get_stock_info(args.symbol)
                    if not stock_data.empty:
                        stock_info['name'] = stock_data.iloc[0]['name']
                except:
                    print(f"警告: 无法获取股票 {args.symbol} 的名称")
            
            # 添加股票
            success = review_core.add_stock_to_review(stock_info)
            
            if success:
                print(f"成功添加股票 {args.symbol} 到复盘池")
            else:
                print(f"添加股票 {args.symbol} 失败")
        
        elif args.command == 'show':
            logger.info("显示复盘池中的股票")
            
            if args.symbol:
                stocks = review_core.get_stock_from_pool(symbol=args.symbol)
                if stocks:
                    print_stock_info(stocks[0])
                else:
                    print(f"未找到股票 {args.symbol}")
            else:
                stocks = review_core.get_stock_from_pool(status=args.status, min_score=args.min_score)
                
                if not stocks:
                    print("复盘池为空或没有符合条件的股票")
                else:
                    print(f"\n找到 {len(stocks)} 只股票:")
                    for stock in stocks:
                        print_stock_info(stock)
        
        elif args.command == 'update':
            logger.info(f"更新股票 {args.symbol} 的状态为 {args.status}")
            
            success = review_core.update_stock_status(
                args.symbol, 
                args.status,
                price=args.price,
                notes=args.notes
            )
            
            if success:
                print(f"成功更新股票 {args.symbol} 的状态为 {args.status}")
            else:
                print(f"更新股票 {args.symbol} 的状态失败")
        
        elif args.command == 'recommend':
            logger.info("获取推荐股票")
            
            recommendations = review_core.get_top_recommendations(
                count=args.count,
                min_score=args.min_score
            )
            
            if not recommendations:
                print("没有推荐股票")
            else:
                print(f"\n找到 {len(recommendations)} 只推荐股票:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. {rec['name']} ({rec['symbol']})")
                    print(f"   智能评分: {rec['smart_score']}")
                    print(f"   推荐: {rec['recommendation']}")
                    print(f"   趋势: {rec['trend']}")
                    print(f"   最新价格: {rec['last_price']}")
                    print(f"   成交量比率: {rec['volume_ratio']}")
                    print('-' * 30)
        
        elif args.command == 'backtest':
            logger.info(f"回测策略 {args.strategy} 在股票 {args.symbol} 上的表现")
            
            result = strategy_engine.backtest_strategy(
                args.strategy,
                args.symbol,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if result['status'] == 'success':
                data = result['data']
                print(f"\n回测成功: {args.strategy} 策略 在 {args.symbol} 上")
                print(f"时间范围: {data['start_date']} 至 {data['end_date']}")
                print(f"总收益率: {data.get('total_return', 0)}%")
                print(f"夏普比率: {data.get('sharpe_ratio', 0)}")
                print(f"最大回撤: {data.get('max_drawdown', 0)}%")
                print(f"胜率: {data.get('win_rate', 0)}%")
                print(f"交易次数: {data.get('trade_count', 0)}")
            else:
                print(f"回测失败: {result['message']}")
        
        elif args.command == 'optimize':
            logger.info(f"优化策略 {args.strategy} 在股票 {args.symbol} 上的参数")
            
            result = strategy_engine.optimize_strategy(
                args.strategy,
                args.symbol,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if result['status'] == 'success':
                print_optimization_result(result['data'])
            else:
                print(f"参数优化失败: {result['message']}")
        
        elif args.command == 'strategies':
            logger.info("查看可用策略")
            
            strategies = strategy_engine.get_available_strategies()
            
            if not strategies:
                print("没有可用策略")
            else:
                print(f"\n找到 {len(strategies)} 个可用策略:")
                for strategy in strategies:
                    print_strategy_info(strategy)
        
        elif args.command == 'performance':
            logger.info("查看交易绩效")
            
            metrics = review_core.get_performance_metrics()
            print_performance_metrics(metrics)
        
        elif args.command == 'history':
            logger.info("查看交易历史")
            
            trades = review_core.get_trade_history(symbol=args.symbol)
            
            if not trades:
                print("没有交易历史记录")
            else:
                print(f"\n找到 {len(trades)} 条交易记录:")
                for trade in trades:
                    print_trade_history(trade)
        
        elif args.command == 'batch-add':
            logger.info(f"批量添加股票，来源文件: {args.file}")
            
            if not os.path.exists(args.file):
                print(f"文件 {args.file} 不存在")
                return
            
            with open(args.file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            symbols = [line.strip() for line in lines if line.strip()]
            
            success_count = 0
            for symbol in symbols:
                try:
                    # 可能包含附加信息，如 000001.SZ,平安银行
                    parts = symbol.split(',')
                    symbol_code = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else None
                    
                    stock_info = {'symbol': symbol_code}
                    if name:
                        stock_info['name'] = name
                    
                    if review_core.add_stock_to_review(stock_info):
                        success_count += 1
                        print(f"添加 {symbol_code} 成功")
                    else:
                        print(f"添加 {symbol_code} 失败")
                except Exception as e:
                    print(f"处理 {symbol} 时出错: {str(e)}")
            
            print(f"\n批量添加完成，成功: {success_count}，总计: {len(symbols)}")
        
        elif args.command == 'batch-backtest':
            logger.info(f"批量回测策略 {args.strategy}")
            
            symbols = []
            if args.symbols:
                symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
            elif args.file and os.path.exists(args.file):
                with open(args.file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                symbols = [line.strip().split(',')[0].strip() for line in lines if line.strip()]
            
            if not symbols:
                print("没有提供股票代码")
                return
            
            print(f"开始批量回测，共 {len(symbols)} 只股票")
            
            result = strategy_engine.batch_backtest(
                args.strategy,
                symbols,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if result['status'] == 'success':
                data = result['data']
                summary = data['summary']
                
                print("\n===== 批量回测结果 =====")
                print(f"策略: {data['strategy_name']} ({data['strategy_id']})")
                print(f"时间范围: {data['start_date']} 至 {data['end_date']}")
                print(f"总计股票: {summary['total_stocks']}")
                print(f"成功回测: {summary['successful_tests']}")
                print(f"失败回测: {summary['failed_tests']}")
                print(f"平均收益率: {summary['avg_return']}%")
                print(f"平均夏普比率: {summary['avg_sharpe']}")
                print(f"平均最大回撤: {summary['avg_drawdown']}%")
                print(f"平均胜率: {summary['avg_win_rate']}%")
                
                if summary['best_stock']:
                    print(f"\n表现最好的股票: {summary['best_stock']} (收益率: {summary['best_return']}%)")
                
                if summary['worst_stock']:
                    print(f"表现最差的股票: {summary['worst_stock']} (收益率: {summary['worst_return']}%)")
                
                print("\n顶级表现股票:")
                for i, stock in enumerate(data['top_performers'], 1):
                    print(f"{i}. {stock['symbol']} - 收益率: {stock['total_return']}%, 夏普比率: {stock['sharpe_ratio']}")
                
                if data['failed_stocks']:
                    print("\n失败的股票:")
                    for i, stock in enumerate(data['failed_stocks'], 1):
                        print(f"{i}. {stock['symbol']} - 失败原因: {stock.get('message', '未知')}")
            else:
                print(f"批量回测失败: {result['message']}")
        
        else:
            logger.warning(f"未知命令: {args.command}")
            print("请使用 --help 查看帮助信息")
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行时出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 