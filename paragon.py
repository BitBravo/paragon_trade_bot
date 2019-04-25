import requests
import json
from threading import Thread

class Paragon(object):
    def __init__(self, api_key):
        super(Paragon, self).__init__()
        self.api_key = api_key
        self.user_levels = {'premium': [9, 10, 11, 8, 5, 6, 7],
                            'free': [4]}
    def get_premium_users(self):
        users_with_premium_role = []
        for level in self.user_levels['premium']:
            url = "https://paragoncryptohub.com/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={}&action=get_level_users&lid={}".format(self.api_key, level)
            res = requests.get(url)
            results = json.loads(res.content)['response']
            for result in results:
                try:
                    user = {
                        'username': result['username'],
                        'user_id': result['user_id']
                    }
                    if user not in users_with_premium_role:
                        users_with_premium_role.append(user)
                except:
                    continue
        return users_with_premium_role
    def get_free_users(self):
        premium_users = self.get_premium_users()
        users_with_free_role = []
        for level in self.user_levels['free']:
            url = "https://paragoncryptohub.com/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={}&action=get_level_users&lid={}".format(self.api_key, level)
            res = requests.get(url)
            results = json.loads(res.content)['response']
            for result in results:
                try:
                    user = {
                        'username': result['username'],
                        'user_id': result['user_id']
                    }
                    if user not in users_with_free_role:
                        users_with_free_role.append(user)
                except:
                    continue
        free_users = []
        for user in users_with_free_role:
            if user not in premium_users:
                free_users.append(user)
        return free_users
    def get_user_level_expired(self, user_id):
        url = "https://paragoncryptohub.com/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={}&action=get_user_levels&uid={}".format(self.api_key, user_id)
        res = requests.get(url)
        results = json.loads(res.content)['response']
        expired = True
        for level in self.user_levels['premium']:
            if str(level) in results:
                if results[str(level)]['is_expired'] == False:
                    expired = False
        return expired
    def get_user_data(self, user_id, result_dict, type):
        try:
            url = "https://paragoncryptohub.com/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={}&action=user_get_details&uid={}".format(self.api_key, user_id)
            res = requests.get(url)
            results = json.loads(res.content)['response']
            user ={
                'name': results['display_name'],
                'email': results['user_email'],
                'joined': results['user_registered']
            }
            if type == "free":
                result_dict['free'].append(user)
            else:
                expired = self.get_user_level_expired(user_id)
                if expired:
                    result_dict['free'].append(user)
                else:
                    result_dict['premium'].append(user)
        except:
            return

    def get_users_with_data(self):
        NUM_WORKER_THREADS = 10
        users_with_data = {
            'free': [],
            'premium': []
        }
        threads = []
        free_users = self.get_free_users()
        for user in free_users:
            if len(threads) >= NUM_WORKER_THREADS:
                for thread in threads:
                    thread.join()
                threads = []
            thread = Thread(target = self.get_user_data, args = (user['user_id'], users_with_data, 'free',))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        threads = []
        premium_users = self.get_premium_users()
        for user in premium_users:
            if len(threads) >= NUM_WORKER_THREADS:
                for thread in threads:
                    thread.join()
                threads = []
            thread = Thread(target = self.get_user_data, args = (user['user_id'], users_with_data, 'premium',))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        return users_with_data


