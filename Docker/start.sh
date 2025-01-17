#!/bin/sh

# Start FastAPI im Hintergrund
cd API
#uvicorn main:app --host 0.0.0.0 --port 8000 &
python3 main.py &

# Start nginx im Vordergrun
cd ..
nginx -g "daemon off;"
