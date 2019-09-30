"""
Utilities for handling file operations through the Globus SDK.
"""

import os
import base64
from pathlib import Path
from tornado.web import HTTPError
from globus_sdk import (
    AccessTokenAuthorizer,
    NativeAppAuthClient,
    TransferClient, 
    TransferData,
    DeleteData,
    GlobusAPIError, 
    exc
)
# from fair_research_login import NativeClient
from globuscontents.default_fs import DefaultFS
from globuscontents.utils import (
    DUMMY_CREATED_DATE,
    spawn_tokens,
    get_tokens
)
from globuscontents.ipycompat import Unicode


class GlobusFS(DefaultFS):
    """
    File System implementation using Globus SDK functionality.
    """
    CLIENT_ID = Unicode(
        help="Globus project Client ID", allow_none=True,
        default_value="7414f0b4-7d05-4bb6-bb00-076fa3f17cf5").tag(
            config=True, env="GLOBUS_CLIENT_ID")

    SCOPES = Unicode(
        help="The scopes you want to request (optional)", allow_none=True, 
        default_value="openid email urn:globus:auth:scope:transfer.api.globus.org:all").tag(
            config=True, env="GLOBUS_SCOPES")

    DEFAULT_ENDPOINT = str(Unicode(
        help="The default Endpoint ID that the system will use (optional)", allow_none=True,
        default_value='ddb59aef-6d04-11e5-ba46-22000b92c6ec').tag(
            config=True, env="GLOBUS_DEFAULT_ENDPOINT"))

    scopes = None
    transfer_client = None
    
    def __init__(self, *args, **kwargs):
        super(GlobusFS, self).__init__(*args, **kwargs)
        # self.log = log

        try:
            # start login/auth process
            spawn_tokens()
            tokens = json.loads(get_tokens())

            # extract the transfer access token
            print(type(tokens))
            transfer_access_token = tokens['transfer.api.globus.org']['access_token']
            # then use that token to create an AccessTokenAuthorizer
            transfer_auth = AccessTokenAuthorizer(transfer_access_token)
            # finally, use the authorizer to create a TransferClient object
            self.transfer_client = TransferClient(authorizer=transfer_auth)

            # first check for existing tokens using the GLOBUS_DATA environment variable
            # tokens = os.getenv('GLOBUS_DATA')

            # if tokens is None:
            #     self.auth_client = NativeAppAuthClient(self.CLIENT_ID)

            #     # convert the scopes from Unicode (to string) to list
            #     self.scopes = str(self.SCOPES).split()
            #     # explicitly start the flow (specify scopes and refresh tokens)
            #     self.auth_client.oauth2_start_flow(requested_scopes=self.scopes, refresh_tokens=True)
            #     # print URL
            #     print("Login Here:\n\n{0}".format(self.auth_client.oauth2_get_authorize_url()))

            #     # prompt user for code
            #     auth_code = input("Please enter the code that you got from the link above: \n")

            #     # exchange code for response object that contains the tokens
            #     tokens = self.auth_client.oauth2_exchange_code_for_tokens(auth_code)
            #     print("GOT TOKENS")
            #     print(token_response)

            #     # save the tokens in the GLOBUS_DATA environment variable
            #     tokens = json.dumps(token_response, indent=4, sort_keys=True)
            #     print("TOKENS")
            #     print(tokens)
            #     os.environ['GLOBUS_DATA'] = tokens

            # else:
            #     print("TOKENS")
            #     print(tokens)

            


            # self.client = NativeClient(client_id=self.CLIENT_ID)

            # # convert the scopes from Unicode (to string) to list
            # self.scopes = str(self.SCOPES).split()

            # # check for existing tokens
            # try:
            #     # TODO: tokens not loading
            #     tokens = self.client.load_tokens(requested_scopes=scopes)
            #     print("TOKENS LOADED")
            # except:
            #     pass

            # # if no tokens, need to start NativeApp authentication process
            # if not tokens:
            #     tokens = self.client.login(requested_scopes=scopes, refresh_tokens=True)
            #     print("LOGIN SUCCESSFUL")

            #     try:
            #         # save the tokens
            #         self.client.save_tokens(tokens)
            #         print("SAVED TOKENS")

            #         # # create environment variable
            #         # os.environ['GLOBUS_DATA'] = json.dumps(tokens, indent=4, sort_keys=True)
            #     except:
            #         pass

        except:
            print("Error occurred when trying to log in to Globus")

    def get_transfer_client(self):
        """
        Gets the Transfer Client using the NativeClient instance.
        """
        # if self.transfer_client is not None:
        #     return self.transfer_client
        
        # globus_env_data = os.getenv('GLOBUS_DATA')
        # tokens = json.loads(globus_env_data)

        # transfer_authorizer = self.client.get_authorizers()['transfer.api.globus.org']
        # self.transfer_client = TransferClient(authorizer=transfer_authorizer)

        return self.transfer_client

    def globus_transfer(self, source_ep=DEFAULT_ENDPOINT, dest_ep=DEFAULT_ENDPOINT,
                        source_path="/~/", dest_path="/~/", 
                        label="Default transfer label"):
        """
        Creates and submits a Globus Transfer task.
        See `Globus Transfer API <https://docs.globus.org/api/transfer/>` for details.
        
        ** Default Parameters **
            - source and destination endpoints: Globus Tutorial Endpoint 1
            - source and destination paths: /~/
            - label: Default transfer label
        """
        # check if the TransferClient exists
        if self.transfer_client is None:
            # if it doesn't then get one
            self.get_transfer_client()

        # get the TransferData
        tdata = TransferData(self.transfer_client, source_ep, dest_ep, label=label)

        # transfer source path contents or file to destination path (and endpoint)
        tdata.add_item(source_path, dest_path, recursive=True)

        # make sure that the endpoint(s) are activated
        self.transfer_client.endpoint_autoactivate(source_ep)
        if source_ep != dest_ep:
            self.transfer_client.endpoint_autoactivate(dest_ep)

        # submit the transfer task and return the task id
        submit_result = self.transfer_client.submit_transfer(tdata)
        return submit_result["task_id"]

    def globus_delete(self, path, endpoint_id=DEFAULT_ENDPOINT, 
                      label="Default delete label"):
        """
        Creates and submits a Globus Delete task.
        See `Globus Transfer API <https://docs.globus.org/api/transfer/>` for details.
        """
        # check if the TransferClient exists
        if self.transfer_client is None:
            # if it doesn't then get one
            self.get_transfer_client()

        # get the DeleteData
        ddata = DeleteData(self.transfer_client, endpoint_id, label=label, recursive=True)

        # delete the path contents (recursively)
        ddata.add_item(path)

        # make sure that the endpoint is activated
        self.transfer_client.endpoint_autoactivate(endpoint_id)

        # submit the delete task and return the task id
        submit_result = self.transfer_client.submit_delete(ddata)
        return submit_result["task_id"]

    # DefaultFS method implementations ------------------------------------------------------------

    def ls(self, path="/~/", endpoint_id=DEFAULT_ENDPOINT):
        if self.transfer_client is None:
            self.get_transfer_client()

        try:
            resp = self.transfer_client.operation_ls(endpoint_id, path=path)
            return resp
        except GlobusAPIError as globus_err:
            print('The specified path is not a directory')
            print(globus_err)
            return globus_err

    def isfile(self, path, endpoint_id=DEFAULT_ENDPOINT):
        # Checks if a file exists at the given path
        resp = self.ls(path, endpoint_id)

        # check if an exception was returned
        if isinstance(resp, exc.TransferAPIError):
            # if the exception is about the item not being a directory then file exists
            return "NotDirectory" in resp.code

        # if an exception was not returned then path does not point to a file
        return False

    def isdir(self, path, endpoint_id=DEFAULT_ENDPOINT):
        # Checks if the given path points to a directory
        resp = self.ls(path, endpoint_id)

        # if value returned is not an exception or None then no directory exists at the given path
        if isinstance(resp, exc.TransferAPIError) or resp is None:
            return False
        
        # if no exception was returned then the given path does point to a directory
        return True

    def mv(self, old_path, new_path, endpoint_id=DEFAULT_ENDPOINT, stop_after=60*60*24):
        """
        Moves a file/directory within a single Globus Endpoint.
        Will keep running until the delete has been completed or 48 hours have passed. 
        
        **Note**
        The optional, stop_after, parameter specifies the amount of time (in seconds) to
        wait before the system should stop. This is used for both the Transfer and Delete
        tasks, which is why the total (default) time that the system will wait is 48 hours
        (24 hours per task).
        """

        try:
            # copy the file/directory
            cp_succeeded = self.cp(old_path, new_path, 
                                   endpoint_id=endpoint_id, stop_after=stop_after)

            # if the file/directory was successfully copied, delete the "old" one
            if cp_succeeded:
                # delete the file/directory and get the task id
                mv_label = "Deleting file/directory after successful transfer task."
                task_id = self.globus_delete(old_path, endpoint_id=endpoint_id,
                                             label=mv_label)

                # wait for the task to complete, polling every 15 seconds.
                completed = self.transfer_client.task_wait(task_id, timeout=stop_after,
                                                           polling_interval=15)
                if completed:
                    print("Delete task finished!")
                    return True
                
                print("Delete task still running after timeout reached.")

            else:
                print("Was not able to copy the file/directory contents.")

        except exc.TransferAPIError:
            print("TransferAPIError occurred when attempting to move file/directory.")
            
        return False

    def cp(self, old_path, new_path, endpoint_id=DEFAULT_ENDPOINT, stop_after=60*60*12):
        """
        Copies a file or directory located at a given path to a new location.
        Does not work between endpoints (see globus_transfer).
        Will keep running until the transfer has been completed or 12 hours (specified
        in seconds by the optional, stop_after, parameter).
        """

        try:
            # transfer the file/directory and get the task id
            task_id = self.globus_transfer(source_ep=endpoint_id, dest_ep=endpoint_id,
                                           source_path=old_path, dest_path=new_path,
                                           label="Copying file/directory")

            # wait for the task to complete, polling every 15 seconds.
            completed = self.transfer_client.task_wait(task_id, timeout=stop_after,
                                                       polling_interval=15)
            if completed:
                print("Transfer task finished!")
                return True
            
            print("Transfer task still running after timeout reached.")

        except exc.TransferAPIError:
            print("TransferAPIError occurred when attempting to copy file/directory.")
            
        return False

    def rm(self, path, endpoint_id=DEFAULT_ENDPOINT, stop_after=60*60*24):
        """
        Deletes a file or directory (recursively) located at a given path.
        """
        try:
            # delete the file/directory and get the task id
            rm_label = "Deleting file/directory."
            task_id = self.globus_delete(path, endpoint_id=endpoint_id,
                                         label=rm_label)

            # wait for the task to complete, polling every 15 seconds.
            completed = self.transfer_client.task_wait(task_id, timeout=stop_after,
                                                       polling_interval=15)
            if completed:
                print("Delete task finished!")
                return True
            
            print("Delete task still running after timeout reached.")

        except exc.TransferAPIError:
            print("TransferAPIError occurred when attempting to delete file/directory.")
        
        return False

    def mkdir(self, path, endpoint_id=DEFAULT_ENDPOINT):
        """
        Creates a new directory on a Globus endpoint using the given path.
        Returns a boolean to indicate whether or not the operation was successful.
        """

        # check if the TransferClient exists
        if self.transfer_client is None:
            # if it doesn't then get one
            self.get_transfer_client()

        try:
            self.transfer_client.operation_mkdir(endpoint_id, path=path)
            return True
        except GlobusAPIError as ex:
            if "Exists" in ex.code:
                print("The specified directory already exists on that endpoint.")
            else:
                raise

        return False

    def read(self, path, endpoint_id=DEFAULT_ENDPOINT):
        if not self.isfile(path, endpoint_id=endpoint_id):
            pass

        with open(path, mode='rb') as f:
            content = f.read().decode("utf-8")

        return content

    def lstat(self, path, endpoint_id=DEFAULT_ENDPOINT):
        parent = Path(path).parent
        files = self.ls(path=parent, endpoint_id=endpoint_id)["DATA"]
        for item in files:
            if item["type"] == "file":
                name = os.path.basename(os.path.normpath(path))
                if item["name"] == name:
                    return item["last_modified"]
        return DUMMY_CREATED_DATE

    def write(self, path, content, format, endpoint_id=DEFAULT_ENDPOINT):
        if format not in {'text', 'base64'}:
            raise HTTPError(400, "Must specify format of file contents as 'text' or 'base64'")

        try:
            if format == 'text':
                w_content = content.encode('utf8')
            else:
                b64_bytes = content.encode('ascii')
                w_content = base64.b64decode(b64_bytes)
        except Exception as exc:
            raise HTTPError(400, u'Encoding error saving %s: %s' % (path, exc))
        
        with open(path, mode='wb') as f:
            f.write(w_content)
         
    def writenotebook(self, path, content):
        with open(path, mode='wb') as f:
            f.write(content.encode("utf-8"))
