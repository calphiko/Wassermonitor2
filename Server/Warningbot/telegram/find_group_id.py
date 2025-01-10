"""
This script interacts with the Telegram Bot API to retrieve updates and
obtain the `group_id` for a specified group. The `group_id` is then added
to the Telegram credentials file (`creds.json`) for further use in other
Telegram bot-related operations.

The script performs the following tasks:
1. Loads the Telegram bot credentials (`creds.json`) from the file system.
2. Sends a request to the Telegram Bot API to retrieve updates, specifically
   looking for group information related to the bot.
3. Finds the group ID corresponding to the group specified in the credentials.
4. Updates the credentials file with the retrieved group ID.

**Prerequisites:**
- A `creds.json` file, which contains the bot's API token and the name of the group.
- The bot must be a member of the group to retrieve the `group_id`.

**Example**:
    1. Copy the template file `creds.json.tmpl` to `creds.json`.
    2. Add your bot's API token and the group name in `creds.json`.
    3. Run the script to automatically retrieve and store the group ID.

**Error Handling**:
- If the `creds.json` file is missing, a message is printed instructing the user
  to copy the template file and provide the necessary credentials.

**Dependencies**:
- `requests`: For making HTTP requests to the Telegram Bot API.
- `json`: For reading and writing JSON data.
- `os`: For handling file paths.

"""

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
