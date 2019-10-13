"""
Globus Contents Manager
"""
import os
import json
import mimetypes
import tempfile
import time
from traitlets import Unicode
import globus_sdk
from fair_research_login import NativeClient
from tornado.web import HTTPError
from datetime import datetime
from nbformat import from_dict, reads
from globuscontents.ipycompat import (
    ContentsManager, 
    HasTraits
)
from globuscontents.globus_fs import GlobusFS
from globuscontents.utils import (
    base_model, 
    convert_to_datetime, 
    DUMMY_CREATED_DATE,
    NBFORMAT_VERSION
)

NBFORMAT_VERSION = 4

TUTORIAL_ENDPOINT1 = "ddb59aef-6d04-11e5-ba46-22000b92c6ec"
TUT1_BASE_PATH = "/~"
DEFAULT_CLIENT_ID = '7414f0b4-7d05-4bb6-bb00-076fa3f17cf5'
DEFAULT_APP_NAME = 'Globus Jupyter Contents Manager'
DEFAULT_SCOPES = 'urn:globus:auth:scope:transfer.api.globus.org:all'

class GlobusContentsManager(ContentsManager, HasTraits):
    """
    Custom Contents Manager with Globus functionality.
    """
    def __init__(self, *args, **kwargs):
        super(GlobusContentsManager, self).__init__(*args, **kwargs)
        client = NativeClient(client_id=self.client_id, app_name=self.app_name)
        tokens = client.load_tokens()
        transfer_access_token = tokens['transfer.api.globus.org']['access_token']

        # then use that token to create an AccessTokenAuthorizer
        transfer_auth = globus_sdk.AccessTokenAuthorizer(transfer_access_token)
        # finally, use the authorizer to create a TransferClient object
        self.transfer_client = globus_sdk.TransferClient(authorizer=transfer_auth)
        self.transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)
        #self._cache_dir = tempfile.TemporaryDirectory()
        self._cache_dir = '/Users/rpwagner/tmp/jupyter_contents_cache'

    client_id = Unicode(help="""The Globus Native App client ID to use.""").tag(config=True)
    def _client_id_default(self):
        return DEFAULT_CLIENT_ID

    app_name = Unicode(help="""The Globus Native App name to use.""").tag(config=True)
    def _app_name_default(self):
        return DEFAULT_APP_NAME
    
    scopes = Unicode(help="""The Globus Auth scopes to use.""").tag(config=True)
    def _scopes_default(self):
        return DEFAULTS_SCOPES
        
    globus_remote_endpoint = Unicode(help="""The remote endpoint to serve
    data from.""").tag(config=True)
    def _globus_remote_endpoint_default(self):
        return TUTORIAL_ENDPOINT1

    globus_remote_endpoint_basepath = Unicode(help="""The absolute path on the
    remote endpoint to become the root of the Jupyter file system.""").tag(config=True)
    def _globus_remote_endpoint_basepath_default(self):
        return TUT1_BASE_PATH

    globus_local_endpoint = Unicode(help="""Local Globus endpoint for caching
    files.""").tag(config=True)

    def _globus_local_endpoint_default(self):
        return ''

    #https://app.globus.org/file-manager?origin_id=
    def get(self, path, content=True, type=None, format=None):
        """ Takes a path for an entity and returns its model
        Parameters
        ----------
        path : str
            the API path that describes the relative path for the target
        content : bool
            Whether to include the contents in the reply
        type : str, optional
            The requested type - 'file', 'notebook', or 'directory'.
            Will raise HTTPError 400 if the content doesn't match.
        format : str, optional
            The requested format for file contents. 'text' or 'base64'.
            Ignored if this returns a notebook or directory model.
        Returns
        -------
        model : dict
            the contents model. If content=True, returns the contents
            of the file or directory as well.
        """

        self.log.debug('Globus Contents get path = {}  type = {}'.format(path, type))
        if type == 'directory':
            model = self._get_dir(path, content=content)
        elif type == 'notebook' or (type is None and path.endswith('.ipynb')):
            model = self._get_notebook(path, content=content)
        elif type == 'file':
            model = self._get_file(path, content=content, format=format)
        else:
            raise HTTPError(400,
                                u'%s no type specified' % path, reason='bad type')
        return model

    def dir_exists(self, path):
        self.log.debug('Globus Contents dir_exists path = {}'.format(path))
        ep_path = os.path.join(self.globus_remote_endpoint_basepath, path.lstrip('/'))
        if ep_path[-1] != '/':
            ep_path = '{}/'.format(ep_path)
        resp = self.transfer_client.operation_ls(self.globus_remote_endpoint, path=ep_path, show_hidden=False)
        # if value returned is not an exception or None then no directory exists at the given path
        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            return False
        # if no exception was returned then the given path does point to a directory
        return True

    def file_exists(self, file_path):
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
            transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)

            # rename the file/directory on the endpoint
            transfer_client.operation_rename(self.globus_remote_endpoint, old_path, new_path)
        except globus_sdk.exc.TransferAPIError:
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
            
            ddata = globus_sdk.DeleteData(transfer_client, self.globus_remote_endpoint, recursive=True)
            # Recursively delete path contents (because of recursive flag set above)
            ddata.add_item(path)

            # Make sure that endpoint is activated
            transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)

            submit_result = transfer_client.submit_delete(ddata)
            print("Task ID:", submit_result["task_id"])
        except:
            pass

        return


    def is_hidden(self, path):
        return False


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

    def _model_from_ls_item(self, path, ls_item):
        model = base_model(os.path.join(path, ls_item['name']))
        model['size'] = ls_item['size']
        model['last_modified'] = ls_item['last_modified']
        if ls_item['type'] == 'dir':
            model['type'] = 'directory'
        else:
            model['type'] = 'file'
            if ls_item['name'].endswith('.ipynb'):
                model['type'] = 'notebook'
        return model

    def _get_dir(self, path, content=True):
        self.log.debug('Globus Contents path path = {}'.format(path))
        ep_path = os.path.join(self.globus_remote_endpoint_basepath, path.lstrip('/'))
        if ep_path[-1] != '/':
            ep_path = '{}/'.format(ep_path)
        resp = self.transfer_client.operation_ls(self.globus_remote_endpoint, path=ep_path,
                                                     show_hidden=False)
        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            raise HTTPError(400, '{} is not a directory'.format(path), reason='bad type')
        model = base_model(path)
        model['type'] = 'directory'
        model['size'] = None
        if content:
            model["format"] = "json"
            model["content"] = [self._model_from_ls_item(path, item) for item in resp]
        self.log.debug('Globus Contents _dir_model path = {} model = {}'.format(path, str(model)))
        return model

    def _get_notebook(self, path, content=True, format=None):
        self.log.debug('Globus Contents get notebook path = {}'.format(path))
        remote_notebook_path = os.path.join(self.globus_remote_endpoint_basepath, path.lstrip('/'))
        local_notebook_path = os.path.join(self._cache_dir, path.lstrip('/'))
        self.log.debug('remote notebook path = {}'.format(remote_notebook_path))
        self.log.debug('local notebook path = {}'.format(local_notebook_path))
        nb_dir = os.path.dirname(local_notebook_path)
        label = "Jupyter ContentsManager caching"
        # TransferData() automatically gets a submission_id for once-and-only-once submission
        tdata = globus_sdk.TransferData(self.transfer_client,
                                            self.globus_remote_endpoint,
                                            self.globus_local_endpoint,
                                            label=label)
        tdata.add_item(remote_notebook_path, local_notebook_path)
        # Ensure endpoints are activated
        self.transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)
        self.transfer_client.endpoint_autoactivate(self.globus_local_endpoint)
        submit_result = self.transfer_client.submit_transfer(tdata)
        stop = False
        while not stop:
            stop = self.transfer_client.get_task(submit_result['task_id']).data["status"] == "SUCCEEDED"
            time.sleep(10)
        
        model = base_model(path)
        model['type'] = 'notebook'
        file_content = open(local_notebook_path, 'r').read()
        nb_content = reads(file_content, as_version=NBFORMAT_VERSION)
        self.mark_trusted_cells(nb_content, path)
        model["format"] = "json"
        model["content"] = nb_content
        self.validate_notebook_model(model)
        return model
