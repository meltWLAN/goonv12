#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证智能推荐系统的股票展示
"""

from smart_recommendation_system import get_recommendation_system, create_recommendation
import os

def main():
    # 获取推荐系统实例
    print("正在获取智能推荐系统实例...")
    sys = get_recommendation_system()
    
    # 获取所有推荐
    all_recommendations = sys.get_all_recommendations()
    print(f"智能推荐系统中共有股票: {len(all_recommendations)}个")
    
    # 按评分排序，获取前10只
    top_recommendations = sorted(
        all_recommendations.values(), 
        key=lambda x: x.score, 
        reverse=True
    )[:10]
    
    # 打印排名靠前的推荐
    print("\n按评分排序的前10只股票:")
    print("{:<10} {:<15} {:<10} {:<10} {:<20}".format(
        "股票代码", "股票名称", "评分", "来源", "推荐理由(部分)"
    ))
    print("-" * 80)
    
    for rec in top_recommendations:
        # 显示推荐理由的前30个字符
        short_reason = rec.reason[:30] + "..." if len(rec.reason) > 30 else rec.reason
        
        print("{:<10} {:<15} {:<10.2f} {:<10} {:<20}".format(
            rec.stock_code,
            rec.stock_name,
            rec.score,
            rec.source,
            short_reason
        ))
    
    # 显示推荐来源统计
    sources = {}
    for rec in all_recommendations.values():
        sources[rec.source] = sources.get(rec.source, 0) + 1
    
    print("\n推荐来源统计:")
    for source, count in sources.items():
        print(f"{source}: {count}个推荐")
    
    # 显示标签统计
    tags = {}
    for rec in all_recommendations.values():
        for tag in rec.tags:
            tags[tag] = tags.get(tag, 0) + 1
    
    print("\n标签统计:")
    for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
        print(f"{tag}: {count}个推荐")

    # 检查是否可以生成报告
    print("\n正在测试报告生成功能...")
    try:
        report_path = sys.generate_recommendation_report()
        if os.path.exists(report_path):
            print(f"报告生成成功: {report_path}")
            report_size = os.path.getsize(report_path) / 1024  # KB
            print(f"报告大小: {report_size:.2f} KB")
        else:
            print("报告生成失败: 文件不存在")
    except Exception as e:
        print(f"报告生成出错: {str(e)}")

def test_add_recommendation():
    """测试添加新推荐"""
    print("\n===== 测试添加新推荐 =====")
    sys = get_recommendation_system()
    
    # 创建测试推荐
    test_rec = create_recommendation(
        stock_code="000001",
        stock_name="平安银行",
        entry_price=20.50,
        target_price=23.58,
        stop_loss=19.27,
        reason="测试添加的推荐: MACD金叉，量能放大，突破前高",
        source="测试系统",
        score=92.0,
        tags=["测试标签", "银行股", "技术突破"]
    )
    
    # 添加到系统
    if sys.add_recommendation(test_rec):
        print("测试推荐添加成功")
        
        # 查询验证
        print("查询验证中...")
        all_recs = sys.get_all_recommendations()
        if "000001" in all_recs:
            print("推荐在系统中找到")
            rec = all_recs["000001"]
            print(f"股票名称: {rec.stock_name}")
            print(f"评分: {rec.score}")
            print(f"标签: {', '.join(rec.tags)}")
            
            # 删除测试推荐
            if sys.remove_recommendation("000001", "测试完成"):
                print("测试推荐已删除")
            else:
                print("测试推荐删除失败")
        else:
            print("错误: 推荐未添加到系统")
    else:
        print("测试推荐添加失败")

if __name__ == "__main__":
    main()
    # 取消注释以测试添加推荐功能
    test_add_recommendation() 