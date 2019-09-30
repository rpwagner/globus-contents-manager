"""
Globus Contents Manager
"""
# import os
import json
import mimetypes
import globus_sdk
from fair_research_login import NativeClient
from tornado.web import HTTPError
from datetime import datetime
from nbformat import from_dict, reads
from globuscontents.default_contents_manager import DefaultContentsManager
from globuscontents.globus_fs import GlobusFS
from globuscontents.utils import (
    base_model, 
    base_directory_model,
    convert_to_datetime, 
    DUMMY_CREATED_DATE,
    NBFORMAT_VERSION
)

# CLIENT_ID = '7414f0b4-7d05-4bb6-bb00-076fa3f17cf5'
# SCOPES = ['urn:globus:auth:scope:transfer.api.globus.org:all']
PATH = "/~/"
DEFAULT_ENDPOINT = "ddb59aef-6d04-11e5-ba46-22000b92c6ec"

class GlobusContentsManager(DefaultContentsManager):
    """
    Custom Contents Manager with Globus functionality.
    """
    def __init__(self, *args, **kwargs):
        super(GlobusContentsManager, self).__init__(*args, **kwargs)
        # super().__init__(*args, **kwargs)

        # self.nc = NativeClient(client_id=CLIENT_ID)
        # self.nc.login(requested_scopes=SCOPES)

        self.fs = GlobusFS()

    def get_ls(self, ls_path=PATH, tc_filter=None):
        """
        Gets the list of directories and files at a given path. Useful for checking if 
        a file or directory exists.
        """
        transfer_client = self.fs.get_transfer_client()
        # auth = self.nc.get_authorizers()['transfer.api.globus.org']
        # transfer_client = globus_sdk.TransferClient(authorizer=auth)

        resp = None
        try:
            # Make sure that endpoint is activated
            transfer_client.endpoint_autoactivate(DEFAULT_ENDPOINT)

            # save the response from the ls operation
            if tc_filter is not None:
                resp = transfer_client.operation_ls(DEFAULT_ENDPOINT, path=ls_path, filter=tc_filter)
            else: 
                resp = self.fs.ls()

        except globus_sdk.GlobusAPIError as ex:
            print('The specified path is not a directory')
            return ex

        return resp

    def dir_exists(self, dir_path=PATH):
        # Checks if the given path points to a directory
        resp = self.get_ls(dir_path)

        # if value returned is not an exception or None then a directory exists at the given path
        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            return False
        
        return True


    def file_exists(self, file_path=PATH):
        # Checks if a file exists at the given path
        resp = self.get_ls(file_path)

        # check if an exception was returned
        if isinstance(resp, globus_sdk.exc.TransferAPIError):
            # if the exception is about the item not being a directory then file exists
            return "NotDirectory" in resp.code

        # if an exception was not returned then file does not exist
        return False


    def rename_file(self, old_path, new_path):
        # Rename a file or directory

        # if possible rename local file/directory
        try:
            super().rename_file(old_path, new_path)
        except FileNotFoundError:
            print("File/directory not found on local storage")
        
        # get the id of the endpoint that the file/directory exists on
        # endpoint_id = input("Enter the Endpoint ID")

        # get the transfer client
        transfer_client = self.fs.get_transfer_client()
        # auth = self.nc.get_authorizers()['transfer.api.globus.org']
        # transfer_client = globus_sdk.TransferClient(authorizer=auth)

        try:
            # Make sure that endpoint is activated
            transfer_client.endpoint_autoactivate(DEFAULT_ENDPOINT)

            # rename the file/directory on the endpoint
            transfer_client.operation_rename(DEFAULT_ENDPOINT, old_path, new_path)
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
            # endpoint_id = input("Enter the Endpoint ID")

            # get the transfer client
            auth = self.nc.get_authorizers()['transfer.api.globus.org']
            transfer_client = globus_sdk.TransferClient(authorizer=auth)
            
            ddata = globus_sdk.DeleteData(transfer_client, DEFAULT_ENDPOINT, recursive=True)
            # Recursively delete path contents (because of recursive flag set above)
            ddata.add_item(path)

            # Make sure that endpoint is activated
            transfer_client.endpoint_autoactivate(DEFAULT_ENDPOINT)

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
        resp = self.get_ls(path, tc_filter="name:.*")

        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            return False
        
        return True


    def save(self, model, path):
        """
        Save a file or directory model to a path.
        """

        # try:
        #     # try to save file/directory model locally
        #     super().save(model, path)
        # except:
        #     pass

        if "type" not in model:
            raise HTTPError(400, "No model type provided")

        if "content" not in model and model["type"] != "directory":
            raise HTTPError(400, "No file content provided")

        if model["type"] not in ("file", "directory", "notebook"):
            raise HTTPError(400, "Unhandled contents type: %s" % model["type"])

        try:
            if model["type"] == "notebook":
                validation_message = self._save_notebook(model, path)
            elif model["type"] == "file":
                validation_message = self._save_file(model, path)
            else:
                validation_message = self._save_directory(path)
        except Exception as exc:
            err_message = "Unexpected error while saving file: %s %s" % (path, exc)
            raise HTTPError(500, err_message)

        model = self.get(path, type=model["type"], content=False)
        if validation_message is not None:
            model["message"] = validation_message

        return model

    def _save_notebook(self, model, path):
        nb_contents = from_dict(model["content"])
        self.check_and_sign(nb_contents, path)
        file_contents = json.dumps(model["content"])
        self.fs.writenotebook(path, file_contents)
        self.validate_notebook_model(model)
        return model.get("message")

    def _save_file(self, model, path):
        file_contents = model["content"]
        file_format = model.get('format')
        self.fs.write(path, file_contents, file_format)
        return ""

    def _save_directory(self, path):
        """
        Creates a new directory using the specified path.
        """
        self.fs.mkdir(path)
        return ""

    #https://app.globus.org/file-manager?origin_id=
    def get(self, path, content=True, type=None, format=None):
        # Get a file or directory

        # try:
        #     super().get(path, content, type)
        # except:
        #     pass

        path_ = path.strip('/')

        if type is None:
            type = self.guess_type(path_)
        
        try:
            func = {
                "directory": self._get_directory,
                "notebook": self._get_notebook,
                "file": self._get_file,
            }[type]
        except KeyError:
            raise ValueError("Unknown type passed: '{}'".format(type))

        return func(path=path_, content=content, format=format)

    def _get_directory(self, path, content=True, format=None):
        return self._directory_model_from_path(path, content=content)

    def _get_notebook(self, path, content=True, format=None):
        return self._notebook_model_from_path(path, content=content, format=format)

    def _get_file(self, path, content=True, format=None):
        return self._file_model_from_path(path, content=content, format=format)

    def _directory_model_from_path(self, dir_path, content=False):
        model = base_directory_model(dir_path)
        if content:
            if not self.dir_exists(dir_path):
                # raise error
                raise HTTPError(404, "No such entity: [{path}]".format(path=dir_path))
            model["format"] = "json"
            dir_content = self.fs.ls(path=dir_path)
            model["content"] = self._convert_file_records(dir_content)
        return model

    def _notebook_model_from_path(self, nb_path, content=False, format=None):
        """
        Build a notebook model.
        """
        model = base_model(nb_path)
        model["type"] = "notebook"
        if self.fs.isfile(nb_path):
            lstat = self.fs.lstat(nb_path)
            if not isinstance(lstat, datetime.datetime):
                lstat = convert_to_datetime(lstat)
            model["last_modified"] = model["created"] = lstat
        else:
            model["last_modified"] = model["created"] = DUMMY_CREATED_DATE

        if content:
            if not self.fs.isfile(nb_path):
                raise HTTPError(404, "No such entity: [{path}]".format(path=nb_path))
            
            file_content = self.fs.read(nb_path)
            nb_content = reads(file_content, as_version=NBFORMAT_VERSION)
            self.mark_trusted_cells(nb_content, nb_path)
            model["format"] = "json"
            model["content"] = nb_content
            self.validate_notebook_model(model)

        return model

    def _file_model_from_path(self, file_path, content=False, format=None):
        """
        Build a file model.
        """
        model = base_model(file_path)
        model["type"] = "file"

        if self.fs.isfile(file_path):
            lstat = self.fs.lstat(file_path)
            if not isinstance(lstat, datetime.datetime):
                lstat = convert_to_datetime(lstat)
            model["last_modified"] = model["created"] = lstat
        else:
            model["last_modified"] = model["created"] = DUMMY_CREATED_DATE

        if content:
            try:
                content = self.fs.read(file_path)
            except Exception:
                raise HTTPError(404, "No such entity: [{path}]".format(path=file_path))
                
            model["format"] = format or "text"
            model["content"] = content
            model["mimetype"] = mimetypes.guess_type(file_path)[0] or "text/plain"

            if format == "base64":
                from base64 import b64decode
                model["content"] = b64decode(content)

        return model

    def _convert_file_records(self, paths):
        """
        Applies _notebook_model_from_path, _file_model_from_path, or _directory_model_from_path
        to each entry of `paths`, depending on the type of the entry.
        """
        records = []
        for path in paths:
            entry_type = self.guess_type(path)
            if entry_type == "notebook":
                records.append(self._notebook_model_from_path(path, False))
            elif entry_type == "file":
                records.append(self._file_model_from_path(path, False, None))
            elif entry_type == "directory":
                records.append(self._directory_model_from_path(path, False))
            else:
                err_message = "Unknown file type %s for file '%s'" % (entry_type, path)
                raise HTTPError(500, err_message)
        
        return records
