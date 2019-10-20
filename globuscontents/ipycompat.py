"""
Utilities for managing compatability between notebook versions.

Taken from: https://github.com/quantopian/pgcontents/blob/master/pgcontents/utils/ipycompat.py
"""

import notebook

from traitlets.config import Config
from notebook.services.contents.checkpoints import (
    Checkpoints,
    GenericCheckpointsMixin
)
from notebook.services.contents.filemanager import FileContentsManager
from notebook.services.contents.filecheckpoints import (
    GenericFileCheckpoints
)
from notebook.services.contents.manager import ContentsManager
from notebook.base.handlers import AuthenticatedFileHandler
#from notebook.services.contents.tests.test_manager import (
#    TestContentsManager
#)
#from notebook.services.contents.tests.test_contents_api import (
#    APITest
#)
#from notebook.tests.launchnotebook import assert_http_error
from notebook.utils import to_os_path
from nbformat import from_dict, reads, writes
from nbformat.v4.nbbase import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_raw_cell,
)
from nbformat.v4.rwbase import strip_transient
from traitlets import (
    Any,
    Bool,
    Dict,
    Instance,
    Integer,
    HasTraits,
    Unicode,
)


__all__ = [
    'APITest',
    'Any',
    'assert_http_error',
    'Bool',
    'Checkpoints',
    'Config',
    'ContentsManager',
    'Dict',
    'AuthenticatedFileHandler',
    'FileContentsManager',
    'GenericCheckpointsMixin',
    'GenericFileCheckpoints',
    'HasTraits',
    'Instance',
    'Integer',
    'TestContentsManager',
    'Unicode',
    'from_dict',
    'new_code_cell',
    'new_markdown_cell',
    'new_notebook',
    'new_raw_cell',
    'reads',
    'strip_transient',
    'to_os_path',
    'writes',
]
