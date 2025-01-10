import requests
import os
import json

from fastapi.exception_handlers import request_validation_exception_handler

creds_path = os.path.abspath('./creds.json')

# Load messages from file
if not os.path.exists(creds_path):
    print ("No creds.json found. Please copy the creds.json.tmpl file to creds.json and add your telegram bot credentials.")
with open(creds_path,'r', encoding='utf-8') as f:
    tgram_creds = json.load(f)

bot_token = tgram_creds['api_token']
url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
response = requests.get(url)

updates = response.json()

for u in updates['result']:
    if 'my_chat_member' in u:
        #print (u['my_chat_member'])
        if u['my_chat_member']['chat']['title'] == tgram_creds['group_name']:

            group_id = u['my_chat_member']['chat']['id']

print (f"adding {group_id} as group_id to your telegram credentials....")
tgram_creds['group_id'] = group_id

with open (creds_path, 'w', encoding='utf-8') as f:
    json.dump(tgram_creds, fp=f)

print ("added")
