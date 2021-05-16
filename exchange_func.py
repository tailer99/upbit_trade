import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

import requests
import configparser

import config
import time
import datetime

buy_sell_type = {'bid': 'BUY', 'ask': 'SELL'}


def search_accounts(api_key):
    payload = {
        'access_key': api_key['access_key'],
        'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, api_key['secret_key'])
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    response = requests.get(api_key['server_url'] + "/v1/accounts", headers=headers)

    # print('search_accounts RESULT : ', response.status_code, " ", response.json())
    if response.status_code == 200:
        pass
    else:
        print("error occurred : ", response.status_code, " ", response.json()['error']['name'],
              response.json()['error']['message'])

    return response


# 주문 가능 정보 조회
def search_order_chance(search_query):
    query = search_query
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': config.api_key['access_key'],
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, config.api_key['secret_key'])
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    response = requests.get(config.api_key['server_url'] + "/v1/orders/chance", params=query, headers=headers)

    print(response.json())

    if response.status_code == 200:
        pass
    else:
        print("error occurred : ", response.status_code, " ", response.json()['error']['name'],
              response.json()['error']['message'])

    return response


# 주문 리스트 조회
def search_orders(search_query):
    query = search_query
    print(query)

    query_string = urlencode(query)
    print(query_string)

    # uuids = [
    #     '9ca023a5-851b-4fec-9f0a-48cd83c2eaae',
    # ]
    uuids = []

    uuids_query_string = '&'.join(["uuids[]={}".format(uuid1) for uuid1 in uuids])

    query['uuids[]'] = uuids
    query_string = "{0}&{1}".format(query_string, uuids_query_string).encode()
    print(query_string)

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': config.api_key['access_key'],
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }
    print(payload)

    jwt_token = jwt.encode(payload, config.api_key['secret_key'])
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    response = requests.get(config.api_key['server_url'] + "/v1/orders", params=query, headers=headers)
    print(response.json())
    return response


# 주문 생성
def create_orders(order_query):
    query = order_query
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': config.api_key['access_key'],
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, config.api_key['secret_key'])
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    response = requests.post(config.api_key['server_url'] + "/v1/orders", params=query, headers=headers)
    # print('create_orders RESULT : ', response.status_code, " ", response.json())

    if response.status_code == 201:
        if buy_sell_type[query['side']] == 'BUY':
            config.position_market.append([datetime.datetime.now(), query['market']])
            config.position_market.sort()
        elif buy_sell_type[query['side']] == 'SELL':
            # print(config.position_market)
            for market in config.position_market:
                if market[1] == query['market']:
                    config.position_market.remove(market)

        log_file_name = config.trade_log_file_name + datetime.datetime.now().date().strftime('%Y%m%d') + '.log'
        with open(log_file_name, 'a', encoding='utf-8') as logfile:
            print(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), '  ', buy_sell_type[query['side']], ' : ', query['market'])
            logfile.writelines(datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ', ' + query['market'] + ', ' +
                               buy_sell_type[query['side']] + ', ' +
                               str(query['price']) + ', ' + str(query['volume']) + ', ' +
                               response.json()['uuid'] + '\n')
    else:
        # print("error occurred : ", response.status_code)
        log_file_name = config.trade_log_file_name + datetime.datetime.now().date().strftime('%Y%m%d') + '.log'
        with open(log_file_name, 'a', encoding='utf-8') as logfile:
            logfile.writelines(datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ', ' + query['market'] + ', ' +
                               buy_sell_type[query['side']] + ', ' +
                               str(query['price']) + ', ' + str(query['volume']) + ', ' +
                               'ERR: ' + response.json()['error']['message'] + '\n')

    return response


# 주문 취소
def cancel_orders(cancel_query):
    query = cancel_query
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': config.api_key['access_key'],
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, config.api_key['secret_key'])
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    response = requests.delete(config.api_key['server_url'] + "/v1/order", params=query, headers=headers)
    print(response)

    if response.status_code == 200:
        with open(config.trade_log_file_name, 'a', encoding='utf-8') as logfile:
            logfile.write(time.strftime('%Y%m%d%H%m%d') + ', ' + query['uuid'] + ' canceled ' + '\n')
    else:
        print("error occurred : ", response.status_code)
        with open(config.trade_log_file_name, 'a', encoding='utf-8') as logfile:
            logfile.write(time.strftime('%Y%m%d%H%m%d') + ', ' + query['uuid'] + ' cancel ' + 'ERR' + '\n')

    return response


# API 접속키 조회
def search_api_key():
    # TODO 사용자 이름을 따로 받아야 한다
    searched_api_key = {'user_name': config.api_key['user_name']}

    config_file = configparser.ConfigParser()
    if config_file.read(config.ini_file_name, encoding='utf-8'):
        # 해당 USER가 있는지 확인하여 값 셋팅
        if config_file.has_section(config.api_key['user_name']):
            searched_api_key['access_key'] = config_file[config.api_key['user_name']]['ACCESS_KEY']
            searched_api_key['secret_key'] = config_file[config.api_key['user_name']]['SECRET_KEY']
            searched_api_key['server_url'] = config_file[config.api_key['user_name']]['SERVER_URL']
            # print(searched_api_key)
            config.api_key = searched_api_key
            return searched_api_key
        else:
            searched_api_key['access_key'] = 'NONE'
            return searched_api_key
    else:
        searched_api_key['access_key'] = 'NONE'
        return searched_api_key


# API 접속키 추가
def insert_api_key():
    config_file = configparser.ConfigParser()
    if config_file.read(config.ini_file_name, encoding='utf-8'):
        print('exists')
    else:
        print('not exists')

    if not config_file.has_section(config.api_key['user_name']):
        config_file.add_section(config.api_key['user_name'])

    config_file[config.api_key['user_name']]['ACCESS_KEY'] = config.api_key['access_key']
    config_file[config.api_key['user_name']]['SECRET_KEY'] = config.api_key['secret_key']
    config_file[config.api_key['user_name']]['SERVER_URL'] = config.api_key['server_url']

    with open(config.ini_file_name, 'w', encoding='utf-8') as configfile:
        config_file.write(configfile)

    return True

