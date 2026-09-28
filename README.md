# Wassermonitor2

New Implementation of Wassermonitor

Wassermonitor is a full implementation for collecting data from distributed sensors and monitoring the data. Goal of the project ist to present the catpured data on a dashboard and warn via email, telegram or signal, if defined borders are crossed.

The Project is currently under development, but I'm sure to deploy a full implementation in a few weeks.

## Current Status

### Legend

| Color | Status         |
|-------|----------------|
| 🔴    | not started    |
| 🟡    | in progression |
| 🟢    | completed      |

### Features

| Module          | Feature                                 | Implemented    | Testing | Documentation |
|-----------------|-----------------------------------------|----------------|---------|---------------|
| API             | Get new signed Measurement values       | 🟢             | 🟡      | 🟡            |
|                 | Provide current values                  | 🟢             | 🟡      | 🟡            |
|                 | Provide values over time with deviation | 🟢             | 🟡      | 🟡            |
|                 | Check data signature                    | 🟢             | 🟡      | 🟡            |
|                 | Authentication with Token               | 🟢 (unsecure!) | 🟡      | 🟡            |
| Dashboard       | Show current status plot                | 🟢             | 🔴      | 🔴            |
|                 | Show time plot                          | 🟢             | 🔴      | 🔴            |
|                 | Show deviation plot                     | 🟢             | 🔴      | 🔴            |
|                 | Support light and dark mode             | 🟢             | 🔴      | 🔴            |
| Warning Bot     | Warn via telegram                       | 🟢             | 🔴      | 🟡            |
|                 | Warn via email                          | 🟢             | 🟡      | 🟡            |
|                 | Warn via signal                         | 🟡             | 🔴      | 🟡            |
|                 | Support multi language                  | 🟢  (en, de)   | 🔴      | 🟡            |
| Datacrawler     | Crawl data from I2C sensors             | 🟢             | 🔴      | 🟡            |
| Datatransmitter | Sign data with psk and send to API      | 🟢             | 🔴      | 🟡            |
| Setup method    | Docker                                  | 🟡             | 🔴      | 🔴            | 
|                 | From Source                             | 🟡             | 🔴      | 🔴            | 

### Documentation
| Module               | Documentation feature   | Status |
|----------------------|-------------------------|--------|
| API                  | Doc-Strings for Sphinx  | 🟢     |
|                      | Full Text Documentation | 🔴     |
| warningbot           | Doc Strings for Sphinx  | 🟡     |
|                      | Full Text documentation | 🔴     |
| Pi                   | Doc-Strings for Sphinx  | 🟢     |
|                      | Full Text documentation | 🟡     |
| Setup Guide - src    | full Text documentation | 🟡     |
| Setup Guide - Docker | full Text documentation | 🟡     |


### Distribution

| Feature                                                                                                 | Status |
|---------------------------------------------------------------------------------------------------------|--------|
| If push to main-branch: Github Action: Automatically deploy documentation                               | 🟢     | 
| If push to main-branch: Github Action: Automatically build .tar.gz packets for server and meas points   | 	🔴    |
| If push to main-branch: Github Action: Automatically build docker containers for server and meas_points | 	🔴    |

## Full documentation

Please find the full documentation under https://doc.wassermonitor.de. 


## Setup


### Server

The server runs an API to receive data from the measurement points. It offers a dashboard in which the current measured value of each connected sensor is displayed, sorted by measuring point, as well as the time course of the measured values and their derivation. 
In addition, the server provides a warning bot that can send warnings by e-mail, telegram or pulse signal if warning and alarm limits are exceeded.

#### Prerequisites

Install all Python dependencies:

```bash
pip install -r requirements.txt
```

#### 1. Backend – API (FastAPI / uvicorn)

The API is located in `Server/API/`. It reads its configuration from `Server/config.cfg`.

```bash
cd Server/API
uvicorn main:app --host 0.0.0.0 --port 8012
```

For development with auto-reload:

```bash
cd Server/API
uvicorn main:app --host 0.0.0.0 --port 8012 --reload
```

Alternatively, the app can be started directly:

```bash
cd Server/API
python main.py
```

The API will then be reachable at `http://<host>:8012`. The interactive API documentation (Swagger UI) is available at `http://<host>:8012/docs`.

#### 2. Backend – Warning Bot

The Warning Bot is located in `Server/Warningbot/`. It is typically run as a scheduled task (e.g. via cron) or as a background service.

```bash
cd Server/Warningbot
python warningbot.py
```

Example cron entry to run the bot every 5 minutes:

```
*/5 * * * * cd /path/to/Server/Warningbot && python warningbot.py
```

#### 3. Frontend – Dashboard (SvelteKit)

The dashboard is located in `Server/Dashboard/wassermonitor-dash/`. It is a SvelteKit application.

Install Node.js dependencies (only required once):

```bash
cd Server/Dashboard/wassermonitor-dash
npm install
```

Build the Rust/WASM time-series processor (required after Rust code changes):

```bash
cd Server/Dashboard/wassermonitor-dash
npm run wasm:build
```

**Development mode** (with hot-reload):

```bash
cd Server/Dashboard/wassermonitor-dash
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

**Production build:**

```bash
cd Server/Dashboard/wassermonitor-dash
npm run build
npm run preview
```

The production preview will be available at `http://localhost:4173`.

---

### Raspberry Pi

Each measurement point is consist of the sensors and a raspberry pi which collects the data of the sensors. The data then is temporarily stored until it can be sent to the API of the server. The raspi needs some upgrades to talk with sps sensors via i2c. Please see the full documentation to
read more about the full setup of a measurement point including hard- and software.

#### Pi – Data Crawler & Transmitter

Install Pi-specific dependencies:

```bash
pip install -r Pi/requirements.txt
```

Start the data crawler (reads sensor values via I2C):

```bash
cd Pi
python datacrawler.py
```

Start the data transmitter (signs and sends data to the API):

```bash
cd Pi
python datatransmitter.py
```

## Recommendation

If you want to use the water monitor for a public presentation on the Internet, please ensure that the data is sufficiently anonymised. If, for example, the water monitor is used to monitor a fire-fighting water reservoir, it is probably quite safe to make the data publicly accessible.
When it comes to water supply, it can be very questionable to make the data publicly accessible on the internet. For example, if only one household is supplied, the data can provide real-time information about whether someone is at home or not. It is less questionable if the monitored system supplies many households, as a certain degree of anonymisation is then achieved. 
You should therefore consider very carefully whether the data is sufficiently anonymised before making it publicly accessible. Otherwise, it may be advisable to only make the data visible within a VPN.




