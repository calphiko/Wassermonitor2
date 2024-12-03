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

config_file = "../config.cfg"

# Parse Config File
config = configparser.ConfigParser()
config.read(config_file)

PORT = int(config['API']['port'])
print (PORT)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def verifiy_token(token: str = Depends(oauth2_scheme)):
    if token != config['API']['token']:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={'WWW-Authentication':'Bearer'},
        )

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

@app.post("/insert/")
async def receive_data(request: Request, token: str = Depends(verifiy_token)):
    json_obj = await request.json()
    x = insert_to_db(json.loads(json_obj))
    #print (x)
    return x
    #return False

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)