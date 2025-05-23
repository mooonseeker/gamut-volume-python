"""
Take the RGB/3D color space coordinate data as input and return the gamut volume in delta E3.
"""

from typing import Tuple

import numpy as np

import cgats


def make_tesselation(gsv: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a tessellation of a 3D grid surface for gamut volume calculation."""

    N = len(gsv)

    # Build the reference RGB table
    J, K = np.meshgrid(gsv, gsv)
    J = J.flatten()
    K = K.flatten()
    Lower = np.zeros_like(J) + gsv[0]
    Upper = np.zeros_like(J) + gsv[-1]

    # On the bottom surface the order must be rotations of Lower,J,K
    # On the top surface the order must be rotations of Upper,K,J
    RGB_ref = np.vstack(
        [
            np.column_stack((Lower, J, K)),
            np.column_stack((K, Lower, J)),
            np.column_stack((J, K, Lower)),
            np.column_stack((Upper, K, J)),
            np.column_stack((J, Upper, K)),
            np.column_stack((K, J, Upper)),
        ]
    )

    # Build the required tessellation
    TRI_ref = np.zeros((12 * (N - 1) ** 2, 3), dtype=int)
    idx = 0
    for s in range(6):
        for q in range(N - 1):
            for p in range(N - 1):
                m = N**2 * s + N * q + p
                # The two triangles must have the same rotation
                # consider A B  triangle 1 = A-B-C
                #         C D  triangle 2 = B-D-C
                # both are clockwise
                TRI_ref[idx] = [m, m + N, m + 1]
                TRI_ref[idx + 1] = [m + N, m + N + 1, m + 1]
                idx += 2

    return TRI_ref, RGB_ref


def map_rows(ref: np.ndarray, targ: np.ndarray) -> np.ndarray:
    """Map the rows of a reference matrix to a target matrix."""

    mapping = np.zeros((ref.shape[0],), dtype=int)
    for m in range(ref.shape[0]):
        # Use np.all and np.where to find matching rows
        IX = np.where(np.all(targ == ref[m, :], axis=1))[0]
        if IX.size > 0:
            mapping[m] = IX[0]
        else:
            mapping[m] = -1
    return mapping


def get_d_C(cgats: dict, Lsteps: int, hsteps: int) -> Tuple[list, list, np.ndarray]:
    """Subprocess of gamut volume calculation."""

    # Check the data format
    fmt = cgats["fmt"]
    if fmt[1] != "RGB_R" or fmt[4] == "XYZ_X":
        raise ValueError("Invaild CGATS data file.")

    # Get the standard tesselation
    RGB = np.array([cgats["RGB_R"], cgats["RGB_G"], cgats["RGB_B"]]).T
    TRI_ref, RGB_ref = make_tesselation(np.unique(RGB))
    # Make a LUT which maps rows in RGB_ref to rows in RGB
    mapping = map_rows(RGB_ref, RGB)
    # Get the standard tesselation referencing rows of RGB instead of RGB_ref
    TRI = mapping[TRI_ref]
    # Get the 3D color space coordinate data, note that the order is a*/b*/L*
    LAB = np.array([cgats[fmt[5]], cgats[fmt[6]], cgats[fmt[4]]]).T

    # Find the minmum and maxmum L* in each triangle
    # Get a matrix of all L values of all TRI vertices
    TRI_L = np.reshape(LAB[TRI, 2], TRI.shape)
    # Then get the max and min
    Max_L = np.max(TRI_L, axis=1)
    Min_L = np.min(TRI_L, axis=1)

    # Define L* and Hue of ray vector boundaries
    L = np.linspace(0, 100, Lsteps + 1)
    Hue = np.linspace(0, 2 * np.pi, hsteps + 1)
    # Note that rays will be defined at the mid-points of these boundaries

    # Initiate the output lists
    d = [[None] * hsteps for _ in range(Lsteps)]
    C = [[None] * hsteps for _ in range(Lsteps)]
    volmap = np.zeros((Lsteps, hsteps), dtype=float)

    # For every step in L*
    for iL in range(Lsteps):
        # The the ray L*, which is the mid-point
        Lmid = (L[iL] + L[iL + 1]) / 2
        # Set the ray origin
        orig = np.array([0, 0, Lmid])

        # Get a list of all tiles which lie at all within the L* boundaries
        IX = np.where((Lmid >= Min_L) & (Lmid <= Max_L))[0]

        # Repeat the origin for element-wise calculations
        orig = np.tile(orig, (len(IX), 1))
        # Get vectors to each vertex of each tile
        vert0 = LAB[TRI[IX, 0], :]
        vert1 = LAB[TRI[IX, 1], :]
        vert2 = LAB[TRI[IX, 2], :]

        # Find vectors for two edges sharing vert0 of each tile
        edge1 = vert1 - vert0
        edge2 = vert2 - vert0
        # and the vector to the origin of each tile
        o = orig - vert0
        # Pre-calculate the cross products outside the inner loop
        e2e1 = np.cross(edge2, edge1)
        e2o = np.cross(edge2, o)
        oe1 = np.cross(o, edge1)
        # and the one determinant which does not involve 'dir'
        e2oe1 = np.sum(edge2 * oe1, axis=1, keepdims=True)  # keepdims is important!
        # Drop the L* coordinate as the 'dir' vector always has dL*=0
        e2e1 = e2e1[:, :-1]
        e2o = e2o[:, :-1]
        oe1 = oe1[:, :-1]

        # For every step in Hue
        for iHue in range(hsteps):
            # The unit vector represented by L* and Hue (just the da*,db* terms)
            Hmid = (Hue[iHue] + Hue[iHue + 1]) / 2
            # Define dir in shape=(2,1)
            dir = np.array([[np.sin(Hmid)], [np.cos(Hmid)]])

            idet = 1.0 / np.dot(e2e1, dir)  # denominator for all calculations
            u = np.dot(e2o, dir) * idet  # 1st barycentric coordinate
            v = np.dot(oe1, dir) * idet  # 2nd barycentric coordinate
            t = e2oe1 * idet  # 'position on the line' coordinate

            # Find the tiles for which the ray passes within their edges
            # The triangle perimiter is defined by edges u=0, v=0 and u+v=1
            # plus the addition of a tolerance to deal with round-off errors
            ix = (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0)
            # If no tile was found, add some tolerance and try again.
            if np.sum(ix) == 0:
                ix = (u >= -0.001) & (v >= -0.001) & (u + v <= 1.001) & (t >= 0)
            # calculate and store the d and C* values for each intersection (if any)
            d[iL][iHue] = -np.sign(idet[ix])
            C[iL][iHue] = t[ix]
            volmap[iL][iHue] = np.sum(-np.sign(idet[ix]) * t[ix] ** 2)

    return d, C, volmap


def get_volume(filename: str) -> float:
    """Calculate the gamut volume."""

    # Read the CGATS file
    input_data = cgats.readCGATS(filename)

    # Calculate the d and C* values for the given L* and h* steps
    h_steps = 360
    L_steps = 100
    _, _, volmap = get_d_C(input_data, L_steps, h_steps)

    # Calculate the scaled sum for each L* and h* step
    # applying the scaling factor AFTER summing rather than before per-element
    # sum the values and correct the scaling
    V = np.sum(volmap) * 100 * np.pi / (L_steps * h_steps)
    return V


def coverage(file: str, ref_file: str) -> Tuple[float, float]:
    """Calculate the intersection and coverage of gamut volume."""

    # Read the CGATS files
    color_data = cgats.readCGATS(file)
    color_ref = cgats.readCGATS(ref_file)

    # Calculate the volume maps for each color set and the intersection
    _, _, volmap = get_d_C(color_data, 100, 360)
    _, _, volmap_ref = get_d_C(color_ref, 100, 360)
    volmap_coverage = np.minimum(volmap, volmap_ref)

    # Fix the scaling of the volume maps
    dH = 2 * np.pi / 360
    volmap_coverage = volmap_coverage * dH / 2
    volmap_ref = volmap_ref * dH / 2

    # Calculate the volume of the intersection and the coverage ratio
    vol_coverage = np.sum(volmap_coverage)
    vol_ref = np.sum(volmap_ref)
    coverage_ratio = vol_coverage / vol_ref

    return vol_coverage, coverage_ratio
