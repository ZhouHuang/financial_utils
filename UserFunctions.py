import pandas as pd 
import numpy as np
from scipy import stats

class UserFunctions():
	def __init__(self):
		pass

	@staticmethod
	def _ts_delay(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')

		return x1.shift(d).values

	@staticmethod
	def _ts_delta(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1 - UserFunctions._ts_delay(x1, d)

	@staticmethod
	def _ts_min(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).min()

	@staticmethod
	def _ts_max(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).max()

	@staticmethod
	def _ts_mean(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).mean()

	@staticmethod
	def _ts_argmin(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).apply(lambda s: s.argmin())

	@staticmethod
	def _ts_argmax(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).apply(lambda s: s.argmax())

	@staticmethod
	def _ts_mean_quantile(x1, d, per=0, upper=True):
		"""
		x1: times series, pd.Series or list
		d: loop back time interval, d days, int
		per: percentile limit, float between 0-1
		upper: boolean. True: Upper part or larger then the quantile. False: lower part or less then the quantile
		return: mean value of the series, under the quantile condition 

		- the default parameters per=0 and upper=True give the general mean function of the time series
		"""
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		if not isinstance(upper, bool):
			raise ValueError(f'Input [upper] must be boolean, got {type(upper)}')
		assert per >= 0 and per <= 1

		def __quantile_filter(array_like):
			if array_like.size == 0:
				return np.nan
			limit = x1.quantile(per)
			if upper:
				new_series = x1[x1>=limit]
			else:
				new_series = x1[x1<limit]
			return new_series.mean()

		return x1.rolling(d, min_periods=int(d/2)).apply(__quantile_filter)

	# 过去 d 天 x1 值构成的时间序列中本截面日 x1 值所处分位数
	@staticmethod
	def _ts_rank(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).apply(
			lambda s: stats.percentileofscore(s, s[-1]) / 100.0
			)

	@staticmethod
	def _ts_sum(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).sum()

	@staticmethod
	def _ts_stddev(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).std()

	@staticmethod
	def _ts_variance(x1, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if isinstance(x1, list):
			x1 = pd.Series(x1)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list or pd.Series, got {type(x1)}')
		return x1.rolling(d, min_periods=int(d/2)).var()

	@staticmethod
	def _ts_corr(x1, x2, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if type(x1) != type(x2):
			raise ValueError(f'Input x1 and x2 are different types, x1[{type(x1)}, x2{type(x2)}')

		def __ts_corr_series(x1, x2, d):
			return x1.rolling(d, min_periods=int(d/2)).corr(x2)

		def __eq(li1, li2):
			if len(li1) != len(li2):
				return False
			for i,v in enumerate(li1):
				if li1[i] != li2[i]:
					return False
			return True

		if isinstance(x1, pd.DataFrame):
			if __eq(x1.index, x2.index) and __eq(x1.columns, x2.columns):
				df_out = pd.DataFrame(index=x1.index, columns=x1.columns)
				for col in x1.columns:
					df_out.loc[:,col] = __ts_corr_series(x1[col], x2[col], d)
				return df_out
			else:
				raise ValueError(f'Input x1 and x2 indices are not same')
					
		elif isinstance(x1, list):
			x1 = pd.Series(x1)
			x2 = pd.Series(x2)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list, pd.Series or pd.DataFrame, got {type(x1)}')

		return __ts_corr_series(x1, x2, d)

	@staticmethod
	def _ts_cov(x1, x2, d):
		if isinstance(d, float):
			d = np.floor(d).astype(int)
		if not isinstance(d, int):
			raise ValueError(f'Input [d] must be int or float, got {type(d)}')
		if type(x1) != type(x2):
			raise ValueError(f'Input x1 and x2 are different types, x1[{type(x1)}, x2{type(x2)}')

		def __ts_cov_series(x1, x2, d):
			return x1.rolling(d, min_periods=int(d/2)).cov(x2)

		def __eq(li1, li2):
			if len(li1) != len(li2):
				return False
			for i,v in enumerate(li1):
				if li1[i] != li2[i]:
					return False
			return True

		if isinstance(x1, pd.DataFrame):
			if __eq(x1.index, x2.index) and __eq(x1.columns, x2.columns):
				df_out = pd.DataFrame(index=x1.index, columns=x1.columns)
				for col in x1.columns:
					df_out.loc[:,col] = __ts_cov_series(x1[col], x2[col], d)
				return df_out
			else:
				raise ValueError(f'Input x1 and x2 indices are not same')
					
		elif isinstance(x1, list):
			x1 = pd.Series(x1)
			x2 = pd.Series(x2)
		elif isinstance(x1, pd.Series):
			pass
		else:
			raise ValueError(f'Input [x1] must be list, pd.Series or pd.DataFrame, got {type(x1)}')

		return __ts_cov_series(x1, x2, d)



