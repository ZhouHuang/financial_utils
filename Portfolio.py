import pandas as pd 
import numpy as np
from scipy.optimize import minimize

class Portfolio():

	def __init__(self, init_weight=None, return_coeff=1, risk_averase=0, method='MVO', ewm=None, lookback=20):
		self._X = None
		self._sh = 0.1
		self._sl = -0.1

		self._H = None
		self._hh = 0.0001
		self._hl = -0.0001

		self._wb = None
		self._wh = 0.02
		self._wl = -0.02

		self._wmax = 0.1
		self._wlim = 2

		self._return_coeff = return_coeff # 目标函数中，目标收益前的系数。只能取1或0，默认为1.
		self._risk_averase = risk_averase # 风险厌恶系数

		self._method = method
		self._ewm = ewm # 指数加权

		self._lookback = lookback # 计算因子mean, std, cov时的回看天数

	@property
	def lookback(self):
		return self._lookback
		

	def set_parameters(self, X_matrix, H_matrix, wb, sh=0.1, sl=-0.1, hh=0.0001, hl=-0.0001, wh=0.02, wl=-0.02, wmax=0.2, wlim=2):
		# if not isinstance(X_matrix, np.ndarray):
		# 	raise KeyError(f'[X matrix] must be numpy.ndarray, got {type(X_matrix)}')
		# if not isinstance(H_matrix, np.ndarray):
		# 	raise KeyError(f'[H matrix] must be numpy.ndarray, got {type(H_matrix)}')
		# if not isinstance(wb, np.ndarray):
		# 	raise KeyError(f'[wb] must be numpy.ndarray, got {type(X_matrix)}')
		self._X = X_matrix
		self._sh = sh
		self._sl = sl

		self._H = H_matrix
		self._hh = hh
		self._hl = hl

		self._wb = wb 
		self._wh = wh
		self._wl = wl

		self._wmax = wmax
		self._wlim = wlim

	def get_constrain(self, prev_weight):
		"""
		权重的约束条件
		"""
		cons = (
			# {'type': 'ineq', 'fun': lambda w: self._sh - np.dot(self._X, (w - self._wb))}, 	# 组合相对基准指数的行业偏离幅度(sh = +0.01%)
			# {'type': 'ineq', 'fun': lambda w: np.dot(self._X, (w - self._wb)) - self._sl}, 	# 组合相对基准指数的风格偏离幅度(sl = -0.01%)

			# {'type': 'ineq', 'fun': lambda w: self._hh - np.dot(self._H, (w - self._wb))}, 	# 组合相对基准指数的行业偏离幅度(hh = +0.01%)
			# {'type': 'ineq', 'fun': lambda w: np.dot(self._H, (w - self._wb)) - self._hl}, 	# 组合相对基准指数的行业偏离幅度(hl = -0.01%)
			
			# {'type': 'ineq', 'fun': lambda w: self._wh - (w - self._wb)}, 	# 权重相对于基准权重的偏离(wh = +2%)
			# {'type': 'ineq', 'fun': lambda w: w - self._wb - self._wl}, 	# 权重相对于基准权重的偏离(wl = -2%)
			
			{'type': 'ineq', 'fun': lambda w: w}, 							# 权重大于等于0
			{'type': 'ineq', 'fun': lambda w: self._wmax - w}, 				# 个股权重最大值为wmax
			
			{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.}, 				# 权重和为1
			
			{'type': 'ineq', 'fun': lambda w: self._wlim - np.sum(np.absolute(w - prev_weight))} # 权重换手率之和小于wlim
			)
		return cons 

	def _get_minimum_variance_optimized_weight(self, df_factor_exposures, prev_weight):
		"""
		均值-方差优化
		df_factor_exposures: 个股因子暴露, pd.DataFrame
		prev_weight: 上次权重
		"""
		assert self._return_coeff in [0,1]
		_vector_f = df_factor_exposures.mean().values
		_cov = df_factor_exposures.cov().values

		object_func = lambda w: -np.sum(w * _vector_f) * self._return_coeff + 0.5 * self._risk_averase * np.dot(np.dot(w, _cov), w) # minimizer最小化目标函数, -1 * U(w)
		cons = self.get_constrain(prev_weight=prev_weight)
		options = {'maxiter': 500}
		result = minimize(fun=object_func, x0=prev_weight, method='SLSQP', constraints=cons, options=options, tol=1e-6)
		return result.x, result.success


	def get_weight(self, df_factor_exposures, prev_weight):
		mvo_method_list = ['MVO', 'MeanVarianceOptimize']
		if self._method in mvo_method_list:
			return self._get_minimum_variance_optimized_weight(df_factor_exposures=df_factor_exposures, prev_weight=prev_weight)
		else:
			raise KeyError(f'method must be one of {mvo_method_list}, got {self._method}')

	def run(self):
		pass
	