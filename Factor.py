import pandas as pd 

import logging

logging.basicConfig(level=logging.INFO, #设置日志输出格式
                    filename="./log/factor.log", #log日志输出的文件位置和文件名
                    filemode="w", #文件的写入格式，w为重新写入文件，默认是追加
                    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s", 
                    # 日志输出的格式,-8表示占位符，让输出左对齐，输出长度都为8位
                    datefmt="%Y-%m-%d %H:%M:%S", #时间输出的格式
                    )

class Factor():
	def __init__(self, df_series=None, name=None):
		if not isinstance(df_series, pd.Series):
			raise NameError('input series error, please load time series')
		df = df_series.copy()
		if name != None:
			df.name = name
		self.fac_series = df
		self.name = self.fac_series.name

	def get_factor_name(self):
		return self.name

	def _check_time_stamps(self):
		pass

	def _set_all_time_stamps(self):
		pass

	# get funciton
	# get all time stamps for the factor series
	def get_all_time_stamps(self):
		"""
		get function, get all time stamps for the factor series
		return: the time stamps of the factor
		"""
		return self.fac_series.index

	def calculate_rolling_z_score(self, window=100):
		self.fac_series = self.fac_series.rolling(window=window).apply(lambda df: z_score(x))

	@staticmethod
	def extreme_MAD(dfall, n=5.2): # 去极值，但极端值之间仍保持有序
	    if (not isinstance(dfall, pd.Series)) and (not isinstance(dfall, pd.DataFrame)):
	        dfall = pd.DataFrame(dfall.copy())
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
	#         print(pd.Series(li).rename(df.name))
	        return pd.Series(li).rename(df.name)
	    
	    if isinstance(dfall, pd.Series):
	        return extreme_MAD_series(dfall,n=n)
	    elif isinstance(dfall, pd.DataFrame):
	        df_res = pd.DataFrame(columns=dfall.columns)
	        for col in dfall.columns:
	            df_res[col] = extreme_MAD_series(dfall[col],n=n)
	        return df_res
	    # we could not reach the end
	    return None

	@staticmethod
	def standardize_z(df):
	    mean = df.mean()
	    std = df.std()
	    if std.all() == 0:
	        std = 1
	    return (df-mean) / std

	@staticmethod    
	def z_score(df_in):
	    df = df_in.copy()
	    df = pd.DataFrame(df)
	    df_temp = standardize_z(extreme_MAD(df, 5.2))
	    return df_temp.iloc[-1]
	#     return df_temp
