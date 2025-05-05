import akshare as ak
import pandas as pd

try:
    # 获取北向资金数据
    print("尝试获取北向资金数据...")
    north_flow = ak.stock_hsgt_fund_flow_summary_em()
    
    print("\n可用列名:")
    print(north_flow.columns.tolist())
    
    print("\n数据示例:")
    print(north_flow.head())
    
    # 检查可能包含资金流向值的列
    print("\n通过北向资金的数据类型查找可能的数值列:")
    for col in north_flow.columns:
        try:
            # 尝试转换为浮点数来找到值列
            val = pd.to_numeric(north_flow[col].iloc[-1])
            print(f"列 '{col}' 最后一行的值为: {val}")
        except:
            continue
            
except Exception as e:
    print(f"获取数据时出错: {str(e)}") 