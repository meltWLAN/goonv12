import numpy as np
from datetime import datetime, timedelta
from backtesting import Backtester

# 生成测试数据
def generate_test_data(days=30):
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    prices = np.random.normal(100, 10, days).cumsum()
    return dates, prices

# 执行测试交易
def run_backtest():
    tester = Backtester(initial_capital=100000)
    dates, prices = generate_test_data()

    # 执行系列买卖操作
    mean_price = np.mean(prices)
    for i in range(len(dates)):
        if prices[i] < mean_price * 0.98:
            tester.execute_trade(dates[i], 'TEST', 'buy', prices[i], 50)
        elif prices[i] > mean_price * 1.02 and i > 0:
            tester.execute_trade(dates[i], 'TEST', 'sell', prices[i], 30)

    # 验证核心指标
    result = tester.calculate_metrics()
    
    print("\n=== 关键指标验证 ===")
    print(f"总交易次数: {result.trade_count}")
    print(f"总收益: {result.total_profit:.2f}")
    print(f"胜率: {result.win_rate*100:.2f}%")
    print(f"最大回撤: {result.max_drawdown:.2f}")
    print(f"平均持仓周期: {result.avg_holding_period:.1f}天")

    # 基本逻辑验证
    assert result.trade_count > 0, "未执行任何交易"
    assert result.total_profit != 0, "收益计算异常"
    assert 0 <= result.win_rate <= 1, "胜率数值异常"

if __name__ == "__main__":
    run_backtest()
    print("\n✅ 回测功能基本验证通过")