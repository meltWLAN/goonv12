#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将热门行业分析功能集成到主系统中
"""

import os
import sys
import re
import shutil
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("IntegrationScript")

def backup_file(file_path):
    """备份文件"""
    backup_path = f"{file_path}.integration.bak"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份 {file_path} 到 {backup_path}")
        return True
    except Exception as e:
        logger.error(f"备份 {file_path} 失败: {str(e)}")
        return False

def update_hot_industry_analysis():
    """更新热门行业分析功能"""
    # 需要更新的文件
    file_path = "stock_analyzer_app.py"
    
    # 首先备份文件
    if not backup_file(file_path):
        logger.error("由于备份失败，停止更新")
        return False
    
    logger.info(f"开始更新 {file_path} 中的热门行业分析功能...")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已导入优化版行业分析器
        if "from optimized_sector_analyzer import OptimizedSectorAnalyzer" not in content:
            # 添加导入语句
            import_pattern = r"import logging\n"
            replacement = "import logging\nfrom optimized_sector_analyzer import OptimizedSectorAnalyzer  # 导入优化版行业分析器\n"
            content = re.sub(import_pattern, replacement, content)
            
            logger.info("已添加优化版行业分析器的导入语句")
        
        # 查找并替换热门行业分析方法
        analyze_pattern = r"def analyze_hot_industries\(self\):.*?except Exception as e:.*?self\.result_text\.append\(f\"分析发生错误: {str\(e\)}\"\)"
        
        # 新的热门行业分析方法
        new_method = '''def analyze_hot_industries(self):
        """热门行业分析和预测功能"""
        try:
            self.result_text.clear()
            self.result_text.append("正在分析热门行业数据，请稍候...")
            QApplication.processEvents()  # 更新UI
            
            # 初始化行业分析器 - 使用优化版行业分析器
            try:
                # 优先使用优化版行业分析器
                sector_analyzer = OptimizedSectorAnalyzer(top_n=15, provider_type='akshare')
                self.logger.info("使用优化版行业分析器(AKShare)")
            except Exception as e:
                # 如果优化版分析器初始化失败，直接显示错误
                self.logger.error(f"行业分析器初始化失败: {str(e)}")
                self.show_error_message('初始化失败', f"行业分析器初始化失败: {str(e)}")
                return
            
            # 获取热门行业分析结果
            self.result_text.append("正在获取行业列表及计算热度...")
            QApplication.processEvents()  # 更新UI
            result = sector_analyzer.analyze_hot_sectors()
            
            # 处理结果
            if 'error' in result:
                self.show_error_message('分析失败', f"热门行业分析失败: {result['error']}")
                return
                
            # 获取热门行业列表
            hot_sectors = result['data']['sectors']
            
            # 获取市场信息
            market_info = result['data'].get('market_info', {
                'market_sentiment': 0,
                'north_flow': 0,
                'volatility': 0,
                'shanghai_change_pct': 0,
                'shenzhen_change_pct': 0,
                'market_avg_change': 0
            })
            
            # 生成热门行业分析报告
            self.result_text.append("\\n===== 热门行业分析报告 =====")
            self.result_text.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.result_text.append(f"市场情绪指数: {market_info.get('market_sentiment', 0):.2f}")
            self.result_text.append(f"北向资金流入(亿元): {market_info.get('north_flow', 0):.2f}")
            self.result_text.append(f"市场波动率: {market_info.get('volatility', 0):.2f}%")
            
            # 显示热门行业排名
            self.result_text.append("\\n【热门行业排名】")
            for i, sector in enumerate(hot_sectors[:10]):  # 显示前10个行业
                # 格式化输出，确保所有必要字段存在
                score = sector.get('score', 0)
                change_1d = sector.get('change_rate_1d', 0)
                
                self.result_text.append(f"{i+1}. {sector['name']} ({sector['code']}) - "
                                      f"评分: {score:.2f} - 涨跌幅: {change_1d:.2f}%")
                
                # 显示更多详细信息
                self.result_text.append(f"   5日涨幅: {sector.get('change_rate_5d', 0):.2f}% | "
                                      f"20日涨幅: {sector.get('change_rate_20d', 0):.2f}% | "
                                      f"趋势强度: {sector.get('trend_strength', 0):.2f}")
            
            # 对比行业与大盘趋势
            self.result_text.append("\\n【行业与大盘对比】")
            QApplication.processEvents()  # 更新UI
            
            try:
                # 获取大盘涨跌
                market_trend = {
                    'shanghai_pct': market_info.get('shanghai_change_pct', 0),
                    'shenzhen_pct': market_info.get('shenzhen_change_pct', 0)
                }
                
                # 获取热门行业中跑赢大盘的比例
                outperform_sectors = [s for s in hot_sectors[:15] if s.get('change_rate_1d', 0) > market_info.get('market_avg_change', 0)]
                outperform_pct = len(outperform_sectors) / min(15, len(hot_sectors)) * 100
                
                self.result_text.append(f"大盘表现: 沪指涨跌 {market_trend['shanghai_pct']:.2f}%, 深指涨跌 {market_trend['shenzhen_pct']:.2f}%")
                self.result_text.append(f"行业超越大盘比例: {outperform_pct:.1f}%")
                
                if outperform_pct > 70:
                    self.result_text.append("市场特征: 行业普遍强于大盘，呈现普涨格局")
                elif outperform_pct < 30:
                    self.result_text.append("市场特征: 行业普遍弱于大盘，呈现普跌格局")
                else:
                    self.result_text.append("市场特征: 行业表现分化，结构性行情明显")
            except Exception as e:
                self.logger.warning(f"获取行业趋势对比数据失败: {str(e)}")
            
            # 获取行业预测结果
            self.result_text.append("\\n正在预测未来行业走势...")
            QApplication.processEvents()  # 更新UI
            
            try:
                prediction_result = sector_analyzer.predict_hot_sectors()
                
                if 'error' in prediction_result:
                    self.result_text.append(f"\\n预测分析失败: {prediction_result['error']}")
                else:
                    # 获取预测行业列表
                    predicted_sectors = prediction_result['data']['predicted_sectors']
                    
                    # 显示预测结果
                    self.result_text.append("\\n【行业走势预测】")
                    self.result_text.append(f"预测周期: {prediction_result['data'].get('prediction_period', '5天')}")
                    
                    for i, pred in enumerate(predicted_sectors[:5]):  # 显示前5个预测
                        self.result_text.append(f"{i+1}. {pred['name']} - 预测评分: {pred.get('score', 0):.2f} - "
                                             f"预测涨跌: {pred.get('predicted_5d_change', 0):.2f}% - "
                                             f"置信度: {pred.get('prediction_confidence', 0):.2f}%")
                        if 'reason' in pred:
                            self.result_text.append(f"   理由: {pred['reason']}")
                    
                    # 行业轮动分析
                    self.result_text.append("\\n【行业轮动分析】")
                    if 'rotation_analysis' in prediction_result['data']:
                        rotation = prediction_result['data']['rotation_analysis']
                        self.result_text.append(f"当前轮动阶段: {rotation.get('current_stage', '未知')}")
                        self.result_text.append(f"轮动方向: {rotation.get('rotation_direction', '未知')}")
                        
                        if 'next_sectors' in rotation:
                            self.result_text.append("可能的下一轮行业:")
                            for sector in rotation['next_sectors'][:3]:
                                self.result_text.append(f"- {sector}")
                    
                    # 行业景气度分析
                    self.result_text.append("\\n【行业景气度评估】")
                    
                    # 计算行业景气度
                    prosperity_data = self._calculate_sector_prosperity(hot_sectors[:15], predicted_sectors[:10])
                    
                    # 显示景气度结果
                    prosperity_data.sort(key=lambda x: x['prosperity_score'], reverse=True)
                    for i, item in enumerate(prosperity_data[:5]):
                        self.result_text.append(f"{i+1}. {item['name']} - 景气度: {item['prosperity_score']:.1f}")
                        self.result_text.append(f"   当前热度: {item['current_heat']:.1f} | 预期变化: {item['change_trend']}")
            except Exception as e:
                self.logger.error(f"预测热门行业时出错: {str(e)}")
                self.result_text.append(f"\\n预测分析失败: {str(e)}")
            
            # 生成投资建议
            self.result_text.append("\\n【投资建议】")
            self.result_text.append("根据行业分析和预测，建议关注以下方向:")
            
            # 提取短期和中期机会
            short_term = [s for s in hot_sectors[:5] if s.get('score', 0) > 50]
            mid_term = [p for p in predicted_sectors[:5] if p.get('score', 0) > 50]
            
            if short_term:
                self.result_text.append("短期关注:")
                for s in short_term:
                    self.result_text.append(f"- {s['name']}: {s.get('analysis_reason', '热度高')}")
            
            if mid_term:
                self.result_text.append("中期布局:")
                for m in mid_term:
                    self.result_text.append(f"- {m['name']}: {m.get('reason', '预期向好')}")
            
            # 强调风险提示
            self.result_text.append("\\n⚠️ 风险提示: 行业分析仅供参考，投资决策需结合多方面因素，注意控制风险。")
            
        except Exception as e:
            import traceback
            self.logger.error(f"热门行业分析出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.show_error_message('分析错误', f"热门行业分析过程中出错: {str(e)}")
            self.result_text.append(f"分析发生错误: {str(e)}")'''
        
        # 替换方法
        content = re.sub(analyze_pattern, new_method, content, flags=re.DOTALL)
        
        logger.info("已替换热门行业分析方法")
        
        # 将修改后的内容写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"成功更新 {file_path} 中的热门行业分析功能")
        return True
    
    except Exception as e:
        logger.error(f"更新 {file_path} 失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始集成热门行业分析功能...")
    
    # 更新热门行业分析功能
    if update_hot_industry_analysis():
        logger.info("热门行业分析功能集成完成!")
    else:
        logger.error("热门行业分析功能集成失败!")
        sys.exit(1)
    
    logger.info("集成完成，请启动主程序测试功能!") 