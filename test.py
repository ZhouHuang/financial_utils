from Factor import Factor
import pandas as pd

df_selected_factors = pd.read_csv('./test_input/df_factors_selected_0815.csv', index_col=0)
fac = Factor(df_series=df_selected_factors.iloc[:,0], name='SW_estate_ir20')

print(fac.get_factor_name())
print(fac.get_all_time_stamps())

# from Account import Account

# acc = Account()

# print(acc.get_cash())

# acc.buy_stock_by_money(stock_name='600300.SH', money=1e9)
# acc.sell_stock_by_money(stock_name='600300.SH', money=1e10)
