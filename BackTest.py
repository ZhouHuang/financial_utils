import pandas as pd
import numpy as np
from Account import Account
import copy
from tqdm import tqdm

import logging
import os 
import datetime

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
	def __init__(self, init_cash=1e8, number_of_longs=1, number_of_groups=1, fee_percent=0, portfolio_optimizer=None):
		self.account = Account(cash=init_cash, fee_percent=fee_percent)
		self._underlying = None # 标的资产价格
		self._index_component = None # 每日指数成分股，即股票池
		self._trade_date = [] # 交易日
		self._df_score = None # 打分表, 所有标的资产的日期序列
		self._asset_values = None # 总资产, 日期序列, 一列
		self._cash_values = None # 每日剩余的现金, 用于计算仓位, pd.Series
		self._number_of_groups = number_of_groups
		self._number_of_longs = number_of_longs # 多头标的个数
		self._df_position = {} # 持有标的的仓位, 日期序列, e.g. {pd.Timestamp('2020-01-01'):account.stock_positions}
		self._df_factors = None # 多因子的时间序列
		self._df_long_group = [] # 分组
		self._st_board = None # ST 风险警示板, dataframe
		self._pause_board = None # 标的停牌, dataframe
		self._turnover = None # 每日交易金额和当日交易前总资产的比值, pd.Series
		self._turnover_buy = None # 每日交易金额中买入标的花费, pd.Series
		self._turnover_sell = None # 每日交易金额中卖出标的所得, pd.Series
		self._portfolio_optimizer = portfolio_optimizer # 组合优化, 默认是均分资产
		self.__optimizer_mode = False

	def runTest(self):
		opt_method = ['MeanVarianceMinimum', 'CSI500enhancement']
		if self._portfolio_optimizer is None:
			print('Back testing by group...')
		else:
			print('Portfolio optimizing...')
			if self._portfolio_optimizer in opt_method and self._number_of_groups == 1 and self._number_of_longs==500:
				self.__optimizer_mode = True
			elif self._portfolio_optimizer not in opt_method:
				raise KeyError(f'Optimizer must be {opt_method}, got {self._portfolio_optimizer}')
			elif self._number_of_groups != 1 or self._number_of_longs != 500:
				raise KeyError(f'In portfolio optimizing mode, number of groups must be 1 (got {self._number_of_groups}), number of longs must be 500 (got {self._number_of_longs})')
		self._calculate_score()
		self._calculate_profit()

	@property
	def turnover(self):
		return self._turnover

	@property
	def turnover_sell(self):
		return self._turnover_sell

	@property
	def turnover_buy(self):
		return self._turnover_buy

	@property
	def df_score(self):
		return self._df_score

	@property
	def asset_values(self):
		return self._asset_values

	@property
	def cash_values(self):
		return self._cash_values

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
		print('*'*20)
		print('计算每日因子打分')
		print('*'*20)
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

		if self._df_factors is None:
			raise NameError('load the factor [DataFrame] first')

		# 检查标的dataframe的名字是否和因子dataframe一致
		test_underlying_names = self._underlying.columns.to_list()
		test_factor_underlying_names = self._df_factors.columns.to_list()
		for i,underlying_name in enumerate(test_underlying_names):
			if underlying_name != test_factor_underlying_names[i]:
				raise KeyError('Underlying and factors DataFrame do not match!')

		factor_date = self._df_factors.index.to_list()

		temp_list = []
		# 带记忆的查找
		previous_day_idx = -1
		for i,day in enumerate(self._trade_date):
			for j in range(previous_day_idx+1, len(factor_date)):
				factor_day = factor_date[j]
				if factor_day >= day:
					assert j>=1
					previous_day_idx = j-1
					break
			# 找到交易日前一个日期的因子
			previous_day = factor_date[previous_day_idx]
			factors = self._df_factors.loc[previous_day]
			# 找到交易日当日的因子
			# factors = self._df_factors.loc[day]

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
			# 注意此处ascending=False,即factor越高，标的越优秀，打分s越低，最终df_score里面排序为1，2，3...，1是最好的标的
			s = factors.rank(ascending=False).values 

			temp_list.append(s)

		self._df_score[self._underlying.columns] = temp_list

		for _ in range(self._number_of_groups):
			self._df_long_group.append(pd.DataFrame(columns=self._trade_date))

		# 按因子打分选出预测表现最好和最差的标的
		progress_bar = tqdm(list(self._trade_date))
		for i, day in enumerate(progress_bar):
			progress_bar.set_description(f'Processing {str(day)[:10]}')

			ordered_score_total_underlyings = self._df_score.loc[day].sort_values(ascending=False).index.to_list()
			stock_pool = list(self._index_component.loc[day].values)
			# 考虑当前交易日停牌或ST的情况，
			_st = self._st_board.loc[day, stock_pool]
			stock_pool = _st[_st==0].index.to_list()
			_pause = self._pause_board.loc[day, stock_pool]
			stock_pool = _pause[_pause==0].index.to_list()
			# 从股票池中选出股票，按打分排序，打分低的为多头，打分高的为空头
			ordered_score_underlyings = [stock for stock in ordered_score_total_underlyings if stock in stock_pool]

			for i_group in range(self._number_of_groups):
				self._df_long_group[i_group][day] = \
					ordered_score_underlyings[len(ordered_score_underlyings)//self._number_of_groups*i_group : len(ordered_score_underlyings)//self._number_of_groups*i_group + self._number_of_longs]

		for i_group in range(self._number_of_groups):
			self._df_long_group[i_group] = self._df_long_group[i_group].T

		self._asset_values = pd.DataFrame(columns=['group_'+str(i+1) for i in range(self._number_of_groups)], index=self._trade_date)
		self._cash_values = pd.Series(index=self._trade_date, name='Cash')
		self._turnover = pd.Series(index=self._trade_date)
		self._turnover_buy = pd.Series(index=self._trade_date, name='money')
		self._turnover_sell = pd.Series(index=self._trade_date, name='money')

	def _set_stock_position(self, stocks, date, total_asset):
		'''
		stocks: 标的名称,list
		date: 交易日期, pd.Timestamp
		return: dict, 不同标的，在交易日期应当持有的总资金
		可以简单均分，也可以ATR仓位控制
		'''
		assert len(stocks) == self._number_of_longs and self._number_of_longs > 0
		# ---- 均分资金 -----
		stock_price_table = self.account.price_table
		pos = {}
		for s in stocks:
			stock_price = stock_price_table.loc[s]
			# 单个标的持有的总资金是100股的股价的倍数
			pos[s] = np.round(total_asset / self._number_of_longs // stock_price // 100 * stock_price * 100, 2)
		return pos 

	def _handle_bar(self, position, date, total_asset, i_group):
		'''
		position: 当日的标的和其资金仓位
		'''
		before_positions = self.account.get_stock_position()
		turnover = 0
		turnover_sell = 0
		turnover_buy = 0

		for stock_name, pos in before_positions.items():
			# 持仓为零的标的
			if pos == 0:
				continue
			if stock_name not in position.keys():
				# 已持有的标的不存在于新的持仓列表中，全部卖出
				trade_money, trade_volume, fee, _ = self.account.order_stock_by_percent(stock_name=stock_name, percent=0, total_asset=total_asset)
				turnover += trade_money
				turnover_sell += trade_money

		for stock_name, money in position.items():
			trade_money, trade_volume, fee, buy_flag = self.account.buy_stock_by_money(stock_name=stock_name, money=money)
			turnover += trade_money
			if buy_flag:
				turnover_buy += trade_money
			else:
				turnover_sell += trade_money

		if i_group == 0:
			self._turnover.loc[date] = turnover / total_asset
			self._turnover_buy.loc[date] = turnover_buy 
			self._turnover_sell.loc[date] = turnover_sell

	def _handle_after_trade(self, date, i_group):
		if i_group == 0:
			self._cash_values.loc[date] = self.account.get_cash()
		# 记录每日真实持仓数，进而计算每日盈亏

	def _calculate_profit(self):
		'''
		根据每日仓位，计算每日收益
		'''
		print('*'*20)
		print('计算每日收益')
		print('*'*20)

		# group test

		for i_group in range(self._number_of_groups):
			print(f'Processing group {i_group}')
			df_long_group_i = self._df_long_group[i_group]
			dict_position = {}
			self.account.refresh_account()
			total_asset_list = []
			# ----- initial state ------
			logging.info(f'group {i_group} test initial state')

			progress_bar = tqdm(list(self._trade_date))
			for i, day in enumerate(progress_bar):
			    progress_bar.set_description(f'Processing {str(day)[:10]}')
			    # ----- before trade -------
			    self.account.set_price_table(prices=self._underlying.loc[day])
			    total_asset = self.account.get_total_asset()
			    logging.info(f'date: {day}, before trade, cash {self.account.get_cash()}, total asset {total_asset}')
			    total_asset_list.append(total_asset)
			    stocks = df_long_group_i.loc[day].values

			    # -------- trade ----------
			    dict_position[day] = self._set_stock_position(stocks=stocks, date=day, total_asset=total_asset)
			    self._handle_bar(position=dict_position[day], date=day, total_asset=total_asset, i_group=i_group)

			    # ----- after trade -------
			    self._handle_after_trade(date=day, i_group=i_group)

			self._asset_values['group_'+str(i_group+1)] = total_asset_list

	@staticmethod
	def print_info(df: pd.Series, df_benchmark: pd.Series):
		'''
		年化收益率，夏普比率，最大回撤，超额收益率，年华超额收益率
		'''
		if not isinstance(df, pd.Series):
			raise NameError(f'Input df should be pd.Series, got {type(df)}')
		if not isinstance(df_benchmark, pd.Series):
			raise NameError(f'Input df_benchmark should be pd.Series, got {type(df)}')
		print('*'*20)
		print(df.name)
		print('*'*20)
		# 年华收益率
		ir_total = df.values[-1] / df.values[0] - 1
		first_day = df.index[0]
		last_day = df.index[-1]
		print(f'开始日期 {first_day} 结束日期 {last_day}')
		ir_yearly = pow((1+ir_total), 1/((last_day.date() - first_day.date())/datetime.timedelta(days=1)/365)) - 1
		print('策略 年化收益率', np.round(ir_yearly, 4))
		df_ir = df / df.shift(1) - 1
		df_ir.iloc[0] = 0
		print('策略 年化波动率', np.round((df_ir.std() * np.sqrt(52)), 4))
		print('策略 夏普比率(忽略无风险收益率)', np.round( (ir_yearly) / (df_ir.std() * np.sqrt(52)), 4) )
		print('策略 最大回撤', np.round( 1 - (df / df.expanding().max()).sort_values().iloc[0], 4), 
		      ' 日期 ', (df / df.expanding().max()).sort_values().index[0])

		exceed_ir = df.iloc[-1] / df_benchmark.iloc[-1] - 1
		print('策略 超额收益率', np.round(exceed_ir, 4))

		ir_total = df_benchmark.values[-1] / df_benchmark.values[0] - 1
		first_day = df.index[0]
		last_day = df.index[-1]
		benchmark_ir_yearly = pow((1+ir_total), 1/((last_day.date() - first_day.date())/datetime.timedelta(days=1)/365)) - 1

		exceed_ir_yealy = (1 + ir_yearly) / (1 + benchmark_ir_yearly) - 1 
		print('策略 超额年化收益率', np.round(exceed_ir_yealy, 4) )

		print('周均超额收益率...')
		
		def __get_week_last_value(array_like):
		    if array_like.size != 0:
		        return array_like.values.reshape(-1,)[-1]
		    else:
		        return np.nan
		value_weekly = df.resample('W').apply(__get_week_last_value)
		benchmark_value_weekly = df_benchmark.resample('W').apply(__get_week_last_value)

		df_ir_weekly = value_weekly / value_weekly.shift(1) - 1
		df_benchmark_ir_weekly = benchmark_value_weekly / benchmark_value_weekly.shift(1) - 1
		exceed_ir_weekly = (1 + df_ir_weekly) / (1 + df_benchmark_ir_weekly) - 1
		return exceed_ir_weekly


		    