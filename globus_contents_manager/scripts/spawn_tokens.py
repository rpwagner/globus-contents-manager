import os
import json
from fair_research_login import NativeClient

CLIENT_ID = 'e54de045-d346-42ef-9fbc-5d466f4a00c6'
APP_NAME = 'My App'
SCOPES = 'openid email profile urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:search.api.globus.org:all'
CONFIG_FILE = 'tokens-data.json'


tokens = None
# try to load tokens from local file (native app config)
client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
try:
    tokens = client.load_tokens(requested_scopes=SCOPES)
except:
    pass

if not tokens:
    # if no tokens, need to start Native App authentication process to get tokens
    tokens = client.login(requested_scopes=SCOPES,
                          refresh_tokens=False)

    try:
        # save the tokens
        client.save_tokens(tokens)
        
        # create environment variable
        os.environ['GLOBUS_DATA'] = json.dumps(tokens, indent=4, sort_keys=True)
    except:
        pass
