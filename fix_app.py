#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复stock_analyzer_app.py中的语法错误
"""

with open('stock_analyzer_app.py', 'r') as f:
    content = f.read()

# 找到问题代码的开始位置
start = content.find('# 将强烈推荐的股票添加到智能推荐系统')
# 找到问题代码的结束位置
end = content.find('def visualize_stocks', start)

# 要替换的问题代码片段
old_code = content[start:end]

# 修复后的代码
fixed_code = """            # 将强烈推荐的股票添加到智能推荐系统
            if HAS_SMART_RECOMMENDATION:
                try:
                    # 获取智能推荐系统实例
                    smart_system = get_recommendation_system()
                    
                    # 过滤出强烈推荐买入的股票
                    strong_recommendations = [r for r in sorted_recommendations 
                                            if r.get('recommendation', '') == '强烈推荐买入' or
                                               r.get('recommendation', '') == '建议买入']
                    
                    # 添加到智能推荐系统
                    from smart_recommendation_system import create_recommendation, StockRecommendation
                    added_to_smart = 0
                    
                    for rec in strong_recommendations[:5]:  # 限制只添加前5个最强推荐
                        # 创建推荐对象
                        stock_code = rec['symbol']
                        stock_name = rec.get('name', rec.get('symbol', '未知'))
                        current_price = rec.get('last_price', rec.get('close', 0))
                        
                        # 计算目标价和止损价
                        target_price = current_price * 1.15  # 15%盈利目标
                        stop_loss = current_price * 0.92    # 8%止损线
                        
                        # 构建推荐理由
                        reason = f"技术分析推荐：{rec.get('recommendation', '建议买入')}。"
                        if rec.get('trend') == 'uptrend':
                            reason += " 处于上升趋势。"
                        if rec.get('volume', 0) > rec.get('volume_ma20', 1):
                            reason += f" 成交量放大{rec.get('volume', 0)/rec.get('volume_ma20', 1):.1f}倍。"
                        
                        # 添加推荐
                        new_recommendation = create_recommendation(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            entry_price=current_price,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            reason=reason,
                            source="股票分析系统",
                            score=85.0,
                            tags=["技术分析", rec.get('trend', 'unknown')]
                        )
                        
                        if smart_system.add_recommendation(new_recommendation):
                            added_to_smart += 1
                    
                    if added_to_smart > 0:
                        self.result_text.append(f'\\n已将 {added_to_smart} 只强烈推荐股票添加到智能推荐系统')
                except Exception as e:
                    self.result_text.append(f'\\n添加股票到智能推荐系统时出错: {str(e)}')
        
        except Exception as e:
            QMessageBox.warning(self, '错误', f'分析过程中出错：{str(e)}')
    
    """

# 替换问题代码
fixed_content = content.replace(old_code, fixed_code)

# 保存修复后的文件
with open('stock_analyzer_app.py', 'w') as f:
    f.write(fixed_content)

print("文件已修复") 