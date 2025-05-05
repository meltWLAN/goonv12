#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
热门行业分析高级诊断工具

全面分析热门行业模块的各个组件，验证数据流和处理流程，
并根据发现的问题提供修复建议。
"""

import os
import sys
import json
import time
import logging
import inspect
import traceback
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sector_diagnosis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SectorDiagnostic')

class SectorAnalysisDiagnostic:
    """热门行业分析诊断工具"""
    
    def __init__(self):
        """初始化诊断工具"""
        self.logger = logger
        self.report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {},
            'tests': [],
            'fixes': [],
            'recommendations': []
        }
        self.test_counter = 0
        
        # 创建诊断报告目录
        self.diagnosis_dir = os.path.join(".", "sector_diagnosis")
        os.makedirs(self.diagnosis_dir, exist_ok=True)
        
        # 诊断报告文件路径
        self.report_path = os.path.join(self.diagnosis_dir, f"sector_diagnosis_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        # 测试数据缓存
        self.test_data = {}
    
    def run_full_diagnosis(self):
        """运行完整诊断流程"""
        self.logger.info("开始热门行业分析全面诊断...")
        
        # 1. 检查模块依赖和导入
        self.check_dependencies()
        
        # 2. 诊断增强版行业分析器
        self.diagnose_sector_analyzer()
        
        # 3. 诊断可视化模块
        self.diagnose_visualization()
        
        # 4. 检查API集成
        self.diagnose_api_integration()
        
        # 5. 验证数据流
        self.validate_data_flow()
        
        # 6. 应用修复并验证
        self.apply_fixes_and_verify()
        
        # 保存诊断报告
        self._save_report()
        
        # 输出诊断摘要
        self._print_summary()
        
        self.logger.info(f"诊断完成，报告已保存至: {self.report_path}")
        return self.report
    
    def check_dependencies(self):
        """检查模块依赖和导入"""
        test_id = self._start_test("模块依赖检查")
        
        try:
            # 检查核心模块是否存在
            modules_to_check = [
                "enhanced_sector_analyzer.py",
                "sector_visualization.py",
                "sector_data_provider.py",
                "sector_analyzer.py"
            ]
            
            missing_modules = []
            for module in modules_to_check:
                if not os.path.exists(module):
                    missing_modules.append(module)
            
            if missing_modules:
                self._end_test(test_id, False, f"缺少核心模块: {', '.join(missing_modules)}")
                self.report['recommendations'].append(f"请重新安装或恢复缺失的模块: {', '.join(missing_modules)}")
            else:
                self._end_test(test_id, True, "所有核心模块存在")
            
            # 尝试导入模块
            test_id = self._start_test("模块导入测试")
            import_errors = []
            
            # 导入测试函数
            def try_import(module_name):
                try:
                    __import__(module_name)
                    return None
                except Exception as e:
                    return str(e)
            
            # 测试导入增强版行业分析器
            module_name = "enhanced_sector_analyzer"
            if os.path.exists(f"{module_name}.py"):
                error = try_import(module_name)
                if error:
                    import_errors.append(f"{module_name}: {error}")
            
            # 测试导入可视化模块
            module_name = "sector_visualization"
            if module_name + ".py" in os.listdir('.'):
                error = try_import(module_name)
                if error:
                    import_errors.append(f"{module_name}: {error}")
            
            if import_errors:
                self._end_test(test_id, False, f"模块导入错误: {'; '.join(import_errors)}")
                self.report['recommendations'].append("修复模块导入错误，检查依赖和语法")
            else:
                self._end_test(test_id, True, "所有模块导入正常")
        
        except Exception as e:
            self._end_test(test_id, False, f"依赖检查过程出错: {str(e)}")
            self.logger.error(f"依赖检查异常: {str(e)}")
            traceback.print_exc()
    
    def diagnose_sector_analyzer(self):
        """诊断增强版行业分析器"""
        test_id = self._start_test("增强版行业分析器诊断")
        
        try:
            # 导入模块
            from enhanced_sector_analyzer import EnhancedSectorAnalyzer
            
            # 实例化分析器
            analyzer = EnhancedSectorAnalyzer()
            
            # 检查关键方法是否存在
            required_methods = [
                'analyze_hot_sectors',
                '_calculate_market_sentiment',
                '_get_sector_index_data',
                '_get_sector_fund_flow'
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(analyzer, method) or not callable(getattr(analyzer, method)):
                    missing_methods.append(method)
            
            if missing_methods:
                self._end_test(test_id, False, f"缺少关键方法: {', '.join(missing_methods)}")
                self.report['recommendations'].append(f"实现缺失的方法: {', '.join(missing_methods)}")
                
                # 添加修复建议
                for method in missing_methods:
                    if method == '_calculate_market_sentiment':
                        self.report['fixes'].append({
                            'file': 'enhanced_sector_analyzer.py',
                            'description': f"添加缺失的{method}方法",
                            'solution': "添加市场情绪计算方法，返回包含score、level等字段的字典"
                        })
            else:
                self._end_test(test_id, True, "所有关键方法都存在")
            
            # 测试热门行业分析功能
            test_id = self._start_test("热门行业分析功能测试")
            try:
                # 分析热门行业
                start_time = time.time()
                result = analyzer.analyze_hot_sectors(top_n=5, force_refresh=True)
                elapsed_time = time.time() - start_time
                
                # 检查结果格式
                if result['status'] == 'success':
                    # 检查数据结构
                    expected_keys = ['hot_sectors', 'total_sectors', 'market_sentiment', 'update_time', 'prediction_data']
                    missing_keys = [key for key in expected_keys if key not in result['data']]
                    
                    if missing_keys:
                        self._end_test(test_id, False, f"结果数据缺少字段: {', '.join(missing_keys)}")
                        
                        # 添加修复建议
                        self.report['fixes'].append({
                            'file': 'enhanced_sector_analyzer.py',
                            'description': f"在analyze_hot_sectors方法返回结果中添加缺失的字段: {', '.join(missing_keys)}",
                            'solution': "修改返回字典结构，确保包含所有必要字段"
                        })
                    else:
                        # 检查是否有空字段
                        empty_fields = []
                        for key in expected_keys:
                            if key in result['data'] and (result['data'][key] is None or (isinstance(result['data'][key], list) and len(result['data'][key]) == 0)):
                                empty_fields.append(key)
                        
                        # 缓存测试数据
                        self.test_data['hot_sectors_result'] = result
                        
                        if empty_fields:
                            self._end_test(test_id, False, f"结果数据有空字段: {', '.join(empty_fields)}")
                            
                            # 添加修复建议
                            for field in empty_fields:
                                if field == 'prediction_data':
                                    self.report['fixes'].append({
                                        'file': 'enhanced_sector_analyzer.py',
                                        'description': f"确保{field}字段非空",
                                        'solution': "修改analyze_hot_sectors方法，添加默认的预测数据生成逻辑"
                                    })
                        else:
                            self._end_test(test_id, True, f"分析成功，返回{len(result['data']['hot_sectors'])}个热门行业，用时{elapsed_time:.2f}秒")
                else:
                    self._end_test(test_id, False, f"分析失败: {result.get('message', '未知错误')}")
                    
                    # 添加修复建议
                    self.report['fixes'].append({
                        'file': 'enhanced_sector_analyzer.py',
                        'description': "修复analyze_hot_sectors方法执行失败的问题",
                        'solution': f"调试并修复错误: {result.get('message', '未知错误')}"
                    })
            
            except Exception as e:
                self._end_test(test_id, False, f"热门行业分析执行出错: {str(e)}")
                self.logger.error(f"热门行业分析异常: {str(e)}")
                traceback.print_exc()
                
                # 添加修复建议
                self.report['fixes'].append({
                    'file': 'enhanced_sector_analyzer.py',
                    'description': "修复analyze_hot_sectors方法异常",
                    'solution': f"调试并修复异常: {str(e)}"
                })
        
        except Exception as e:
            self._end_test(test_id, False, f"行业分析器诊断过程出错: {str(e)}")
            self.logger.error(f"行业分析器诊断异常: {str(e)}")
            traceback.print_exc()
    
    def diagnose_visualization(self):
        """诊断可视化模块"""
        test_id = self._start_test("行业可视化模块诊断")
        
        try:
            # 获取可视化模块文件内容
            if not os.path.exists('sector_visualization.py'):
                self._end_test(test_id, False, "无法找到sector_visualization.py文件")
                return
            
            with open('sector_visualization.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查add_prediction_tab方法的实现
            if 'def add_prediction_tab' not in content:
                self._end_test(test_id, False, "缺少add_prediction_tab方法")
                self.report['recommendations'].append("在sector_visualization.py中实现add_prediction_tab方法")
            else:
                # 检查prediction_data的访问方式
                prediction_data_access = "prediction_data = self.viz_data['data']['prediction_data']"
                safe_prediction_data_access = "prediction_data = self.viz_data['data'].get('prediction_data', [])"
                
                if prediction_data_access in content and safe_prediction_data_access not in content:
                    self._end_test(test_id, False, "预测数据访问方式不安全，可能导致KeyError")
                    self.report['fixes'].append({
                        'file': 'sector_visualization.py',
                        'description': "修复预测数据访问方式",
                        'solution': f"将'{prediction_data_access}'替换为'{safe_prediction_data_access}'"
                    })
                else:
                    self._end_test(test_id, True, "预测数据访问方式正确")
            
            # 检查行业轮动图表实现
            test_id = self._start_test("行业轮动图表诊断")
            if 'def add_cycle_tab' not in content:
                self._end_test(test_id, False, "缺少add_cycle_tab方法")
                self.report['recommendations'].append("在sector_visualization.py中实现add_cycle_tab方法")
            else:
                # 检查变量初始化
                if "sector_name =" in content and "sector_name = \"\"" not in content and "sector_name = ''" not in content:
                    self._end_test(test_id, False, "sector_name变量可能未正确初始化")
                    self.report['fixes'].append({
                        'file': 'sector_visualization.py',
                        'description': "修复sector_name变量初始化",
                        'solution': "在使用sector_name变量前先初始化为空字符串"
                    })
                else:
                    self._end_test(test_id, True, "轮动图表实现正确")
            
            # 如果有测试数据，尝试模拟可视化过程
            if 'hot_sectors_result' in self.test_data:
                test_id = self._start_test("可视化数据处理模拟")
                try:
                    # 提取结果数据
                    result = self.test_data['hot_sectors_result']
                    
                    # 检查prediction_data格式
                    prediction_data = result['data'].get('prediction_data', [])
                    
                    # 创建一个简单的Figure对象进行图表绘制测试
                    fig = Figure(figsize=(8, 6))
                    ax = fig.add_subplot(111)
                    
                    if prediction_data:
                        valid_data = []
                        for item in prediction_data:
                            if isinstance(item, dict) and 'name' in item and 'technical_score' in item:
                                valid_data.append(item)
                        
                        if valid_data:
                            names = [item['name'] for item in valid_data]
                            scores = [item['technical_score'] for item in valid_data]
                            
                            # 绘制简单条形图
                            ax.barh(range(len(names)), scores, height=0.7)
                            ax.set_yticks(range(len(names)))
                            ax.set_yticklabels(names)
                            
                            self._end_test(test_id, True, f"成功模拟绘制了包含{len(valid_data)}个预测项的图表")
                        else:
                            self._end_test(test_id, False, "预测数据格式不正确，缺少必要字段")
                            self.report['fixes'].append({
                                'file': 'enhanced_sector_analyzer.py',
                                'description': "修复prediction_data格式",
                                'solution': "确保每个预测项包含name和technical_score字段"
                            })
                    else:
                        self._end_test(test_id, False, "预测数据为空")
                        self.report['fixes'].append({
                            'file': 'enhanced_sector_analyzer.py',
                            'description': "生成有效的预测数据",
                            'solution': "修改analyze_hot_sectors方法，添加默认的预测数据生成逻辑"
                        })
                
                except Exception as e:
                    self._end_test(test_id, False, f"可视化数据处理模拟失败: {str(e)}")
                    self.logger.error(f"可视化数据处理模拟异常: {str(e)}")
                    traceback.print_exc()
        
        except Exception as e:
            self._end_test(test_id, False, f"行业可视化诊断过程出错: {str(e)}")
            self.logger.error(f"行业可视化诊断异常: {str(e)}")
            traceback.print_exc()
    
    def diagnose_api_integration(self):
        """检查API集成"""
        test_id = self._start_test("API集成诊断")
        
        try:
            # 检查tushare集成
            if not os.path.exists('tushare_api_manager.py') and not os.path.exists('tushare_data_service.py'):
                self._end_test(test_id, False, "缺少tushare API集成模块")
                self.report['recommendations'].append("检查tushare API集成是否完整")
            else:
                self._end_test(test_id, True, "找到tushare API集成模块")
            
            # 检查数据提供者模块
            data_provider_files = ['sector_data_provider.py', 'enhanced_data_provider.py']
            found_providers = [f for f in data_provider_files if os.path.exists(f)]
            
            if not found_providers:
                test_id = self._start_test("数据提供者检查")
                self._end_test(test_id, False, "缺少数据提供者模块")
                self.report['recommendations'].append("检查数据提供者模块是否完整")
            else:
                test_id = self._start_test("数据提供者检查")
                self._end_test(test_id, True, f"找到数据提供者模块: {', '.join(found_providers)}")
        
        except Exception as e:
            self._end_test(test_id, False, f"API集成诊断过程出错: {str(e)}")
            self.logger.error(f"API集成诊断异常: {str(e)}")
            traceback.print_exc()
    
    def validate_data_flow(self):
        """验证数据流"""
        test_id = self._start_test("数据流验证")
        
        try:
            # 创建检查点
            checkpoints = []
            
            # 验证行业分析器到可视化组件的数据流
            if 'hot_sectors_result' in self.test_data:
                # 检查结果
                result = self.test_data['hot_sectors_result']
                checkpoints.append(f"行业分析结果状态: {result['status']}")
                
                if result['status'] == 'success':
                    # 检查数据字段
                    for key in ['hot_sectors', 'total_sectors', 'market_sentiment', 'update_time', 'prediction_data']:
                        if key in result['data']:
                            data_type = type(result['data'][key]).__name__
                            if isinstance(result['data'][key], list):
                                data_len = len(result['data'][key])
                                checkpoints.append(f"字段 '{key}': 类型 {data_type}, 长度 {data_len}")
                            else:
                                checkpoints.append(f"字段 '{key}': 类型 {data_type}")
                        else:
                            checkpoints.append(f"缺少字段 '{key}'")
                    
                    # 检查热门行业数据
                    if 'hot_sectors' in result['data'] and result['data']['hot_sectors']:
                        first_sector = result['data']['hot_sectors'][0]
                        sector_keys = list(first_sector.keys())
                        checkpoints.append(f"热门行业字段: {', '.join(sector_keys)}")
                        
                        # 检查预测数据是否与热门行业对应
                        if 'prediction_data' in result['data'] and result['data']['prediction_data']:
                            hot_sector_names = [s['name'] for s in result['data']['hot_sectors']]
                            pred_names = [p['name'] for p in result['data']['prediction_data'] if 'name' in p]
                            
                            matching_names = set(hot_sector_names).intersection(set(pred_names))
                            if matching_names:
                                checkpoints.append(f"预测数据与热门行业匹配: {len(matching_names)}/{len(hot_sector_names)}")
                            else:
                                checkpoints.append("预测数据与热门行业不匹配")
                                self.report['fixes'].append({
                                    'file': 'enhanced_sector_analyzer.py',
                                    'description': "修复预测数据与热门行业的对应关系",
                                    'solution': "确保预测数据与热门行业具有相同的名称"
                                })
                    
                    self._end_test(test_id, True, "\n".join(checkpoints))
                else:
                    self._end_test(test_id, False, f"行业分析失败: {result.get('message', '未知错误')}")
            else:
                self._end_test(test_id, False, "缺少测试数据，无法验证数据流")
        
        except Exception as e:
            self._end_test(test_id, False, f"数据流验证过程出错: {str(e)}")
            self.logger.error(f"数据流验证异常: {str(e)}")
            traceback.print_exc()
    
    def apply_fixes_and_verify(self):
        """应用修复并验证"""
        test_id = self._start_test("修复建议汇总")
        
        try:
            # 汇总修复建议
            if self.report['fixes']:
                fix_summary = "\n".join([f"{i+1}. {fix['description']} ({fix['file']})" for i, fix in enumerate(self.report['fixes'])])
                self._end_test(test_id, False, f"需要应用{len(self.report['fixes'])}个修复:\n{fix_summary}")
                
                # 添加一个全面修复的脚本建议
                self.report['recommendations'].append(
                    "运行fix_sector_prediction.py脚本应用所有修复并清理缓存"
                )
            else:
                self._end_test(test_id, True, "无需修复，所有测试通过")
            
            # 添加验证步骤建议
            self.report['recommendations'].append(
                "修复后运行verify_hot_sectors.py进行验证"
            )
        
        except Exception as e:
            self._end_test(test_id, False, f"修复汇总过程出错: {str(e)}")
            self.logger.error(f"修复汇总异常: {str(e)}")
            traceback.print_exc()
    
    def _start_test(self, name):
        """开始一个测试"""
        self.test_counter += 1
        test_id = f"test-{self.test_counter}"
        self.report['tests'].append({
            'id': test_id,
            'name': name,
            'status': 'running',
            'message': None,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.logger.info(f"开始测试: {name} (ID: {test_id})")
        return test_id
    
    def _end_test(self, test_id, passed, message):
        """结束一个测试"""
        for test in self.report['tests']:
            if test['id'] == test_id:
                test['status'] = 'passed' if passed else 'failed'
                test['message'] = message
                test['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                log_level = logging.INFO if passed else logging.WARNING
                self.logger.log(log_level, f"测试 {test['name']} {'通过' if passed else '失败'}: {message}")
                break
    
    def _save_report(self):
        """保存诊断报告"""
        # 更新摘要
        total_tests = len(self.report['tests'])
        passed_tests = sum(1 for test in self.report['tests'] if test['status'] == 'passed')
        
        self.report['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'fixes_count': len(self.report['fixes']),
            'recommendations_count': len(self.report['recommendations'])
        }
        
        # 保存为JSON文件
        with open(self.report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
    
    def _print_summary(self):
        """打印诊断摘要"""
        summary = self.report['summary']
        
        print("\n" + "="*60)
        print(f"热门行业分析诊断报告摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*60)
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['passed_tests']}")
        print(f"失败: {summary['failed_tests']}")
        print(f"修复建议: {summary['fixes_count']}")
        print(f"推荐操作: {summary['recommendations_count']}")
        print("="*60)
        
        # 打印失败的测试
        if summary['failed_tests'] > 0:
            print("\n失败的测试:")
            for test in self.report['tests']:
                if test['status'] == 'failed':
                    print(f"- {test['name']}: {test['message']}")
        
        # 打印推荐操作
        if self.report['recommendations']:
            print("\n推荐操作:")
            for i, rec in enumerate(self.report['recommendations']):
                print(f"{i+1}. {rec}")
        
        print("\n完整报告已保存至:", self.report_path)
        print("="*60)

def main():
    """主函数"""
    print("\n🔍 启动热门行业分析高级诊断工具...\n")
    
    diagnoser = SectorAnalysisDiagnostic()
    diagnoser.run_full_diagnosis()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 