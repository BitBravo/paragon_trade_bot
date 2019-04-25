import requests

url = "http://127.0.0.1:5012/create_trade"

payload = {
    'pair': "BTC_MFT",
    'buy_price': "0.00000075",
    'stop_loss': '0.00000077',
    'tp1': '0.00000087',
    'tp2': '0.00000091',
    'tp3': '0.00000095',
    'tp4': '0.00000100',
    'note': 'test'
}

res = requests.post(url, data = payload)