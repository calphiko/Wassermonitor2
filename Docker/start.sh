#!/bin/sh

# Start FastAPI in background
cd API
#uvicorn main:app --host 0.0.0.0 --port 8000 &
python3 main.py &

# Start nginx
cd ..
nginx -g "daemon off;"
