"""
Read from and write to a CGATS data file.

This module provides functions for reading and writing data
in the CGATS (Committee for Graphic Arts Technologies Standards) format.

"""

import numpy as np


def readCGATS(filename):
    """Read a CGATS data file and return a CGATS dict."""

    # Read all lines of the file to a list
    with open(filename, "r") as data_file:
        lines = data_file.readlines()

    # Check the version number - must be in the first line of the file
    ver = int(lines[0].strip().split(".")[1])
    if ver < 17:
        raise ValueError("Unsupported file format.")

    # Find important headers
    bdf = lines.index("BEGIN_DATA_FORMAT\n")
    edf = lines.index("END_DATA_FORMAT\n")
    bd = lines.index("BEGIN_DATA\n")
    ed = lines.index("END_DATA\n")
    nos = [i for i, line in enumerate(lines) if "NUMBER_OF_SETS" in line]
    if any(x is None for x in [bdf, edf, bd, ed, nos]):
        raise ValueError("Invalid CGATS file.")

    # Get the data set count and check it against the data rows in the file
    N = int(lines[nos[0]].strip().split()[1])
    if ed - bd - 1 != N:
        raise ValueError("NUMBER_OF_SETS does not match the data count.")

    # Get all format strings
    fmt = lines[bdf + 1 : edf]
    fmt = [f.strip().split() for f in fmt]  # Split each line by whitespace
    fmt = [item for sublist in fmt for item in sublist]  # Flatten the list

    # Read data into a matrix
    data = []
    for n in range(N):
        data.append([float(x) for x in lines[bd + n + 1].split()])

    # Build the cgats dictionary
    cgats = {"fmt": fmt}
    for i, f in enumerate(fmt):
        cgats[f] = [row[i] for row in data]

    # Store headers
    hdrs = list(range(0, bdf)) + list(range(edf + 1, bd))
    cgats["headers"] = [lines[i] for i in hdrs if i not in nos]

    return cgats


def writeCGATS(cgats, filename):
    """Take a CGATS dict and write a CGATS data file."""

    with open(filename, "w") as f:
        # Write out the headers
        for header in cgats["headers"]:
            f.write(f"{header}")

        # Write out the data format
        f.write("BEGIN_DATA_FORMAT\n")
        f.write(" ".join(cgats["fmt"]) + "\n")
        f.write("END_DATA_FORMAT\n")

        # Build a data array from the format names and their properties in cgats
        data = np.column_stack([cgats[fmt] for fmt in cgats["fmt"]])

        # Write out the set count then all of the data
        f.write(f"NUMBER_OF_SETS {data.shape[0]}\n")
        f.write("BEGIN_DATA\n")
        np.savetxt(f, data, fmt="%g")
        f.write("END_DATA\n")
