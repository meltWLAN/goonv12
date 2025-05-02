#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simplified test script to verify the integration of LazyStockAnalyzer with StockReview's analyze_performance method
"""

import os
import sys
import time
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("LazyIntegrationTest")

# Initialize QApplication for Qt components
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    logger.info("QApplication initialized successfully")
except ImportError:
    try:
        from PySide2.QtWidgets import QApplication
        app = QApplication(sys.argv)
        logger.info("QApplication initialized successfully (PySide2)")
    except ImportError:
        logger.warning("Neither PyQt5 nor PySide2 could be imported. GUI components may not work.")
        app = None

def test_analyze_performance():
    """Test the analyze_performance method in StockReview class with LazyStockAnalyzer integration"""
    try:
        logger.info("Testing StockReview analyze_performance method integration with LazyStockAnalyzer")
        
        # First run the integration script
        import integrate_lazy_analyzer
        success = integrate_lazy_analyzer.main()
        if not success:
            logger.error("Integration script failed to run successfully")
            return False
        
        logger.info("Integration script executed successfully")
        
        # Import required classes
        from stock_review import StockReview
        from lazy_analyzer import LazyStockAnalyzer
        
        # Initialize StockReview with headless mode if possible
        token = '0e65a5c636112dc9d9af5ccc93ef06c55987805b9467db0866185a10'
        # Check if headless parameter exists
        import inspect
        has_headless = 'headless' in inspect.signature(StockReview.__init__).parameters
        
        if has_headless:
            review = StockReview(token=token, headless=True)
            logger.info("StockReview initialized in headless mode")
        else:
            review = StockReview(token=token)
            logger.info("StockReview initialized in normal mode")
        
        # Test stock
        symbol = '000001.SZ'  # Ping An Bank
        
        # Get the current date and date 90 days ago
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing stock {symbol} from {start_date} to {end_date}")
        
        # Time the analysis
        start_time = time.time()
        result = review.analyze_performance(symbol, start_date, end_date)
        end_time = time.time()
        
        # Check if result contains error
        if isinstance(result, dict) and 'error' in result:
            logger.error(f"Analysis failed: {result['error']}")
            return False
        
        logger.info(f"Analysis completed in {end_time - start_time:.2f} seconds")
        
        # Log result details
        if isinstance(result, dict):
            logger.info(f"Symbol: {result.get('symbol', 'unknown')}")
            logger.info(f"Name: {result.get('name', 'unknown')}")
            logger.info(f"Trend: {result.get('trend', 'unknown')}")
            logger.info(f"Strength: {result.get('strength', 0):.2f}")
            
            # Check if analysis field is present and contains indicators
            if 'analysis' in result and isinstance(result['analysis'], dict):
                indicators = result['analysis']
                logger.info(f"Number of calculated indicators: {len(indicators)}")
                
                # Print a few important indicators
                if 'ma5' in indicators:
                    logger.info(f"MA5: {indicators['ma5']}")
                if 'macd' in indicators:
                    logger.info(f"MACD: {indicators['macd']}")
                if 'rsi14' in indicators:
                    logger.info(f"RSI(14): {indicators['rsi14']}")
        else:
            logger.error("Result is not a dictionary")
            return False
        
        logger.info("StockReview analyze_performance test completed successfully")
        return True
        
    except Exception as e:
        import traceback
        logger.error(f"Test failed with error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting LazyStockAnalyzer integration test")
    success = test_analyze_performance()
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    
    # Clean up Qt application if it was initialized
    if app:
        logger.info("Cleaning up QApplication")
        app.quit()
    
    sys.exit(0 if success else 1) 