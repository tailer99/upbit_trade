import requests
import time, datetime
import exchange_func
import config

def search_market_list():
    # print("#############  market list   ###########")
    url = "https://api.upbit.com/v1/market/all"
    querystring = {"isDetails": "false"}
    response = requests.request("GET", url, params=querystring)

    # print(response.text)

    markets = []
    # currencies = ["KRW", "BTC", "USDT"]
    currencies = ["KRW"]

    i = 0
    for currency in currencies:
        # print(type(list(result.values())), result)

        for result in response.json():
            if result['market'].find(currency) == 0:
                # currencies.append("KRW")
                if i == 0:
                    # markets.append(list(result.keys()))
                    # markets[i].insert(0, "currency")
                    pass
                else:
                    markets.append(list(result.values()))
                    # title 을 제거하면서 index를 -1 처리함
                    markets[i-1].insert(0, currency)

                i += 1

    # print(markets)
    return markets


# 캔들 챠트 조회
def search_candle_chart(market, time_unit, interval, count):
    # print("#############  candle        ###########")
    # print("=========== trendSearch : ", market, "  ", time_unit, "  ", interval)
    candle_var = []

    candle_query_str = {'market': market, 'count': count}
    # print(candle_query_str)

    if time_unit == "minutes":
        url = "https://api.upbit.com/v1/candles/" + time_unit + "/" + str(interval)
    else:
        url = "https://api.upbit.com/v1/candles/" + time_unit
    # print("searchURL : ", url)

    # querystring = {"market":"KRW-XRP","count":"5"}
    querystring = candle_query_str

    response = requests.request("GET", url, params=querystring)

    # print("searchResult :  ", response.json())

    i = 0
    for result in response.json():
        if i == 0:
            candle_var.append(list(result.keys()))
            candle_var.append(list(result.values()))
        else:
            candle_var.append(list(result.values()))

        # print(i, list(result.keys()), list(result.values()))
        # print(list(result.values()))
        # print(candle_var[i][9])
        i += 1

    return candle_var


def search_ticks(market, count):
    # print("#############  ticks      ###########")
    tick_list = []
    url = "https://api.upbit.com/v1/trades/ticks"

    querystring = {"market": market, "count": count}

    response = requests.request("GET", url, params=querystring)
    # print('status : ', response.status_code, '  ,url : ', response.url, '  ,results : ', response.text)

    if response.status_code == 200:
        last_dt = datetime.datetime.strptime(
            response.json()[0]['trade_date_utc'] + ' ' + response.json()[0]['trade_time_utc'], "%Y-%m-%d %H:%M:%S")

        first_dt = datetime.datetime.strptime(
            response.json()[len(response.json()) - 1]['trade_date_utc'] + ' ' +
            response.json()[len(response.json()) - 1]['trade_time_utc'], "%Y-%m-%d %H:%M:%S")

        deltatime = last_dt - first_dt
        if deltatime.seconds <= 30:
            # print('많은 거래 : ', market)
            retrun_market = find_buy_target_by_3min_candle([['KRW', market]])
            # print(' return_market : ', retrun_market, type(retrun_market))
            if len(retrun_market) > 0:
                return deltatime.seconds, retrun_market[0]
            else:
                return 0, 'X'
        else:
            return 0, 'X'


def search_ticker(market_list):
    # print("#############  ticker      ###########")
    ticker_list = []
    url = "https://api.upbit.com/v1/ticker"

    market_string = ""
    for market in market_list:
        market_string += market + ", "

    querystring = {"markets": market_string[:-2]}

    response = requests.request("GET", url, params=querystring)
    # print('status : ', response.status_code, '  ,url : ', response.url, '  ,results : ', response.text)

    if response.status_code == 200:
        for i, result in enumerate(response.json()):
            if i == 0:
                ticker_list.append(list(result.keys()))
                ticker_list.append(list(result.values()))
            else:
                ticker_list.append(list(result.values()))

    return ticker_list


def calc_trade_variable_rate(candle_list):
    # print("==== calc_trade_variable_rate ")

    # avg trade
    candle_trade_sum = 0
    # print(candle_list[0])
    for j, candle in enumerate(candle_list[1:]):
        # print(j, candle)
        # print("5Min ", candle, candle[9], candleVar5Min[j+1][9], len(candleVar5Min[1:]))
        if j > 0:
            candle_trade_sum = candle_trade_sum + candle_list[j+1][9]

    # print(candle_list[1][9], candle_list[2][9], candle_trade_sum, len(candle_list[2:]))
    # 최근값 / 평균 ( 이후 값의 합 / 개수 )
    # trade_variable_rate = "{0:.2%}".format(round(candle_list[1][9] / (candle_trade_sum / len(candle_list[2:])), 5))
    trade_variable_rate = round(candle_list[1][9] / (candle_trade_sum / len(candle_list[2:])), 5)

    return trade_variable_rate


# 5분봉과 1분봉 거래량으로 거래대상 찾기
def find_buy_target_by_amount(target_market):
    buy_list = []

    for market in target_market:
        # print("market name : ", market)
        if market[0] == "KRW":
            # print("market : ", market[1])
            candle_5min = search_candle_chart(market[1], "minutes", 5, 10)
            candle_1min = search_candle_chart(market[1], "minutes", 1, 30)
            candle_day = search_candle_chart(market[1], "weeks", 0, 10)

            candle_5min_rate = calc_trade_variable_rate(candle_5min)
            # print("after 5: ", market[1], "  ", str(candle_5Min_rate))
            candle_1min_rate = calc_trade_variable_rate(candle_1min)
            # print("after 1: ", market[1], "  ", str(candle_1Min_rate))

            # 1분당 거래량 증가량이 5분 거래량 증가량보다 3배 높고 현재가가 봉 시작가보다 높을 때 매수
            if candle_1min_rate > candle_5min_rate * 3 and \
               candle_1min_rate > 0.01 and \
               candle_5min[1][6] > candle_5min[1][3] and \
               candle_1min[1][6] > candle_1min[1][3]:

                # print(" =======================")
                # print(" buy ====> ", market[1])
                # print(" =======================")
                buy_list.append(market[1])

            time.sleep(0.5)

    if len(buy_list) > 0:
        print(" === buy_list : ", buy_list)
    return buy_list


# 5분봉과 1분봉 거래량으로 거래대상 찾기
def find_buy_target_by_3min_candle(target_market):
    buy_list = []

    for market in target_market:
        # print("market name : ", market)
        if market[0] == "KRW":
            # print("market : ", market[1])
            # candle_5min = search_candle_chart(market[1], "minutes", 5, 5)
            candle_1min = search_candle_chart(market[1], "minutes", 1, 10)

            # print('a ', candle_1min[1][6], ', ', candle_1min[1][3], ', ', candle_1min[2][6], ', ', candle_1min[2][3])
            if candle_1min[1][6] > candle_1min[1][3] * 2 and \
                    candle_1min[2][6] > candle_1min[2][3]:
                # print(" buy ====> ", market[1])
                buy_list.append(market[1])

            time.sleep(0.5)

    if len(buy_list) > 0:
        print(" === buy_list : ", buy_list)
    return buy_list


# 1분봉이 5분봉보다 낮으면 매도
def find_sell_target(profit_percent=0):
    sell_list = []

    if profit_percent == 0:
        profit_percent = config.sell_movement_percent

    accounts_res = exchange_func.search_accounts(exchange_func.search_api_key())
    if accounts_res.status_code == 200:
        for acc in accounts_res.json():
            if acc['currency'] not in acc['unit_currency']:
                # print(' TODO : find condition ')
                market = acc['unit_currency'] + '-' + acc['currency']
                orderbook_list = search_orderbook(market)

                price = float(orderbook_list[1][4][0]['ask_price'])

                # 변동량이 1% 이상일때만 거래
                if abs(float(acc['avg_buy_price']) - price) / float(acc['avg_buy_price']) * 100 > \
                        profit_percent:
                    sell_list.append(market)

                time.sleep(0.5)

    if len(sell_list):
        print(" === sell_list : ", sell_list)
    return sell_list


# 매수값 보다 5% 이상 차이나면 매도
def find_sell_5pct_target():
    sell_list = []

    accounts_res = exchange_func.search_accounts(exchange_func.search_api_key())
    if accounts_res.status_code == 200:
        for acc in accounts_res.json():
            if acc['currency'] not in 'KRW':
                day_ticker = search_ticker(['KRW-' + acc['currency']])
                # print('avg_buy_price : ', acc['avg_buy_price'], ', current price : ', day_ticker[0][9])
                if abs(float(acc['avg_buy_price']) - float(day_ticker[0][9])) / float(acc['avg_buy_price']) > 0.05:
                    sell_list.append('KRW-' + acc['currency'])

    if len(sell_list) > 0:
        print(" === sell 5% list : ", sell_list)
    return sell_list


def search_market_day_ticker(market_list):
    # print("#############  ticker      ###########")
    tickerVar = []
    url = "https://api.upbit.com/v1/ticker"

    market_string = ""
    for market in market_list:
        # print(market[1])
        if market[0] == "KRW":
            market_string += market[1] + ", "

    querystring = {"markets": market_string[:-2]}
    # querystring = {"markets":"KRW-XRP, KRW-DOGE"}
    # querystring = {"markets":"KRW-XLM,KRW-XRP,KRW-DOGE,KRW-BTT,KRW-ETC,KRW-VET"}

    response = requests.request("GET", url, params=querystring)
    # print('status : ', response.status_code, '  ,url : ', response.url, '  ,results : ', response.text)

    i = 0
    for result in response.json():
        if i == 0:
            tickerVar.append(list(result.keys()))
            tickerVar.append(list(result.values()))
        else:
            tickerVar.append(list(result.values()))

        # print(i, list(result.keys()), list(result.values()))
        # print(list(result.values()))
        i += 1

    # sort by 'acc_trade_price_24h'
    print(tickerVar[0][0], "  ", tickerVar[0][3], "  ", tickerVar[0][4], "  ", tickerVar[0][5], "  ", tickerVar[0][6], "  ", tickerVar[0][7], "  ",
          tickerVar[0][8], "  ", tickerVar[0][9], "  ", tickerVar[0][10], "  ", tickerVar[0][11], "  ", tickerVar[0][14], "  ", tickerVar[0][15], "  ",
          tickerVar[0][17], "  ", tickerVar[0][18], "  ", tickerVar[0][19], "  ", tickerVar[0][20], "  ", tickerVar[0][21], "  ", tickerVar[0][22],
          "  ", tickerVar[0][23], "  ", tickerVar[0][24])
    for ticker in sorted(tickerVar[1:], key=lambda ticker: ticker[18], reverse=True):
        print(ticker[0], "  ", ticker[3], "  ", ticker[4], "  ", ticker[5], "  ", ticker[6], "  ", ticker[7], "  ",
              ticker[8], "  ", ticker[9], "  ", ticker[10], "  ", ticker[11], "  ", ticker[14], "  ", "{0:.2%}".format(ticker[15]), "  ",
              ticker[17], "  ", ticker[18], "  ", ticker[19], "  ", ticker[20], "  ", ticker[21], "  ", ticker[22],
              "  ", ticker[23], "  ", ticker[24])

    print("#############  ticker      ###########")


def search_orderbook(orderbook_market):
    # print("#############  orderbook      ###########")

    orderbook_list = []
    url = "https://api.upbit.com/v1/orderbook"

    querystring = {"markets": orderbook_market}
    # querystring = {"markets":"KRW-XRP"}

    response = requests.request("GET", url, params=querystring)

    # print('status : ', response.status_code, '  ,url : ', response.url, '  ,results : ', response.text)
    # print(response.json()[0]['market'])

    for i, result in enumerate(response.json()):
        if i == 0:
            orderbook_list.append(list(result.keys()))
            orderbook_list.append(list(result.values()))
        else:
            orderbook_list.append(list(result.values()))

    # print("orderbook_list : " , orderbook_list[1][4])
    # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][0]['ask_price'])

    return orderbook_list


def mornitering_market(market):
    # print(market)
    buy_sign = config.buy_sign

    candle_var = search_candle_chart(market, 'minutes', 1, 5)
    # print(candle_var)
    for i, min_candle in enumerate(candle_var[:2]):
        if i == 0:
            # print(min_candle)
            pass
        else:
            # print('1시가:', min_candle[3], ' 종가:', min_candle[6], ' 이전시가:', candle_var[i + 1][3],' 이전종가:', candle_var[i + 1][6])
            # print(round((min_candle[6] - min_candle[3]) / min_candle[3],3),
            #       round((candle_var[i + 1][6] - candle_var[i + 1][3]) / candle_var[i + 1][3],3) )
            if round((min_candle[6] - min_candle[3]) / min_candle[3], 3) < -0.002 and \
                    round((candle_var[i + 1][6] - candle_var[i + 1][3]) / candle_var[i + 1][3], 3) < -0.002:
                config.buy_sign = False
                print('>>>>>>>>>>>> 1 ', datetime.datetime.now(), ' : ', market, ' 급락 START', ', buy_sign : ', config.buy_sign)
            elif round((min_candle[6] - min_candle[3]) / min_candle[3], 3) < -0.002:
                print('>>>>>>>>>>>> 1 ', datetime.datetime.now(), ' : ', market, ' 하락 START', ', buy_sign : ', config.buy_sign)
                config.buy_sign = True
            elif round((min_candle[6] - min_candle[3]) / min_candle[3], 3) > 0.002:
                print('>>>>>>>>>>>> 1 ', datetime.datetime.now(), ' : ', market, ' 상승 START', ', buy_sign : ', config.buy_sign)
                config.buy_sign = True
            elif round((min_candle[6] - min_candle[3]) / min_candle[3], 3) > 0.002 and \
                    round((candle_var[i + 1][6] - candle_var[i + 1][3]) / candle_var[i + 1][3], 3) > 0.002:
                print('>>>>>>>>>>>> 1 ', datetime.datetime.now(), ' : ', market, ' 급등 START', ', buy_sign : ', config.buy_sign)
                config.buy_sign = True

    candle_var = search_candle_chart(market, 'minutes', 5, 5)
    # print(candle_var)
    for i, min_candle in enumerate(candle_var[0:2]):
        if i == 0:
            # print(min_candle)
            pass
        else:
            # print('5시가:', min_candle[3], ' 종가:', min_candle[6], ' 이전시가:', candle_var[i + 1][3], ' 이전종가:',
            #       candle_var[i + 1][6])
            # print(round((min_candle[6] - min_candle[3]) / min_candle[3], 3),
            #       round((candle_var[i + 1][6] - candle_var[i + 1][3]) / candle_var[i + 1][3], 3))

            if round((min_candle[6] - min_candle[3]) / min_candle[3], 3) < -0.01 and \
                    round((candle_var[i + 1][6] - candle_var[i + 1][3]) / candle_var[i + 1][3], 3) < -0.01 and \
                    round((candle_var[i + 2][6] - candle_var[i + 2][3]) / candle_var[i + 2][3], 3) < -0.01:
                config.buy_sign = True
                print('>>>>>>>>>>>> 5 ', datetime.datetime.now(), ' : ', market, ' 급락 : BUY All', ', buy_sign : ', config.buy_sign)
            elif round((min_candle[6] - min_candle[3]) / min_candle[3], 3) < -0.01:
                config.buy_sign = False
                print('>>>>>>>>>>>> 5 ', datetime.datetime.now(), ' : ', market, ' 하락 : Caution', ', buy_sign : ', config.buy_sign)
            elif round((min_candle[6] - min_candle[3]) / min_candle[3], 3) > 0.01:
                config.buy_sign = True
                print('>>>>>>>>>>>> 5 ', datetime.datetime.now(), ' : ', market, ' 상승 : Buy', ', buy_sign : ', config.buy_sign)
            elif round((min_candle[6] - min_candle[3]) / min_candle[3], 3) > 0.01 and \
                    round((candle_var[i + 1][6] - candle_var[i + 1][3]) / candle_var[i + 1][3], 3) > 0.01 and \
                    round((candle_var[i + 2][6] - candle_var[i + 2][3]) / candle_var[i + 2][3], 3) > 0.01:
                config.buy_sign = True
                print('>>>>>>>>>>>> 5 ', datetime.datetime.now(), ' : ', market, ' 급등 : BUY All', ', buy_sign : ', config.buy_sign)

    if buy_sign != config.buy_sign:
        print('buy sing changed : ', buy_sign)


# 하루 거래량이 다른 날의 평균 거래량보다 5배 이상 많은 종목 선정
def search_9am_target(market):
    # print(market)
    candle_var = search_candle_chart(market, 'days', 0, 250)
    # print(candle_var)
    trade_volume_sum = 0
    trade_volume_avg = 0

    for i, day_candle in enumerate(candle_var[0:21]):
        if i == 0:
            pass
        else:
            # print(i, ' ', day_candle)
            # print(day_candle[2], day_candle[4], day_candle[5], day_candle[3], day_candle[12])
            trade_volume_sum += day_candle[9]
            #print(candle_var[i+j+1][2], ' 거래량 : ', candle_var[i+j+1][9], ', trade_volume_sum : ', trade_volume_sum)

    trade_volume_avg = trade_volume_sum / len(candle_var[0:21])
    # print(' trade_volume_avg : ', trade_volume_avg)

    for i, day_candle in enumerate(candle_var[0:21]):
        if i == 0:
            pass
        else:
            if float(day_candle[9]) > trade_volume_avg * 5:
                # print(' day target : ', market)
                return market
    time.sleep(0.5)


# 하루 거래량이 다른 날의 평균 거래량보다 5배 이상 많은 종목 선정
def search_min_target(market):
    candle_var = search_candle_chart(market, 'minutes', 5, 200)
    trade_volume_sum = 0

    for i, min_candle in enumerate(candle_var):
        if i == 0:
            pass
        else:
            # print(i, ' ', min_candle)
            # print(min_candle[2][11:16], min_candle[9])
            trade_volume_sum += min_candle[9]
            # print(candle_var[i+j+1][2], ' 거래량 : ', candle_var[i+j+1][9], ', trade_volume_sum : ', trade_volume_sum)

    trade_volume_avg = trade_volume_sum / len(candle_var[1:])
    # print(' trade_volume_avg : ', trade_volume_avg)

    for i, min_candle in enumerate(candle_var[1:]):
        # print('check : ', min_candle)
        if min_candle[2][11:16] == '09:00' and float(min_candle[9]) > trade_volume_avg * 10:
            print(' 9AM target : ', market)
            return market
    time.sleep(0.5)
