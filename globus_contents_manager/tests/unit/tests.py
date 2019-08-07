from unittest.mock import Mock
import pytest
import globus_sdk
# from .mocks import GlobusTransferTaskResponse

from . import testfuncs

class MockGlobusResponse:
    """Mimics the GlobusSDK Response object"""
    data = {}

@pytest.fixture
def mock_ls_response():
    """Mock an operation_ls response to return the following data."""
    r = MockGlobusResponse()
    r.data = {'DATA': [{'name': 'foo.txt'}, {'name': 'bar.txt'}]}
    return r

@pytest.fixture
def mock_operation_ls(monkeypatch, mock_ls_response):
    """Mock the globus_sdk directly, so anything that calls
    TransferClient.operation_ls() is mocked with a mock_ls_response. NOTE! This
    will not work for any modules that do
    'from globus_sdk import TransferClient'. This is because the module will
    import the class before we mock it."""
    mock_transfer_instance = Mock()
    mock_transfer_instance.operation_ls.return_value = mock_ls_response

    mock_transfer_class = Mock(return_value=mock_transfer_instance)

    monkeypatch.setattr(globus_sdk, 'TransferClient', mock_transfer_class)
    return mock_operation_ls

@pytest.fixture
def mock_get_transfer_client(monkeypatch, mock_ls_response):
    """Mocking the 'get_transfer_client' function"""
    mock_transfer_instance = Mock()
    mock_transfer_instance.operation_ls.return_value = mock_ls_response

    mock_get_tc = Mock(return_value=mock_transfer_instance)

    monkeypatch.setattr(testfuncs, 'get_transfer_client', mock_get_tc)
    return mock_operation_ls

def test_make_directory(mock_get_transfer_client):
    """Testing the creation of a new directory (using operation_mkdir)"""
    response_str = testfuncs.make_directory()
    assert response_str == "Success"

def test_rename(mock_get_transfer_client):
    """Testing the rename operation (operation_rename)"""
    response_str = testfuncs.rename()
    assert response_str == "Success"

def test_count_files(mock_operation_ls):
    output = testfuncs.count_files()
    assert output == 2

def test_count_files_again(mock_get_transfer_client):
    output = testfuncs.count_files()
    assert output == 2
