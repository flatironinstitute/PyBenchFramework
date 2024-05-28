import os,sys
import pathlib

def ensure_log_directory_exists(directory, createdir):
    if not os.path.exists(directory):
        if createdir == 1:
            os.makedirs(directory)
