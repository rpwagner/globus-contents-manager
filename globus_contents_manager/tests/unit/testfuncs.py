from fair_research_login import NativeClient
import globus_sdk
import json

def get_transfer_client():
    nc = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5')
    nc.login(requested_scopes=['urn:globus:auth:scope:transfer.api.globus.org:all'])
    auth = nc.get_authorizers()['transfer.api.globus.org']
    return globus_sdk.TransferClient(authorizer=auth)
    
def make_directory():
    """Create a directory at the specified path on an endpoint filesystem."""
    transfer_client = get_transfer_client()
    try:
        transfer_client.operation_mkdir('ddb59aef-6d04-11e5-ba46-22000b92c6ec',
                                        path='~/newdir')
        return "Success"
    except globus_sdk.exc.TransferAPIError:
        print("Error occurred with the TransferAPI. Please make sure that the directory you are trying to create does not already exist.")

def rename():
    """Rename or move a file, directory, or symlink on an endpoint filesystem."""
    transfer_client = get_transfer_client()
    try:
        transfer_client.operation_rename('ddb59aef-6d04-11e5-ba46-22000b92c6ec',
                                         oldpath='~/newdir', newpath='~/renameddir')
        return "Success"
    except globus_sdk.TransferAPIError:
        print("Error occurred with the TransferAPI.")


def count_files():
    transfer_client = get_transfer_client()
    resp = transfer_client.operation_ls('ddb59aef-6d04-11e5-ba46-22000b92c6ec',
                                        path='/share/godata')
    return len(resp.data['DATA'])


if __name__ == '__main__':
    count = count_files()
    print(f'Count contains {count} files!')
    print('output successful, now try running with pytest!')

    res = make_directory()
    print(res)

    renamed = rename()
    print(renamed)