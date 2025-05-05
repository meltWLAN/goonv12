import akshare as ak
import pandas as pd

try:
    # 获取行业资金流向数据
    print("尝试获取行业资金流向数据...")
    sector_flow = ak.stock_sector_fund_flow_rank(indicator="今日")
    
    print("\n可用列名:")
    print(sector_flow.columns.tolist())
    
    print("\n前两行数据示例:")
    print(sector_flow.head(2))
    
    # 检查是否有类似于"净额"的列
    fund_columns = [col for col in sector_flow.columns if '净' in col or 'flow' in col.lower() or '资金' in col]
    print("\n可能的资金流向列:")
    print(fund_columns)
    
except Exception as e:
    print(f"获取数据时出错: {str(e)}") 