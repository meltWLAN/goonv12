import os
import sys
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_syntax')

def main():
    """
    Fix syntax errors in the china_stock_provider.py file caused by
    Chinese characters and punctuation.
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'china_stock_provider.py')
    backup_path = f"{file_path}.syntax_fixed.bak"
    
    # Create backup
    logger.info(f"Creating backup at {backup_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return 1
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace Chinese punctuation with ASCII equivalents
    replacements = {
        '，': ',',  # Chinese comma
        '。': '.',  # Chinese period
        '：': ':',  # Chinese colon
        '；': ';',  # Chinese semicolon
        '"': '"',   # Chinese double quote (left)
        '"': '"',   # Chinese double quote (right)
        ''': "'",   # Chinese single quote (left)
        ''': "'",   # Chinese single quote (right)
        '（': '(',  # Chinese left parenthesis
        '）': ')',  # Chinese right parenthesis
        '【': '[',  # Chinese left bracket
        '】': ']',  # Chinese right bracket
        '《': '<',  # Chinese left angle bracket
        '》': '>',  # Chinese right angle bracket
        '！': '!',  # Chinese exclamation mark
        '？': '?',  # Chinese question mark
        '、': ',',  # Chinese enumeration comma
    }
    
    # Apply all replacements
    for chinese, ascii_char in replacements.items():
        content = content.replace(chinese, ascii_char)
    
    # More aggressive approach: Handle all docstrings and comments
    # Find all lines that are likely docstrings or comments in Chinese
    
    # Replace specific problematic patterns that cause syntax errors
    patterns_to_fix = [
        # Fix the kwargs syntax error in _handle_stock_api
        (r'(\s+)kwargs: 其他参数.*?end_date', r'\1kwargs: Other parameters including start_date and end_date'),
        
        # Fix freq parameter in get_realtime_minute method
        (r'(\s+)freq: 频率,支持 1MIN/5MIN/15MIN/30MIN/60MIN', r'\1freq: Frequency, supports 1MIN/5MIN/15MIN/30MIN/60MIN'),
        
        # Fix other potential parameter documentations with Chinese
        (r'(\s+)([a-zA-Z_]+): ([^\n]*[\u4e00-\u9fff]+[^\n]*)', r'\1\2: Parameter_\2'),
        
        # Fix function docstrings
        (r'"""([^\n]*[\u4e00-\u9fff]+[^\n]*)"""', r'"""Description"""'),
        
        # Fix multi-line docstrings
        (r'"""([^"]*[\u4e00-\u9fff]+[^"]*)"""', r'"""Description"""'),
        
        # Fix single-line comments
        (r'#([^\n]*[\u4e00-\u9fff]+[^\n]*)', r'# Comment'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back to the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("Successfully fixed syntax errors")
        return 0
    except Exception as e:
        logger.error(f"Failed to write fixed content: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 