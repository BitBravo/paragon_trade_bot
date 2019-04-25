import requests
import json


class GetResponse(object):
    def __init__(self, api_key):
        super(GetResponse, self).__init__()
        self.api_key = api_key
        self.cancelled_campaign = "8ZBdp"
        self.premium_campaign = "agELC"
        self.free_campaign = "8ZBYu" 
        self.deleted_campaign = "82x9c"
        self.temp = "8xNde"
        self.headers = {
            "X-Auth-Token": "api-key {}".format(self.api_key)
        }

    def get_campaigns(self):
        url = "https://api.getresponse.com/v3/campaigns"
        res = requests.get(url, headers = self.headers)
        return json.loads(res.content)

    def search_contacts(self, email):
        url = "https://api.getresponse.com/v3/contacts?query[email]={}&fields=name,email,campaign&perPage=30".format(email)
        res = requests.get(url, headers = self.headers)
        return json.loads(res.content)
    def get_campaign_contacts(self, campaign_id):
        page = 1
        users = []
        while True:
            url = "https://api.getresponse.com/v3/campaigns/{}/contacts?page={}&perPage=100".format(campaign_id, page)
            res = requests.get(url, headers = self.headers)
            current_users = json.loads(res.content)
            if len(current_users) < 1:
                break
            users.extend(current_users)
            page += 1
        return users

    def get_all_users(self):
        all_users = {
            'free': self.get_campaign_contacts(self.free_campaign),
            'premium': self.get_campaign_contacts(self.premium_campaign),
            'cancelled': self.get_campaign_contacts(self.cancelled_campaign),
            'deleted': self.get_campaign_contacts(self.deleted_campaign),
            'temp': self.get_campaign_contacts(self.temp)
        }
        return all_users

    def get_contact(self, contact_id):
        url = "https://api.getresponse.com/v3/contacts/{}".format(contact_id)
        res = requests.get(url, headers = self.headers) 
        return json.loads(res.content)

    def change_contact_campaign(self, contact_id, campaign_id):
        url = "https://api.getresponse.com/v3/contacts/{}".format(contact_id)
        payload = {
            'campaign':{    
                'campaignId': campaign_id
            }

        }
        res = requests.post(url, headers = self.headers, json = payload) 
         

    def create_contact(self, name, email, campaign_id):
        url = "https://api.getresponse.com/v3/contacts"
        payload = {
            'name': name,
            'email': email,
            'campaign':{    
                'campaignId': campaign_id
            }
        }
        res = requests.post(url, headers = self.headers, json = payload) 
    
    def delete_contact(self, contact_id):
        url = "https://api.getresponse.com/v3/contacts/{}".format(contact_id)
        res = requests.delete(url, headers = self.headers) 
        print(res.content)
