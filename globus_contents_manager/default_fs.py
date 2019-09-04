"""
Default FileSystem class to be used by the DefaultContentsManager.

Taken and modified from: 
    https://github.com/danielfrg/s3contents/blob/master/s3contents/genericfs.py
"""

from globus_contents_manager.ipycompat import HasTraits


class DefaultFS(HasTraits):

    def ls(self, path="", endpoint_id=None):
        """
        Lists the files and directories at the given path.
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def isfile(self, path, endpoint_id=None):
        """
        Checks if a given path points to a file.
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def isdir(self, path, endpoint_id=None):
        """
        Checks if a given path points to a directory.
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def mv(self, old_path, new_path, endpoint_id=None, stop_after=0):
        """
        Moves a file from it's current location (old_path) to a new location (new_path).
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def cp(self, old_path, new_path, endpoint_id=None, stop_after=0):
        """
        Copies a file or directory located at a given path to a new location.
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def rm(self, path, endpoint_id=None):
        """
        Deletes a file or directory (recursively) located at a given path.
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def mkdir(self, path, endpoint_id=None):
        """
        Creates a new directory using the given path.
        """
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def read(self, path, endpoint_id=None):
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def lstat(self, path, endpoint_id=None):
        raise NotImplementedError("Should be implemented by the file system abstraction")

    def write(self, path, content, format, endpoint_id=None):
        raise NotImplementedError("Should be implemented by the file system abstraction")


class DefaultFSError(Exception):
    pass


class NoSuchFile(DefaultFSError):

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.message = "No such file or directory: {}".format(path)
        super(NoSuchFile, self).__init__(self.message, *args, **kwargs)
    