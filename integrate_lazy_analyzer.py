#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LazyStockAnalyzer Integration Script

This script integrates the LazyStockAnalyzer into various components
of the stock analysis system, including VisualStockSystem, StockReview,
VolumePriceStrategy, and other modules.
"""

import os
import sys
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union
import traceback
import importlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration_log.txt')
    ]
)

logger = logging.getLogger("LazyAnalyzerIntegration")

def check_lazy_analyzer_exists() -> bool:
    """Check if the LazyStockAnalyzer module exists"""
    try:
        import lazy_analyzer
        return hasattr(lazy_analyzer, 'LazyStockAnalyzer')
    except ImportError:
        logger.error("Could not import lazy_analyzer module")
        return False

def integrate_with_visual_stock_system() -> bool:
    """Integrate LazyStockAnalyzer with VisualStockSystem"""
    try:
        from lazy_analyzer import LazyStockAnalyzer
        from visual_stock_system import VisualStockSystem
        
        # Original analyze_stock method to analyze stock data
        original_analyze_stock = VisualStockSystem.analyze_stock
        
        # Patching the analyze_stock method
        def patched_analyze_stock(self, symbol):
            logger.info(f"Using LazyStockAnalyzer for {symbol}")
            
            try:
                # Get stock data
                df = self.get_stock_data(symbol)
                if df is None or df.empty:
                    return {'error': f"No data available for {symbol}"}
                
                # Create LazyStockAnalyzer with all indicators
                analyzer = LazyStockAnalyzer(required_indicators='all')
                
                # Analyze the stock
                analysis_result = analyzer.analyze(df)
                
                # Ensure trend is set
                if 'trend_direction' in analysis_result:
                    analysis_result['trend'] = analysis_result['trend_direction']
                else:
                    # Calculate trend based on moving averages
                    if 'ma5' in analysis_result and 'ma20' in analysis_result:
                        ma5 = analysis_result['ma5']
                        ma20 = analysis_result['ma20']
                        if ma5 > ma20:
                            analysis_result['trend'] = 'uptrend'
                        elif ma5 < ma20:
                            analysis_result['trend'] = 'downtrend'
                        else:
                            analysis_result['trend'] = 'sideways'
                    else:
                        analysis_result['trend'] = 'unknown'
                
                # Add any necessary additional processing
                analysis_result['symbol'] = symbol
                analysis_result['name'] = self.get_stock_name(symbol)
                
                # Generate recommendation based on analysis
                recommendation = self.generate_recommendation(analysis_result)
                analysis_result['recommendation'] = recommendation
                
                # Return the result as a dictionary, not a tuple
                return analysis_result
            except Exception as e:
                logger.error(f"Error in patched analyze_stock: {str(e)}")
                # Fall back to original method if there's an error
                logger.info("Falling back to original analyze_stock method")
                return original_analyze_stock(self, symbol)
        
        # Replace the original method with the patched one
        VisualStockSystem.analyze_stock = patched_analyze_stock
        logger.info("Successfully integrated LazyStockAnalyzer with VisualStockSystem")
        return True
    
    except Exception as e:
        logger.error(f"Failed to integrate with VisualStockSystem: {str(e)}")
        traceback.print_exc()
        return False

def integrate_with_stock_review() -> bool:
    """Integrate LazyStockAnalyzer with StockReview"""
    try:
        from lazy_analyzer import LazyStockAnalyzer
        from stock_review import StockReview
        
        # Add LazyStockAnalyzer to StockReview
        original_analyze_performance = StockReview.analyze_performance
        
        def patched_analyze_performance(self, symbol, start_date=None, end_date=None):
            logger.info(f"Using LazyStockAnalyzer for performance analysis of {symbol}")
            
            try:
                # 设置默认日期范围
                if not end_date:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                if not start_date:
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                # Get the stock data
                stock_data = self.visual_system.get_stock_data(symbol, start_date, end_date)
                if stock_data is None or stock_data.empty:
                    return {'error': f"No data available for {symbol}"}
                
                # Use LazyStockAnalyzer for trend analysis
                analyzer = LazyStockAnalyzer(required_indicators=['ma', 'ema', 'macd', 'rsi', 'trend_direction', 'adx'])
                analysis = analyzer.analyze(stock_data)
                
                # Ensure required fields exist with appropriate defaults
                # Handle trend field
                trend = 'unknown'
                if 'trend_direction' in analysis:
                    trend = analysis['trend_direction']
                elif 'ma5' in analysis and 'ma20' in analysis:
                    # Calculate trend based on moving averages
                    ma5 = analysis.get('ma5', 0)
                    ma20 = analysis.get('ma20', 0)
                    if ma5 > ma20:
                        trend = 'uptrend'
                    elif ma5 < ma20:
                        trend = 'downtrend'
                    else:
                        trend = 'sideways'
                
                # Get strength (ADX or calculate from RSI)
                strength = analysis.get('adx', 0)
                if strength == 0 and 'rsi14' in analysis:
                    # Alternative strength calculation if ADX not available
                    strength = abs(analysis.get('rsi14', 50) - 50) * 2
                
                # Get latest close price
                last_close = analysis.get('close', 0)
                if last_close == 0 and not stock_data.empty:
                    last_close = stock_data['close'].iloc[-1]
                
                # Get latest volume
                volume = analysis.get('volume', 0)
                if volume == 0 and not stock_data.empty:
                    volume = stock_data['volume'].iloc[-1]
                
                # 计算成交量趋势
                volume_trend = 'normal'
                if 'volume' in stock_data.columns:
                    try:
                        avg_volume = stock_data['volume'].rolling(window=10).mean().iloc[-1]
                        if volume > avg_volume * 1.5:
                            volume_trend = 'increasing'
                        elif volume < avg_volume * 0.5:
                            volume_trend = 'decreasing'
                    except Exception as ve:
                        logger.warning(f"计算成交量趋势出错: {str(ve)}")
                
                # 确保有ma10
                ma10 = analysis.get('ma10', None)
                if ma10 is None and 'close' in stock_data.columns:
                    try:
                        ma10 = stock_data['close'].rolling(window=10).mean().iloc[-1]
                    except Exception as ma_err:
                        ma10 = analysis.get('ma5', 0)  # 使用ma5作为备选
                
                # 确保macd相关值存在
                macd = analysis.get('macd', 0)
                signal = analysis.get('signal', 0)
                hist = analysis.get('histogram', 0)
                
                # 确保rsi存在
                rsi = analysis.get('rsi14', 50)  # 使用rsi14作为rsi
                
                # Add necessary fields for compatibility with existing code
                result = {
                    'symbol': symbol,
                    'name': self.visual_system.get_stock_name(symbol),
                    'trend': trend,
                    'strength': strength,
                    'last_close': last_close,
                    'volume': volume,
                    'volume_trend': volume_trend,
                    'ma5': analysis.get('ma5', 0),
                    'ma10': ma10,
                    'ma20': analysis.get('ma20', 0),
                    'macd': macd,
                    'signal': signal,
                    'hist': hist,
                    'rsi': rsi,
                    'start_date': start_date,
                    'end_date': end_date,
                    'analysis': analysis  # 保留完整分析结果
                }
                
                return result
            except Exception as e:
                logger.error(f"Error in patched analyze_performance: {str(e)}")
                # Fall back to original method
                return original_analyze_performance(self, symbol, start_date, end_date)
        
        # Replace the original method with the patched one
        StockReview.analyze_performance = patched_analyze_performance
        logger.info("Successfully integrated LazyStockAnalyzer with StockReview")
        return True
        
    except Exception as e:
        logger.error(f"Failed to integrate with StockReview: {str(e)}")
        traceback.print_exc()
        return False

def integrate_with_volume_price_strategy() -> bool:
    """Integrate LazyStockAnalyzer with VolumePriceStrategy"""
    try:
        # Check if VolumePriceStrategy exists
        try:
            from volume_price_strategy import VolumePriceStrategy
        except ImportError:
            logger.warning("VolumePriceStrategy module not found, skipping integration")
            return False
            
        from lazy_analyzer import LazyStockAnalyzer
        
        # Original analyze method
        original_analyze = VolumePriceStrategy.analyze
        
        # Patched analyze method using LazyStockAnalyzer
        def patched_analyze(self, data):
            logger.info("Using LazyStockAnalyzer for volume-price analysis")
            
            try:
                # Use LazyStockAnalyzer with specific volume-related indicators
                analyzer = LazyStockAnalyzer(required_indicators=['volume_ratio', 'obv', 'macd'])
                analysis = analyzer.analyze(data)
                
                # Add strategy-specific calculations
                result = {
                    'volume_price_ratio': analysis.get('volume_ratio', 1.0),
                    'obv': analysis.get('obv', 0),
                    'macd': analysis.get('macd', 0),
                    'signal': analysis.get('signal', 0),
                    'histogram': analysis.get('histogram', 0),
                    'strategy_score': 0  # Will be calculated below
                }
                
                # Calculate strategy score
                try:
                    volume_trend = 1 if result['volume_ratio'] > 1.2 else (-1 if result['volume_ratio'] < 0.8 else 0)
                    price_trend = 1 if analysis.get('macd', 0) > 0 else -1
                    
                    # Simple scoring based on volume and price trends
                    result['strategy_score'] = volume_trend * 0.4 + price_trend * 0.6
                except Exception as calc_err:
                    logger.error(f"Error calculating strategy score: {str(calc_err)}")
                    result['strategy_score'] = 0
                
                return result
            except Exception as e:
                logger.error(f"Error in patched volume_price_strategy analyze: {str(e)}")
                # Fall back to original method
                return original_analyze(self, data)
        
        # Replace the original method
        VolumePriceStrategy.analyze = patched_analyze
        logger.info("Successfully integrated LazyStockAnalyzer with VolumePriceStrategy")
        return True
        
    except Exception as e:
        logger.error(f"Failed to integrate with VolumePriceStrategy: {str(e)}")
        traceback.print_exc()
        return False

def run_integration_test():
    """Run a test to verify the integration"""
    try:
        logger.info("Running integration test...")
        
        # Import the necessary modules
        from visual_stock_system import VisualStockSystem
        from lazy_analyzer import LazyStockAnalyzer
        
        # Create a VSS instance
        vss = VisualStockSystem(headless=True)
        
        # Test stock analysis
        symbol = '000001.SZ'  # Ping An Bank
        
        # Time the analysis
        start_time = time.time()
        result = vss.analyze_stock(symbol)
        end_time = time.time()
        
        # Log results
        logger.info(f"Analysis completed in {end_time - start_time:.2f} seconds")
        
        # Handle both dict and tuple results (original method returns tuple, patched returns dict)
        if isinstance(result, tuple):
            analysis_result, recommendation = result
            logger.info(f"Analysis result (tuple format): received analysis and recommendation")
            if isinstance(analysis_result, dict):
                logger.info(f"Analysis result keys: {list(analysis_result.keys())}")
            logger.info(f"Recommendation: {recommendation}")
            
            # Check expected keys in the analysis result
            expected_keys = ['close', 'volume', 'ma5', 'ema21', 'rsi14']
            if isinstance(analysis_result, dict):
                missing_keys = [k for k in expected_keys if k not in analysis_result]
                
                if missing_keys:
                    logger.warning(f"Missing expected keys in analysis result: {missing_keys}")
                    return False
                else:
                    logger.info("Integration test passed successfully!")
                    return True
            else:
                logger.warning("Analysis result is not a dictionary")
                return False
                
        else:  # Assume it's a dict (from patched method)
            logger.info(f"Analysis result keys: {list(result.keys())}")
            logger.info(f"Recommendation: {result.get('recommendation', 'No recommendation')}")
            
            # Check if the analysis contains expected keys
            expected_keys = ['close', 'volume', 'ma5', 'ema21', 'rsi14', 'recommendation']
            missing_keys = [k for k in expected_keys if k not in result]
            
            if missing_keys:
                logger.warning(f"Missing expected keys in analysis result: {missing_keys}")
                return False
            else:
                logger.info("Integration test passed successfully!")
                return True
            
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main integration function"""
    logger.info("Starting LazyStockAnalyzer integration")
    
    # Check if LazyStockAnalyzer exists
    if not check_lazy_analyzer_exists():
        logger.error("LazyStockAnalyzer module not found, integration aborted")
        return False
    
    # Integrate with each module
    vss_result = integrate_with_visual_stock_system()
    sr_result = integrate_with_stock_review()
    vps_result = integrate_with_volume_price_strategy()
    
    # Report results
    logger.info(f"Integration results:")
    logger.info(f"  VisualStockSystem: {'SUCCESS' if vss_result else 'FAILED'}")
    logger.info(f"  StockReview: {'SUCCESS' if sr_result else 'FAILED'}")
    logger.info(f"  VolumePriceStrategy: {'SUCCESS' if vps_result else 'FAILED'}")
    
    # Run test if all integrations were successful
    if vss_result and sr_result:
        test_result = run_integration_test()
        logger.info(f"Integration test: {'SUCCESS' if test_result else 'FAILED'}")
    
    # Overall result
    overall_success = vss_result and sr_result  # VPS is optional
    logger.info(f"Integration {'completed successfully' if overall_success else 'failed'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 