import pandas as pd
from Account import Account
import copy

import logging
import os 

log_file_name = "./log/backtest.log"
if not os.path.exists('log'):
	os.mkdir('log')


logging.basicConfig(level=logging.INFO, #设置日志输出格式
                    filename=log_file_name, #log日志输出的文件位置和文件名
                    filemode="w", #文件的写入格式，w为重新写入文件，默认是追加
                    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s", 
                    # 日志输出的格式,-8表示占位符，让输出左对齐，输出长度都为8位
                    datefmt="%Y-%m-%d %H:%M:%S", #时间输出的格式
                    )

class BackTest():
	def __init__(self, init_cash=1e8, number_of_longs=1, number_of_groups=2):
		self.account = Account(cash=init_cash)
		self._underlying = None # 标的资产价格
		self._index_component = None # 每日指数成分股，即股票池
		self._trade_date = [] # 交易日
		self._df_score = None # 打分表, 所有标的资产的日期序列
		self._asset_values = None # 总资产, 日期序列, 一列
		self._number_of_groups = number_of_groups
		self._number_of_longs = number_of_longs # 多头标的个数
		self._df_position = {} # 持有标的的仓位, 日期序列, e.g. {pd.Timestamp('2020-01-01'):account.stock_positions}
		self._df_factors = None # 多因子的时间序列
		self._df_long = None # 空头标的 时间序列
		self._df_short = None # 多头标的 时间序列
		self._df_long_group = [] # 分组
		self._st_board = None # ST 风险警示板, dataframe
		self._pause_board = None # 标的停牌, dataframe

	def runTest(self):
		self._calculate_score()
		self._calculate_profit()

	@property
	def df_score(self):
		return self._df_score

	@property
	def asset_values(self):
		return self._asset_values

	def set_init_cash(self, money):
		self.account.set_init_cash(money)

	@property
	def st_board(self):
		return self._st_board

	@st_board.setter 
	def st_board(self, df):
		if not isinstance(df, pd.DataFrame):
			raise NameError('input error, please load st board [DataFrame]')
		self._st_board = df.copy()

	@property
	def pause_board(self):
		return self._pause_board

	@pause_board.setter
	def pause_board(self, df):
		if not isinstance(df, pd.DataFrame):
			raise NameError('input error, please load pause board [DataFrame]')
		self._pause_board = df.copy()

	@property
	def number_of_groups(self):
		return self._number_of_groups

	@number_of_groups.setter 
	def number_of_groups(self, n):
		self._number_of_groups = n

	@property
	def number_of_longs(self):
		return self._number_of_longs

	@number_of_longs.setter
	def number_of_longs(self, n):
		self._number_of_longs = n

	@property
	def index_component(self):
		return self._index_component

	@index_component.setter
	def index_component(self, df):
		if not isinstance(df, pd.DataFrame):
			raise NameError('input error, please load index component [DataFrame]')
		self._index_component = df.copy()

	@property
	def underlying(self):
		return self._underlying

	@underlying.setter
	def underlying(self, df):
		if not isinstance(df, pd.DataFrame):
			raise NameError('input error, please load underlying price [DataFrame]')
		self._underlying = df.copy()

	@property
	def df_long_group(self):
		return self._df_long_group

	@property
	def df_long(self):
		return self._df_long

	@property
	def df_short(self):
		return self._df_short

	@property
	def df_factors(self):
		return self._df_factors

	@df_factors.setter
	def df_factors(self, df):
		if not isinstance(df, pd.DataFrame):
			raise NameError('input error, please load factors [DataFrame]')
		if df.index[0] >= self._trade_date[0]:
			raise NameError('input factor date do not cover the trading date')
		self._df_factors = df.copy()
		print(f'df factors shape {df.shape}')

	@property
	def trade_date(self):
		return self._trade_date

	@trade_date.setter
	def trade_date(self, li):
		if not isinstance(li, list):
			raise NameError('input error, please load trade date [list]')
		self._trade_date = li.copy()

	def _calculate_score(self):
		'''
		计算每日因子打分. 
		因为涉及未来数据原因, 可能无法取得当天的因子值, 用前一日的因子值代替
		'''
		if self._underlying is None:
			raise NameError('input error, please load underlying price [DataFrame] first')
		if self._index_component is None:
			raise NameError('input error, please load index component [DataFrame] first')
		if len(self._trade_date) == 0:
			raise NameError('input error, please set trade date [list] first')
		self._df_score = pd.DataFrame(index=self._trade_date, columns=self._underlying.columns)
		'''
		# implement score calculation here
		# 因子显示，标的越优秀，打分越低，比如国开1分，信用2分，应当买入国开
		'''
		'''
		temp_list = []
		for i,day in enumerate(self._trade_date):
			if i % 2 == 0:
				s = [n for n in range(len(self._underlying.columns))]
			else:
				s = [n for n in range(len(self._underlying.columns))][::-1]
			temp_list.append(s)
		self._df_score[self._underlying.columns] = temp_list
		'''
		temp_list = []
		if self._df_factors is None:
			raise NameError('load the factor [DataFrame] first')
		factor_date = self._df_factors.index.to_list()

		# 带记忆的查找
		previous_day_idx = 0
		for i,day in enumerate(self._trade_date):
			for j,factor_day in enumerate(factor_date[previous_day_idx:]):
				if factor_day >= day:
					assert j>=1
					previous_day_idx = j-1
					break
			# 找到交易日前一个日期的因子
			previous_day = factor_date[previous_day_idx]
			factors = self._df_factors.loc[previous_day]
			# 找到交易日当日的因子
			# factores = self._df_factors.loc[day]

			# 根据因子值，判断应该交易的标的打分情况
			# 1.一或多个共有因子判断多个标的分数，非横截面
			# profit = factors.values[0]
			# if profit>=0:
			# 	# 国开
			# 	s = [1,2]
			# else:
			# 	# 信用
			# 	s = [2,1]
			# 2.每个标的一个因子，横截面因子
			s = factors.rank().values 

			temp_list.append(s)

		self._df_score[self._underlying.columns] = temp_list
		self._df_long = pd.DataFrame(columns=self._trade_date)
		self._df_short = pd.DataFrame(columns=self._trade_date)

		for _ in range(self._number_of_groups):
			self._df_long_group.append(pd.DataFrame(columns=self._trade_date))

		# 按因子打分选出预测表现最好和最差的标的
		for i, day in enumerate(self._trade_date):
			ordered_score_total_underlyings = self._df_score.loc[day].sort_values().index.to_list()
			stock_pool = list(self._index_component.loc[day].values)
			# 考虑当前交易日停牌或ST的情况，
			_st = self._st_board.loc[day, stock_pool]
			stock_pool = _st[_st==0].index.to_list()
			_pause = self._pause_board.loc[day, stock_pool]
			stock_pool = _pause[_pause==0].index.to_list()
			# 从股票池中选出股票，按打分排序，打分低的为多头，打分高的为空头
			ordered_score_underlyings = [stock for stock in ordered_score_total_underlyings if stock in stock_pool]

			self._df_long[day] = ordered_score_underlyings[0:self._number_of_longs]
			self._df_short[day] = ordered_score_underlyings[len(ordered_score_underlyings)-self._number_of_longs:]
			for i_group in range(self._number_of_groups):
				self._df_long_group[i_group][day] = ordered_score_underlyings[len(ordered_score_underlyings)//self._number_of_groups*i_group : len(ordered_score_underlyings)//self._number_of_groups*i_group + self._number_of_longs]


		self._df_long = self._df_long.T
		self._df_short = self._df_short.T
		for i_group in range(self._number_of_groups):
			self._df_long_group[i_group] = self._df_long_group[i_group].T

		self._asset_values = pd.DataFrame(columns=['group_'+str(i+1) for i in range(self._number_of_groups)], index=self._trade_date)

	def _set_stock_position(self, stocks, date):
		'''
		stocks: 标的名称,list
		date: 交易日期, pd.Timestamp
		return: dict, 不同标的，在交易日期应当持有的总资金
		可以简单均分，也可以ATR仓位控制
		'''
		assert len(stocks) == self._number_of_longs and self._number_of_longs > 0
		# ---- 均分资金 -----
		total_asset = self.account.get_total_asset()
		pos = {}
		for s in stocks:
			pos[s] = total_asset / self._number_of_longs
		return pos 

	def _handle_bar(self, position):
		'''
		position: 当日的标的和其资金仓位
		'''
		before_positions = self.account.get_stock_position()

		for stock_name, pos in before_positions.items():
			# 持仓为零的标的
			if pos == 0:
				continue
			if stock_name not in position.keys():
				# 已持有的标的不存在于新的持仓列表中，全部卖出
				self.account.order_stock_by_percent(stock_name=stock_name, percent=0)

		for stock_name, money in position.items():
			self.account.buy_stock_by_money(stock_name=stock_name, money=money)



	def _calculate_profit(self):
		'''
		根据每日仓位，计算每日收益
		'''
		# self._asset_values = pd.DataFrame(columns=['LONG', 'SHORT'], index=self._trade_date)

		# long
		dict_position = {} # 预设的仓位，实际上未必能完全复刻
		self.account.refresh_account()
		total_asset_long = []

		# ----- initial state ------
		logging.info(f'long initial state')

		for i, day in enumerate(self._trade_date):
		    # ----- before trade -------
		    self.account.set_price_table(prices=self._underlying.loc[day])

		    logging.info(f'date: {day}, before trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
		    # 每日交易前的资产总和
		    total_asset_long.append(self.account.get_total_asset())
		    stocks = self._df_long.loc[day].values

		    # -------- trade ----------
		    dict_position[day] = self._set_stock_position(stocks=stocks, date=day)
		    self._handle_bar(position=dict_position[day])

		    # ----- after trade -------
		    # logging.info(f'date: {day}, after trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
		self._df_position = dict_position.copy()
		# self._asset_values['LONG'] = total_asset_long

		# short
		dict_position = {}
		self.account.refresh_account()
		total_asset_short = []

		# ----- initial state ------
		logging.info(f'short initial state')

		for i, day in enumerate(self._trade_date):
		    # ----- before trade -------
		    self.account.set_price_table(prices=self._underlying.loc[day])
		    
		    logging.info(f'date: {day}, before trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
		    total_asset_short.append(self.account.get_total_asset())
		    stocks = self._df_short.loc[day].values

		    # -------- trade ----------
		    dict_position[day] = self._set_stock_position(stocks=stocks, date=day)
		    self._handle_bar(position=dict_position[day])

		    # ----- after trade -------
		    # logging.info(f'date: {day}, after trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')

		# self._asset_values['SHORT'] = total_asset_short

		# group test

		for i_group in range(self._number_of_groups):
			df_long_group_i = self._df_long_group[i_group]
			dict_position = {}
			self.account.refresh_account()
			total_asset_list = []
			# ----- initial state ------
			logging.info(f'group {i_group} test initial state')

			for i, day in enumerate(self._trade_date):
			    # ----- before trade -------
			    self.account.set_price_table(prices=self._underlying.loc[day])
			    
			    logging.info(f'date: {day}, before trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')
			    total_asset_list.append(self.account.get_total_asset())
			    stocks = df_long_group_i.loc[day].values

			    # -------- trade ----------
			    dict_position[day] = self._set_stock_position(stocks=stocks, date=day)
			    self._handle_bar(position=dict_position[day])

			    # ----- after trade -------
			    # logging.info(f'date: {day}, after trade, cash {self.account.get_cash()}, total asset {self.account.get_total_asset()}')

			self._asset_values['group_'+str(i_group+1)] = total_asset_list

	@staticmethod
	def strategy_info(df: pd.DataFrame(), group: str):
	    """
	    df: 策略净值
	    gourp: 'LONG' , 策略名称
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
