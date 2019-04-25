import requests
import json
import hmac
import hashlib
import base64
import time
from urllib.parse import urlencode

class ThreeCommas(object):
    def __init__(self, apiKey, secretKey):
        super(ThreeCommas, self).__init__()
        self.apiKey = apiKey
        self.secretKey = secretKey
        self.base_url = "https://3commas.io"
    def http_request(self, method, url, headers = None, params = None, data = None):
        RETRY = 5
        i = 0
        if method == "GET":
            while i < RETRY:
                try:
                    i += 1
                    res = requests.get(url, headers = headers, data = data, params = params)
                    return res
                except:
                    time.sleep(5)
                    continue
        elif method == "POST":
            while i < RETRY:
                try:
                    i += 1
                    res = requests.post(url, headers = headers, data = data, params = params)
                    return res
                except:
                    time.sleep(5)
                    continue
        elif method == "PATCH":
            while i < RETRY:
                try:
                    i += 1
                    res = requests.patch(url, headers = headers, data = data, params = params)
                    return res
                except:
                    time.sleep(5)
                    continue
        return False

    def generate_signature(self, url ,parameters):
        end_point = url + "?" + urlencode(parameters)
        digest = hmac.new(self.secretKey.encode("ascii"), msg=end_point.encode('ascii'), digestmod=hashlib.sha256).hexdigest()
        return digest
    

    def add_account(self, type, name, api_key, secret):
        url = "/public/api/ver1/accounts/new"
        params = {
            'type': type,
            'name': name,
            'api_key': api_key,
            'secret': secret
        }
        signature = self.generate_signature(url, params)
        
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("POST", api_url, headers = headers, params = params)
        return json.loads(res.content)

    def get_accounts(self):
        url = "/public/api/ver1/accounts"
        params = {}
        signature = self.generate_signature(url, params)
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("GET", api_url, headers = headers, params = params)
        return json.loads(res.content)

    def get_balance(self, account_name, asset):
        accounts = self.get_accounts()
        for account in accounts:
            if account['name'] == account_name:
                account_id = account['id']
        url = "/public/api/ver1/accounts/{}/pie_chart_data".format(account_id)
        params = {
        }
        signature = self.generate_signature(url, params)
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("POST", api_url, headers = headers, params = params)
        balances = json.loads(res.content)
        total_portfolio = 0
        for balance in balances:
            if balance['code'] == asset:
                total_available =  balance['amount']
            total_portfolio += balance['btc_value']
        return {'total_btc_value': total_portfolio, 'total_available': total_available}
    def get_smart_trades(self, account_name):
        account_id = ""
        url = "/public/api/ver1/smart_trades"
        accounts = self.get_accounts()
        for account in accounts:
            if account['name'] == account_name:
                account_id = account['id']
        offset = 0
        limit = 10
        smart_trades = []
        while True:
            params = {
                'scope': 'active',
                'account_id': account_id,
                'type': "SmartTrade::Classic",
                'limit': limit,
                'offset': offset
            }
            signature = self.generate_signature(url, params)
            headers = {
                'APIKEY': self.apiKey,
                'Signature': signature
            }
            api_url = self.base_url + url
            res = self.http_request("GET", api_url, headers = headers, params = params)
            trades = json.loads(res.content)
            if len(trades) < 1:
                break
            smart_trades.extend(trades)
            offset += limit
        return smart_trades
        

    def create_smart_trade(self, account_name, pair, units_to_buy,
                            buy_price, targets, stop_loss,
                            take_profit_sell_method = "market",
                            buy_method ="limit", note = ""):
        url = "/public/api/ver1/smart_trades/create_smart_trade"
        accounts = self.get_accounts()
        for account in accounts:
            if account['name'] == account_name:
                account_id = account['id']
        take_profit_orders = []
        targets = targets[:4]
        i = 0
        for target in targets:
            if len(targets) == 3:
                if i == 0:
                    percent = '34'
                else:
                    percent = '33'
            else:
                percent = str(100/len(targets))
            target_order = {'percent': percent , 'price': target , 'price_method': 'bid'}
            take_profit_orders.append(target_order)
            i += 1
        params = {
            'account_id': account_id,
            'pair': pair,
            'units_to_buy': units_to_buy,
            'buy_price': buy_price,
            'buy_method': buy_method,
            'trailing_buy_enabled': "false",
            'take_profit_enabled': "true",
            'take_profit_type': 'step_sell',
            'take_profit_step_orders': json.dumps(take_profit_orders),
            'take_profit_sell_method': take_profit_sell_method,
            'trailing_take_profit': "false",
            'stop_loss_enabled': "true",
            'stop_loss_price_condition': stop_loss,
            'note': note 
        }
        signature = self.generate_signature(url, params)
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("POST", api_url, headers = headers, data = params)
        return json.loads(res.content)

    def update_smart_trade(self, trade_id, stop_loss, targets, take_profit_sell_method = "market"):
        url = "/public/api/ver1/smart_trades/{}/update".format(trade_id)
        params = {
            'take_profit_enabled': "true",
            'take_profit_type': 'step_sell',
            'take_profit_step_orders': json.dumps(targets),
            'take_profit_sell_method': 'market',
            'stop_loss_enabled': "true",
            'stop_loss_price_condition': stop_loss
        }
        signature = self.generate_signature(url, params)
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("PATCH", api_url, headers = headers, data = params)
        return json.loads(res.content)

    def get_currencies(self, pair):
        url = "/public/api/ver1/accounts/currency_rates"
        take_profit_orders = []
        params = {
            'pretty_display_type': "Binance",
            'pair': pair,
        }
        signature = self.generate_signature(url, params)
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("GET", api_url, headers = headers, data = params)
        return json.loads(res.content)

    def get_total_trades(self,coin, account_name):
        smart_trades = self.get_smart_trades(account_name)
        total_trades = 0
        for smart_trade in smart_trades:
            if smart_trade['to_currency_code'].strip().lower() == coin.strip().lower():
                total_trades += 1
        return total_trades

    def cancel_smart_trade(self, smart_trade_id):
        url = "/public/api/ver1/smart_trades/{}/cancel".format(smart_trade_id)
        params = {}
        signature = self.generate_signature(url, params)
        headers = {
            'APIKEY': self.apiKey,
            'Signature': signature
        }
        api_url = self.base_url + url
        res = self.http_request("POST", api_url, headers = headers, params = params)
        return json.loads(res.content)

#1539659
'''apiKey = "1963a7bf73df4d7a81ccaa1833d82d1d6c69cda646eb44eb8018abb4435d4869"
secretKey = "7c072c4e10329b3b65b9b67b0338f75f11621080be70443a0aeeeb064515b9c99a18f7b6c39d5efab6fac9d7c27b6e5b3cf402323803709b64ddd0f74c99644b7bcd80084f281f293f261c99bed941a3ea06120349002573b93b72f44b496b3aef164d04"
Bot = ThreeCommas(apiKey, secretKey)
#print(Bot.get_balance('Binance','BTC_XRP'))

trade = Bot.create_smart_trade("Binance", "BTC_ETH", '0.5', '0.021102', ['0.021103', '0.021104', '0.021105', '0.021106'], '0.021100', note="ParagonBotTest")
#trade = Bot.update_smart_trade("1542814", "0.021100", ['0.021103', '0.021104', '0.021105', '0.021106'])

print(trade)
while 1:
    print(Bot.get_smart_trades())
    time.sleep(5)'''
