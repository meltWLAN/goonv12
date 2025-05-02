import os
import sys
import logging
import argparse
from datetime import datetime
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('update_provider')

def main():
    """
    Script to update the china_stock_provider.py file with enhanced Tushare API integration.
    This will:
    1. Backup the existing provider file
    2. Integrate the TushareAPIManager for improved caching and error handling
    """
    parser = argparse.ArgumentParser(description='Update China Stock Provider with enhanced Tushare API support')
    parser.add_argument('--token', type=str, help='Tushare API token to use')
    parser.add_argument('--backup', action='store_true', default=True, help='Create a backup of the original file')
    args = parser.parse_args()
    
    # Check if token is provided via argument or environment
    token = args.token or os.environ.get('TUSHARE_TOKEN')
    if not token:
        logger.error("No Tushare token provided. Please provide via --token or TUSHARE_TOKEN environment variable")
        return 1
    
    # File paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    provider_path = os.path.join(current_dir, 'china_stock_provider.py')
    api_manager_path = os.path.join(current_dir, 'tushare_api_manager.py')
    
    # Check if files exist
    if not os.path.exists(provider_path):
        logger.error(f"Provider file not found: {provider_path}")
        return 1
    
    if not os.path.exists(api_manager_path):
        logger.error(f"API Manager file not found: {api_manager_path}")
        return 1
    
    # Create backup if requested
    if args.backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{provider_path}.{timestamp}.bak"
        try:
            shutil.copy2(provider_path, backup_path)
            logger.info(f"Created backup of original provider file: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return 1
    
    # Test the Tushare API Manager with the provided token
    logger.info("Testing Tushare API Manager with provided token...")
    try:
        sys.path.append(current_dir)
        from tushare_api_manager import TushareAPIManager
        
        api = TushareAPIManager(token=token)
        if not api.validate_token():
            logger.error("Token validation failed. Cannot proceed with update.")
            return 1
        
        logger.info("Token validated successfully. Proceeding with update...")
    except Exception as e:
        logger.error(f"Error testing API Manager: {str(e)}")
        return 1
    
    # Read the original provider file
    try:
        with open(provider_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading provider file: {str(e)}")
        return 1
    
    # Create the modified file
    output_lines = []
    in_tushare_method = False
    tushare_method_content = []
    imports_updated = False
    init_updated = False
    
    # Modify the file line by line
    for line in lines:
        # Update imports
        if "import tushare as ts" in line and not imports_updated:
            output_lines.append("import tushare as ts\nimport akshare as ak\nimport pandas as pd\nfrom tushare_api_manager import TushareAPIManager\n")
            imports_updated = True
            # Skip the next two lines which should be the original akshare and pandas imports
            continue
            
        # Skip the skipped import lines
        if imports_updated and ("import akshare as ak" in line or "import pandas as pd" in line):
            continue
            
        # Update init method to add the TushareAPIManager
        if "def __init__(self, tushare_token=None" in line:
            output_lines.append(line)
            # Add our new initialization code after the first line of the init method
            # We'll look for the first indented line after this
            continue
            
        if not init_updated and imports_updated and line.startswith("        ") and "def " not in line:
            output_lines.append(line)
            output_lines.append("        # Initialize the TushareAPIManager for improved API handling\n")
            output_lines.append("        self.tushare_manager = TushareAPIManager(token=tushare_token, cache_dir='./cache/tushare')\n")
            init_updated = True
            continue
            
        # Identify and store the original _get_stock_data_tushare method
        if "def _get_stock_data_tushare(self" in line:
            in_tushare_method = True
            tushare_method_content.append(line)
            continue
            
        if in_tushare_method:
            if line.strip() and (line.startswith("    def ") or not line.startswith(" ")):
                # We've reached the end of the method
                in_tushare_method = False
                
                # Add our new implementation
                output_lines.append("    def _get_stock_data_tushare(self, symbol, start_date, end_date):\n")
                output_lines.append("        # Use the TushareAPIManager for better caching and error handling\n")
                output_lines.append("        try:\n")
                output_lines.append("            # Get stock data with technical indicators\n")
                output_lines.append("            df = self.tushare_manager.get_stk_factor(\n")
                output_lines.append("                ts_code=symbol,\n")
                output_lines.append("                start_date=start_date,\n")
                output_lines.append("                end_date=end_date\n")
                output_lines.append("            )\n")
                output_lines.append("            \n")
                output_lines.append("            if df is not None and not df.empty:\n")
                output_lines.append("                self.logger.info(f\"Retrieved {len(df)} days of data from Tushare for {symbol}\")\n")
                output_lines.append("                return df\n")
                output_lines.append("            \n")
                output_lines.append("            # Fallback to basic daily data if stk_factor is unavailable\n")
                output_lines.append("            df = self.tushare_manager.get_daily_data(\n")
                output_lines.append("                ts_code=symbol,\n")
                output_lines.append("                start_date=start_date,\n")
                output_lines.append("                end_date=end_date\n")
                output_lines.append("            )\n")
                output_lines.append("            \n")
                output_lines.append("            if df is not None and not df.empty:\n")
                output_lines.append("                self.logger.info(f\"Retrieved {len(df)} days of basic data from Tushare for {symbol}\")\n")
                output_lines.append("                return df\n")
                output_lines.append("            \n")
                output_lines.append("            self.logger.warning(f\"No data available from Tushare for {symbol}\")\n")
                output_lines.append("            return None\n")
                output_lines.append("        except Exception as e:\n")
                output_lines.append("            self.logger.error(f\"Error getting data from Tushare: {str(e)}\")\n")
                output_lines.append("            return None\n")
                output_lines.append("            \n")
                output_lines.append("    def _get_stock_data_tushare_old(self, symbol, start_date, end_date):\n")
                
                # Add the original method content as _get_stock_data_tushare_old
                for old_line in tushare_method_content[1:]:  # Skip the def line
                    output_lines.append(old_line)
                    
                # Add the current line which marks the end of the method
                output_lines.append(line)
                continue
            else:
                tushare_method_content.append(line)
                continue
        
        # Add all other lines unchanged
        output_lines.append(line)
    
    # Write the modified file
    try:
        with open(provider_path, 'w') as f:
            f.writelines(output_lines)
    except Exception as e:
        logger.error(f"Error writing modified provider file: {str(e)}")
        return 1
    
    # Create a README about the changes
    readme_content = """# Enhanced China Stock Provider

This module has been updated to use the TushareAPIManager class for improved API handling.
Key enhancements:

1. Better caching of API requests
2. Improved error handling
3. Rate limiting to prevent API throttling
4. More efficient handling of token authentication

To use the enhanced provider, simply initialize it with your Tushare token:

```python
from china_stock_provider import ChinaStockProvider

provider = ChinaStockProvider(tushare_token='your_token_here')
data = provider.get_data('daily', '000001.SZ')
```

The provider will automatically use the TushareAPIManager for API requests
while maintaining compatibility with existing code.
"""
    
    readme_path = os.path.join(current_dir, 'PROVIDER_README.md')
    try:
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        logger.info(f"Created documentation at {readme_path}")
    except Exception as e:
        logger.error(f"Error creating README: {str(e)}")
    
    logger.info("Successfully updated china_stock_provider.py with TushareAPIManager integration")
    logger.info("The original _get_stock_data_tushare method was preserved as _get_stock_data_tushare_old")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 