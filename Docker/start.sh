#!/bin/sh

# Start FastAPI im Hintergrund
uvicorn API.main:app --host 0.0.0.0 --port 8000 &

# Start nginx im Vordergrund
nginx -g "daemon off;"