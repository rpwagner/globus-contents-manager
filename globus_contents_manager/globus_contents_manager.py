"""
Globus Contents Manager
"""
import os
import tika
import globus_sdk
from tika import parser
from . import DefaultContentsManager
from fair_research_login import NativeClient

CLIENT_ID = '7414f0b4-7d05-4bb6-bb00-076fa3f17cf5'
SCOPES = ['urn:globus:auth:scope:transfer.api.globus.org:all']
PATH = '/~/'

class GlobusContentsManager(DefaultContentsManager):
    """
    Custom Contents Manager with Globus functionality.
    """
    def __init__(self, *args, **kwargs):
        # super(GlobusContentsManager, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.nc = NativeClient(client_id=CLIENT_ID)
        self.nc.login(requested_scopes=SCOPES)

    def get_ls(self, path=PATH, filter=None):
        """
        Gets the list of directories and files at a given path. Useful for checking if file or directory exists.
        """
        auth = self.nc.get_authorizers()['transfer.api.globus.org']
        transfer_client = globus_sdk.TransferClient(authorizer=auth)

        resp = None
        try:
            resp = transfer_client.operation_ls(CLIENT_ID, path=path, filter=filter)
        except globus_sdk.GlobusAPIError as e:
            print('The specified path is not a directory')
            return e

        return resp

    def dir_exists(self, path=PATH):
        # Checks if the given path points to a directory
        resp = self.get_ls(path)

        # if value returned is not an exception or None then a directory exists at the given path
        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            return False
        
        return True


    def file_exists(self, path=PATH):
        # Checks if a file exists at the given path
        resp = self.get_ls(path)

        # check if an exception was returned
        if isinstance(resp, globus_sdk.exc.TransferAPIError):
            # if the exception is about the item not being a directory then file exists
            return "NotDirectory" in resp.code

        # if an exception was not returned then file does not exist
        return False


    def rename_file(self, old_path, new_path):
        # Rename a file or directory

        # rename local file/directory
        try:
            super().rename_file(self, old_path, new_path)
        except FileNotFoundError:
            print("File/directory not found on local storage")

        try:
            # if possible, rename local file/directory
            super().rename_file(old_path, new_path)
        except:
            pass
        
        # get the id of the endpoint that the file/directory exists on
        endpoint_id = input("Enter the Endpoint ID")

        # get the transfer client
        auth = self.nc.get_authorizers()['transfer.api.globus.org']
        transfer_client = globus_sdk.TransferClient(authorizer=auth)

        try:
            # rename the file/directory on the endpoint
            transfer_client.operation_rename(endpoint_id, old_path, new_path)
        except globus_sdk.TransferAPIError:
            print("Error occurred when trying to rename file/directory")

    def delete_file(self, path):
        # Delete the file or directory at the given path

        try:
            # if possible, delete local file/directory
            super().delete_file(path)
        except:
            pass
        
        
        try:
            # get the id of the endpoint that the file/directory exists on
            endpoint_id = input("Enter the Endpoint ID")

            # get the transfer client
            auth = self.nc.get_authorizers()['transfer.api.globus.org']
            transfer_client = globus_sdk.TransferClient(authorizer=auth)
            
            ddata = globus_sdk.DeleteData(transfer_client, endpoint_id, recursive=True)
            # Recursively delete path contents (because of recursive flag set above)
            ddata.add_item(path)

            # Make sure that endpoint is activated
            transfer_client.endpoint_autoactivate(endpoint_id)

            submit_result = transfer_client.submit_delete(ddata)
            print("Task ID:", submit_result["task_id"])
        except:
            pass

        return


    def is_hidden(self, path):
        # Check if file or directory is hidden

        try:
            # Check local file/directory
            local = super().is_hidden(path)

            if isinstance(local, bool):
                return local
        except:
            pass

        # get all hidden files and directories
        resp = self.get_ls(path, "name:.*")

        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            return False
        
        return True


    def save(self, model, path):
        # Save a file or directory model to a path

        try:
            # try to save file/directory model locally
            super().save(model, path)
        except:
            pass

        

        return


    #https://app.globus.org/file-manager?origin_id=
    def get(self, path, content=True, modelType=None):
        # Get a file or directory

        try:
            super().get(path, content, modelType)
        except:
            pass
            
        return