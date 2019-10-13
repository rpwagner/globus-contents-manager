#!/usr/bin/env python
import os
import json
from fair_research_login import NativeClient

CLIENT_ID = '7414f0b4-7d05-4bb6-bb00-076fa3f17cf5'
APP_NAME = 'My App'
SCOPES = 'openid email profile urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:search.api.globus.org:all'
CONFIG_FILE = 'tokens-data.json'


tokens = None
# try to load tokens from local file (native app config)
client = NativeClient(client_id=CLIENT_ID, app_name=APP_NAME)
tokens = client.login(requested_scopes=SCOPES,
                          refresh_tokens=True)
