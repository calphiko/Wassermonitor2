Setup
=====

Setup of the server
-------------------

Docker
~~~~~~

From source
~~~~~~~~~~~

Warningbot
~~~~~~~~~~

Telegram
""""""""

1. Contact Botfather
    a) Open the telegram app on your smartphone and search for user ``botfather``:
        New Chat --> Search for Botfather

    b) type ``/start`` to start a new conversation and ``/newbot`` to create a new bot

    c) Name the new bot

    d) Give the bot a new username

    Now you can go to the website ``http://t.me/<your_bot_username>`` and add a description for the bot.
    Your will get a token to access the telegram HTTP API.

2. Create a group for your users to be warned

3. Add your bot to the group``

3. Enter API token, group_name and username to ``/Server/Warningbot/telegram/creds.json``

4. start the ``find_group_id.py``-script in the telegram-directory
    It will automatically add the group id to your telegram-creds.json and enables messaging


Setup of a measurement point
----------------------------


.. toctree::
   :maxdepth: 3
   :caption: Contents: