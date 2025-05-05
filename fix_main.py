#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复stock_analyzer_app.py中main函数的缩进问题
"""

with open('stock_analyzer_app.py', 'r') as f:
    content = f.read()

# 找到问题代码的位置
start = content.find("def main():")
end = content.find("if __name__ ==", start)

# 获取有问题的代码块
old_code = content[start:end]

# 修复后的代码 - 注意使用单引号避免嵌套三引号的问题
fixed_code = '''def main():
    """主函数"""
    try:
        # 保存进程ID
        save_pid()

        # 初始化QApplication
        app = QApplication(sys.argv)
        
        # 创建并显示股票分析应用
        analyzer_app = StockAnalyzerApp()
        analyzer_app.show()
        
        # 运行应用
        return app.exec_()
    except Exception as e:
        print(f"启动应用出错: {str(e)}")
        logging.error(f"启动应用出错: {str(e)}", exc_info=True)
        return 1

'''

# 替换问题代码
fixed_content = content.replace(old_code, fixed_code)

# 保存修复后的文件
with open('stock_analyzer_app.py', 'w') as f:
    f.write(fixed_content)

print("main函数已修复") 