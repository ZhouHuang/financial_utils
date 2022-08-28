import pandas as pd
from Account import Account
import copy

import logging

logging.basicConfig(level=logging.INFO, #设置日志输出格式
                    filename="./log/backtest.log", #log日志输出的文件位置和文件名
                    filemode="w", #文件的写入格式，w为重新写入文件，默认是追加
                    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s", 
                    # 日志输出的格式,-8表示占位符，让输出左对齐，输出长度都为8位
                    datefmt="%Y-%m-%d %H:%M:%S", #时间输出的格式
                    )

class BackTest():
	def __init__(self, init_cash=1e8, number_of_longs=1):
		self.account = Account(cash=init_cash)
		self.underlying = None # 标的资产价格
		self.trade_date = [] # 交易日
		self.df_score = None # 打分表, 所有标的资产的日期序列
		self.asset_values = None # 总资产, 日期序列, 一列
		self.number_of_longs = number_of_longs # 多头标的个数
		self.df_position = {} # 持有标的的仓位, 日期序列, e.g. {pd.Timestamp('2020-01-01'):account.stock_value}

	def set_init_cash(self, money):
		self.account.set_init_cash(money)

	def get_number_of_longs(self):
		return self.number_of_longs

	def set_number_of_longs(self, n):
		self.number_of_longs = n

	def load_underlying(self, df):
		if not isinstance(df, pd.DataFrame):
			raise NameError('input error, please load underlying price [DataFrame]')
		self.underlying = df.copy()

	def set_trade_date(self, li):
		if not isinstance(li, list):
			raise NameError('input error, please load trade date [list]')
		self.trade_date = li.copy()

	def _calculate_score(self):
		if self.underlying is None:
			raise NameError('input error, please load underlying price [DataFrame] first')
		if len(self.trade_date) == 0:
			raise NameError('input error, please set trade date [list] first')
		self.df_score = pd.DataFrame(index=self.trade_date, columns=self.underlying.columns)
		'''
		# implement score calculation here
		# 因子显示，标的越优秀，打分越低，比如国开1分，信用2分，应当买入国开
		'''
		# return self.df_score

	def _set_stock_position(self, stocks, date):
		'''
		stocks: 标的名称,list
		date: 交易日期, pd.Timestamp
		return: dict, 不同标的，在交易日期应当持有的总资金
		可以简单均分，也可以ATR仓位控制
		'''
		assert len(stocks) == self.number_of_longs and self.number_of_longs > 0
		# ---- 均分资金 -----
		total_asset = self.account.get_total_asset()
		pos = {}
		for s in stocks:
			pos[s] = total_asset / self.number_of_longs
		return pos 

	def _handle_bar(self, position):
		'''
		position: 当日的标的和其资金仓位
		'''
		pass

	def calculate_profit(self):
		self.asset_values = pd.DataFrame(columns=['LONG', 'SHORT'], index=self.trade_date)

		df_long = pd.DataFrame(columns=self.trade_date)
		df_short = pd.DataFrame(columns=self.trade_date)

		# 按因子打分选出预测表现最好和最差的标的
		for i, day in enumerate(self.trade_date):
		    df_long[day] = self.df_score.loc[day].sort_values().head(self.number_of_longs).index.to_list()
		    df_short[day] = self.df_score.loc[day].sort_values().tail(self.number_of_longs).index.to_list()

		df_long = df_long.T
		df_short = df_short.T
		dict_position = {} # 预设的仓位，实际上未必能完全复刻

		total_asset_long = []
		self.account.refresh_account()
		# long
		# ----- initial state ------
		logging.info(f'initial state: cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')

		for i, day in enumerate(self.trade_date):
		    # ----- before trade -------
		    logging.info(f'date: {day}, before trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
		    total_asset_long.append(self.account.get_total_asset())
		    stocks = df_long.loc[day].values
		    dict_position[day] = _set_stock_position(stocks=stocks, date=day)
		    _handle_bar(position=dict_position[day])
		    # ----- after trade -------
		    # logging.info(f'date: {day}, after trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
		self.df_position = dict_position.copy()
		self.asset_values['LONG'] = total_asset_long

		total_asset_short = []
		self.account.refresh_account()
		# short
		# ----- initial state ------
		logging.info(f'initial state: cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')

		for i, day in enumerate(self.trade_date):
		    # ----- before trade -------
		    logging.info(f'date: {day}, before trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
		    total_asset_short.append(self.account.get_total_asset())
		    stocks = df_short.loc[day].values
		    dict_position[day] = _set_stock_position(stocks=stocks, date=day)
		    _handle_bar(position=dict_position[day])
		    # ----- after trade -------
		    # logging.info(f'date: {day}, after trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')

		self.asset_values['SHORT'] = total_asset_short

		'''
		## 多头和空头的收益率
		long_ir = pd.DataFrame(index=self.trade_date, columns=range(number_of_longs))
		short_ir = pd.DataFrame(index=self.trade_date, columns=range(number_of_longs))

		for day_i in range(len(long_ir.index)):
		    day = long_ir.index[day_i]
		    if day_i==0:
		        continue
		    for j in range(number_of_longs):
		        # 回测，填入下期的收益率
		        bond_code = df_long.loc[day, j]
		        long_ir.loc[day,i] = df_bond_profit.loc[day,bond_code]
		        bond_code = df_short.loc[day,j]
		        short_ir.loc[day,i] = df_bond_profit.loc[day,bond_code]

		long_net = long_ir.mean(axis=1)[1:].to_frame('LONG').shift(1)
		short_net = short_ir.mean(axis=1)[1:].to_frame('SHORT').shift(1)

		for i in range(len(long_net.index)):
		    # 基准点选为1 或行业等权的净值
		    if i==0:
		        long_net.iloc[i] = 1
		        short_net.iloc[i] = 1
		    else:
		        long_net.iloc[i] = long_net.iloc[i-1] * (1 + long_net.iloc[i])
		        short_net.iloc[i] = short_net.iloc[i-1] * (1 + short_net.iloc[i])
		'''

	@staticmethod
	def strategy_info(df: pd.DataFrame(), group: str):
	    """
	    df: 策略净值
	    gourp: 'LONG' 
	    最大回撤 最大亏损 按年来算，收益也按年算
	    """
	    
	    def get_return_by_year(arr):
	        return arr[-1] / arr[0] - 1

	    print(group,'策略 各年度收益',df.resample('1Y').apply(get_return_by_year))

	    print(group,'策略 最大回撤',1 - (df / df.expanding().max()).sort_values(by=group).iloc[0,0], 
	          ' 日期 ', (df / df.expanding().max()).sort_values(by=group).index[0])
	    print(group,'策略 最大净值', df.max())
	    first_day = df.index[0]
	    last_day = df.index[-1]
	    ir_yearly = (df.loc[last_day] - df.loc[first_day])/ df.loc[first_day] / ((last_day.date() - first_day.date())/datetime.timedelta(days=1)) * 365
	    print(group,'策略 {sy}年至{ey}年间 年化收益率'.format(sy=first_day,ey=last_day), ir_yearly[0])

	    df_ir = df / df.shift(1) - 1
	    df_ir.iloc[0] = 0
	    print(group,'策略 年化波动率', (df_ir.std()[0] * np.sqrt(52)))
	    print(group,'策略 夏普比率(忽略无风险收益率)', (ir_yearly[0]) / (df_ir.std()[0] * np.sqrt(52)))
	    print('-'*20)
	    print()
	    return ir_yearly[0], (ir_yearly[0]) / (df_ir.std()[0] * np.sqrt(52))
