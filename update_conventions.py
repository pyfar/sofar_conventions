import os
import glob
import json
import requests
from bs4 import BeautifulSoup


def update_conventions(conventions_path=None, assume_yes=False):
    """
    Update SOFA conventions.

    SOFA convention define what data is stored in a SOFA file and how it is
    stored. Updating makes sure that sofar is using the latest conventions.
    This is done in three steps

    1.
        Download official SOFA conventions as csv files from
        https://github.com/sofacoustics/SOFAtoolbox/tree/master/SOFAtoolbox/conventions.
    2.
        Convert csv files to json files to be read by sofar.
    3.
        Notify which conventions were newly added or updated.

    The csv and json files are stored at sofar/conventions. Sofar works only on
    the json files. To get a list of all currently available SOFA conventions
    and their paths see :py:func:`~sofar.list_conventions`.

    .. note::
        If the official convention contain errors, calling this function might
        break sofar. If this is the case sofar must be re-installed, e.g., by
        running ``pip install --force-reinstall sofar``. Be sure that you want
        to do this.

    Parameters
    ----------
    conventions_path : str, optional
        Path to the folder where the conventions are saved. The default is
        ``None``, which saves the conventions inside the sofar package.
        Conventions saved under a different path can not be used by sofar. This
        parameter was added mostly for testing and debugging.
    response : bool, optional

        ``True``
            Updating the conventions must be confirmed by typing "y".
        ``False``
            The conventions are updated without confirmation.

        The default is ``True``
    """

    if not assume_yes:
        # these lines were only tested manually. I was too lazy to write a test
        # coping with keyboard input
        print(("Are you sure that you want to update the conventions? "
               "Read the documentation before continuing. "
               "If updateing breaks sofar it has to be re-installed"
               "(y/n)"))
        response = input()
        if response != "y":
            print("Updating the conventions was canceled.")
            return

    # url for parsing and downloading the convention files
    url = ("https://github.com/sofacoustics/SOFAtoolbox/tree/master/"
           "SOFAtoolbox/conventions")
    url_raw = ("https://raw.githubusercontent.com/sofacoustics/SOFAtoolbox/"
               "master/SOFAtoolbox/conventions")
    ext = 'csv'

    print(f"Reading SOFA conventions from {url} ...")

    # get file names of conventions from the SOFA Matlab/Octave API
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    conventions = [os.path.split(node.get('href'))[1]
                   for node in soup.find_all('a')
                   if node.get('href').endswith(ext)]

    # directory handling
    if conventions_path is None:
        conventions_path = os.path.dirname(__file__)
    if not os.path.isdir(os.path.join(conventions_path, "source")):
        os.mkdir(os.path.join(conventions_path, "source"))
    if not os.path.isdir(os.path.join(conventions_path, "json")):
        os.mkdir(os.path.join(conventions_path, "json"))

    # Loop and download conventions if they changed
    updated = False
    for convention in conventions:

        # exclude these conventions
        if convention.startswith(("General_", "GeneralString_")):
            continue

        filename_csv = os.path.join(conventions_path, "source", convention)

        # download SOFA convention definitions to package diretory
        data = requests.get(url_raw + "/" + convention)
        # remove trailing tabs
        data = data.content.replace(b"\t\n", b"\n").replace(b"\r\n", b"\n")

        # check if convention needs to be added or updated
        update = False
        if not os.path.isfile(filename_csv):
            update = True
            updated = f"- added new convention: {convention}"
        else:
            with open(filename_csv, "rb") as file:
                data_current = b"".join(file.readlines())
                data_current = data_current.replace(b"\r\n", b"\n")
            if data_current != data:
                update = True
                updated = f"- updated existing convention: {convention}"

        # update convention
        if update:
            with open(filename_csv, "wb") as file:
                file.write(data)
            print(updated)

    # compile json files from csv file
    # (this is also done if nothing changed. It won't affect the content of
    #  the json files but the time-stamp will be updated)
    _compile_conventions(conventions_path)

    if updated:
        print("... done.")
    else:
        print("... conventions already up to date.")


def _compile_conventions(conventions_path=None):
    """
    Compile SOFA conventions (json files) from source conventions (csv files
    from SOFA SOFAtoolbox), i.e., only do step 2 from `update_conventions`.
    This is a helper function for debugging and developing and might break
    sofar.

    Parameters
    ----------
    conventions_path : str
        Path to the folder containing the conventions as json files (might be
        empty) and the source convention as csv files in the subfolder `source`
        (must not be empty). The default is ``None``, which uses the
        default location inside the sofar package.
    """
    # directory handling
    if conventions_path is None:
        conventions_path = os.path.join(os.path.dirname(__file__),
                                        "conventions")
    if not os.path.isdir(os.path.join(conventions_path, "source")):
        raise ValueError("conventions_path must contain the folder 'source'")

    # get list of source conventions
    csv_files = glob.glob(os.path.join(
        conventions_path, "source", "*.csv"))
    csv_files = [os.path.split(csv_file)[1] for csv_file in csv_files]

    for csv_file in csv_files:

        # directories for reading and writing
        json_file = os.path.join(
            conventions_path, "json", csv_file[:-3] + "json")
        csv_file = os.path.join(conventions_path, "source", csv_file)

        # convert SOFA conventions from csv to json
        convention_dict = _convention_csv2dict(csv_file)
        with open(json_file, 'w') as file:
            json.dump(convention_dict, file, indent=4)


def _convention_csv2dict(file: str):
    """
    Read a SOFA convention as csv file from the official Matlab/Octave API for
    SOFA (SOFAtoolbox) and convert them to a Python dictionary. The dictionary
    can be written for example to a json file using

    import json

    with open(filename, 'w') as file:
        json.dump(dictionary, file, indent=4)

    Parameters
    ----------
    file : str
        filename of the SOFA convention

    Returns
    -------
    convention : dict
        SOFA convention as nested dictionary. Each attribute is a sub
        dictionary with the keys `default`, `flags`, `dimensions`, `type`, and
        `comment`.
    """

    # read the file
    # (encoding should be changed to utf-8 after the SOFA conventions repo is
    # clean.)
    # TODO: add explicit test for this function that checks the output
    with open(file, 'r', encoding="windows-1252") as fid:
        lines = fid.readlines()

    # write into dict
    convention = {}
    for idl, line in enumerate(lines):

        try:
            # separate by tabs
            line = line.strip().split("\t")
            # parse the line entry by entry
            for idc, cell in enumerate(line):
                # detect empty cells and leading trailing white spaces
                cell = None if cell.replace(' ', '') == '' else cell.strip()
                # nothing to do for empty cells
                if cell is None:
                    line[idc] = cell
                    continue
                # parse text cells that do not contain arrays
                if cell[0] != '[':
                    # check for numbers
                    try:
                        cell = float(cell) if '.' in cell else int(cell)
                    except ValueError:
                        pass

                    line[idc] = cell
                    continue

                # parse array cell
                # remove brackets
                cell = cell[1:-1]

                if ';' not in cell:
                    # get rid of white spaces
                    cell = cell.strip()
                    cell = cell.replace(' ', ',')
                    cell = cell.replace(' ', '')
                    # create flat list of integers and floats
                    numbers = cell.split(',')
                    cell = [float(n) if '.' in n else int(n) for n in numbers]
                else:
                    # create a nested list of integers and floats
                    # separate multidimensional arrays
                    cell = cell.split(';')
                    cell_nd = [None] * len(cell)
                    for idx, cc in enumerate(cell):
                        # get rid of white spaces
                        cc = cc.strip()
                        cc = cc.replace(' ', ',')
                        cc = cc.replace(' ', '')
                        numbers = cc.split(',')
                        cell_nd[idx] = [float(n) if '.' in n else int(n)
                                        for n in numbers]

                    cell = cell_nd

                # write parsed cell to line
                line[idc] = cell

            # first line contains field names
            if idl == 0:
                fields = line[1:]
                continue

            # add blank comment if it does not exist
            if len(line) == 5:
                line.append("")
            # convert empty defaults from None to ""
            if line[1] is None:
                line[1] = ""

            # make sure some unusual default values are converted for json
            if line[1] == "permute([0 0 0 1 0 0; 0 0 0 1 0 0], [3 1 2]);":
                # Field Data.SOS in SimpleFreeFieldHRSOS and SimpleFreeFieldSOS
                line[1] = [[[0, 0, 0, 1, 0, 0], [0, 0, 0, 1, 0, 0]]]
            if line[1] == "permute([0 0 0 1 0 0], [3 1 2]);":
                # Field Data.SOS in GeneralSOS
                line[1] = [[[0, 0, 0, 1, 0, 0]]]
            if line[1] == "{''}":
                line[1] = ['']
            # convert versions to strings
            if "Version" in line[0] and not isinstance(line[1], str):
                line[1] = str(float(line[1]))

            # write second to last line
            convention[line[0]] = {}
            for ff, field in enumerate(fields):
                convention[line[0]][field.lower()] = line[ff + 1]

        except: # noqa
            raise ValueError((f"Failed to parse line {idl}, entry {idc} in: "
                              f"{file}: \n{line}\n"))

    # reorder the fields to be nicer to read and understand
    # 1. Move everything to the end that is not GLOBAL
    keys = [key for key in convention.keys()]
    for key in keys:
        if "GLOBAL" not in key:
            convention[key] = convention.pop(key)
    # 1. Move Data entries to the end
    for key in keys:
        if key.startswith("Data"):
            convention[key] = convention.pop(key)

    return convention
