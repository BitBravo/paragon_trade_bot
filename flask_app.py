from flask import Flask,jsonify,request,url_for,abort,g, render_template, redirect
from apscheduler.scheduler import Scheduler
from flask import Response
import requests
from db import DBSession, User, ProcessedTarget, Signal, Trade, Account, Channel, Profile
from threading import Thread
import time
from ThreeCommas import ThreeCommas
import traceback
import json
import math
from email_lib import Mailer
import random
from paragon import Paragon
from get_response import GetResponse
from binance.client import Client
import datetime

NUM_WORKER_THREADS = 1000

app = Flask(__name__)

def get_buy_step_size(coin):
    client = Client(api_key="", api_secret="")
    for filt in client.get_symbol_info('{}BTC'.format(coin))['filters']:
        if filt['filterType'] == 'LOT_SIZE':
            return filt['stepSize']
        
def format_value(amount, step_size_str):
    precision = step_size_str.find('1') - 1
    if precision > 0:
        return "{:0.0{}f}".format(amount, precision)
    return math.floor(int(amount))

def check_smart_trades_for_user(user):
    while True:
        session = DBSession()
        try:
            account = session.query(Account).filter_by(user_name = user.username, type = 'binance').first()
            if account.active == False:
                session.close()
                continue
            apiKey = account.api_key
            apiSecret = account.api_secret
            account_name = account.name.strip()
            profile = session.query(Profile).filter_by(user_id= user.id).first()
            if profile:
                auto_close_timer = profile.auto_close_timer.split(":")
                auto_close_timer = int(auto_close_timer[0]) * 60 + int(auto_close_timer[1])
            else:
                auto_close_timer = 720 #minutes
            bot = ThreeCommas(apiKey, apiSecret)
            try:
                smart_trades = bot.get_smart_trades(account_name)
            except:
                traceback.print_exc()
                #send_debug_email("While fetching smart trades", user.user_name, traceback.format_exc())
            if smart_trades is None:
                print("Something wrong with: ", user.username)
                time.sleep(5)
                continue
            for smart_trade in smart_trades:
                
                if smart_trade['status'] == "buy_order_placed":
                    created_at = datetime.datetime.strptime(smart_trade["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
                    now = datetime.datetime.utcnow()
                    minutes_diff = (now - created_at).total_seconds() / 60
                    if minutes_diff >= auto_close_timer:
                        bot.cancel_smart_trade(smart_trade['id'])
                        continue

                updated_targets = []
                processed_target = None
                for target in smart_trade['take_profit_steps']:
                    prev_target = {'percent': target['percent'], 'price': target['price'], 'price_method': 'bid', 'position': target['position'] }
                    updated_targets.append(prev_target)
                    if target['status'] == "processed":
                        already_updated = session.query(ProcessedTarget).filter_by(user_name = user.username, trade_id = smart_trade['id'], step_id = target['id']).first()
                        if already_updated:
                            continue
                        processed_target = target
                if processed_target is not None:
                    stop_loss = None
                    if processed_target['position'] == 1:
                        stop_loss = smart_trade['buy_price']
                    else:
                        for step in smart_trade['take_profit_steps']:
                            if processed_target['position'] - 1 == step['position']:
                                stop_loss = step['price']
                                break
                    update = bot.update_smart_trade(smart_trade['id'], stop_loss, updated_targets)
                    try:
                        if update['id']:
                            processed = ProcessedTarget()
                            processed.user_name = user.username
                            processed.trade_id = update['id']
                            processed.step_id = processed_target['id']
                            session.add(processed)
                            session.commit()
                            #send_update_email(user.user_name, "trade_id = {}, step = {}, stop_loss = {}".format(update['id'], processed_target['position'], stop_loss))
                    except:
                        traceback.print_exc()
                        processed = ProcessedTarget()
                        processed.user_name = user.username
                        processed.trade_id = smart_trade['id']
                        processed.step_id = processed_target['id']
                        session.add(processed)
                        session.commit()
                        #send_debug_email("While updating stop loss after fetching smart trades", user.user_name, json.dumps(update) + "\n" + traceback.format_exc())
        except:
            traceback.print_exc()
            pass
        session.close()
        time.sleep(5)
        

def check_active_trades():
    with app.app_context():
        session = DBSession()
        threads = []
        users = session.query(User).filter_by(is_active = True).all()
        for user in users:
            if len(threads) >= NUM_WORKER_THREADS:
                print("waiting for threads to join")
                for thread in threads:
                    thread.join()
                threads = []
            thread = Thread(target = check_smart_trades_for_user, args = (user,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        session.close()


def search_dict(items,key, value):
    for item in items:
        if item[key] == value:
            return item

def update_get_response_list():
    while True:
        try:
            paragon = Paragon('r0XfXWfD9CRrwqvy77mZETHOSIRZD')

            paragon_users = paragon.get_users_with_data()

            get_response = GetResponse("0dc31e4f444e59eba59cffb6e8f609c8")

            get_response_users = get_response.get_all_users()

            for paragon_user in paragon_users['free']:
                get_response_user = search_dict(get_response_users['premium'], 'email', paragon_user['email']) 
                if get_response_user is not None:
                    contactId = get_response_user['contactId']
                    get_response.change_contact_campaign(contactId, get_response.cancelled_campaign)

            for paragon_user in paragon_users['premium']:
                get_response_user = search_dict(get_response_users['cancelled'], 'email', paragon_user['email']) 
                if get_response_user is not None:
                    contactId = get_response_user['contactId']
                    get_response.change_contact_campaign(contactId, get_response.premium_campaign)

            for paragon_user in paragon_users['free']:
                get_response_user_free = search_dict(get_response_users['free'], 'email', paragon_user['email']) 
                get_response_user_cancelled = search_dict(get_response_users['cancelled'], 'email', paragon_user['email']) 
                get_response_user_deleted = search_dict(get_response_users['deleted'], 'email', paragon_user['email']) 
                if get_response_user_free is None and get_response_user_cancelled is None and get_response_user_deleted is None:
                    name = paragon_user['name']
                    email = paragon_user['email']
                    get_response.create_contact(name,email, get_response.free_campaign)

            for paragon_user in paragon_users['premium']:
                get_response_user = search_dict(get_response_users['premium'], 'email', paragon_user['email']) 
                get_response_user_deleted = search_dict(get_response_users['deleted'], 'email', paragon_user['email']) 
                if get_response_user is None and get_response_user_deleted is None:
                    name = paragon_user['name']
                    email = paragon_user['email']
                    get_response.create_contact(name,email, get_response.premium_campaign)
        except:
            continue
        time.sleep(3*60)    
@app.before_first_request
def initialize():
    apsched = Scheduler()
    apsched.start()
    thread = Thread(target = check_active_trades, args = ())
    thread.daemon = True
    thread.start()
    thread = Thread(target = update_get_response_list, args = ())
    thread.daemon = True
    thread.start()

def create_smart_trade(user, pair, buy_price, targets, stop_loss, note, signal_id, code, stepSize):
    try:
        session = DBSession()
        account = session.query(Account).filter_by(user_name = user.username, type = 'binance').first()
        if account.active == False:
            session.close()
            return
        apiKey = account.api_key
        apiSecret = account.api_secret
        bot = ThreeCommas(apiKey, apiSecret)
        account_name = account.name.strip()
        channel = session.query(Channel).filter_by(user_name = user.username, code = code).first()
        if channel.active == False:
            session.close()
            return
        profile = session.query(Profile).filter_by(user_id= user.id).first()
        if profile:
            max_trades_per_coin = profile.max_trades_per_coin
            coin = pair.split("_")[-1]
            total_trades = bot.get_total_trades(coin, account_name)
            if total_trades >= max_trades_per_coin:
                db_trade = Trade(signal_id = signal_id,
                         channel = code,
                         user_name = user.username,
                         response = json.dumps({"status": "Ignored", "message": "max_trades_per_coin is reached for {}".format(pair)}))
                session.add(db_trade)
                session.commit()
                session.close()
                return
        else:
            session.close()
            return
        risk = channel.risk_percent
        allowed = channel.allowed_percent
        
        base_asset = pair.split("_")[0]
        balance = bot.get_balance(account_name, base_asset)
        total_value = float(balance['total_btc_value']) * (allowed/100)
        if float(buy_price) > 0.0001:
            buy_amount_total_potfolio = math.floor(((total_value * (float(risk)/100))/(abs((float(stop_loss)/float(buy_price))- 1)) / float(buy_price))*100)/100
            buy_amount_available_btc = math.floor((float(balance['total_available']) / float(buy_price))*100)/100
            min_amount = round(0.0011 * len(targets) / float(buy_price), 2)
        else:
            buy_amount_total_potfolio = math.floor((total_value * (float(risk)/100))/(abs((float(stop_loss)/float(buy_price))- 1)) / float(buy_price))
            buy_amount_available_btc = math.floor(float(balance['total_available']) / float(buy_price))
            min_amount = round(0.0011 * len(targets) / float(buy_price), 0)
        buy_amount = buy_amount_total_potfolio
        if float(balance['total_available']) < buy_amount_total_potfolio * float(buy_price):
            buy_amount = buy_amount_available_btc
        buy_amount = max(buy_amount , min_amount)
        if user.username == "bot_refrence_user":
            if float(buy_price) > 0.00011:
                buy_amount = round((0.0011 * len(targets))/ float(buy_price), 2)
            else:
                buy_amount = math.ceil((0.0011 * len(targets))/ float(buy_price))
                
        buy_amount = format_value(buy_amount, stepSize)
        trade = bot.create_smart_trade(account_name = account_name, pair = pair, units_to_buy = buy_amount,
                                       buy_price = buy_price, targets = targets, stop_loss = stop_loss, note= note)
        db_trade = Trade(signal_id = signal_id,
                         channel = code,
                         user_name = user.username,
                         response = json.dumps(trade))
        session.add(db_trade)
        session.commit()
        session.close()
    except:
        traceback.print_exc()
        session.close()
        #send_debug_email("While creating trade", user.user_name, traceback.format_exc())

@app.route("/")
def hello():
    return redirect("https://dashboard.paragoncryptohub.com", code=302)
    
@app.route('/create_trade', methods=['POST'])
def create_trade():
    session = DBSession()
    pair = request.form.get('pair')
    if pair.endswith("BTC"):
        pair = pair.split("_")
        pair = pair[1] + "_" + pair[0]
    buy_price = request.form.get('buy_price')
    stop_loss = request.form.get('stop_loss')
    targets = []
    tp1 = request.form.get('tp1')
    tp2 = request.form.get('tp2')
    tp3 = request.form.get('tp3')
    tp4 = request.form.get('tp4')
    note = request.form.get('note')
    code = request.form.get('code')
    if tp1 is not None and tp1 is not "":
        targets.append(tp1)
    else:
        return jsonify({"status" : "error", "message": "Target 1 is required."})
    if tp2 is not None and tp2 is not "":
        targets.append(tp2)
    if tp3 is not None and tp3 is not "":
        targets.append(tp3)
    if tp4 is not None and tp4 is not "":
        targets.append(tp4)
    signal = session.query(Signal).filter_by(pair = pair,
                                             buy_price = buy_price,
                                             stop_loss = stop_loss,
                                             tp1 = tp1,
                                             tp2 = tp2,
                                             tp3 = tp3,
                                             tp4 = tp4,
                                             note = note,
                                             channel = code).first()
    if signal:
        return jsonify({"status" : "error", "message": "Trade already taken"})
    signal = Signal(pair = pair,
                    buy_price = buy_price,
                    stop_loss = stop_loss,
                    tp1 = tp1,
                    tp2 = tp2,
                    tp3 = tp3,
                    tp4 = tp4,
                    note = note,
                    channel = code)
    session.add(signal)
    session.commit()
    users = session.query(User).filter_by(is_active = True).all()
    threads = []
    stepSize = get_buy_step_size(pair.split("_")[1])
    for user in users:
        if len(threads) >= NUM_WORKER_THREADS:
            print("waiting for threads to join")
            for thread in threads:
                thread.join()
            threads = []
        thread = Thread(target = create_smart_trade, args = (user, pair, buy_price, targets, stop_loss, note, signal.id, code, stepSize))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    session.close()
    return jsonify({"status" : "ok", "message": "Creating smart orders started."})

@app.route('/get_markets')
def get_markets():
    res= requests.get("https://www.binance.com/api/v1/ticker/allBookTickers")
    return Response(res.text,
                mimetype='application/json')

@app.route('/get_price')
def get_price():
    pair = request.args.get('symbol') 
    res= requests.get("https://www.binance.com/api/v3/ticker/price?symbol={}".format(pair))
    return Response(res.text,
                mimetype='application/json')

def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('https://auto.paragoncryptohub.com')
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)
            except:
                print('Server not yet started')
            time.sleep(2)

    print('Started runner')
    thread = Thread(target=start_loop)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    start_runner()
    app.run(debug=True,threaded=True, port = 5012)