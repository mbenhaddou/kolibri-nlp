import os
from pathlib import Path
import sys

#import click
import dropbox
#import pyperclip


DROPBOX_ACCESS_TOKEN = "sl.Ar1Pz1fHD4J_Iaav5BO4oO-3C5r3AQIBbjeF7mkd5F6X_0wWwhFVGdyrJatbgOt9eN-F6cJdCbkfo1pChSKTRDJcyxGGDn2C3EDNMp50b3B0AR8eLDIvPf2zJp6cKhUNHyyopRI8T2A"
DROPBOX_ROOT_PATH = "/Users/mohamedmentis/Dropbox"
LB = '\n'





def share_file(filepath):
    try:
        shared_link = get_client().sharing_create_shared_link(filepath)
    except dropbox.exceptions.ApiError as e:
        raise Exception('There was a problem with the path.')
    else:
        return shared_link.url


def get_relative_path(filepath):
    DROPBOX_ROOT = Path(DROPBOX_ROOT_PATH).expanduser()

    if '/' not in filepath:
        filepath = f'/{filepath}'

    elif not filepath.startswith('/') and not filepath.startswith('~'):
        *path_parts, filename = filepath.split('/')
        relevant_path_parts = []
        for path_part in path_parts:
            if path_part not in DROPBOX_ROOT_PATH:
                relevant_path_parts.append(path_part)
        filepath = os.path.join(*relevant_path_parts, f'/{filename}')

    filepath_expanded_user = Path(filepath).expanduser()

    path = Path(str(filepath_expanded_user).replace(str(DROPBOX_ROOT), ''))

    return str(path)


def check_for_valid_access_token():
    if not DROPBOX_ACCESS_TOKEN:
        raise Exception(
            'Please get an access token here and store it in an environment '
            'variable called "DROPBOX_ACCESS_TOKEN": '
            ' https://www.dropbox.com/developers/apps')
    try:
        dbx = get_client()
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError as e:
        raise Exception(str(e))


def check_for_env_vars():
    check_for_valid_access_token()
    check_for_dropbox_root_path()


def check_for_dropbox_root_path():
    if not DROPBOX_ROOT_PATH:
        raise Exception(
            'Please create an environment variable called "DROPBOX_ROOT_PATH" '
            'with the path to your computer\'s root Dropbox folder.')
    if not Path(DROPBOX_ROOT_PATH).exists:
        raise Exception(f'{DROPBOX_ROOT_PATH} doesn\'t exist!')


def get_client():
    return dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)



share_file('/Users/mohamedmentis/Dropbox/kolibri_data/contractions')