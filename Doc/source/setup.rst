Setup
=====

To set up a comprehensive water monitoring system, you need to configure a server entity and at least one measurement point to send data to the server.

In this chapter, we will guide you through setting up the server and dashboard using two methods:

    1. Using Docker

    2. Installing from Source

We strongly recommend using the Docker method for its simplicity and reliability.

Setup of the server
-------------------

Docker
~~~~~~

1. Clone directory and create authorized_keys-file and data directory.

.. code-block:: console
    git clone -b docker https://github.com/calphiko/Wassermonitor2.git
    mkdir .wassermonitor
    touch "<public key of measurement point in rsa format>" >> .wassermonitor/authozired_keys
    mkdir data

2. Build container

.. code-block:: console
    cd Wassermonitor2
    docker build --rm -t wassermonitor2 .

3. Start container

.. code-block:: console
    docker run --rm -it -d -v /path/to/data/:/Data/ -v /path/to/.wassermonitor/:/etc/wassermonitor/ -p 8012:8012 -p 7070:5173 --name wm2 wassermonitor2

From source
~~~~~~~~~~~

Configure Warningbot
~~~~~~~~~~~~~~~~~~~~

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

3. Add your bot to the group.

4. Copy ``creds.json.template`` file to a json and add your telegram configuration

    .. code-block:: console
        cd Server/Warningbot/telegram
        cp creds.json.tmpl creds.json


5. Enter API token, group_name and username to ``/Server/Warningbot/telegram/creds.json``


6. Start the ``find_group_id.py``-script in the telegram-directory. It will automatically add the group id to your telegram-creds.json and enables messaging via telegram.

Email
"""""
1. Copy ``creds.json.template`` file to a json and add your mail server configuration

    .. code-block:: console

        cd Server/Warningbot/email
        cp creds.json.tmpl creds.json

2. Enable mail notification in the server config file ``Server/config.cfg`` in the warning-section-

Signal
""""""

Setup of a measurement point
----------------------------


.. toctree::
   :maxdepth: 3
   :caption: Contents: