from unittest.mock import Mock
import pytest
import globus_sdk
from .mocks import GlobusTransferTaskResponse


@pytest.fixture
def mock_transfer_client(monkeypatch):
    st = Mock()
    monkeypatch.setattr(globus_sdk.TransferClient, 'submit_transfer', st)
    st.return_value = GlobusTransferTaskResponse()
    monkeypatch.setattr(globus_sdk, 'TransferData', Mock())
    return st
