import json
import os
from pathlib import Path
import json


if os.name == 'posix':
    sunless_sea_folder = os.path.join(Path.home(),
                             ".config/unity3d/Failbetter Games/Sunless Sea")
elif os.name == 'nt':
    sunless_sea_folder = os.path.join(Path.home(),
                             "AppData/LocalLow/Failbetter Games/Sunless Sea")
else: # Is a Mac
    sunless_sea_folder = os.path.join(Path.home(),
                             "Library/Caches/unity.Failbetter Games.Sunless Sea")


def FindSSFile(filename, listmode=False):
    """Find a file inside the Sunless Sea directory tree

    Walks the Sunless Sea directory in search of a file matching the supplied
    filename. If listmode is true, returns a list of files matching the supplied
    filename instead.

    Args:
        filename: a string with the file's name. Don't need to be the full
    		file's name.
    	listmode: If true, this functions returns a list of files matching the
    		filename instead of a filepath string.

    Returns:
    	A string with the absolute path for a file.
    	If no file was found, returns None,

    	If listmode is True, returns a list of files instead. Still returns
    	None if no file was found.

    """
    files = []
    for (dirpath, dirname, filenames) in os.walk(sunless_sea_folder):
        for i in filenames:
            if filename in i:
                files.append(os.path.join(dirpath, i))

    if listmode:
        if len(files) > 0:
            return files
        else:
            return None
    else:
        try:
            return files[0]
        except IndexError:
            return None

def ObjectsFromJsonFile(filename='.json'):
    """Yields objects readed from file named filename inside Sunless Sea folders

    Args:
    	filename: a string with the full or partial file's name

    Yields:
    	A python object representing each json object inside the file named
    	filename.
    """
    for filepath in FindSSFile(filename, listmode=True):
        with open(filepath, 'r') as datafile:
            rawdata = datafile.read()
            json_object = json.loads(rawdata)
            del rawdata
            try:
                for i in json_object:
                    yield i
            except TypeError:
                yield json_object