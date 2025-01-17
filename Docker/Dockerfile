# Build container for Svelte dashboard
FROM node:18-alpine AS dahsboard-builder

WORKDIR /Dashboard
COPY ../Server/Dashboard/wassermonitor-dash/package.json ./
RUN npm install
COPY ../Server/Dashboard/wassermonitor-dash/ ./
RUN npm run build

# Main Container: Python with API and dashboard
FROM python:3.10-slim

# INSTALL PYTHON REQUIREMENTS
WORKDIR /app
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY API
COPY ../Server/API ./API

# COPY DASHBOARD
COPY --from=dashboard-builder /dashboard/build ./Dashboard

# Install nginx
RUN apt-get update && apt-get install -y nginx && apt-get clean
COPY nginx.conf /etc/nginx/nginx.conf

# PORTS
EXPOSE 8000 80

# Startscript
COPY start.sh .
RUN chmod +x start.sh