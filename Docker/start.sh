#!/bin/sh

# Start FastAPI in background
cd API
#uvicorn main:app --host 0.0.0.0 --port 8000 &
python3 main.py &
cd ..

# Start Warningbot
cd Warningbot
python3 warningbot.py
cd ..

# Start nginx
nginx -g "daemon off;"
