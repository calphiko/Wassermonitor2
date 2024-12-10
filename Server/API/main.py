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
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_406_NOT_ACCEPTABLE
from pydantic import BaseModel, ValidationError
import database_utils as dbu
import configparser
import json
import time
from datetime import datetime

config_file = "../config.cfg"

# Parse Config File
config = configparser.ConfigParser()
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
    pi_name: str
    sensor_id: int
    values: list[float]

class request_json(BaseModel):
    """
        request_json represents the structure of the expected JSON to request data from the database.

        Attributes:
            dt_begin (datetime): The earliest data to request.
            dt_end (datetime): The latest data to request
        """
    dt_begin: datetime
    dt_end: datetime

def validate_json(data: dict):
    """
    Validates the JSON data against the SensorData model.

    Args:
        data (dict): The JSON data to be validated.

    Raises:
        ValidationError: If the data does not conform to the SensorData model.

    Returns:
        None
    """
    try:
        sensor_data = SensorData(**data)
        return True
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JSON Structure",
        )

def validate_request_json(data: dict):
    """
    Validates the JSON data against the request_json model.

    Args:
        data (dict): The JSON data to be validated.

    Raises:
        ValidationError: If the data does not conform to the SensorData model.

    Returns:
        True if request_json structure is valid
    """
    try:
        sensor_data = request_json(**data)
        return True
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JSON Structure",
        )
def verify_token(token: str = Depends(oauth2_scheme)):
    """
     Verifies the provided token against the expected token from the configuration.

     Parameters:
     token (str): The token to be verified, obtained from the OAuth2 scheme.

     Raises:
     HTTPException: If the token is invalid, an HTTP 401 Unauthorized exception is raised with a delay.

     Example:
     >>> from fastapi import Depends, HTTPException
     >>> token = "example_token"
     >>> verifiy_token(token)
     """
    if token != config['API']['token']:
        time.sleep(5)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={'WWW-Authentication':'Bearer'},
        )

def insert_to_db(measurement):
    """
    Inserts a measurement into the database if it is a dictionary, otherwise returns a default message.

    Parameters:
    measurement (dict): The measurement data to be inserted into the database.

    Returns:
    dict: The result of the dbu.insert_value function if the measurement is a dictionary.
    dict: A default message if the measurement is not a dictionary.

    Example:
    >>> measurement = {
    ...     'datetime': '2024-12-05T07:11:32+00:00',
    ...     'pi_name': 'pi_1',
    ...     'sensor_id': 1,
    ...     'values': [23.5, 24.0, 22.8]
    ... }
    >>> insert_to_db(measurement)
    {'message': 'Measurement inserted successfully'}
    """
    if isinstance(measurement, dict):
        return dbu.insert_value(config['database'], measurement)
    return {'message':'Received'}


def request_measurement_data(request_dict):
    data = dbu.get_meas_data_from_sqlite_db(
        config['database'],
        datetime.fromisoformat(request_dict['dt_begin']),
        datetime.fromisoformat(request_dict['dt_end'])
    )
    #print(data)
    return data.to_json(orient='records', date_format='iso')

def request_last_measurements():
    data = dbu.get_last_meas_data_from_sqlite_db(
        config['database']
    )
    #print(data)
    return data.to_json(orient='records', date_format='iso')


origins = [
    "http://127.0.0.1:8012",
    "http://127.0.0.1:63342",
    "http://localhost:8012",
    "http://localhost:63342",
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
    """
    Receives JSON data from a POST request, verifies the token, and inserts the data into the database.

    Parameters:
    request (Request): The request object containing the JSON data.
    token (str): The token for authentication, verified by the verifiy_token function.

    Returns:
    dict: The result of the insert_to_db function.

    """

    json_obj = await request.json()
    json_dict = json.loads(json_obj)
    if validate_json(json_dict):
        x = insert_to_db(json_dict)
    #print (x)
        return x
    #return False

@app.post("/get/")
async def receive_data(request:Request, token: str = Depends(verify_token)):
    json_obj = await request.json()
    json_dict = json.loads(json_obj)
    if validate_request_json(json_dict):
        return request_measurement_data(json_dict)

@app.post("/get_latest/")
async def receive_last_data(token: str = Depends(verify_token)):
    return request_last_measurements()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)