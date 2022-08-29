import pandas as pd
import numpy as np

import logging
import os 
import sys

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
	def __init__(self, cash=1e8):
		self.cash = cash # 持有的现金
		self.init_cash = cash
		self.stock_positions = {} # key: stock 名字, value: 持有标的总股数
		self.price_table = None # 标的价格表, series

	def set_price_table(self, prices):
		if not isinstance(prices, pd.Series):
			raise NameError('input prices error, please input price cross section series')
		for stock_name in self.stock_positions:
			try:
				p = prices.loc[stock_name]
			except KeyError:
				logging.error(f'stock {stock_name} price not exsist')
				sys.exit()
		self.price_table = prices

	def get_stock_position(self):
		return self.stock_positions

	def refresh_account(self):
		self.cash = self.init_cash
		self.stock_positions = {}

	def set_init_cash(self, money):
		self.cash = money
		self.init_cash = money

	def get_total_asset(self):
		money = self.cash
		for stock_name, pos in self.stock_positions.items():
			p = self.price_table.loc[stock_name]
			money += pos * p
		return money

	def get_cash(self):
		return self.cash

	def buy_stock_by_money(self, stock_name='STOCK', money=1e3):
		'''
		stocke_name: 买入标的名称
		stock_price: 买入单价
		money: 买入的总价格
		按照指定的总价格买入，注意此处的总价格包含了已持有的标的价值
		'''
		assert money > 0
		buy_money = money
		stock_price = self.price_table.loc[stock_name]
		hold_pos = self.stock_positions.get(stock_name)
		if hold_pos in [None, 0]:
			pass
		elif hold_pos > 0:
			hold_money = hold_pos * stock_price
			# 已经持有标的
			if buy_money < hold_money:
				# 买入总价格比当前持有的标的总价值小
				logging.warning('buy warning, target buy money smaller than the hold value, sell the stock actually')
				self.sell_stock_by_money(stock_name=stock_name, money=hold_money-buy_money)
				buy_money = 0
			else:
				# 买入总价格比当前持有的标的总价值大
				buy_money -= hold_money
		if buy_money > self.cash:
			# 需要额外买入的总价格大于当前持有的现金
			logging.warning('buy warning, target buy money larger than the cash')
			buy_money = self.cash

		if hold_pos != None:
			self.stock_positions[stock_name] += buy_money / stock_price
		else:
			self.stock_positions[stock_name] = buy_money / stock_price
		self.cash -= buy_money
		logging.info(f'buy stock {stock_name}, money {buy_money}, cash {self.cash}')


	def sell_stock_by_money(self, stock_name='STOCK', money=1e3):
		'''
		按照指定的总价格卖出
		'''
		assert money > 0 
		hold_pos = self.stock_positions.get(stock_name)
		stock_price = self.price_table.loc[stock_name]
		sell_money = money

		if hold_pos in [None, 0]:
			raise NameError(f'sell error, stock {stock_name} not hold')
		hold_money = hold_pos * stock_price
		if sell_money - hold_money > 0:
			logging.warning('sell warning, target money larger than the hold value')
			sell_money = hold_money
		self.stock_positions[stock_name] -= sell_money / stock_price
		self.cash += sell_money
		logging.info(f'sell stock {stock_name}, money {sell_money}, cash {self.cash}')

	def order_stock_by_percent(self, stock_name='STOCK', percent=1):
		'''
		按照当前总资产价值的一定比例进行买卖
		'''
		assert percent>=0 and percent<=1
		total_asset = self.get_total_asset()
		money = total_asset * percent
		stock_price = self.price_table.loc[stock_name]
		self.buy_stock_by_money(stock_name=stock_name, money=money)

	def buy_stock_by_volumns(self):
		'''
		按照指定的手数买入
		'''
		raise NotImplementedError

	def sell_stock_by_volumns(self):
		'''
		按照指定的手数卖出
		'''
		raise NotImplementedError



