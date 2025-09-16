# -*- coding: utf-8 -*-
# Backtrader + Baostock 分钟线可视化（支持 1m/5m，含成交量；可选交互）
import os
import sys
import math
import pandas as pd
import numpy as np
import datetime as dt

import baostock as bs
import backtrader as bt

# ========== 用户参数 ==========
SYMBOL = 'sh.601012'        # 隆基绿能（Baostock代码前缀：sh./sz.）
FREQ   = '5'                # '1' = 1分钟, '5' = 5分钟
DAYS   = 5                  # 最近 N 个交易日
ADJ    = '3'                # 复权：'1'后复权 / '2'前复权 / '3'不复权（分钟线建议 3）
USE_BOKEH = True            # True: 用 backtrader_plotting 互动图；False: Matplotlib
TITLE  = f'{SYMBOL} 近{DAYS}个交易日 {FREQ}分钟'

# ========== 数据获取 ==========
def fetch_baostock_minute_df(code, start_date, end_date, freq='5', adj='3'):
    """
    从 Baostock 拉分钟线到 DataFrame。
    fields: date,time,code,open,high,low,close,volume,amount
    """
    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f'Baostock 登录失败: {lg.error_code}, {lg.error_msg}')

    fields = 'date,time,code,open,high,low,close,volume,amount'
    rs = bs.query_history_k_data_plus(
        code, fields,
        start_date=start_date, end_date=end_date,
        frequency=freq, adjustflag=adj
    )
    if rs.error_code != '0':
        bs.logout()
        raise RuntimeError(f'Baostock 查询失败: {rs.error_code}, {rs.error_msg}')

    data_list = []
    while rs.next():
        data_list.append(rs.get_row_data())
    bs.logout()

    if not data_list:
        return pd.DataFrame()

    df = pd.DataFrame(data_list, columns=fields.split(','))
    # 转换数据类型
    num_cols = ['open','high','low','close','volume','amount']
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    # 组合时间戳
    if 'time' in df.columns and df['time'].notna().any():
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    else:
        df['datetime'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['datetime'])
    df = df.sort_values('datetime')
    # 设为索引供 Backtrader 使用
    df.set_index('datetime', inplace=True)
    # Backtrader 需要的列名：open high low close volume openinterest
    df['openinterest'] = 0
    return df[['open','high','low','close','volume','openinterest']]

def get_last_n_trade_day_range(n=5):
    """取最近 n 个交易日的自然日范围（向后多给几天做缓冲）。"""
    today = dt.date.today()
    start = today - dt.timedelta(days=20)   # 粗取20天，涵盖节假日
    return start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')

# ========== Backtrader 策略（仅展示，不交易） ==========
class ShowOnly(bt.Strategy):
    params = dict()
    def __init__(self):
        # 可以在这里加指标（例如均线/MACD），仅用于图上展示
        self.sma_fast = bt.ind.SMA(self.data.close, period=20)
        self.sma_slow = bt.ind.SMA(self.data.close, period=60)
        # MACD 示例（如要做信号：交叉可作为金叉/死叉）
        self.macd = bt.ind.MACD(self.data, period_me1=12, period_me2=26, period_signal=9)
        self.crossover = bt.ind.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        # 只看图，不自动交易；需要可在此写下单逻辑
        pass

# ========== 主流程 ==========
def run():
    start, end = get_last_n_trade_day_range(DAYS)
    print(f'取数区间: {start} ~ {end}  |  频率: {FREQ}min  |  复权: {ADJ}')

    df = fetch_baostock_minute_df(SYMBOL, start, end, freq=FREQ, adj=ADJ)
    if df.empty:
        print('未获得数据，请检查代码/频率/时间范围/网络。')
        sys.exit(0)

    # 仅保留最近 N 个交易日的分钟数据（按日期切片）
    # 用 index.date 分组，取最近 N 个不同日期
    dates = pd.Index(df.index.date).unique()
    last_n = dates[-DAYS:] if len(dates) >= DAYS else dates
    df = df[df.index.date.astype('O').isin(last_n)]

    # 准备 Backtrader
    cerebro = bt.Cerebro()
    # timeframe & compression
    compression = int(FREQ)
    data = bt.feeds.PandasData(
        dataname=df,
        timeframe=bt.TimeFrame.Minutes,
        compression=compression
    )
    cerebro.adddata(data, name=f'{SYMBOL}-{FREQ}m')
    cerebro.addstrategy(ShowOnly)
    cerebro.broker.setcash(1_000_000.0)
    cerebro.broker.setcommission(commission=0.0003)  # 仅示例

    # 画图
    if USE_BOKEH:
        try:
            from backtrader_plotting import Bokeh
            from backtrader_plotting.schemes import Tradimo
            b = Bokeh(style='bar', plot_mode='single', scheme=Tradimo(), filename='bt_plot.html', output_mode='show')
            cerebro.plot(b)
        except Exception as e:
            print(f'[WARN] Bokeh 绘图失败，回退为 Matplotlib：{e}')
            cerebro.plot(style='candle', barup='red', bardown='green', volup='red', voldown='green')
    else:
        cerebro.plot(style='candle', barup='red', bardown='green', volup='red', voldown='green')

if __name__ == '__main__':
    run()
