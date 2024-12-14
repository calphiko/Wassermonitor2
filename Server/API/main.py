"""
Module Name: Wassermonitor2 API

Description:
    This module provides an API for interacting with the Wassermonitor Filesystem. It includes functions for inserting values into the database and retrieving stored values.
    The module is designed to create a new sqlite file for each month of the year. It supports error handling to ensure robust operations.

    Typical use cases:
    - /insert/: Store calibrated sensor readings (in the unit of cm) in the database. A measurement usually consists of 5 single values.
    - /read/: Read values from the database and return them in JSON format.

Dependencies:
    - fastapi
    - pydantic
    - configparser
    - json
    - time
    - datetime.datetime
    - database_utils from the project

Configuration:
    - Some parameters can be configured in the config_file ../config.cfg.

Author:
    - Carl Philipp Koppen (admin@wassermonitor.de)

Example:
    -
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_406_NOT_ACCEPTABLE
from pydantic import BaseModel, ValidationError
import database_utils as dbu
import configparser
import json
import time
from datetime import datetime
import pandas as pd

config_file = "../config.cfg"

# Parse Config File
config = configparser.RawConfigParser()
config.read(config_file)

PORT = int(config['API']['port'])
print (PORT)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

class SensorData(BaseModel):
    """
    SensorData represents the structure of the expected JSON data.

    Attributes:
        datetime (datetime): The date and time of the sensor reading.
        pi_name (str): The name of the Raspberry Pi or sensor.
        sensor_id (int): The unique ID of the sensor.
        values (List[int]): A list of integer values measured by the sensor.
    """
    datetime: datetime
    meas_point: str
    sensor_name: str
    max_val: float
    warn: float
    alarm: float
    values: list[float]

class request_json(BaseModel):

    dt_begin: datetime
    dt_end: datetime

def validate_json(data: dict):

    try:
        sensor_data = SensorData(**data)
        return True
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JSON Structure",
        )

def validate_request_json(data: dict):

    try:
        sensor_data = request_json(**data)
        return True
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JSON Structure",
        )
def verify_token(token: str = Depends(oauth2_scheme)):

    if token != config['API']['token']:
        time.sleep(5)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={'WWW-Authentication':'Bearer'},
        )

def insert_to_db(measurement):

    if isinstance(measurement, dict):
        return dbu.insert_value(config['database'], measurement)
    return {'message':'Received'}


def request_measurement_data(request_dict):
    data = dbu.get_meas_data_from_sqlite_db(
        config['database'],
        datetime.fromisoformat(request_dict['dt_begin']),
        datetime.fromisoformat(request_dict['dt_end'])
    )
    data_json = {
    }
    for mp in data['mpName'].unique():
        d_mp = data[data['mpName']==mp]
        data_json[mp] = list()
        for s in d_mp['sensorId'].unique():
            d_s = d_mp[d_mp['sensorId'] == s]
            data_json[mp].append(
                {
                    'sensorID':s,
                    'dt': d_s['dt'].tolist(),
                    'values': d_s['value'].to_list(),
                    'max_val':d_s['max_val'].to_list(),
                    'warn': d_s['warn'].to_list(),
                    'alarm': d_s['alarm'].to_list(),
                }
            )

    return JSONResponse(content=data_json)

def request_last_measurements():
    data = dbu.get_last_meas_data_from_sqlite_db(
        config['database']
    )
    data_json = {}

    for mp in data:
        data_json[mp] = {
            "mp_name":[f"{x}\n{datetime.fromisoformat(data[mp][x]['dt']).strftime(config['API']['dtformat'])}" for x in data[mp]],
            "dt":[data[mp][x]["dt"] for x in data[mp]],
            "value": [data[mp][x]["value"] for x in data[mp]],
            "color": [data[mp][x]["color"] for x in data[mp]],
            "warn": [data[mp][x]["warn"] for x in data[mp]],
            "alarm": [data[mp][x]["alarm"] for x in data[mp]],
            "max_val": [data[mp][x]["max_val"] for x in data[mp]],
        }

    return JSONResponse(content=json.dumps(data_json, indent=4))


origins = [
    "http://127.0.0.1:8012",
    "http://127.0.0.1:5173",
    "http://localhost:8012",
    "http://localhost:5173",
]
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
    if validate_json(json_dict):
        x = insert_to_db(json_dict)
    #print (x)
        return x
    #return False

@app.post("/get/")
async def post_data(request:Request):
    json_obj = await request.json()
    json_dict = json.loads(json_obj)
    if validate_request_json(json_dict):
        return request_measurement_data(json_dict)

@app.post("/get_latest/")
async def post_last_data():
    return request_last_measurements()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)