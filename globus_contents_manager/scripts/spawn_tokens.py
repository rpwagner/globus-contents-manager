import os
import json
import pickle
import base64
from fair_research_login import NativeClient

# # Get the content
# GLOBUS_ENV_DATA = os.getenv('GLOBUS_DATA')
# PICKLED_TOKENS = base64.b64decode(GLOBUS_ENV_DATA)

# # Unpickle and get the dictionary
# TOKENS = pickle.loads(PICKLED_TOKENS)

# # Minimal sanity check, did we get the data type we expected?
# isinstance(TOKENS, dict)
# print(json.dumps(TOKENS, indent=4, sort_keys=True))

# async def pre_spawn_start(self, user, spawner):
#     """Add tokens to the spawner whenever the spawner starts a notebook.
#     This will allow users to create a transfer client:
#     globus-sdk-python.readthedocs.io/en/stable/tutorial/#tutorial-step4
#     """
#     spawner.environment['GLOBUS_LOCAL_ENDPOINT'] = \
#         self.globus_local_endpoint
#     state = await user.get_auth_state()
#     if state:
#         globus_data = base64.b64encode(
#             pickle.dumps(state)
#         )
#         spawner.environment['GLOBUS_DATA'] = globus_data.decode('utf-8')

CLIENT_ID = ''
APP_NAME = ''
SCOPES = ''
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
        os.environ['GLOBUS_DATA'] = base64.b64encode(pickle.dumps(tokens))
    except:
        pass
