#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能推荐系统修复和验证脚本
用于检测和修复智能推荐系统中的潜在问题
"""

import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

def check_ui_module():
    """检查UI模块是否正常"""
    print("检查智能推荐系统UI模块...")
    try:
        from smart_recommendation_ui import show_recommendation_ui
        print("✓ UI模块导入成功")
        return True
    except Exception as e:
        print(f"✗ UI模块导入失败: {str(e)}")
        traceback.print_exc()
        return False

def check_data_module():
    """检查数据模块是否正常"""
    print("检查智能推荐系统数据模块...")
    try:
        from smart_recommendation_system import get_recommendation_system, StockRecommendation
        system = get_recommendation_system()
        count = len(system.get_all_recommendations())
        print(f"✓ 数据模块导入成功，当前有 {count} 个推荐")
        return True
    except Exception as e:
        print(f"✗ 数据模块导入失败: {str(e)}")
        traceback.print_exc()
        return False

def check_data_directory():
    """检查数据目录是否存在且可写"""
    print("检查数据目录...")
    data_dir = "smart_recommendation_data"
    recommendations_file = os.path.join(data_dir, "recommendations.json")
    
    if not os.path.exists(data_dir):
        print(f"✗ 数据目录 {data_dir} 不存在，尝试创建...")
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f"✓ 已创建数据目录 {data_dir}")
        except Exception as e:
            print(f"✗ 创建数据目录失败: {str(e)}")
            return False
    else:
        print(f"✓ 数据目录 {data_dir} 存在")
    
    # 检查文件是否存在
    if os.path.exists(recommendations_file):
        print(f"✓ 推荐数据文件 {recommendations_file} 存在")
        # 检查文件权限
        try:
            with open(recommendations_file, 'r') as f:
                pass
            print(f"✓ 推荐数据文件可读")
        except Exception as e:
            print(f"✗ 推荐数据文件读取失败: {str(e)}")
            return False
    else:
        print(f"✗ 推荐数据文件 {recommendations_file} 不存在，将在启动时自动创建")
    
    return True

def fix_path_issues():
    """修复路径问题"""
    print("修复潜在路径问题...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        print(f"✓ 已将当前目录添加到Python路径: {script_dir}")
    return True

def check_dependencies():
    """检查依赖库"""
    print("检查依赖库...")
    try:
        import PyQt5
        print("✓ PyQt5 已安装")
        
        import pandas
        print("✓ pandas 已安装")
        
        import numpy
        print("✓ numpy 已安装")
        
        import json
        print("✓ json 模块可用")
        
        return True
    except ImportError as e:
        print(f"✗ 依赖库检查失败: {str(e)}")
        return False

def test_ui_launch():
    """测试UI启动"""
    print("测试UI启动...")
    try:
        from smart_recommendation_ui import show_recommendation_ui
        
        # 仅创建应用实例，不实际显示窗口
        app = QApplication.instance() or QApplication(sys.argv)
        
        # 测试创建窗口
        window = show_recommendation_ui()
        
        print("✓ UI启动成功")
        return True
    except Exception as e:
        print(f"✗ UI启动失败: {str(e)}")
        traceback.print_exc()
        return False

def check_integration_with_main_app():
    """检查与主应用的集成"""
    print("检查与主应用的集成...")
    try:
        # 检查主应用是否存在
        if not os.path.exists("stock_analyzer_app.py"):
            print("✗ 主应用文件不存在")
            return False
        
        # 检查导入语句
        import_found = False
        button_found = False
        function_found = False
        
        with open("stock_analyzer_app.py", "r") as f:
            content = f.read()
            
            if "from smart_recommendation_ui import show_recommendation_ui" in content:
                import_found = True
                print("✓ 导入语句正确")
            else:
                print("✗ 主应用未正确导入智能推荐UI模块")
            
            if "self.create_styled_button('智能推荐系统')" in content:
                button_found = True
                print("✓ 找到智能推荐系统按钮")
            else:
                print("✗ 未找到智能推荐系统按钮")
            
            if "def show_smart_recommendation" in content:
                function_found = True
                print("✓ 找到显示智能推荐系统的函数")
            else:
                print("✗ 未找到显示智能推荐系统的函数")
        
        return import_found and button_found and function_found
    except Exception as e:
        print(f"✗ 检查集成失败: {str(e)}")
        return False

def fix_integration_issues():
    """修复集成问题"""
    print("修复集成问题...")
    
    try:
        with open("stock_analyzer_app.py", "r") as f:
            content = f.readlines()
        
        # 查找导入部分
        import_section_end = 0
        for i, line in enumerate(content):
            if "import logging" in line:
                import_section_end = i
                break
        
        # 添加缺失的导入
        import_added = False
        for i, line in enumerate(content):
            if "from smart_recommendation_ui import show_recommendation_ui" in line:
                import_added = True
                break
        
        if not import_added and import_section_end > 0:
            content.insert(import_section_end + 1, "\n# 导入智能推荐系统\ntry:\n    from smart_recommendation_ui import show_recommendation_ui\n    from smart_recommendation_system import get_recommendation_system\n    HAS_SMART_RECOMMENDATION = True\nexcept ImportError:\n    HAS_SMART_RECOMMENDATION = False\n    logging.warning(\"智能推荐系统未找到，相关功能将被禁用\")\n")
            print("✓ 已添加缺失的导入语句")
        
        # 查找并修复show_smart_recommendation函数
        func_found = False
        for i, line in enumerate(content):
            if "def show_smart_recommendation" in line:
                func_found = True
                
                # 检查是否需要更新函数实现
                j = i + 1
                found_try_except = False
                while j < len(content) and "def " not in content[j]:
                    if "try:" in content[j]:
                        found_try_except = True
                    j += 1
                
                if not found_try_except:
                    # 替换函数实现
                    func_end = j
                    new_func = [
                        "    def show_smart_recommendation(self):\n",
                        "        \"\"\"显示智能推荐系统\"\"\"\n",
                        "        try:\n",
                        "            print(\"正在启动智能推荐系统...\")\n",
                        "            # 添加一个调试日志消息到控制台\n",
                        "            self.result_text.clear()\n",
                        "            self.result_text.append(\"正在启动智能推荐系统...\")\n",
                        "            QApplication.processEvents()  # 确保UI更新\n",
                        "            \n",
                        "            # 打开智能推荐系统界面\n",
                        "            from smart_recommendation_ui import show_recommendation_ui\n",
                        "            show_recommendation_ui()\n",
                        "            \n",
                        "            print(\"智能推荐系统启动完成\")\n",
                        "        except Exception as e:\n",
                        "            print(f\"智能推荐系统启动失败: {str(e)}\")\n",
                        "            import traceback\n",
                        "            traceback.print_exc()\n",
                        "            self.show_error_message('错误', f'启动智能推荐系统时出错：{str(e)}')\n",
                        "            self.result_text.clear()\n",
                        "            self.result_text.append(f'加载失败：{str(e)}')\n"
                    ]
                    content[i:func_end] = new_func
                    print("✓ 已更新智能推荐系统显示函数")
                else:
                    print("✓ 智能推荐系统显示函数已经包含错误处理")
                break
        
        if not func_found:
            # 查找适合添加函数的位置
            insert_pos = 0
            for i, line in enumerate(content):
                if "def analyze_sectors" in line:
                    insert_pos = i
                    break
            
            if insert_pos > 0:
                new_func = [
                    "    def show_smart_recommendation(self):\n",
                    "        \"\"\"显示智能推荐系统\"\"\"\n",
                    "        try:\n",
                    "            print(\"正在启动智能推荐系统...\")\n",
                    "            # 添加一个调试日志消息到控制台\n",
                    "            self.result_text.clear()\n",
                    "            self.result_text.append(\"正在启动智能推荐系统...\")\n",
                    "            QApplication.processEvents()  # 确保UI更新\n",
                    "            \n",
                    "            # 打开智能推荐系统界面\n",
                    "            from smart_recommendation_ui import show_recommendation_ui\n",
                    "            show_recommendation_ui()\n",
                    "            \n",
                    "            print(\"智能推荐系统启动完成\")\n",
                    "        except Exception as e:\n",
                    "            print(f\"智能推荐系统启动失败: {str(e)}\")\n",
                    "            import traceback\n",
                    "            traceback.print_exc()\n",
                    "            self.show_error_message('错误', f'启动智能推荐系统时出错：{str(e)}')\n",
                    "            self.result_text.clear()\n",
                    "            self.result_text.append(f'加载失败：{str(e)}')\n",
                    "\n"
                ]
                content.insert(insert_pos, "".join(new_func))
                print("✓ 已添加智能推荐系统显示函数")
        
        # 保存修改后的文件
        with open("stock_analyzer_app.py", "w") as f:
            f.writelines(content)
        
        print("✓ 已保存修复后的文件")
        return True
    except Exception as e:
        print(f"✗ 修复集成问题失败: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("===== 智能推荐系统检查和修复工具 =====")
    
    checks = [
        fix_path_issues,
        check_dependencies,
        check_data_directory,
        check_data_module,
        check_ui_module,
        check_integration_with_main_app
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if not all_passed:
        print("\n发现一些问题，尝试修复...")
        fix_integration_issues()
        
        print("\n修复完成，开始测试UI启动...")
        test_ui_launch()
        
        print("\n请重新启动股票分析系统，智能推荐系统按钮应该能正常工作了。")
    else:
        print("\n所有检查通过，智能推荐系统应该能正常工作。")
        test_ui_launch()

if __name__ == "__main__":
    main() 