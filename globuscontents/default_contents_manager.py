"""
WIP
"""
import os
from datetime import datetime
from tika import parser
from globuscontents.ipycompat import (
    ContentsManager, 
    HasTraits
)

PATH = '/~/'
class DefaultContentsManager(ContentsManager, HasTraits):
    """
    Default ContentsManager
    """
    def __init__(self, *args, **kwargs):
        super(DefaultContentsManager, self).__init__(*args, **kwargs)
        self.path = PATH
        self.files = {}
        self.directories = {}

        for root, dirs, files in os.walk(self.path):
            for name in files:
                local_path = os.path.join(root, name)
                self.files[local_path] = parser.from_file(local_path)
            for name in dirs:
                local_path = os.path.join(root, name)
                items = os.listdir(local_path)
                self.directories[local_path] = items

    def is_hidden(self, path):
        # Check if file or directory is hidden

        return path.startswith('.')

    def dir_exists(self, path):
        # Checks if a directory exists at the given path
        if path in self.directories.keys():
            return True
        return False

    def file_exists(self, path):
        # Checks if a file exists at the given path
        file_paths = self.files.keys()
        if path in file_paths:
            return True
        return False

    def get(self, path, content=True, type=None, format=None):
        # Get a file or directory
        if type == 'directory':
            if self.dir_exists(path):
                return self.directories[path]
        else:
            if self.file_exists(path):
                return self.files[path]
        return

    def save(self, model, path):
        # Save a file or directory model to a path
        if model["type"] == "file":
            # file_obj = open(path, 'a+')
            # file_obj.write(model)
            self.files[path] = model
        elif model["type"] == "directory":
            # os.mkdir(path, model)
            self.directories[path] = []

    def delete_file(self, path):
        # Delete the file or directory at the given path
        if self.file_exists(path):
            self.files.pop(path)
        elif self.dir_exists(path):
            self.directories.pop(path)

    def rename_file(self, old_path, new_path):
        # Rename a file or directory
        if self.file_exists(old_path):
            item = self.files.pop(old_path)
            self.files[new_path] = item
        elif self.dir_exists(old_path):
            item = self.directories.pop(old_path)
            self.directories[new_path] = item

    ### Utils

    # from https://github.com/quantopian/pgcontents/blob/master/pgcontents/pgmanager.py
    def guess_type(self, path, allow_directory=True):
        """
        Guess the type of a file.
        If allow_directory is False, don't consider the possibility that the
        file is a directory.
        """
        if path.endswith('.ipynb'):
            return 'notebook'
        elif allow_directory and self.dir_exists(path):
            return 'directory'
        
        return 'file'
    
    def get_basic_model(self, path):
        model_type = self.guess_type(path)
        return {
            "name": path.rsplit('/', 1)[-1],
            "path": path,
            "type": model_type,
            "created": None,
            "last_modified": None,
            "content": None,
            "mimetype": None,
            "format": None,
            "writable": True,
        }

    def is_valid_model(self, model, model_type):
        """
        Checks that the model fits the correct criteria depending on the model type
        """
        # notebook model: format is always "json", mimetype is always None,
        # content field must contain a nbformat.notebooknode.NotebookNode
        # that represents the .ipynb file that the model represents
        if model_type == "notebook":
            # check format
            if model["format"] != "json":
                print("Invalid format for notebook model. Must be 'json'.")
                return False

            # check mimetype
            if model["mimetype"] is not None:
                print("Invalid mimetype for notebook model. Must be None.")
                return False

            # TODO: check content

            # if none of the above conditions have been met, model is valid
            return True

        # file model: format is either "text" or "base64", mimetype (unicode) is
        # either text/plain (text-format) or application/octet-stream (base64-format),
        # content field is always of type unicode (text-format: file's bytes after
        # decoding as UTF-8; base64 should be read as bytes, base64 encoded, then
        # decoded as UTF-8)
        elif model_type == "file":
            # check format
            model_format = model["format"]
            if model_format != "text" and model_format != "base64":
                print("Invalid format for file model. Must be 'text' or 'base64'.")
                return False
            
            # check mimetype (depends on model_format)
            if model_format == "text" and model["mimetype"] != 'text/plain':
                print("Invalid mimetype for (text) file model. Must be text/plain.")
                return False
            elif model_format == "base64" and model["mimetype"] != 'application/octet-stream':
                print("Invalid mimetype for (base64) file model. Must be application/octet-stream.")
                return False
            
            # TODO: check content

            # if none of the above conditions have been met, model is valid
            return True

        # directory model: format is always "json", mimetype is always None, content
        # contains a list of content-free models representing the entities in the
        # directory
        else:
            # check format
            if model["format"] != "json":
                print("Invalid format for directory model. Must be 'json'.")
                return False

            # check mimetype
            if model["mimetype"] is not None:
                print("Invalid mimetype for directory model. Must be None.")
                return False
            
            # TODO: check content

            # if none of the above conditions have been met, model is valid
            return True
