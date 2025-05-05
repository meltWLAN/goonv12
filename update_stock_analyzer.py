#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新stock_analyzer_app.py的热门行业分析功能，使其使用优化版行业分析器
"""

import re

def update_hot_industries(file_path):
    """更新热门行业分析功能"""
    print(f"开始更新 {file_path} 的热门行业分析功能...")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    with open(f"{file_path}.hot_industry.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 添加导入语句
    if "from optimized_sector_analyzer import OptimizedSectorAnalyzer" not in content:
        import_pattern = r"import logging\n"
        replacement = "import logging\nfrom optimized_sector_analyzer import OptimizedSectorAnalyzer  # 导入优化版行业分析器\n"
        content = re.sub(import_pattern, replacement, content)
    
    # 更新analyze_hot_industries方法
    analyzer_pattern = r"# 初始化行业分析器\n\s+sector_analyzer = SectorAnalyzer\(top_n=15\)"
    replacement = "# 初始化行业分析器 - 使用优化版行业分析器\n            try:\n                # 优先使用优化版行业分析器\n                sector_analyzer = OptimizedSectorAnalyzer(top_n=15, provider_type='akshare')\n                self.logger.info(\"使用优化版行业分析器(AKShare)\")\n            except Exception as e:\n                # 如果优化版分析器初始化失败，回退到原有分析器\n                self.logger.warning(f\"优化版行业分析器初始化失败: {str(e)}，使用原有分析器\")\n                from sector_analyzer import SectorAnalyzer\n                sector_analyzer = SectorAnalyzer(top_n=15)"
    content = re.sub(analyzer_pattern, replacement, content)
    
    # 更新结果处理代码，适应优化版行业分析器的返回格式
    result_pattern = r"result = sector_analyzer\.analyze_hot_sectors\(\)\s+\n\s+if result\['status'\] != 'success':"
    replacement = "result = sector_analyzer.analyze_hot_sectors()\n            \n            # 处理不同格式的结果\n            if isinstance(result, dict) and 'error' in result:\n                self.show_error_message('分析失败', f\"热门行业分析失败: {result['error']}\")\n                return\n            elif isinstance(result, dict) and 'status' in result and result['status'] != 'success':"
    content = re.sub(result_pattern, replacement, content)
    
    # 更新获取热门行业列表的代码
    sectors_pattern = r"hot_sectors = result\['data'\]\['hot_sectors'\]"
    replacement = "# 适配不同格式的返回结果\n            if isinstance(result, dict) and 'data' in result and 'sectors' in result['data']:\n                # 优化版行业分析器返回格式\n                hot_sectors = result['data']['sectors']\n                # 转换为原有格式\n                for sector in hot_sectors:\n                    # 添加原有格式所需的字段\n                    if 'hot_score' not in sector and 'score' in sector:\n                        sector['hot_score'] = sector['score']\n                    if 'change_pct' not in sector and 'change_rate_1d' in sector:\n                        sector['change_pct'] = sector['change_rate_1d']\n                    if 'volume' not in sector:\n                        sector['volume'] = 0.0\n            elif isinstance(result, dict) and 'data' in result and 'hot_sectors' in result['data']:\n                # 原有行业分析器返回格式\n                hot_sectors = result['data']['hot_sectors']"
    content = re.sub(sectors_pattern, replacement, content)
    
    # 更新市场信息的获取代码
    market_info_pattern = r"# 创建市场信息字典，使用默认值\s+market_info = \{\s+'market_sentiment': 0,\s+'north_flow': result\['data'\]\.get\('north_flow', 0\),\s+'volatility': 0,\s+'shanghai_change_pct': 0,\s+'shenzhen_change_pct': 0,\s+'market_avg_change': 0\s+\}"
    replacement = "# 创建市场信息字典\n            if isinstance(result, dict) and 'data' in result and 'market_info' in result['data']:\n                # 优化版行业分析器返回的市场信息\n                market_info = result['data']['market_info']\n            else:\n                # 使用默认值\n                market_info = {\n                    'market_sentiment': 0,\n                    'north_flow': result['data'].get('north_flow', 0) if isinstance(result, dict) and 'data' in result else 0,\n                    'volatility': 0,\n                    'shanghai_change_pct': 0,\n                    'shenzhen_change_pct': 0,\n                    'market_avg_change': 0\n                }"
    content = re.sub(market_info_pattern, replacement, content)
    
    # 更新预测部分
    prediction_pattern = r"prediction_result = sector_analyzer\.predict_next_hot_sectors\(\)"
    replacement = "try:\n                # 适配不同版本的分析器\n                if hasattr(sector_analyzer, 'predict_hot_sectors'):\n                    # 优化版行业分析器\n                    prediction_result = sector_analyzer.predict_hot_sectors()\n                elif hasattr(sector_analyzer, 'predict_next_hot_sectors'):\n                    # 原有行业分析器\n                    prediction_result = sector_analyzer.predict_next_hot_sectors()\n                else:\n                    self.logger.warning(\"行业分析器没有预测方法\")\n                    prediction_result = {'status': 'error', 'message': '行业分析器没有预测方法'}\n            except Exception as e:\n                self.logger.error(f\"预测热门行业时出错: {str(e)}\")\n                prediction_result = {'status': 'error', 'message': f'预测出错: {str(e)}'}"
    content = re.sub(prediction_pattern, replacement, content)
    
    # 更新预测结果处理
    prediction_result_pattern = r"if prediction_result\['status'\] == 'success':\s+predictions = prediction_result\['data'\]\['predicted_sectors'\]"
    replacement = "if 'error' in prediction_result:\n                self.result_text.append(f\"\\n预测分析失败: {prediction_result['error']}\")\n            elif isinstance(prediction_result, dict) and prediction_result.get('status') == 'success':\n                # 原有行业分析器格式\n                predictions = prediction_result['data']['predicted_sectors']\n            elif isinstance(prediction_result, dict) and 'data' in prediction_result and 'predicted_sectors' in prediction_result['data']:\n                # 优化版行业分析器格式\n                predictions = prediction_result['data']['predicted_sectors']\n                \n                # 适配字段名\n                for pred in predictions:\n                    if 'prediction_score' not in pred and 'score' in pred:\n                        pred['prediction_score'] = pred['score']\n                    if 'predicted_change_pct' not in pred and 'predicted_5d_change' in pred:\n                        pred['predicted_change_pct'] = pred['predicted_5d_change']\n                    if 'confidence' not in pred and 'prediction_confidence' in pred:\n                        pred['confidence'] = pred['prediction_confidence']"
    content = re.sub(prediction_result_pattern, replacement, content)
    
    # 将修复后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"文件 {file_path} 的热门行业分析功能已更新")

if __name__ == "__main__":
    # 更新stock_analyzer_app.py文件
    update_hot_industries('stock_analyzer_app.py')
    print("更新完成!") 