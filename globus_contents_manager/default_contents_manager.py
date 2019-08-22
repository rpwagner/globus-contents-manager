"""
WIP
"""
from notebook.services.contents.manager import ContentsManager
import os
import tika
from tika import parser

if os.name == 'nt':
    import win32api, win32con

PATH = '/~/'
class DefaultContentsManager(ContentsManager):
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
        # check if file or directory is hidden
        if os.name == 'nt':
            # check if windows os
            attribute = win32api.GetFileAttributes(path)
            return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        # check if unix os
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

    def get(self, path, content=True, modelType=None):
        # Get a file or directory
        if modelType == 'directory':
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
