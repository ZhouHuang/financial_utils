import pandas as pd

import os

code_to_name = {'CBA02521.CS':'国开1-3年',
                'CBA02551.CS':'国开7-10年',
                'CBA04221.CS':'信用3A1-3年',
                'CBA04251.CS':'信用3A7-10年'}

df_index = pd.read_csv('./wind_data/指数数据/close.csv')
df_index['DateTime'] = df_index['DateTime'].astype('datetime64[ns]')
df_index = df_index.set_index('DateTime')
df_index = df_index[sorted(df_index.columns.to_list())]
df_index = df_index.dropna(axis=0)
df_index = df_index.rename(code_to_name, axis='columns')


ytm_3y3A = pd.read_excel('./wind_data/到期收益率/中债中短期票据收益率曲线-全.xlsx', index_col=0)
ytm_3y3A = ytm_3y3A.query('中债中短期票据到期收益率3年AAA!=0')
ytm_3y3A.index = ytm_3y3A.index.astype('datetime64[ns]')

ytm_10y = pd.read_excel('./wind_data/到期收益率/中债国开债收益率曲线-全.xlsx', index_col=0)
ytm_10y = ytm_10y.query('中债国开债到期收益率10年!=0')
ytm_10y.index = ytm_10y.index.astype('datetime64[ns]')
ytm_10y = ytm_10y.loc[ytm_3y3A.index]

df_increase_rate = pd.DataFrame(index=ytm_3y3A.index)
df_increase_rate['y10Y'] = ytm_10y['中债国开债到期收益率10年']
df_increase_rate['y3Y3A'] = ytm_3y3A['中债中短期票据到期收益率3年AAA']

df_rate_sub = pd.DataFrame(columns=['rate_sub'])
df_rate_sub['rate_sub'] = df_increase_rate['y10Y'] - df_increase_rate['y3Y3A']

from Factor import Factor 

date_format_list = df_index.query('index>"2014-12-15" and index<"2022-08-14"').index.to_list()
# print(len(date_format_list))
Factor.set_date_format(li=date_format_list)
fac_rate_sub = Factor(df_series=df_rate_sub['rate_sub'])
# print(fac_rate_sub.get_factor())

from BackTest import BackTest
import matplotlib.pyplot as plt

tester = BackTest()

df_date_weekly = pd.read_csv('./wind_data/日期序列/weekly.csv', index_col=0)
df_date_weekly['DateTime'] = df_date_weekly['DateTime'].astype('datetime64[ns]')

tester.underlying = df_index[['国开7-10年','信用3A1-3年']]
tester.trade_date = df_date_weekly.DateTime.to_list()
tester.df_factors = df_rate_sub
tester.runTest()

df_asset = tester.asset_values
df_asset.plot()
plt.show()
