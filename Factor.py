import pandas as pd 

import logging
import os 

log_file_name = "./log/factor.log"
if not os.path.exists('log'):
	os.mkdir('log')

logging.basicConfig(level=logging.INFO, #设置日志输出格式
                    filename=log_file_name, #log日志输出的文件位置和文件名
                    filemode="w", #文件的写入格式，w为重新写入文件，默认是追加
                    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s", 
                    # 日志输出的格式,-8表示占位符，让输出左对齐，输出长度都为8位
                    datefmt="%Y-%m-%d %H:%M:%S", #时间输出的格式
                    )

class Factor():
	_underlying_date = None # 投资标的的日期序列

	def __init__(self, df_series, name=None):
		if not isinstance(df_series, pd.Series):
			raise NameError('input series error, please load time series')
		df = df_series.copy()
		if name != None:
			df.name = name
		self.fac_series = df

	@classmethod
	def set_date_format(cls, li):
		if not isinstance(li, list):
			raise NameError('input date series is not list')
		cls._underlying_date = pd.DataFrame(index=li)

	def set_factor_name(self, name):
		if not isinstance(name, str):
			raise NameError('input name is not str')
		self.fac_series.name = name

	# 设置日期延迟，避免使用未来数据
	def set_delay(self, window=1):
		self.fac_series = self.fac_series.shift(window)

	# 返回因子时间序列
	def get_factor(self):
		if self._underlying_date is None:
			raise KeyError('underlying date not defined, set date format first')
		self.fac_series = pd.concat([self._underlying_date, self.fac_series], axis=1)
		self.fac_series.fillna(method='ffill', inplace=True)
		self.fac_series.fillna(method='bfill', inplace=True)

		return self.fac_series

	# 计算Zscore
	def calculate_rolling_z_score(self, window=100):
		self.fac_series = self.fac_series.rolling(window=window).apply(lambda df: z_score(df))

	# 季度调整
	def calculate_seasonal(self, period=365):
		raise NotImplementedError

	@staticmethod
	def extreme_MAD(dfall, n=5.2): # 去极值，但极端值之间仍保持有序
	    if not isinstance(dfall, pd.Series):
	    	raise NameError('input must be times seires object')
	    def extreme_MAD_series(df, n=5.2):
	        assert isinstance(df, pd.Series)
	        median = df.quantile(0.5)
	        new_median = (abs((df - median)).quantile(0.5))
	        up = median + n*new_median
	        down = median - n*new_median
	        abnormal_up_index = []
	        abnormal_down_index = []
	        li = df.values.ravel()
	        for i in range(len(li)):
	            di = li[i]
	            if di <= down:
	                abnormal_down_index.append(i)
	            if di >= up:
	                abnormal_up_index.append(i)
	        if len(abnormal_down_index)>0:
	            rank_abnomal = pd.Series([li[i] for i in abnormal_down_index])
	            rank_abnomal = rank_abnomal.rank(ascending=False) # 降序
	            for i in range(len(abnormal_down_index)):
	                li[abnormal_down_index[i]] = down - new_median*(1./rank_abnomal.size)*rank_abnomal[i]
	        if len(abnormal_up_index)>0:
	            rank_abnomal = pd.Series([li[i] for i in abnormal_up_index])
	            rank_abnomal = rank_abnomal.rank(ascending=True) # 降序
	            for i in range(len(abnormal_up_index)):
	                li[abnormal_up_index[i]] = up + new_median*(1./rank_abnomal.size)*rank_abnomal[i]
	        return pd.Series(li).rename(df.name)

	    return extreme_MAD_series(dfall,n=n)

	@staticmethod
	def standardize_z(df):
	    mean = df.mean()
	    std = df.std()
	    if std.all() == 0:
	        std = 1
	    return (df-mean) / std

	@staticmethod    
	def z_score(df_in):
		if not isinstance(df_in, pd.Series):
			raise NameError('input must be times seires object')
		df = df_in.copy()
		df_temp = standardize_z(extreme_MAD(df, 5.2))
		return df_temp.iloc[-1]

