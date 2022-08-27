import pandas as pd
import numpy as np

import logging

logging.basicConfig(level=logging.INFO, #设置日志输出格式
                    filename="./log/account.log", #log日志输出的文件位置和文件名
                    filemode="w", #文件的写入格式，w为重新写入文件，默认是追加
                    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s", 
                    # 日志输出的格式,-8表示占位符，让输出左对齐，输出长度都为8位
                    datefmt="%Y-%m-%d %H:%M:%S", #时间输出的格式
                    )

class Account():
	def __init__(self, cash=1e8):
		self.cash = cash
		self.stock_values = {} # key: stock 名字, value: 持有标的总价值
		self.total_asset = self.cash

	def set_init_cash(self, money):
		self.cash = money

	def get_total_asset(self):
		money = self.cash
		for key, value in stock_values:
			money += value
		return money

	def get_cash(self):
		return self.cash

	def buy_stock_by_money(self, stock_name='STOCK', money=1e3):
		'''
		按照指定的总价格买入，注意此处的总价格包含了已持有的标的价值
		'''
		assert money > 0
		buy_money = money
		hold_money = self.stock_values.get(stock_name)
		if hold_money in [None, 0]:
			pass
		elif hold_money > 0:
			# 已经持有标的
			if buy_money < hold_money:
				# 买入总价格比当前持有的标的总价值小
				logging.warning('buy warning, target buy money smaller than the hold value, sell the stock actually')
				sell_stock_by_money(stock_name=stock_name, money=hold_money-buy_money)
				buy_money = 0
			else:
				# 买入总价格比当前持有的标的总价值大
				buy_money -= hold_money
		if buy_money > self.cash:
			# 需要额外买入的总价格大于当前持有的现金
			logging.warning('buy warning, target buy money larger than the cash')
			buy_money = self.cash

		if hold_money != None:
			self.stock_values[stock_name] += buy_money
		else:
			self.stock_values[stock_name] = buy_money
		self.cash -= buy_money
		logging.info(f'buy stock {stock_name}, money {buy_money}, cash {self.cash}')


	def sell_stock_by_money(self, stock_name='STOCK', money=1e3):
		'''
		按照指定的总价格卖出
		'''
		assert money > 0
		hold_money = self.stock_values.get(stock_name)
		sell_money = money
		if hold_money in [None, 0]:
			raise NameError(f'sell error, stock {stock_name} not hold')
		if sell_money - hold_money > 0:
			logging.warning('sell warning, target money larger than the hold value')
			sell_money = hold_money
		self.stock_values[stock_name] -= sell_money
		self.cash += sell_money
		logging.info(f'sell stock {stock_name}, money {sell_money}, cash {self.cash}')


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

	def buy_stock_by_percent(self):
		'''
		按照现有总资产的比例买入
		'''
		raise NotImplementedError

	def sell_stock_by_percent(self):
		'''
		按照现有总资产的比例卖出
		'''
		raise NotImplementedError

