import configparser
import sys
from operator import itemgetter

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import requests
import quotation_func
import exchange_func
import config
import time
import datetime
import schedule
import multiprocessing as mp


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setGeometry(100, 200, 300, 200)
        self.setWindowTitle("Coin Trade")

        self.btnSearch = QPushButton("시세조회", self)
        self.btnSearch.move(1200, 100)
        self.btnSearch.setToolTip('Search Market')
        self.btnSearch.clicked.connect(self.search_today_ticker)

        self.btnSearchAccount = QPushButton("계좌조회", self)
        self.btnSearchAccount.move(1200, 130)
        self.btnSearchAccount.clicked.connect(self.search_account)

        self.btnTrade = QPushButton("매매", self)
        self.btnTrade.move(1300, 130)
        self.btnTrade.clicked.connect(self.trade_coin)

        self.chbAutoTrade = QCheckBox("자동매매", self)
        self.chbAutoTrade.move(1310, 160)
        # self.chbAutoTrade.stateChanged.connect(self.start_auto_trade)

        self.btnCalcProfit = QPushButton("수익률 계산", self)
        self.btnCalcProfit.move(1200, 160)
        self.btnCalcProfit.clicked.connect(self.calc_top_item_profit)

        self.txtProfit10 = QTextEdit(self)
        self.txtProfit10.move(1200, 200)
        self.txtProfit20 = QTextEdit(self)
        self.txtProfit20.move(1200, 250)

        # KRW 마켓 목록
        self.marketTable = QTableWidget(4, 3, self)
        self.marketTable.setGeometry(10, 100, 200, 300)

        # 당일 시세 목록
        self.tickerTableLabel = QLabel("당일 시세", self)
        self.tickerTableLabel.move(10, 70)
        self.tickerTable = QTableWidget(self)
        self.tickerTable.setGeometry(10, 100, 1150, 400)
        self.tickerTable.doubleClicked.connect(self.ticker_double_clicked)
        self.tickerTable.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.tickerTable.setSelectionBehavior(QAbstractItemView.SelectRows)  # Row 단위 선택
        self.tickerTable.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 셀 edit 금지

        ticker_add_favor_action = QAction('계속 보유에 추가', self.tickerTable)
        ticker_add_except_action = QAction('거래 제외에 추가', self.tickerTable)
        ticker_buy_coin_action = QAction('매수', self.tickerTable)

        self.tickerTable.addAction(ticker_add_favor_action)
        self.tickerTable.addAction(ticker_add_except_action)
        self.tickerTable.addAction(ticker_buy_coin_action)

        ticker_add_favor_action.triggered.connect(self.ticker_add_favor)
        ticker_add_except_action.triggered.connect(self.ticker_add_except)
        ticker_buy_coin_action.triggered.connect(self.ticker_buy_coin)

        # 보유 마켓 목록
        self.accountTableLabel = QLabel("보유 종목", self)
        self.accountTableLabel.move(10, 500)
        self.accountTable = QTableWidget(0, 0, self)
        self.accountTable.setGeometry(10, 530, 650, 300)
        self.accountTable.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.accountTable.setSelectionBehavior(QAbstractItemView.SelectRows)  # Row 단위 선택
        self.accountTable.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 셀 edit 금지

        acc_add_favor_action = QAction('계속 보유에 추가', self.accountTable)
        acc_add_except_action = QAction('거래 제외에 추가', self.accountTable)
        acc_sell_coin_action = QAction('매도', self.accountTable)

        self.accountTable.addAction(acc_add_favor_action)
        self.accountTable.addAction(acc_add_except_action)
        self.accountTable.addAction(acc_sell_coin_action)

        acc_add_favor_action.triggered.connect(self.acc_add_favor)
        acc_add_except_action.triggered.connect(self.acc_add_except)
        acc_sell_coin_action.triggered.connect(self.acc_sell_coin)

        # 거래 관심 대상 목록
        self.favorMarketTableLabel = QLabel("보유 대상 종목", self)
        self.favorMarketTableLabel.move(700, 500)
        self.favorMarketTable = QTableWidget(0, 1, self)
        self.favorMarketTable.setGeometry(700, 530, 130, 300)
        self.favorMarketTable.horizontalHeader().setVisible(False)  # 열번호 안나오게 하는 코드
        self.favorMarketTable.setSelectionBehavior(QAbstractItemView.SelectRows)  # Row 단위 선택
        self.favorMarketTable.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 셀 edit 금지
        self.favorMarketTable.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.favorMarketTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        remove_favor_action = QAction('제거', self.favorMarketTable)
        self.favorMarketTable.addAction(remove_favor_action)
        remove_favor_action.triggered.connect(self.favor_remove_market)

        # 거래 제외 대상 목록
        self.exceptMarketTableLabel = QLabel("제외 대상 종목", self)
        self.exceptMarketTableLabel.move(850, 500)
        self.exceptMarketTable = QTableWidget(0, 1, self)
        self.exceptMarketTable.setGeometry(850, 530, 130, 300)
        self.exceptMarketTable.horizontalHeader().setVisible(False)  # 열번호 안나오게 하는 코드
        self.exceptMarketTable.setSelectionBehavior(QAbstractItemView.SelectRows)  # Row 단위 선택
        self.exceptMarketTable.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 셀 edit 금지
        self.exceptMarketTable.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.exceptMarketTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        remove_except_action = QAction('제거', self.exceptMarketTable)
        self.exceptMarketTable.addAction(remove_except_action)
        remove_except_action.triggered.connect(self.except_remove_market)


        # 급등 종목
        self.hotTableLabel = QLabel("급등 종목", self)
        self.hotTableLabel.move(1000, 500)
        self.hotTableLabel = QTableWidget(0, 1, self)
        self.hotTableLabel.setGeometry(1000, 530, 130, 300)
        self.hotTableLabel.horizontalHeader().setVisible(False)  # 열번호 안나오게 하는 코드
        self.hotTableLabel.setSelectionBehavior(QAbstractItemView.SelectRows)  # Row 단위 선택
        self.hotTableLabel.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 셀 edit 금지
        self.hotTableLabel.setContextMenuPolicy(Qt.ActionsContextMenu)

        # MarketCap List
        self.marketCapTableLabel = QLabel("마켓 순위", self)
        self.marketCapTableLabel.move(1200, 320)
        self.marketCapTable = QTableWidget(0, 1, self)
        self.marketCapTable.setGeometry(1200, 350, 200, 500)
        self.marketCapTable.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.statusBar().showMessage('Ready')

        self.exitAction = QAction(QIcon('exit.png'), 'Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(qApp.quit)

        self.searched_user_api_key = []

        self.timer_one = QTimer()
        self.timer_one.setInterval(60000)
        self.timer_one.timeout.connect(self.do_time_schedule)
        self.timer_one.start()

        # 화면 구성

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.exitAction)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(self.exitAction)

        # 시작할 때 바로 수
        self.config_add_favor()
        self.do_time_schedule()
        # self.chbAutoTrade.setChecked(True)


    '''
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_F:
            self.showFullScreen()
        elif e.key() == Qt.Key_N:
            self.showNormal()
    def mousePressEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            print('LEFT')
        if e.buttons() & Qt.RightButton:
            print('RIGHT')
    '''

    '''
    자동매매 체크 버튼 상태 변화시 수행
    def start_auto_trade(self, state):
        print('chbox1 : ' + str(state))
        if state:
            print('ok')
    '''

    def ticker_double_clicked(self):
        row = self.tickerTable.currentRow()
        col = self.tickerTable.currentColumn()
        item = self.tickerTable.currentItem()
        print(row, col, item, item.text())

    def ticker_add_favor(self):
        market = self.tickerTable.item(self.tickerTable.currentRow(), 0).text()
        # print('tickerTable_add_favor', item)
        self.favorMarketTable.insertRow(self.favorMarketTable.rowCount())
        self.favorMarketTable.setItem(self.favorMarketTable.rowCount() -1, 0, QTableWidgetItem(market))
        # ini 파일에 추가
        self.update_config_market('I', 'FAVOR', market)

    def ticker_add_except(self):
        market = self.tickerTable.item(self.tickerTable.currentRow(), 0).text()
        # print('tickerTable_add_except', item)
        self.exceptMarketTable.insertRow(self.exceptMarketTable.rowCount())
        self.exceptMarketTable.setItem(self.exceptMarketTable.rowCount() -1, 0, QTableWidgetItem(market))
        # ini 파일에 추가
        self.update_config_market('I', 'EXCEPT', market)

    def acc_add_favor(self):
        market = self.accountTable.item(self.accountTable.currentRow(), 5).text() + '-' + \
                 self.accountTable.item(self.accountTable.currentRow(), 0).text()
        # print('tickerTable_add_favor', item)
        self.favorMarketTable.insertRow(self.favorMarketTable.rowCount())
        self.favorMarketTable.setItem(self.favorMarketTable.rowCount() -1, 0, QTableWidgetItem(market))
        # ini 파일에 추가
        self.update_config_market('I', 'FAVOR', market)

    def acc_add_except(self):
        market = self.accountTable.item(self.accountTable.currentRow(), 5).text() + '-' + \
                 self.accountTable.item(self.accountTable.currentRow(), 0).text()
        # print('tickerTable_add_except', item)
        self.exceptMarketTable.insertRow(self.exceptMarketTable.rowCount())
        self.exceptMarketTable.setItem(self.exceptMarketTable.rowCount() -1, 0, QTableWidgetItem(market))
        # ini 파일에 추가
        self.update_config_market('I', 'EXCEPT', market)

    def favor_remove_market(self):
        market = self.favorMarketTable.item(self.favorMarketTable.currentRow(), 0).text()
        self.update_config_market('D', 'FAVOR', market)
        self.favorMarketTable.removeRow(self.favorMarketTable.currentRow())

    def except_remove_market(self):
        market = self.exceptMarketTable.item(self.exceptMarketTable.currentRow(), 0).text()
        self.update_config_market('D', 'EXCEPT', market)
        self.exceptMarketTable.removeRow(self.exceptMarketTable.currentRow())

    # Config 에 등록되어 있는 항목을 화면에 반영
    def config_add_favor(self):
        config_file = configparser.ConfigParser()
        if config_file.read(config.ini_file_name, encoding='utf-8'):
            # 해당 USER가 있는지 확인하여 값 셋팅
            if config_file.has_section('MARKET'):
                if config_file.has_option('MARKET', 'FAVOR'):
                    favor_market = config_file['MARKET']['FAVOR'].split(',')
                    for market in favor_market:
                        self.favorMarketTable.insertRow(self.favorMarketTable.rowCount())
                        self.favorMarketTable.setItem(self.favorMarketTable.rowCount() -1, 0, QTableWidgetItem(market))
                if config_file.has_option('MARKET', 'EXCEPT'):
                    except_market = config_file['MARKET']['EXCEPT'].split(',')
                    for market in except_market:
                        self.exceptMarketTable.insertRow(self.exceptMarketTable.rowCount())
                        self.exceptMarketTable.setItem(self.exceptMarketTable.rowCount() -1, 0, QTableWidgetItem(market))

    def search_account_market(self):
        account_market = []
        for row in range(0, self.accountTable.rowCount()):
            market = self.accountTable.item(row, 5).text() + '-' + self.accountTable.item(row, 0).text()
            # print(row, market)
            if self.accountTable.item(row, 5).text() != self.accountTable.item(row, 0).text():
                account_market.append(market)
        return account_market

    def buy_coin(self, order_market, side_val, hoga_level=0, buy_volume=0, buy_amount=0):

        orderbook_market = order_market
        orderbook_list = quotation_func.search_orderbook(orderbook_market)
        price = 0
        position_amount = 0

        if side_val == 'bid' and hoga_level >= 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][hoga_level]['ask_price'],
            #       orderbook_list[1][4][hoga_level]['ask_size'])
            price = orderbook_list[1][4][hoga_level]['ask_price']
        elif side_val == 'bid' and hoga_level < 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][abs(hoga_level+1)]['bid_price'],
            #       orderbook_list[1][4][abs(hoga_level+1)]['bid_size'])
            price = orderbook_list[1][4][abs(hoga_level + 1)]['bid_price']
        elif side_val == 'ask' and hoga_level >= 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][hoga_level]['bid_price'],
            #       orderbook_list[1][4][hoga_level]['bid_size'])
            price = orderbook_list[1][4][hoga_level]['bid_price']
        elif side_val == 'ask' and hoga_level < 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][abs(hoga_level+1)]['ask_price'],
            #       orderbook_list[1][4][abs(hoga_level+1)]['ask_size'])
            price = orderbook_list[1][4][abs(hoga_level + 1)]['ask_price']

        order_market_currency = order_market.split('-')[0]
        # print('BUY ', order_market.split('-')[1], ' from ', order_market.split('-')[0])

        accounts_res = exchange_func.search_accounts(self.searched_user_api_key)
        if accounts_res.status_code == 200:
            for acc in accounts_res.json():
                if acc['currency'] == order_market_currency:
                    position_amount = float(acc['balance'])
        else:
            print('account search error occurred')
            return False

        if buy_volume > 0:
            volume = buy_volume
            trade_amount = volume * price
            if trade_amount > position_amount:
                print('주문 금액이 보유현금보다 큽니다.')
                return False
        elif buy_amount > position_amount:
            print('주문 금액이 보유현금보다 큽니다.')
            return False
        elif buy_amount < 0:
            print('주문 금액이 0보다 작습니다.')
            return False
        elif buy_amount == 0:
            trade_amount = config.amount_per_order
            volume = round(trade_amount / price, 3)
            if trade_amount > position_amount:
                print('주문 금액이 보유현금보다 큽니다.')
                return False
        else:
            trade_amount = buy_amount
            volume = round(trade_amount / price, 3)
            if trade_amount > position_amount:
                print('주문 금액이 보유현금보다 큽니다.')
                return False

        # print('volume : ', volume, ' , price : ', price, ' , trade_amount : ', trade_amount, ' , position_amount : ', position_amount)

        if trade_amount > position_amount:
            print('주문 금액이 보유현금보다 큽니다.')
            return False
        else:
            # 주문 생성
            order_query = {'market': orderbook_list[1][0], 'side': side_val,  # bid 매수 / ask 매도
                           'volume': volume, 'price': price, 'ord_type': 'limit'}
            # print(order_query)
            exchange_func.create_orders(order_query)

        # 거래후 보유 종목 조회
        self.search_account()

    def sell_coin(self, order_market, side_val, hoga_level=0, sell_volume=0, sell_percent=0):

        orderbook_market = order_market
        orderbook_list = quotation_func.search_orderbook(orderbook_market)
        price = 0
        volume = 0

        if side_val == 'bid' and hoga_level >= 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][hoga_level]['ask_price'],
            #       orderbook_list[1][4][hoga_level]['ask_size'])
            price = float(orderbook_list[1][4][hoga_level]['ask_price'])
        elif side_val == 'bid' and hoga_level < 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][abs(hoga_level+1)]['bid_price'],
            #       orderbook_list[1][4][abs(hoga_level+1)]['bid_size'])
            price = float(orderbook_list[1][4][abs(hoga_level + 1)]['bid_price'])
        elif side_val == 'ask' and hoga_level >= 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][hoga_level]['bid_price'],
            #       orderbook_list[1][4][hoga_level]['bid_size'])
            price = float(orderbook_list[1][4][hoga_level]['bid_price'])
        elif side_val == 'ask' and hoga_level < 0:
            # print("check >> ", orderbook_list[1][0], orderbook_list[1][4][abs(hoga_level+1)]['ask_price'],
            #       orderbook_list[1][4][abs(hoga_level+1)]['ask_size'])
            price = float(orderbook_list[1][4][abs(hoga_level + 1)]['ask_price'])

        if sell_volume > 0:
            volume = float(sell_volume)
        elif sell_percent > 0:
            order_market_currency = order_market.split('-')[1]
            print('SELL ', order_market.split('-')[1], ' to ', order_market.split('-')[0])

            accounts_res = exchange_func.search_accounts(self.searched_user_api_key)
            if accounts_res.status_code == 200:
                for acc in accounts_res.json():
                    if acc['currency'] == order_market_currency:
                        # print('avg_buy_price:', acc['avg_buy_price'], ', price: ', price)
                        volume = round(float(acc['balance']) * float(sell_percent) / 100, 3)
            else:
                print('account search error occurred')
                return False
        else:
            order_market_currency = order_market.split('-')[1]
            # print(order_market_currency)

            accounts_res = exchange_func.search_accounts(self.searched_user_api_key)
            if accounts_res.status_code == 200:
                for acc in accounts_res.json():
                    if acc['currency'] == order_market_currency:
                        # print('avg_buy_price:', acc['avg_buy_price'], ', price: ', price)
                        volume = float(acc['balance'])
            else:
                print('account search error occurred')
                return False

        # 금액과 수량이 정상적으로 계산되었을 때에만 매도 주문 실행
        if volume > 0 and price > 0:
            # 주문 생성
            order_query = {'market': orderbook_list[1][0], 'side': side_val,  # bid 매수 / ask 매도
                           'volume': volume, 'price': price, 'ord_type': 'limit'}
            # print(order_query)
            exchange_func.create_orders(order_query)
        else:
            print('금액 또는 수량에 문제가 있습니다.', str(volume), str(price))

        # 거래후 보유 종목 조회
        self.search_account()

    def search(self):
        result_data = quotation_func.search_market_list()
        self.marketTable.setColumnCount(len(result_data[0]))
        self.marketTable.setRowCount(len(result_data))
        column_headers = ['기준화폐', '종목코드', '한글종목명', '영어종목명']
        self.marketTable.setHorizontalHeaderLabels(column_headers)

        for row, market in enumerate(result_data):
            for col, val in enumerate(market):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.marketTable.setItem(row, col, item)

        self.marketTable.resizeColumnsToContents()
        self.marketTable.resizeRowsToContents()

        # print(self.findChild(QTableWidget, name='qtable'))

    def search_account(self):

        # 거래전 API KEY 있는지 체크하고 config 에 입력
        self.searched_user_api_key = exchange_func.search_api_key()
        # print('search : ', self.searched_user_api_key)
        if self.searched_user_api_key['access_key'] == 'NONE':
            print(">>>  No User KEY ")

            # TODO 화면 입력시 처리할 함수, 테스트용으로 여기서 수행
            # exchange_func.insert_api_key()

        row = 0
        self.accountTable.setRowCount(row)

        # 계좌정보 조회
        accounts_res = exchange_func.search_accounts(self.searched_user_api_key)
        for row, acc in enumerate(accounts_res.json()):
            # print('현재 보유 항목 : ', row, '  ', acc)
            if row == 0:
                column_headers = list(acc.keys())
                column_headers.append('buy amount')
                column_headers.append('cur amount')
                column_headers.append('rate')
                self.accountTable.setColumnCount(len(column_headers))
                self.accountTable.setHorizontalHeaderLabels(column_headers)
                self.accountTable.setColumnWidth(0, 70)
                self.accountTable.setColumnWidth(8, 60)

            if acc['currency'] != acc['unit_currency']:
                config.position_market.append([datetime.datetime.now(), acc['unit_currency'] + '-' + acc['currency']])

            self.accountTable.insertRow(row)

            for col, val in enumerate(acc.values()):
                item = QTableWidgetItem(str(''))

                if col in (2, 4):
                    self.accountTable.setColumnHidden(col, True)
                # print(val)
                elif col == 1:
                    if acc['currency'] == acc['unit_currency']:
                        val = 0
                    else:
                        val = val
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                elif col == 3:
                    val = round(float(val), 3)
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                else:
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)

                self.accountTable.setItem(row, col, item)

            if acc['currency'] == acc['unit_currency']:
                item = QTableWidgetItem(str(round(float(acc['balance']))))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.accountTable.setItem(row, 6, item)
            else:
                buy_price = float(acc['avg_buy_price'])
                buy_amt = round(float(acc['balance']) * buy_price)
                item = QTableWidgetItem(str(buy_amt))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.accountTable.setItem(row, 6, item)

                market = acc['unit_currency'] + '-' + acc['currency']
                for ticker_row in range(0, self.tickerTable.rowCount()):
                    if market == self.tickerTable.item(ticker_row, 0).text():
                        # print(ticker_row, ' ', market, ' ', self.tickerTable.item(ticker_row, 9).text())
                        item = QTableWidgetItem(self.tickerTable.item(ticker_row, 9).text())
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                        self.accountTable.setItem(row, 7, item)

                        cur_price = float(self.tickerTable.item(ticker_row, 9).text())
                        # print('cur_price : ', cur_price)
                        rate = round((cur_price - buy_price) / buy_price * 100, 1)
                        item = QTableWidgetItem(str(rate))
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                        self.accountTable.setItem(row, 8, item)

        # self.accountTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.accountTable.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)

    def trade_coin(self):
        print(' trade_coin START  ', datetime.datetime.now())

        ticker_market = []
        # print('trade market ranking : ', config.trade_target_rank10)
        for row in range(0, config.trade_target_rank10):
            print(row, self.tickerTable.item(row, 0).text())
            ticker_market.append(self.tickerTable.item(row, 0).text())

        # print(ticker_market)

        # 계속 보유할 대상 조회
        favor_market = []
        for row in range(0, self.favorMarketTable.rowCount()):
            favor_market.append(self.favorMarketTable.item(row, 0).text())

        # 보유하지 않을 대상 조회
        except_market = []
        for row in range(0, self.exceptMarketTable.rowCount()):
            except_market.append(self.exceptMarketTable.item(row, 0).text())

        # 보유 종목 조회
        account_market = self.search_account_market()
        # print(account_market)

        # 보유종목에서 매도 대상 처리
        for market in account_market:
            # 당일 시세 순위에 없고 보유대상 종목에 없으면 매도
            if market not in ticker_market and \
               market not in favor_market:
                if market != 'KRW-VTHO':
                    print(market, '  not found, SELL')
                    self.sell_coin(market, 'ask', 0, 0, 0)

            # 제외 대상 종목에 있으면 매도
            if market in except_market:
                if market != 'KRW-VTHO':
                    print(market, '  except target, SELL')
                    self.sell_coin(market, 'ask', 0, 0, 0)

        # 당일 시세 상위 종목 매수
        for row in range(0, config.trade_target_rank10):
            # print(row, self.tickerTable.item(row, 0).text())
            if self.tickerTable.item(row, 0).text() not in account_market and \
               self.tickerTable.item(row, 0).text() not in except_market:
                print(self.tickerTable.item(row, 0).text(), '  not found, BUY')
                self.buy_coin(self.tickerTable.item(row, 0).text(), 'bid', 0, 0, 0)

        # 보유 대상에 있는 목록중 보유종목에 없으면 매수
        for market in favor_market:
            if market not in account_market:
                print(market, '  favor target, BUY')
                self.buy_coin(market, 'ask', 0, 0, 0)

        print(' trade_coin END  ', datetime.datetime.now())


    def search_today_ticker(self):
        result_data = quotation_func.search_market_list()
        # print(result_data)

        market_list_all = []
        for market in result_data:
            market_list_all.append(market[1])

        day_ticker_result = quotation_func.search_ticker(market_list_all)
        # print(day_ticker_result)
        self.tickerTable.setColumnCount(len(day_ticker_result[0]))
        self.tickerTable.setRowCount(len(day_ticker_result) - 1)
        column_headers = day_ticker_result[0]
        sorted_day_ticker_result = sorted(day_ticker_result[1:], key=itemgetter(18), reverse=True)
        self.tickerTable.setHorizontalHeaderLabels(column_headers)
        # self.tickerTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tickerTable.setColumnHidden(2, True)

        for row, market in enumerate(sorted_day_ticker_result):
            # print(market)
            for col, val in enumerate(market):
                # if row == 0:
                #    print(val)
                if col in (1, 2, 3, 4, 5, 12, 13, 16, 19, 20, 25):
                    val = ''
                    self.tickerTable.setColumnHidden(col, True)
                elif col == 15:
                    val = round(float(val) * 100, 2)
                elif col in (17, 18):
                    val = round(val / 1000000)

                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tickerTable.setItem(row, col, item)

                # self.tickerTable.setItem(row, col, QTableWidgetItem(str(val)))

                # print(self.tickerTable.item(row, col).ItemType)

        # self.tickerTable.resizeColumnsToContents()
        # self.tickerTable.resizeRowsToContents()

        # self.tickerTable.setItem(3, 1, QTableWidgetItem(day_ticker_result[1][6]))

    # 순위 내의 수익률 계산
    def calc_profit(self, rank):

        rowcount = self.tickerTable.rowCount()

        if rank > rowcount:
            return False

        buy_amount = 10000

        sum_value = 0
        for i in range(0, rank):
            # print(self.tickerTable.item(i, 0).text(), ' : ', self.tickerTable.item(i, 6).text(),
            #       self.tickerTable.item(i, 15).text(),
            #       round(float(self.tickerTable.item(i, 6).text()) *
            #             float(self.tickerTable.item(i, 15).text()) / 100,2))

            # 각 마켓의 수익금액
            sum_value = sum_value + buy_amount * float(self.tickerTable.item(i, 15).text()) / 100

        # 수익률 평균 계산
        return round(sum_value / rank / 100, 3)

    def calc_top_item_profit(self):

        self.txtProfit10.setText(str(self.calc_profit(10)))
        self.txtProfit20.setText(str(self.calc_profit(20)))

    def search_market_list(self):
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
                        pass
                    else:
                        markets.append(list(result.values()))
                        # title 을 제거하면서 index를 -1 처리함
                        markets[i-1].insert(0, currency)

                    i += 1

        # print(markets)
        return markets

    def ticker_buy_coin(self):
        market = self.tickerTable.item(self.tickerTable.currentRow(), 0).text()
        print(market, '  TICKER MANUAL BUY')
        self.buy_coin(market, 'bid', 0, 0, 0)

    def acc_sell_coin(self):
        market = self.accountTable.item(self.accountTable.currentRow(), 5).text() + '-' + \
                 self.accountTable.item(self.accountTable.currentRow(), 0).text()
        print(market, '  ACCOUNT MANUAL SELL')
        self.sell_coin(market, 'ask', 0, 0, 0)

    def sell_all_coin(self):
        print(time.strftime('%Y%m%d %H%M%s'), ' : sell_all_coin start')
        # 거래량으로 매도 대상 찾기
        sell_target = self.search_account_market()
        # print(sell_target)

        # 찾은 대상으로 주문하기
        for market in sell_target:
            # random 으로 값이 1인 경우에만 매수
            self.sell_coin(market, 'ask', 0, 0, 0)
            time.sleep(0.5)

    # 거래량 급등하는 종목 선정
    def buy_trade_volume_increase(self):
        print(' buy_trade_volume_increase START  ', datetime.datetime.now())
        ticks_target = []

        trade_market_list = quotation_func.search_market_list()
        # print(trade_market_list)

        for market in trade_market_list[:50]:
            order, day_market = quotation_func.search_ticks(market[1], 300)
            if day_market != 'X':
                ticks_target.append([order, day_market])
            time.sleep(0.05)

        # 순간 체결량이 많은 순서로 정렬
        ticks_target.sort()
        cur_time = datetime.datetime.now().strftime('%Y%m%d %H:%M:%s')
        print(cur_time, ' : ticks_target all : ', ticks_target)

        # 찾은 대상으로 주문하기

        for order, market in ticks_target:
            item = QTableWidgetItem(market)
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            row = self.hotTableLabel.insertRow()
            self.hotTableLabel.setItem(row, 0, item)
            self.hotTableLabel.setItem(row, 1, QTableWidgetItem(cur_time))

        print(' buy_trade_volume_increase END  ', datetime.datetime.now())

    def do_time_schedule(self):
        self.search_today_ticker()
        self.search_account()

        cur_datetime = datetime.datetime.now()
        cur_weekday = cur_datetime.weekday()
        cur_time = cur_datetime.strftime('%H:%M')

        if cur_weekday == 6 and cur_time <= '08:30':
            print('일요일 오전 쉬기 ')
            pass
        elif cur_weekday == 5 and cur_time == '11:55':
            print('일요일 오전 쉬기, 모두 팔아버림')
            self.acc_sell_coin()

        elif cur_time == '08:58':
            print('시간 : ', cur_time)
            self.acc_sell_coin()
            print('처리 확인')
            # self.buy_kimchi_coin()

        elif cur_time == '09:10':
            print('김치코인 정리')
            # self.sell_kimchi_coin()

        elif self.chbAutoTrade.isChecked():
            self.trade_coin()

            p = mp.Process(name='trade_by_volume', target=self.buy_trade_volume_increase)
            p.start()

        # else:
        #     print(cur_time)


    # API 접속키 추가
    def update_config_market(self, cmd, market_kind, market):
        config_file = configparser.ConfigParser()
        if config_file.read(config.ini_file_name, encoding='utf-8'):
            print('exists')
        else:
            print('not exists')

        if not config_file.has_section('MARKET'):
            config_file.add_section('MARKET')

        if cmd == 'I':
            # print(config_file['MARKET'][market_kind])
            if config_file.has_option('MARKET', market_kind):
                config_file['MARKET'][market_kind] = config_file['MARKET'][market_kind] + ',' + market
                # print('a : ', config_file['MARKET'][market_kind])
            else:
                config_file['MARKET'][market_kind] = market

            with open(config.ini_file_name, 'w', encoding='utf-8') as configfile:
                config_file.write(configfile)
        elif cmd == 'D':
            if config_file.has_option('MARKET', market_kind):
                pos_market = config_file['MARKET'][market_kind].find(market)
                content1 = config_file['MARKET'][market_kind][0:pos_market]
                content2 = config_file['MARKET'][market_kind][config_file['MARKET'][market_kind].find(',', pos_market)+1:]

                config_file['MARKET'][market_kind] = content1 + content2

                with open(config.ini_file_name, 'w', encoding='utf-8') as configfile:
                    config_file.write(configfile)

        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.setGeometry(10, 10, 1200, 800)

    # window.show()
    window.showFullScreen()
    sys.exit(app.exec_())

