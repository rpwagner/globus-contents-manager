"""
Various useful utilities.
"""

from datetime import datetime

NBFORMAT_VERSION = 4
DUMMY_CREATED_DATE = datetime.fromtimestamp(0)

def base_model(path):
    """
    Represents a basic file model.
    """
    return {
        "name": path.rsplit('/', 1)[-1],
        "path": path,
        "writable": True,
        "last_modified": None,
        "created": None, 
        "content": None,
        "format": None,
        "mimetype": None,
    }

def base_directory_model(path):
    """
    Represents a basic directory model.
    """
    model = base_model(path)
    model.update(
        type="directory",
        last_modified=DUMMY_CREATED_DATE,
        created=DUMMY_CREATED_DATE,)
    
    return model

def convert_to_datetime(globus_time):
    """
    Converts a time given in Globus format to datetime.

    Globus format for time is as follows:
        YYYY-MM-DD HH:MM:SS+00:00
    """
    # use space separator to seperate date and time
    times = globus_time.split(" ")
    date_part = times[0]
    time_part = times[1]

    # extract the different parts of the date
    year = date_part[0:4]
    month = date_part[5:7]
    day = date_part[8:]
    hour = time_part[0:2]
    minute = time_part[3:5]
    second = time_part[6:8]

    # no need to specify timezone since it is always UTC
    return datetime(year, month, day, hour, minute, second)

import os
import json
from fair_research_login import NativeClient

CLIENT_ID = '7414f0b4-7d05-4bb6-bb00-076fa3f17cf5'
APP_NAME = 'My App'
SCOPES = 'openid email profile urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:search.api.globus.org:all'
CONFIG_FILE = 'tokens-data.json'


def spawn_tokens(client_id=CLIENT_ID, req_scopes=SCOPES, name=APP_NAME):
    """
    Checks if Globus tokens already exists and spawns them if they don't.
    Returns instance of 'NativeClient'.
    """

    tokens = os.getenv('GLOBUS_DATA')
    # try to load tokens from local file (native app config)
    client = NativeClient(client_id=client_id, app_name=name)
    # try:
    #     tokens = client.load_tokens(requested_scopes=req_scopes)
    # except:
    #     pass

    if not tokens:
        # if no tokens, need to start Native App authentication process to get tokens
        tokens = client.login(requested_scopes=req_scopes, refresh_tokens=True)

        try:
            # save the tokens
            client.save_tokens(tokens)
            
            # create environment variable
            os.environ['GLOBUS_DATA'] = json.dumps(tokens, indent=4, sort_keys=True)
        except:
            pass

    # return client

def get_tokens():
    """
    Retrieves the Globus tokens.
    """

    tokens = os.getenv('GLOBUS_DATA')
    print("TOKENS BELOW")
    print(tokens)
    return json.loads(tokens)
