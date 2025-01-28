# Build container for Svelte dashboard
FROM node:18-alpine AS dashboard-builder

WORKDIR /Dashboard
COPY Server/Dashboard/wassermonitor-dash/package.json ./
#COPY Server/Dashboard/wassermonitor-dash/package-lock.json ./
RUN npm install
COPY Server/Dashboard/wassermonitor-dash ./
RUN npm run build

# Main Container: Python with API and dashboard
FROM python:3.10-slim

# Add User
RUN useradd -m -s /bin/bash appuser

#RUN apt update && apt -y install python3-pip && apt clean

# INSTALL PYTHON REQUIREMENTS
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# COPY API
COPY Server/API ./API

# Warningbot
COPY Server/Warningbot ./Warningbot

# COPY DASHBOARD
COPY --from=dashboard-builder /Dashboard/build ./Dashboard

# Install nginx
RUN apt-get update && apt-get install -y nginx && apt-get clean
COPY Docker/nginx.conf /etc/nginx/nginx.conf

# PORTS
EXPOSE 8012 80

# Configfile
COPY Server/config.cfg .
COPY Server/messages.json .

RUN chown -R appuser:appuser /app /var/log/nginx /var/lib/nginx /etc/nginx
RUN mkdir -p /app/run && chown appuser:appuser /app/run

# Startscript
COPY Docker/start.sh .
RUN chmod +x start.sh && chown appuser:appuser start.sh

USER appuser

CMD ["./start.sh"]