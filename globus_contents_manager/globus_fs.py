"""
Utilities for handling file operations through the Globus SDK.
"""

from globus_sdk import TransferClient
from fair_research_login import NativeClient
from globus_contents_manager.default_fs import DefaultFS
from ipycompat import Unicode


class GlobusFS(DefaultFS):

    CLIENT_ID = Unicode(
        help="Globus project Client ID").tag(
            config=True, env="GLOBUS_CLIENT_ID")

    SCOPES = Unicode(
        help="The scopes you want to request (optional)", allow_none=True, 
        default_value=["openid", "email", "urn:globus:auth:scope:transfer.api.globus.org:all"]).tag(
            config=True, env="GLOBUS_SCOPES")

    REFRESH_TOKENS = Unicode(
        help="Affects whether or not refresh tokens are used (default is False)", allow_none=True,
        default_value=False).tag(
            config=True, env="GLOBUS_REFRESH_TOKENS")

    tokens = None
    client = None
    
    def __init__(self, log, **kwargs):
        super(GlobusFS, self).__init__(**kwargs)
        self.log = log

        try:
            self.client = NativeClient(client_id=self.CLIENT_ID)

            # check for existing tokens
            try:
                self.tokens = self.client.load_tokens(requested_scopes=self.SCOPES)
            except:
                # if it fails, then get new tokens
                self.tokens = self.client.login(
                    requested_scopes=self.SCOPES,
                    refresh_tokens=self.REFRESH_TOKENS
                )

        except:
            print("Error occurred when trying to log in to Globus")

    def get_transfer_client(self):
        """
        Returns a TransferClient client instance using NativeClient
        """
        auth = self.client.get_authorizers()['transfer.api.globus.org']
        return TransferClient(authorizer=auth)

    # DefaultFS method implementations ------------------------------------------------------------

    def ls(self, path="", endpoint_id='ddb59aef-6d04-11e5-ba46-22000b92c6ec'):
        transfer_client = self.get_transfer_client()

        return transfer_client.operation_ls(endpoint_id, path=path)

    def isfile(self, path, endpoint_id='ddb59aef-6d04-11e5-ba46-22000b92c6ec'):
        return
        
