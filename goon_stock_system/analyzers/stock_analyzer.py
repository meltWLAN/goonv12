def analyze_technical_factors(ts_code, start_date=None, end_date=None, output_format='table'):
    """分析股票的技术面因子
    
    Args:
        ts_code (str): 股票代码
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
        output_format (str, optional): 输出格式，'table' 或 'json'
        
    Returns:
        dict or pd.DataFrame: 技术面因子分析结果
    """
    from ..utils.tushare_api import get_stk_factor, get_daily_data, get_stock_basics
    
    # 获取股票信息
    stock_info = get_stock_basics(ts_code=ts_code)
    if stock_info.empty:
        print(f"未找到股票 {ts_code} 的基本信息")
        return pd.DataFrame() if output_format == 'table' else {}
    
    # 获取技术面因子数据
    factors_df = get_stk_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
    if factors_df.empty:
        print(f"未找到股票 {ts_code} 在指定日期范围的技术面因子数据")
        return pd.DataFrame() if output_format == 'table' else {}
    
    # 计算常用指标的趋势
    if len(factors_df) > 1:
        # 按日期排序
        factors_df = factors_df.sort_values('trade_date')
        
        # 计算移动平均线趋势
        factors_df['ma5_trend'] = factors_df['ma5'].diff().apply(lambda x: '上升' if x > 0 else '下降' if x < 0 else '平稳')
        factors_df['ma10_trend'] = factors_df['ma10'].diff().apply(lambda x: '上升' if x > 0 else '下降' if x < 0 else '平稳')
        factors_df['ma20_trend'] = factors_df['ma20'].diff().apply(lambda x: '上升' if x > 0 else '下降' if x < 0 else '平稳')
        
        # 计算MACD信号
        factors_df['macd_signal'] = (factors_df['macd'] > 0).apply(lambda x: '多头' if x else '空头')
        
        # 计算KDJ信号
        factors_df['kdj_signal'] = ((factors_df['kdj_j'] > factors_df['kdj_k']) & 
                                   (factors_df['kdj_k'] > factors_df['kdj_d'])).apply(lambda x: '金叉' if x else '死叉')
    
    # 获取最新的因子数据
    latest_factors = factors_df.iloc[-1] if not factors_df.empty else None
    
    if latest_factors is not None:
        # 构建分析结果
        analysis_result = {
            'ts_code': ts_code,
            'name': stock_info.iloc[0]['name'] if not stock_info.empty else '',
            'latest_date': latest_factors['trade_date'],
            'price': latest_factors['close'],
            'technical_indicators': {
                'macd': {
                    'dif': latest_factors['macd_dif'],
                    'dea': latest_factors['macd_dea'],
                    'macd': latest_factors['macd'],
                    'signal': latest_factors.get('macd_signal', '')
                },
                'kdj': {
                    'k': latest_factors['kdj_k'],
                    'd': latest_factors['kdj_d'],
                    'j': latest_factors['kdj_j'],
                    'signal': latest_factors.get('kdj_signal', '')
                },
                'rsi': {
                    'rsi_6': latest_factors['rsi_6'],
                    'rsi_12': latest_factors['rsi_12'],
                    'rsi_24': latest_factors['rsi_24']
                },
                'boll': {
                    'upper': latest_factors['boll_upper'],
                    'mid': latest_factors['boll_mid'],
                    'lower': latest_factors['boll_lower']
                },
                'ma': {
                    'ma5': latest_factors['ma5'],
                    'ma10': latest_factors['ma10'],
                    'ma20': latest_factors['ma20'],
                    'ma30': latest_factors['ma30'],
                    'ma60': latest_factors['ma60'],
                    'ma120': latest_factors['ma120'],
                    'ma250': latest_factors['ma250'],
                    'ma5_trend': latest_factors.get('ma5_trend', ''),
                    'ma10_trend': latest_factors.get('ma10_trend', ''),
                    'ma20_trend': latest_factors.get('ma20_trend', '')
                }
            },
            'max_drawdown': latest_factors['max_dd'] if 'max_dd' in latest_factors else None,
            'volume_ratio': latest_factors['vol_ratio'] if 'vol_ratio' in latest_factors else None
        }
        
        if output_format == 'json':
            return analysis_result
        else:
            # 构建表格形式的结果
            result_df = pd.DataFrame([
                {'指标类型': 'MACD', '指标值': f"DIF: {latest_factors['macd_dif']:.4f}, DEA: {latest_factors['macd_dea']:.4f}, MACD: {latest_factors['macd']:.4f}", '信号': latest_factors.get('macd_signal', '')},
                {'指标类型': 'KDJ', '指标值': f"K: {latest_factors['kdj_k']:.2f}, D: {latest_factors['kdj_d']:.2f}, J: {latest_factors['kdj_j']:.2f}", '信号': latest_factors.get('kdj_signal', '')},
                {'指标类型': 'RSI', '指标值': f"RSI6: {latest_factors['rsi_6']:.2f}, RSI12: {latest_factors['rsi_12']:.2f}, RSI24: {latest_factors['rsi_24']:.2f}", '信号': '超买' if latest_factors['rsi_6'] > 80 else '超卖' if latest_factors['rsi_6'] < 20 else '中性'},
                {'指标类型': 'BOLL', '指标值': f"上轨: {latest_factors['boll_upper']:.2f}, 中轨: {latest_factors['boll_mid']:.2f}, 下轨: {latest_factors['boll_lower']:.2f}", '信号': '上穿上轨' if latest_factors['close'] > latest_factors['boll_upper'] else '下穿下轨' if latest_factors['close'] < latest_factors['boll_lower'] else '区间内'},
                {'指标类型': '均线', '指标值': f"MA5: {latest_factors['ma5']:.2f}, MA10: {latest_factors['ma10']:.2f}, MA20: {latest_factors['ma20']:.2f}", '信号': f"MA5: {latest_factors.get('ma5_trend', '')}, MA10: {latest_factors.get('ma10_trend', '')}, MA20: {latest_factors.get('ma20_trend', '')}"},
                {'指标类型': '其他', '指标值': f"最大回撤: {latest_factors.get('max_dd', 'N/A')}, 量比: {latest_factors.get('vol_ratio', 'N/A')}", '信号': ''}
            ])
            
            return result_df
    
    return pd.DataFrame() if output_format == 'table' else {}

def analyze_nineturn(ts_code, freq='D', start_date=None, end_date=None, output_format='table'):
    """分析股票的神奇九转指标
    
    Args:
        ts_code (str): 股票代码
        freq (str, optional): 周期类型 (D-日, W-周, M-月)
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
        output_format (str, optional): 输出格式，'table' 或 'json'
        
    Returns:
        dict or pd.DataFrame: 神奇九转指标分析结果
    """
    from ..utils.tushare_api import get_stk_nineturn, get_stock_basics
    
    # 获取股票信息
    stock_info = get_stock_basics(ts_code=ts_code)
    if stock_info.empty:
        print(f"未找到股票 {ts_code} 的基本信息")
        return pd.DataFrame() if output_format == 'table' else {}
    
    # 获取神奇九转指标数据
    nineturn_df = get_stk_nineturn(ts_code=ts_code, freq=freq, start_date=start_date, end_date=end_date)
    if nineturn_df.empty:
        print(f"未找到股票 {ts_code} 在指定日期范围的神奇九转指标数据")
        return pd.DataFrame() if output_format == 'table' else {}
    
    # 按日期排序
    nineturn_df = nineturn_df.sort_values('trade_date')
    
    # 获取最新的指标数据
    latest_data = nineturn_df.iloc[-1]
    
    if output_format == 'json':
        result = {
            'ts_code': ts_code,
            'name': stock_info.iloc[0]['name'] if not stock_info.empty else '',
            'latest_date': latest_data['trade_date'],
            'freq': latest_data['freq'],
            'nturn_value': latest_data['nturn_value'],
            'nt_remark': latest_data['nt_remark'],
            'nt_signal': latest_data['nt_signal'],
            'history': nineturn_df.to_dict('records')
        }
        return result
    else:
        # 添加股票名称列
        nineturn_df['name'] = stock_info.iloc[0]['name'] if not stock_info.empty else ''
        
        # 选择要显示的列并重命名
        result_df = nineturn_df[['ts_code', 'name', 'trade_date', 'freq', 'nturn_value', 'nt_remark', 'nt_signal']]
        result_df.columns = ['股票代码', '股票名称', '交易日期', '周期', '神奇九转值', '级别', '信号']
        
        return result_df

def analyze_auction_data(ts_code, auction_type='open', start_date=None, end_date=None, output_format='table'):
    """分析股票的集合竞价数据
    
    Args:
        ts_code (str): 股票代码
        auction_type (str): 竞价类型，'open' 为开盘竞价，'close' 为收盘竞价
        start_date (str, optional): 开始日期，格式YYYYMMDD
        end_date (str, optional): 结束日期，格式YYYYMMDD
        output_format (str, optional): 输出格式，'table' 或 'json'
        
    Returns:
        dict or pd.DataFrame: 集合竞价分析结果
    """
    from ..utils.tushare_api import get_stk_auction_o, get_stk_auction_c, get_stock_basics
    
    # 获取股票信息
    stock_info = get_stock_basics(ts_code=ts_code)
    if stock_info.empty:
        print(f"未找到股票 {ts_code} 的基本信息")
        return pd.DataFrame() if output_format == 'table' else {}
    
    # 根据竞价类型获取数据
    if auction_type == 'open':
        auction_df = get_stk_auction_o(ts_code=ts_code, start_date=start_date, end_date=end_date)
    else:  # 'close'
        auction_df = get_stk_auction_c(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    if auction_df.empty:
        print(f"未找到股票 {ts_code} 在指定日期范围的{auction_type}集合竞价数据")
        return pd.DataFrame() if output_format == 'table' else {}
    
    # 按日期排序
    auction_df = auction_df.sort_values('trade_date')
    
    if output_format == 'json':
        result = {
            'ts_code': ts_code,
            'name': stock_info.iloc[0]['name'] if not stock_info.empty else '',
            'auction_type': auction_type,
            'auction_data': auction_df.to_dict('records')
        }
        return result
    else:
        # 添加股票名称列
        auction_df['name'] = stock_info.iloc[0]['name'] if not stock_info.empty else ''
        
        # 选择要显示的列
        columns = auction_df.columns.tolist()
        # 将名称和代码移到前面
        if 'name' in columns:
            columns.remove('name')
            columns = ['name'] + columns
        if 'ts_code' in columns:
            columns.remove('ts_code')
            columns = ['ts_code'] + columns
            
        result_df = auction_df[columns]
        
        # 重命名列
        rename_dict = {
            'ts_code': '股票代码',
            'name': '股票名称',
            'trade_date': '交易日期'
        }
        
        result_df = result_df.rename(columns=rename_dict)
        
        return result_df 