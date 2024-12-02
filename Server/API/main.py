# API DEAMON FOR WASSERSTAND
#

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import database_utils as dbu
import configparser
import json

config_file = "../config.cfg"

# Parse Config File
config = configparser.ConfigParser()
config.read(config_file)


def insert_to_db(measurement):
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

@app.get("/items/{item_id}")
async def root( item_id : int):
    if item_id == 0:
        return hello_world()
    else:
        return insert_to_db(meas_dict)

@app.post("/insert/")
async def root(request: Request):
    json_obj = await request.json()
    x = insert_to_db(json.loads(json_obj))
    print (x)
    return x