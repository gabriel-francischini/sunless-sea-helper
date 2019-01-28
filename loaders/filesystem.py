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

    If there is more than one file named filename, files closer to the Sunless Sea
    root directory (i.e. file that aren't in deeply nested folders) will be given
    preference.

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

    files.sort(key=lambda x: sum([1 if c == '/' else 0 for c in x]))

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
    """Returns JSON objects from files matching filename inside Sunless Sea folders

    Args:
    	filename: a string with the file's name. If this is a filepath, open that
    	file, else open files whose filename matches fully or partially this string.

    Yields:
    	An iterable where each item represents each json object inside the file(s)
    	whose name matches filename.
    """
    filepaths = []
    if sunless_sea_folder in filename and os.path.isfile(filename):
        filepaths.append(filename)
    else:
        for filepath in FindSSFile(filename, listmode=True):
            filepaths.append(filepath)

    for filepath in filepaths:
        with open(filepath, 'r') as datafile:
            rawdata = datafile.read()
            json_object = json.loads(rawdata)
            del rawdata
            try:
                # Dicts are iterable, but it doesn't do what we expect
                if type(json_object) == type(dict()):
                    raise TypeError
                for i in json_object:
                    yield i
            except TypeError:
                yield json_object
