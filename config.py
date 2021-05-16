import datetime

ini_file_name = 'account.ini'
trade_log_file_name = 'upbit_trade_'
account_log_file_name = 'upbit_account_summary.log'
buy_sign = True
position_market = []
trade_target_rank10 = 10
trade_target_rank20 = 20

korean_market = ['KRW-IQ', 'KRW-MOC', 'KRW-MARO', 'KRW-STRK', 'KRW-MFM']

steady_market = ['KRW-ADA', 'KRW-DOT', 'KRW-XLM']

except_market = ['KRW-DOGE', ]

# TODO 화면에서 받은 값으로 입력
api_key = {'user_name': 'DANIEL',
           'access_key': 'ACCESS_KEY',
           'secret_key': 'SECRET_KEY',
           'server_url': 'https://api.upbit.com'}

amount_per_order = 10000
sell_movement_percent = 5

auto_trade = 1
