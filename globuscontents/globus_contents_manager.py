"""
Globus Contents Manager
"""
import os
import os
import json
import pickle
import mimetypes
import tempfile
import time
from traitlets import (Unicode, Int)
import globus_sdk
from fair_research_login import NativeClient
from tornado.web import HTTPError
from datetime import datetime
from nbformat import from_dict, reads
try: #PY3
    from base64 import encodebytes, decodebytes, b64decode
except ImportError: #PY2
    from base64 import encodestring as encodebytes, decodestring as decodebytes
from globuscontents.ipycompat import (
    ContentsManager,
    HasTraits
)
from globuscontents.utils import (
    base_model, 
    convert_to_datetime, 
    DUMMY_CREATED_DATE,
    NBFORMAT_VERSION
)

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
        tokens = {}
        globus_env_data = os.getenv('GLOBUS_DATA')
        if not globus_env_data:
            client = NativeClient(client_id=self.client_id, app_name=self.app_name)
            tokens = client.load_tokens()
        else:
            pickled_tokens = b64decode(globus_env_data)
            tokens = pickle.loads(pickled_tokens)['tokens']
        transfer_access_token = tokens['transfer.api.globus.org']['access_token']

        # then use that token to create an AccessTokenAuthorizer
        transfer_auth = globus_sdk.AccessTokenAuthorizer(transfer_access_token)
        # finally, use the authorizer to create a TransferClient object
        self.transfer_client = globus_sdk.TransferClient(authorizer=transfer_auth)
        self.transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)

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

    globus_local_endpoint_cache_dir = Unicode(help="""Path to cache dir on the local
    endpoint.""").tag(config=True)
    def _globus_local_endpoint_cache_dir_default(self):
        return '/cache'

    globus_local_fs_cache_dir = Unicode(help="""Path to cache dir on the local file
    system.""").tag(config=True)
    def _globus_local_fs_cache_dir_default(self):
        return '/home/researcher/projects/cache'
    
    globus_cache_wait = Int(help="""How long to wait for a caching transfer to
    finish in seconds.""").tag(config=True)
    def _globus_cache_wait_default(self):
        return 60

    globus_cache_wait_poll = Int(help="""How frequently to poll (in seconds) a
    transfer status when caching.""").tag(config=True)
    def _globus_cache_wait_poll_default(self):
        return 10

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

        # TODO: CACHING! Layer goes here.
        
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
        self.log.debug('Globus Contents dir_exists ep_path = {}'.format(ep_path))
        resp = self.transfer_client.operation_ls(self.globus_remote_endpoint, path=ep_path, show_hidden=False)
        # if value returned is not an exception or None then no directory exists at the given path
        if isinstance(resp, globus_sdk.exc.TransferAPIError) or resp is None:
            return False
        # if no exception was returned then the given path does point to a directory
        return True

    def file_exists(self, file_path):
        # TODO: Implement
        return True


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
        #transfer_client = self.fs.get_transfer_client()
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
        #self.fs.writenotebook(path, file_contents)
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
                model['format'] = 'json'
            else:
                model['mimetype'] = mimetypes.guess_type(ls_item['name'])[0] or 'text/plain'
                model['format'] = 'text'
                if not model['mimetype'].startswith('text'):
                    model['format'] = None
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
        # TODO: Needs checkpoints
        # This should become the general "get file" layer.
        # Turn off notifications.
        self.log.debug('Globus Contents get notebook path = {}'.format(path))
        remote_notebook_path = os.path.join(self.globus_remote_endpoint_basepath, path.lstrip('/'))
        local_ep_notebook_path = os.path.join(self.globus_local_endpoint_cache_dir, path.lstrip('/'))
        local_fs_notebook_path = os.path.join(self.globus_local_fs_cache_dir, path.lstrip('/'))
        self.log.debug('remote notebook path = {}'.format(remote_notebook_path))
        self.log.debug('local ep notebook path = {}'.format(local_ep_notebook_path))
        self.log.debug('local fs notebook path = {}'.format(local_fs_notebook_path))
        nb_dir = os.path.dirname(local_fs_notebook_path)
        label = "Jupyter ContentsManager caching"
        # TransferData() automatically gets a submission_id for once-and-only-once submission
        tdata = globus_sdk.TransferData(self.transfer_client,
                                            self.globus_remote_endpoint,
                                            self.globus_local_endpoint,
                                            notify_on_succeeded=False,
                                            label=label)
        tdata.add_item(remote_notebook_path, local_ep_notebook_path)
        # Ensure endpoints are activated
        self.transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)
        self.transfer_client.endpoint_autoactivate(self.globus_local_endpoint)
        submit_result = self.transfer_client.submit_transfer(tdata)
        task_id = submit_result['task_id']
        if self.transfer_client.task_wait(task_id, timeout=self.globus_cache_wait,
                                              polling_interval=self.globus_cache_wait_poll):
            task = self.transfer_client.get_task(task_id)
            status = task["status"]
            if status != "SUCCEEDED":
                self.transfer_client.cancel_task(task_id)
                HTTPError(502, 'Unable to cache {}'.format(path), reason='bad transfer')
        else:
            self.transfer_client.cancel_task(task_id)
            HTTPError(408, 'Too long getting {}'.format(path), reason='slow caching')

        model = base_model(path)
        model['type'] = 'notebook'
        file_content = open(local_fs_notebook_path, 'r').read()
        nb_content = reads(file_content, as_version=NBFORMAT_VERSION)
        self.mark_trusted_cells(nb_content, path)
        model["format"] = "json"
        model["content"] = nb_content
        self.validate_notebook_model(model)
        return model

    def _read_local_file(self, local_path, format):
        """Read a non-notebook file.
        local_path: The path to be read.
        format:
          If 'text', the contents will be decoded as UTF-8.
          If 'base64', the raw bytes contents will be encoded as base64.
          If not specified, try to decode as UTF-8, and fall back to base64
        """
        
        with open(local_path, 'rb') as f:
            bcontent = f.read()

        if format is None or format == 'text':
            # Try to interpret as unicode if format is unknown or if unicode
            # was explicitly requested.
            try:
                return bcontent.decode('utf8'), 'text'
            except UnicodeError:
                if format == 'text':
                    raise HTTPError(
                        400,
                        "%s is not UTF-8 encoded" % local_path,
                        reason='bad format',
                    )
        return encodebytes(bcontent).decode('ascii'), 'base64'
    
    def _get_file(self, path, content=True, format=None):
        # TODO: Needs checkpoints
        # This should become the general "get file" layer.
        # Turn off notifications.
        self.log.debug('Globus Contents get file path = {} contents = {}  format = {}'.format(path, str(content), format))
        remote_file_path = os.path.join(self.globus_remote_endpoint_basepath, path.lstrip('/'))
        local_ep_file_path = os.path.join(self.globus_local_endpoint_cache_dir, path.lstrip('/'))
        local_fs_file_path = os.path.join(self.globus_local_fs_cache_dir, path.lstrip('/'))
        self.log.debug('remote file path = {}'.format(remote_file_path))
        self.log.debug('local ep file path = {}'.format(local_ep_file_path))
        self.log.debug('local fs file path = {}'.format(local_fs_file_path))
        nb_dir = os.path.dirname(local_fs_file_path)
        label = "Jupyter ContentsManager caching"
        # TransferData() automatically gets a submission_id for once-and-only-once submission
        tdata = globus_sdk.TransferData(self.transfer_client,
                                            self.globus_remote_endpoint,
                                            self.globus_local_endpoint,
                                            notify_on_succeeded=False,
                                            label=label)
        tdata.add_item(remote_file_path, local_ep_file_path)
        # Ensure endpoints are activated
        self.transfer_client.endpoint_autoactivate(self.globus_remote_endpoint)
        self.transfer_client.endpoint_autoactivate(self.globus_local_endpoint)
        submit_result = self.transfer_client.submit_transfer(tdata)
        task_id = submit_result['task_id']
        if self.transfer_client.task_wait(task_id, timeout=self.globus_cache_wait,
                                              polling_interval=self.globus_cache_wait_poll):
            task = self.transfer_client.get_task(task_id)
            status = task["status"]
            if status != "SUCCEEDED":
                self.transfer_client.cancel_task(task_id)
                HTTPError(502, 'Unable to cache {}'.format(path), reason='bad transfer')
        else:
            self.transfer_client.cancel_task(task_id)
            HTTPError(408, 'Too long getting {}'.format(path), reason='slow caching')

        model = base_model(path)
        model['type'] = 'file'
        model['last_modified'] = model['created'] = DUMMY_CREATED_DATE
        model['format'] = format or 'text'
        model['mimetype'] = mimetypes.guess_type(path)[0]
        self.log.debug('Globus Contents get file path = {} model = {}'.format(path, str(model)))
        if content:
            content, format = self._read_local_file(local_fs_file_path, format)
            if model['mimetype'] is None:
                default_mime = {
                    'text': 'text/plain',
                    'base64': 'application/octet-stream'
                }[format]
                model['mimetype'] = default_mime

            model.update(
                content=content,
                format=format,
            )
        return model
