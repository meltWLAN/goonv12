import sys
import logging
import traceback

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='debug_visual_stock.log',
    filemode='w'
)
logger = logging.getLogger('DebugVisualStock')

# 导入必要模块
try:
    from visual_stock_system import VisualStockSystem
    from single_stock_analyzer import SingleStockAnalyzer
    logger.info("成功导入所需模块")
except Exception as e:
    logger.error(f"导入模块时出错: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def test_stock_data():
    """测试股票数据获取功能"""
    try:
        logger.info("初始化VisualStockSystem (headless=True)")
        system = VisualStockSystem(headless=True)
        
        # 测试列表
        test_stocks = ['000001.SZ', '600000.SH', '300622.SZ']
        
        for stock in test_stocks:
            try:
                logger.info(f"测试获取股票数据: {stock}")
                df = system.get_stock_data(stock)
                
                if df is None:
                    logger.error(f"获取股票数据失败: {stock} - 返回None")
                    continue
                    
                logger.info(f"成功获取股票数据 {stock}, 行数: {len(df)}, 列数: {len(df.columns)}")
                logger.info(f"列名: {list(df.columns)}")
                
                # 显示样本数据
                logger.info(f"前2行样本数据:\n{df.head(2)}")
                
                # 测试分析功能
                logger.info(f"测试分析股票: {stock}")
                analysis, _ = system.analyze_stock(stock)
                
                if analysis:
                    logger.info(f"分析成功: {stock}")
                    logger.info(f"分析结果: {analysis.keys()}")
                else:
                    logger.error(f"分析失败: {stock}")
                
            except Exception as e:
                logger.error(f"处理股票 {stock} 时出错: {str(e)}")
                traceback.print_exc()
                
    except Exception as e:
        logger.error(f"测试股票数据时出错: {str(e)}")
        traceback.print_exc()

def test_single_stock_analyzer():
    """测试SingleStockAnalyzer类"""
    try:
        logger.info("初始化SingleStockAnalyzer")
        analyzer = SingleStockAnalyzer()
        
        # 测试列表
        test_stocks = ['000001.SZ', '600000.SH', '300622.SZ']
        
        for stock in test_stocks:
            try:
                logger.info(f"测试SingleStockAnalyzer分析股票: {stock}")
                result = analyzer.get_detailed_analysis(stock)
                
                if result['status'] == 'success':
                    logger.info(f"SingleStockAnalyzer分析成功: {stock}")
                    logger.info(f"分析结果: {result['data'].keys()}")
                else:
                    logger.error(f"SingleStockAnalyzer分析失败: {stock} - {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"SingleStockAnalyzer处理股票 {stock} 时出错: {str(e)}")
                traceback.print_exc()
                
    except Exception as e:
        logger.error(f"测试SingleStockAnalyzer时出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("开始调试视觉股票系统")
    
    try:
        # 测试股票数据获取
        test_stock_data()
        
        # 测试单股分析器
        test_single_stock_analyzer()
        
        logger.info("调试完成")
    except Exception as e:
        logger.error(f"主程序执行出错: {str(e)}")
        traceback.print_exc() 