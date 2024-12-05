# API DEAMON FOR WASSERSTAND
#

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED
from datetime import datetime
import database_utils as dbu
import configparser
import json
import time

config_file = "../config.cfg"

# Parse Config File
config = configparser.ConfigParser()
config.read(config_file)

PORT = int(config['API']['port'])
print (PORT)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def verifiy_token(token: str = Depends(oauth2_scheme)):
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


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/insert/")
async def receive_data(request: Request, token: str = Depends(verifiy_token)):
    """
    Receives JSON data from a POST request, verifies the token, and inserts the data into the database.

    Parameters:
    request (Request): The request object containing the JSON data.
    token (str): The token for authentication, verified by the verifiy_token function.

    Returns:
    dict: The result of the insert_to_db function.

    """

    json_obj = await request.json()
    x = insert_to_db(json.loads(json_obj))
    #print (x)
    return x
    #return False

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)