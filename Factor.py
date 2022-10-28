import pandas as pd 
from UserFunctions import UserFunctions

class Factor():
	_underlying_date = None # 投资标的的日期序列

	def __init__(self, df_series, name=None):
		if not isinstance(df_series, pd.Series):
			raise NameError(f'input error, please load time series, got {type(df_series)}')
		df = df_series.copy()
		if name != None:
			df.name = name
		self.fac_series = df

	@classmethod
	def set_date_format(cls, li):
		if not (isinstance(li, list) or isinstance(li, pd.Series)):
			raise NameError('input date series is not list or pandas.Series')
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
		self.fac_series = self.fac_series.rolling(window=window).apply(lambda df: rolling_z_score(df))

	# 季度调整
	def calculate_seasonal(self, period=365):
		raise NotImplementedError

	@staticmethod
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

	@staticmethod
	def rolling_extreme_MAD(dfall, n=5.2): # 去极值，但极端值之间仍保持有序
	    if not isinstance(dfall, pd.Series):
	    	raise NameError('input must be times seires object')

	    return extreme_MAD_series(dfall,n=n)

	@staticmethod
	def rolling_standardize_z(df):
	    mean = df.mean()
	    std = df.std()
	    if std.all() == 0:
	        std = 1
	    return (df-mean) / std

	@staticmethod    
	def rolling_z_score(df_in):
		if not isinstance(df_in, pd.Series):
			raise NameError('input must be times seires object')
		df = df_in.copy()
		df_temp = rolling_standardize_z(rolling_extreme_MAD(df, 5.2))
		return df_temp.iloc[-1]

	@staticmethod
	def fill_cross_sectional_na(dfall):
	    if not isinstance(dfall, pd.DataFrame):
	        raise NameError(f'input must be pd.DataFrame, got {type(dfall)}')
	    print('processing fill_cross_sectional_na...')
	    
	    df_out = pd.DataFrame(index=dfall.index, columns=dfall.columns)
	    for day in df_out.index:
	        stocks_pool = CSI500_stocks_list.loc[day].to_list()
	        series_cross_sectional_factor = dfall.loc[day, stocks_pool]
	        mean_values_in_pool = series_cross_sectional_factor.mean(skipna=True)
	        df_temp = series_cross_sectional_factor.fillna(mean_values_in_pool)
	        df_out.loc[day, stocks_pool] = df_temp.values

	    return df_out


	@staticmethod
	def cross_sectional_extreme_MAD(dfall, n=5.2): # 去极值，但极端值之间仍保持有序
	    if not isinstance(dfall, pd.DataFrame):
	        raise NameError(f'input must be pd.DataFrame, got {type(dfall)}')
	    print('processing extreme_MAD...')
	    
	    df_out = pd.DataFrame(index=dfall.index, columns=dfall.columns)
	    for day in df_out.index:
	        stocks_pool = CSI500_stocks_list.loc[day].to_list()
	        series_cross_sectional_factor = dfall.loc[day, stocks_pool]
	        df_temp = Factor.extreme_MAD_series(series_cross_sectional_factor)
	        df_out.loc[day, stocks_pool] = df_temp.values

	    return df_out

	@staticmethod
	def cross_sectional_standardize_z(dfall):
	    if not isinstance(dfall, pd.DataFrame):
	        raise NameError(f'input must be pd.DataFrame, got {type(dfall)}')
	    print('processing standardize_z...')
	    def standardize_z_series(df):
	        mean = df.mean()
	        std = df.std()
	        if std.all() == 0:
	            std = 1
	        return (df-mean) / std
	    
	    df_out = pd.DataFrame(index=dfall.index, columns=dfall.columns)
	    for day in df_out.index:
	        stocks_pool = CSI500_stocks_list.loc[day].to_list()
	        series_cross_sectional_factor = dfall.loc[day, stocks_pool]
	        df_out.loc[day, stocks_pool] = standardize_z_series(df=series_cross_sectional_factor).values

	    return df_out

	@staticmethod
	def cross_sectional_winsorize(df, capital_neutral=True, industry_neutral=True):
	    if not isinstance(df, pd.DataFrame):
	        raise ValueError(f'Input [df] must be pd.DataFrame, got {type(df)}')
	    print('processing winsorize...')

	    import statsmodels.api as sm

	    # CirculatingMarketCap
	    df_stocks_CirculatingMarketCap = pd.DataFrame()
	    for stock in stock_valuation_standard.index.levels[0]:
	        try:
	            df_stocks_CirculatingMarketCap[stock] = stock_valuation_standard.loc[(stock, 'CirculatingMarketCap'), :]
	        except :
	            pass
	    df_stocks_LogCirculatingMarketCap = np.log(df_stocks_CirculatingMarketCap)
	    df_stocks_LogCirculatingMarketCap = standardize_z(extreme_MAD( fill_cross_sectional_na(df_stocks_LogCirculatingMarketCap)))

	    # SW industrial dummies
	    df_industry_dummy_SW2016 = pd.read_csv('./causis_本地数据下载/industry_dummy_SWI2016.csv', index_col=0)
	    
	    df_out = pd.DataFrame(index=df.index, columns=df.columns)
	    for day in df_out.index:
	        stocks_pool = CSI500_stocks_list.loc[day].to_list()
	        y = df.loc[day, stocks_pool].rename('Cross_section_factor') # factor cross-sectional values
	        if capital_neutral and industry_neutral:
	            x = df_industry_dummy_SW2016.loc[stocks_pool,:]
	            log_cap = df_stocks_LogCirculatingMarketCap.loc[day,stocks_pool].rename('LogCirculatingMarketCap')
	            x = pd.concat([x, log_cap], axis=1)
	            y = y.to_frame()
	        elif capital_neutral:
	            x = df_stocks_LogCirculatingMarketCap.loc[day,stocks_pool].rename('LogCirculatingMarketCap')
	        elif industry_neutral:
	            x = df_industry_dummy_SW2016.loc[stocks_pool,:]
	            y = y.to_frame()
	        else:
	            raise ValueError(f'neutral flag input error')
	#         print(f'shape y {y.shape}, x shape {x.shape}')
	        try:
	            fit_result = sm.OLS(y.astype(float),x.astype(float)).fit()
	        except :
	            print(f'SVD did not converge date {day}')
	        else:
	#             print(f'{type(fit_result.resid)} shape of fit result residual {fit_result.resid.shape}')
	            df_out.loc[day,stocks_pool] = fit_result.resid

	    return df_out
	    
