"""
This module is a FastAPI application that provides various endpoints for handling sensor data.
It supports data insertion, retrieval of measurement data, and fetching available measurement points.

The module handles authentication via signature verification and processes sensor data stored in a database.

**Dependencies**:

    - FastAPI: Web framework for building APIs.
    - Pydantic: For data validation using models.
    - SQLite: For database interactions through `database_utils`.
    - configparser: For reading configuration settings from a file.
    - json: For JSON serialization.
    - psk_auth: For handling public keys and signature verification.
    - datetime: For working with date and time.
    - base64: For encoding and decoding signatures.

**API Endpoints**:

    - `POST /insert/`: Inserts sensor data into the database after verifying the signature.
    - `POST /get/`: Retrieves sensor data within a specified time range.
    - `POST /get_latest/`: Retrieves the most recent sensor measurements.
    - `POST /get_available_meas_points`: Fetches available measurement points from the database.

**Classes**:

    - `SensorData`: Defines the structure of the sensor data, including measurement details and values.
    - `request_json`: Defines the structure for requests containing time ranges (start and end datetimes).

**Functions**:

    - `validate_json(data: dict)`: Validates sensor data against the `SensorData` model. Raises HTTPException if validation fails.
    - `validate_request_json(data: dict)`: Validates the time range data against the `request_json` model. Raises HTTPException if validation fails.
    - `insert_to_db(measurement)`: Inserts valid measurement data into the database.
    - `request_measurement_data(request_dict)`: Fetches and returns measurement data from the database for a given time range.
    - `request_last_measurements()`: Retrieves the most recent measurements from the database.
    - `request_measurement_points()`: Returns a list of available measurement points in the database.
    - `verify_signature(public_key, data, signature)`: Verifies the authenticity of the signature using the public key.

**Configuration**:

- The configuration is read from the file specified by `config_file`, which includes API settings (e.g., authorized keys, port number) and database settings.

**Example Usage**::

    1. To insert data, send a POST request to `/insert/` with the sensor data and signature.
    2. To retrieve data for a specific time range, send a POST request to `/get/` with the time range data.
    3. To get the most recent measurements, send a POST request to `/get_latest/`.

**Author**:
    - Carl Philipp Koppen (admin@wassermonitor.de)
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_406_NOT_ACCEPTABLE
from pydantic import BaseModel, ValidationError
import time
import database_utils as dbu
import configparser
import json
from datetime import datetime
from psk_auth import load_authorized_keys, verify_signature
import base64
import os
import logging

# Loggerconfig
logger = logging.getLogger('wassermonitor warning bot')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(os.path.abspath("../log/API.log"))
fh.setFormatter(formatter)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)


config_file_pos = [os.path.abspath("../config.cfg"), os.path.abspath("../Server/config.cfg")]
for c in config_file_pos:
    #logger.debug (f"Config File Path: {os.path.abspath(c)})
    if os.path.exists(c):
        config_file = c
        break
logger.info(f"Wassermonitor2 starting at {datetime.now()} ...")
logger.info(f"reading config from {config_file} ...")

# Parse Config File
config = configparser.RawConfigParser()
config.read(config_file)
authorized_keys = load_authorized_keys(os.path.abspath(config['API']['authorized_keys_file']))

msg_json = str()
msg_json_pos = [os.path.abspath('../messages.json'), os.path.abspath("../Server/messages.json")]
for c in msg_json_pos:
    logger.debug (os.path.abspath(c))
    if os.path.exists(c):
        msg_json = c
        break
# Load messages from file
with open(msg_json,'r', encoding='utf-8') as f:
    messages = json.load(f)

PORT = int(config['API']['port'])
logger.info (f"API-Port:{PORT}")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Verifies the provided token against the expected token from the configuration.

    **Parameters**:

        - `token` (str): The token to be verified, obtained from the OAuth2 scheme.

    **Raises**:

        - `HTTPException`: If the token is invalid, an HTTP 401 Unauthorized exception is raised with a delay.

    **Example**::

        from fastapi import Depends, HTTPException
        token = "example_token"
        verify_token(token)
    """

    if token != config['API']['token']:
        time.sleep(5)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={'WWW-Authentication':'Bearer'},
        )

class SensorData(BaseModel):
    """
    SensorData represents the structure of the expected JSON data for sensor readings.

    This class is used to define the structure of the sensor data as it is expected
    to be received or processed. It includes information about the sensor's
    reading time, the sensor's details, and the values it measures.

    **Attributes**:

        - `datetime` (datetime): The date and time of the sensor reading.
        - `meas_point` (str): The name of the measurement point the sensor is associated with.
        - `sensor_name` (str): The name of the sensor.
        - `tank_height` (float): The zero offset of the sensor setup.
        - `max_val` (float): The maximum allowed value for the sensor measurement.
        - `warn` (float): The warning threshold for the sensor.
        - `alarm` (float): The alarm threshold for the sensor.
        - `values` (list[float]): A list of float values measured by the sensor at the specified datetime.

    **Example**::

        sensor_data = SensorData(
            datetime=datetime(2024, 12, 15, 10, 0),
            meas_point='raspi1',
            sensor_name='Sensor1',
            tank_height=155.0,
            max_val=100.0,
            warn=80.0,
            alarm=90.0,
            values=[75.0, 76.0, 77.5]
        )
    """
    datetime: datetime
    meas_point: str
    sensor_name: str
    tank_height: float
    max_val: float
    warn: float
    alarm: float
    values: list[float]

class request_json(BaseModel):
    """
    request_json represents the structure of a JSON request containing a time range.

    This class is used to define the structure of a JSON object that includes
    two datetime attributes, which specify the beginning and end of a time period.

    **Attributes**:

        - `dt_begin` (datetime): The start date and time of the requested period.
        - `dt_end` (datetime): The end date and time of the requested period.

    **Example**::

        request = request_json(
            dt_begin=datetime(2024, 12, 1, 8, 0),
            dt_end=datetime(2024, 12, 1, 18, 0)
        )
    """
    dt_begin: datetime
    dt_end: datetime

def validate_json(data: dict):
    """
    Validates the structure of a given JSON-like dictionary using the SensorData model.

    This function attempts to create an instance of the `SensorData` class using the
    provided `data`. If the data matches the expected structure, the function returns
    `True`. If the data does not match the expected structure (i.e., a validation error
    occurs), the function raises an HTTP exception with a 406 status code and a
    message indicating that the JSON structure is invalid.

    **Args**:

        - `data` (dict): A dictionary representing the JSON data to validate. It should contain keys and values matching the `SensorData` model's attributes (e.g., `datetime`,`meas_point`, `sensor_name`, etc.).

    **Returns**:

        - `bool`: `True` if the data is valid and matches the `SensorData` model.

    **Raises**:

        - `HTTPException`: If the data does not match the expected structure, an HTTPexception with status code 406 (Not Acceptable) is raised.

    **Example usage**::

        data = {
            "datetime": "2024-12-15T10:00:00",
            "meas_point": "raspi1",
            "sensor_name": "TempSensor1",
            "tank_height": 120,
            "max_val": 100.0,
            "warn": 80.0,
            "alarm": 90.0,
            "values": [75.0, 76.0, 77.5]
        }
        result = validate_json(data)
    """
    try:
        sensor_data = SensorData(**data)
        return True
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JSON Structure",
        )

def validate_request_json(data):
    """
    Validates the structure of a given JSON-like dictionary using the request_json model.

    This function attempts to create an instance of the `request_json` class using the
    provided `data`. If the data matches the expected structure, the function returns
    `True`. If the data does not match the expected structure (i.e., a validation error
    occurs), the function raises an HTTP exception with a 406 status code and a
    message indicating that the JSON structure is invalid.

    **Args**:

        - `data` (dict): A dictionary representing the JSON data to validate. It should
          contain keys and values matching the `request_json` model's attributes (e.g., `dt_begin`,
          `dt_end`).

    **Returns**:

        - `bool`: `True` if the data is valid and matches the `request_json` model.

    **Raises**:

        - `HTTPException`: If the data does not match the expected structure, an HTTP
          exception with status code 406 (Not Acceptable) is raised.

    **Example usage**::

        data = {
            "dt_begin": "2024-12-01T08:00:00",
            "dt_end": "2024-12-01T18:00:00"
        }
        result = validate_request_json(data)
    """
    try:
        sensor_data = request_json(**data)
        return True
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JSON Structure",
        )

def insert_to_db(measurement):
    """
    Inserts measurement data into the database.

    This function checks whether the provided `measurement` is a dictionary. If it is,
    it attempts to insert the measurement data into the database using the `insert_value`
    function from the `dbu` module. If the provided `measurement` is not a dictionary,
    it returns a simple message.

    **Args**:

        - `measurement` (any): The data to be inserted into the database. If it is a dictionary,
          it is passed to the `insert_value` function for insertion.

    **Returns**:

        - `dict`:
        - If the `measurement` is not a dictionary, a message `{'message': 'Received'}` is returned.

        - If it is a dictionary, the result of the `insert_value` function is returned, which is typically a database insert operation.

    **Example**::

        measurement = {
            'datetime': '2024-12-15T10:00:00',
            'meas_point': 'Temperature',
            'sensor_name': 'TempSensor1',
            'max_val': 100.0,
            'warn': 80.0,
            'alarm': 90.0,
            'values': [75.0, 76.0, 77.5]
        }

        result = insert_to_db(measurement)
    """
    if isinstance(measurement, dict):
        return dbu.insert_value(config['database'], measurement)
    return {'message':'Received'}


def request_measurement_data(request_dict):
    """
    Requests measurement data from the database and formats it into a JSON response.

    This function retrieves measurement data from a database based on the provided
    `dt_begin` and `dt_end` dates in the `request_dict`. It then processes and formats
    the data into a nested JSON structure, grouping it by measurement point and sensor.
    The resulting data includes timestamps, values, sensor details, and derivations.

    **Args**:

      - `request_dict` (dict): A dictionary containing the request parameters, specifically:
      - 'dt_begin' (str): The start datetime for the requested period.
      - 'dt_end' (str): The end datetime for the requested period.

    **Returns**:

        - `JSONResponse`: A JSON response containing the processed measurement data, structured by measurement point and sensor.

    **Example**::

        request_dict = {
            'dt_begin': '2024-12-01T08:00:00',
            'dt_end': '2024-12-01T18:00:00'
        }

        response = request_measurement_data(request_dict)

    """

    data = dbu.get_meas_data_from_sqlite_db(
        config['database'],
        datetime.fromisoformat(request_dict['dt_begin']),
        datetime.fromisoformat(request_dict['dt_end'])
    )
    data_json = {
    }
    if not data.empty:
        for mp in data['mpName'].unique():
            d_mp = data[data['mpName']==mp]
            max_d = max(d_mp['derivation_10'])
            min_d = min(d_mp['derivation_10'])
            if d_mp.empty:
                continue
            data_json[mp] = []
            for s in d_mp['sensorId'].unique():
                d_s = d_mp[d_mp['sensorId'] == s]
                if d_s.empty or not 'value' in list(d_s.keys()):
                    continue

                data_json[mp].append(
                    {
                        'sensorID': s,
                        'values': [
                            {
                                'timestamp': d_s['dt'].iloc[x],
                                'value': d_s['value'].iloc[x],
                                'tank_height': d_s['tank_height'].iloc[x],
                                'max_val':d_s['max_val'].iloc[x],
                                'warn':d_s['warn'].iloc[x],
                                'alarm':d_s['alarm'].iloc[x],
                            }
                        for x in range(len(d_s))],
                        'deriv': [
                            {
                                'timestamp': d_s['dt'].iloc[x],
                                'value': d_s['derivation'].iloc[x],
                                'value_10': d_s['derivation_10'].iloc[x],
                                'peaks_pos': d_s['peaks_pos'].iloc[x],
                                'peaks_neg': d_s['peaks_neg'].iloc[x],
                            }
                        for x in range(len(d_s))],

                        'y_max':max(d_s['max_val'].to_list())+10,
                        'deriv_y_max': round(max_d,0) + 10,
                        'deriv_y_min': round(min_d,0) - 10,
                    }
                )
        return JSONResponse(content=json.dumps(data_json, indent=4))
    else:
        return JSONResponse(content=json.dumps({}, indent=4))

def request_last_measurements():
    """
    Requests the last measurement data from the database and formats it into a JSON response.

    This function retrieves the most recent measurement data from the database and processes
    it into a structured JSON format. The data is organized by measurement point and includes
    details such as sensor name, timestamp, value, color, warning, alarm, and maximum value.
    The timestamp is formatted according to the specified date-time format in the configuration.

    **Returns**:
    - `JSONResponse`: A JSON response containing the most recent measurement data, structured by measurement point.

    **Example**::

        response = request_last_measurements()
    """
    data = dbu.get_last_meas_data_from_sqlite_db(
        config['database']
    )
    data_json = {}
    #print (data)
    for mp in data:
        data_json[mp] = {
            "sensor_name":[f"{x}\n{datetime.fromisoformat(data[mp][x]['dt']).strftime(messages['dtformat'][config['API']['language']])}" for x in data[mp]],
            "dt":[data[mp][x]["dt"] for x in data[mp]],
            "value": [data[mp][x]["value"] for x in data[mp]],
            "color": [data[mp][x]["color"] for x in data[mp]],
            "warn": [data[mp][x]["warn"] for x in data[mp]],
            "alarm": [data[mp][x]["alarm"] for x in data[mp]],
            "max_val": [data[mp][x]["max_val"] for x in data[mp]],
            "tank_height": [data[mp][x]["tank_height"] for x in data[mp]],
        }

    return JSONResponse(content=json.dumps(data_json, indent=4))

def request_measurement_points():
    data = dbu.get_available_meas_points_from_sqlite_db(
        config['database']
    )
    return JSONResponse(content=json.dumps(data, indent=4))


origins = [
    "http://127.0.0.1:8012",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5173",
    "http://localhost:8012",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:5173",
]

# FOR DOCKER
origins = ["*"]


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/insert/")
async def receive_data(request: Request, token: str = Depends(verify_token)):

    json_obj = await request.json()
    json_dict = json.loads(json_obj)
    data = json_dict["data"]
    signature = base64.b64decode(json_dict["signature"])
    client_id = json_dict["client_id"]

    public_key = authorized_keys.get(client_id)
    if not public_key:
        raise HTTPException(status_code=401, detail="Unauthorized client")

    try:
        verify_signature(public_key, data, signature)
        return insert_to_db(data)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid signature")


@app.post("/get/")
async def post_data(request: Request):
    json_obj = await request.json()
    if validate_request_json(json_obj):
        return request_measurement_data(json_obj)

@app.post("/get_latest/")
async def post_last_data():
    return request_last_measurements()

@app.post("/get_available_meas_points/")
async def post_meas_points():
    return request_measurement_points()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
