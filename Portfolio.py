import pandas as pd 
import numpy as np
from scipy.optimize import minimize

class Portfolio():

	def __init__(self, loopback_window=120, min_window=1, init_weight=None):
		pass

	def get_constrain(self, prev_weight):
		"""
		权重的约束条件
		"""
		cons = (
			{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.},
			{'type': 'inqe', 'fun': lambda w: 0.1 - np.sum(np.absolute(w - prev_weight))}
			)
		return cons 

	def get_minimum_variance_weight(self, weight, prev_weight):
		"""
		均值-方差优化
		"""
		pass

	def get_weight(self):
		pass

	def run(self):
		pass
	