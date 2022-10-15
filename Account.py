import pandas as pd
import numpy as np

import logging
import os 
import sys
import math

log_file_name = "./log/account.log"
if not os.path.exists('log'):
	os.mkdir('log')

logging.basicConfig(level=logging.INFO, #设置日志输出格式
                    filename=log_file_name, #log日志输出的文件位置和文件名
                    filemode="w", #文件的写入格式，w为重新写入文件，默认是追加
                    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s", 
                    # 日志输出的格式,-8表示占位符，让输出左对齐，输出长度都为8位
                    datefmt="%Y-%m-%d %H:%M:%S", #时间输出的格式
                    )

class Account():
	def __init__(self, cash=1e8, fee_percent=0):
		self.cash = cash # 持有的现金
		self.init_cash = cash
		self.stock_positions = {} # key: stock 名字, value: 持有标的总股数
		self.price_table = None # 标的价格表, series
		self._fee_percent = fee_percent # 交易费用, 默认为0, 回测常取0.0005

	@property
	def fee_percent(self):
		return self._fee_percent

	@fee_percent.setter
	def fee_percent(self, _fee_pct):
		self._fee_percent = _fee_pct

	def set_price_table(self, prices):
		if not isinstance(prices, pd.Series):
			raise NameError('input prices error, please input price cross section series')
		for stock_name in self.stock_positions:
			try:
				p = prices.loc[stock_name]
			except KeyError:
				logging.error(f'stock {stock_name} price not exsist')
				raise KeyError(f'stock {stock_name} price not exsist')
			if math.isnan(p) and self.stock_positions[stock_name] > 1e-6:
				logging.warning(f'stock {stock_name} price is NAN')
				# raise KeyError(f'stock {stock_name} price is NAN')
		self.price_table = prices

	def show_asset(self):
		for stock_name, pos in self.stock_positions.items():
			if pos == 0:
				continue
			else:
				logging.info(f'hold stock {stock_name} position {pos}')

	def get_stock_position(self):
		return self.stock_positions

	def refresh_account(self):
		self.cash = self.init_cash
		self.stock_positions = {}

	def set_init_cash(self, money):
		self.cash = money
		self.init_cash = money

	def get_total_asset(self):
		money = np.round(self.cash, 2)
		for stock_name, pos in self.stock_positions.items():
			# print(f'stock {stock_name} pos {pos}')
			if pos > 1e-6:
				p = self.price_table.loc[stock_name]
				if math.isnan(pos * p):
					raise NameError(f'stock {stock_name} pos {pos} price {p}')
				else:
					money += pos * p					
		return np.round(money, 2)

	def get_cash(self):
		return self.cash

	def buy_stock_by_money(self, stock_name='STOCK', money=1e3):
		'''
		stocke_name: 买入标的名称
		stock_price: 买入单价
		money: 买入的总价格
		按照指定的总价格买入，注意此处的总价格包含了已持有的标的价值
		'''
		assert money >= 0
		buy_money = money
		stock_price = self.price_table.loc[stock_name]
		# stock_price = np.round(float(stock_price), 2)
		hold_pos = self.stock_positions.get(stock_name)
		if hold_pos in [None, 0]:
			pass
		elif hold_pos > 0:
			hold_money = hold_pos * stock_price
			# 已经持有标的
			if buy_money < hold_money:
				# 买入总价格比当前持有的标的总价值小
				if buy_money != 0:
					logging.info('buy warning, target buy money smaller than the hold value, sell the stock actually')
				self.sell_stock_by_money(stock_name=stock_name, money=hold_money-buy_money)
				buy_money = 0
				return
			else:
				# 买入总价格比当前持有的标的总价值大
				buy_money = np.round(buy_money - hold_money, 2)
		if buy_money > self.cash:
			# 需要额外买入的总价格大于当前持有的现金
			logging.info('buy warning, target buy money larger than the cash')
			buy_money = self.cash

		if buy_money == 0:
			return
		if self.cash < 5:
			logging.info(f'buy failed, lack of cash for fee!')
			return

		def calculate_buy_money_volume_fee(_buy_money, _buy_volume=100):
			if np.round(_buy_money / stock_price, 2) % 100 == 0:
				_buy_volume = np.round(_buy_money / stock_price, 2)
			else :
				_buy_volume = _buy_money // stock_price
			if _buy_volume < 100:
				logging.info(f'buy warning, stock {stock_name} price {stock_price}, buy money {_buy_money}, buy volume {_buy_volume} < 100, failed to buy. before buy volume {hold_pos}')
				return 0, 0, 0
			# 买入股数为100的整数倍
			_buy_volume = _buy_volume // 100 * 100
			_buy_money = np.round(_buy_volume * stock_price, 2)
			_fee = _buy_money * self._fee_percent
			if self._fee_percent > 0:
				_fee = max(_fee, 5)
			_fee = np.round(_fee, 2)
			return _buy_money, _buy_volume, _fee

		buy_money, buy_volume, fee = calculate_buy_money_volume_fee(buy_money, 100)

		# 如果现金不足以支付买入股票的费用和交易费用, 则以现金扣除买入股票费用剩余的部分为最大交易费用, 反推总买入费用
		if fee > 0 and np.round(self.cash - buy_money, 2) < fee :
			buy_money = np.round(self.cash - buy_money, 2) / self._fee_percent
			buy_money, buy_volume, fee = calculate_buy_money_volume_fee(buy_money, 100)
			assert self.cash - buy_money >= fee

		if hold_pos != None:
			self.stock_positions[stock_name] += buy_volume
		else:
			self.stock_positions[stock_name] = buy_volume
		self.cash = np.round(self.cash - buy_money, 2) 
		self.cash = np.round(self.cash - fee, 2)
		if buy_money != 0:
			logging.info(f'buy stock {stock_name}, before buy volume {hold_pos}, buy money {buy_money}, fee {fee}, volume {buy_volume} after buy cash {self.cash}')


	def sell_stock_by_money(self, stock_name='STOCK', money=1e3):
		'''
		按照指定的总价格卖出
		'''
		assert money > 0, f'ERROR: money {money}'
		hold_pos = self.stock_positions.get(stock_name)
		stock_price = self.price_table.loc[stock_name]
		# stock_price = np.round(float(stock_price), 2)
		sell_money = money

		if hold_pos in [None, 0]:
			raise NameError(f'sell error, stock {stock_name} not hold')
		hold_money = hold_pos * stock_price
		if sell_money >= hold_money:
			# logging.info('sell warning, target money larger than the hold value, sell all stocks')
			sell_money = np.round(hold_money, 2)
			sell_volume = hold_pos
		else:
			if np.round(sell_money / stock_price, 2) % 100 == 0:
				sell_volume = np.round(sell_money / stock_price, 2)
			else :
				sell_volume = sell_money // stock_price // 100 * 100
			sell_money = np.round(sell_volume * stock_price, 2)

		self.stock_positions[stock_name] -= sell_volume
		self.cash = np.round(self.cash + sell_money, 2)
		fee = sell_money * self._fee_percent
		if self._fee_percent > 0:
			fee = max(fee, 5)
		fee = np.round(fee, 2)
		self.cash = np.round(self.cash - fee, 2)
		logging.info(f'sell stock {stock_name}, before sell volume {hold_pos}, sell money {sell_money}, fee {fee}, volume {sell_volume} after sell cash {self.cash}')

	def order_stock_by_percent(self, stock_name='STOCK', percent=1):
		'''
		按照当前总资产价值的一定比例进行买卖
		'''
		assert percent>=0 and percent<=1
		total_asset = self.get_total_asset()
		money = total_asset * percent
		self.buy_stock_by_money(stock_name=stock_name, money=money)


	def buy_stock_by_volumns(self, stock_name='STOCK', volume=100):
		'''
		按照指定的股数买入
		'''
		stock_price = self.price_table.loc[stock_name]
		buy_money = stock_price * volume
		assert buy_money >= 0
		self.buy_stock_by_money(stock_name=stock_name, money=buy_money)

	def sell_stock_by_volumns(self, stock_name='STOCK', volume=100):
		'''
		按照指定的股数卖出
		'''
		stock_price = self.price_table.loc[stock_name]
		sell_money = stock_price * volume
		assert sell_money > 0
		self.sell_stock_by_money(stock_name=stock_name, money=sell_money)



