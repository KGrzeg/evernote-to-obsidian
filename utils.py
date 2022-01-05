import os
from pathlib import Path


def safe_open(path, mode):
    parent = Path(path).parent.absolute()

    try:
        os.makedirs(parent)
    except FileExistsError:
        # directory already exists
        pass

    return open(path, mode)

def create_directory(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        # directory already exists
        pass

def basename_without_ext(path):
    path, _ = os.path.splitext(path)
    return os.path.basename(path)
