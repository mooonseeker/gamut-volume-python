"""
Convert RGB/XYZ data to RGB/3D color space coordinate data.

This module provides:
- Generation of 3D color space coordinate data.
- Supported model: 
    - CIELAB-D65/D50: RGB/LAB
    - CAM16-UCS: RGB/Jab
    - ICtCp: RGB/ICtCp
- (independent) Bradford chromatic adaptation
- (independent) XYZ to L*a*b*

Note: If higher accuracy is required, it is still recommended to use the chromatic adaptation fucntion from colour-science.

"""

import numpy as np
import colour
import cgats


def make_gamut_envelope(input_file: str, output_file: str = None, model: str = None):
    """Convert RGB/XYZ data to RGB/3D color space coordinate data."""

    # Read the color data from the cgats file
    color_data = cgats.readCGATS(input_file)

    # Build the XYZ and RGB arrays
    RGB = np.array([color_data["RGB_R"], color_data["RGB_G"], color_data["RGB_B"]]).T
    XYZ = np.array([color_data["XYZ_X"], color_data["XYZ_Y"], color_data["XYZ_Z"]]).T
    output_fmt = ["LAB_L", "LAB_A", "LAB_B"]

    if model == "ICtCp":
        # In the ICtCp model, I represents the absolute luminance value.
        # Normalization is not required.
        CIELAB = colour.XYZ_to_ICtCp(XYZ)
        output_fmt = ["ICtCp_I", "ICtCp_Ct", "ICtCp_Cp"]
    else:
        # Find the white point at max RGB
        RGBmax = np.max(RGB, axis=0)
        if not np.all(RGBmax == RGBmax[0]):
            raise ValueError("Invalid CGATS file: white point missing.")
        XYZn = XYZ[np.all(RGB == RGBmax, axis=1)][0]
        # Normalize the XYZ/XYZn
        Lmax = XYZn[1]
        XYZ /= Lmax
        XYZn /= Lmax

        if model == "CAM16-UCS":
            # Calculate CAM16-UCS Jab
            CIELAB = colour.XYZ_to_CAM16UCS(XYZ)
            output_fmt = ["JAB_J", "JAB_A", "JAB_B"]
        elif model == "LAB-D65":
            D65_White = np.array([0.9504, 1, 1.0888])
            XYZ_adapted = colour.adaptation.chromatic_adaptation(XYZ, XYZn, D65_White)
            CIELAB = colour.XYZ_to_Lab(
                XYZ_adapted,
                colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"],
            )
        else:
            # Get a D50 white point of equivalent luminance
            D50_White = np.array([0.9642, 1, 0.8249])

            # Chromatically adapt CIE XYZ to D50 using CIECAM02 CAT
            # XYZ_adapted = colour.adaptation.chromatic_adaptation(XYZ, XYZn, D50_White)
            XYZ_adapted = chromatic_adaptation(XYZ, XYZn, D50_White)

            # Calculate CIELAB
            # CIELAB = colour.XYZ_to_Lab(XYZ_adapted,colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D50"])
            CIELAB = XYZ_to_Lab(XYZ_adapted, D50_White)

    # Assign the LAB values to the appropriate property
    color_data[output_fmt[0]] = CIELAB[:, 0]
    color_data[output_fmt[1]] = CIELAB[:, 1]
    color_data[output_fmt[2]] = CIELAB[:, 2]

    # Change the list of values to output - excluding XYZ, including LAB
    color_data["fmt"] = [
        "SampleID",
        "RGB_R",
        "RGB_G",
        "RGB_B",
        output_fmt[0],
        output_fmt[1],
        output_fmt[2],
    ]
    output_data = {
        key: value
        for key, value in color_data.items()
        if key not in ["XYZ_X", "XYZ_Y", "XYZ_Z"]
    }

    if output_file is None:
        output_file = input_file[:-7] + model + ".txt"
    cgats.writeCGATS(output_data, output_file)
    return CIELAB


def chromatic_adaptation(XYZ, XYZn, White):
    """Bradford chromatic adaptation."""

    # Bradford chromatic adaptation transform matrix
    M = np.array(
        [
            [0.8951, 0.2664, -0.1614],
            [-0.7502, 1.7135, 0.0367],
            [0.0389, -0.0685, 1.0296],
        ]
    ).T

    # Convert to new "cone" space
    RGBn = np.dot(XYZn, M)
    RGBa = np.dot(White, M)

    # Calculate corresponding colors
    A = np.diag(RGBa / RGBn)
    M_inv = np.linalg.inv(M)
    MAM = M_inv @ A @ M

    # Correct the XYZ tristimulus values
    output = np.dot(XYZ, MAM)
    return output


def XYZ_to_Lab(XYZ, XYZn):
    """Converr XYZ to L*a*b*."""

    ratio = XYZ / XYZn

    # Calculate f(X/Xn),f(Y/Yn),f(Y/Yn)
    fX = np.cbrt(ratio)
    idx = ratio <= 216 / 24389
    fX[idx] = ratio[idx] * 24389 / 3132 + 16 / 116

    # Calcultae L*, a*, b*
    Lab = np.zeros_like(XYZ)
    Lab[:, 0] = 116 * fX[:, 1] - 16
    Lab[:, 1] = 500 * (fX[:, 0] - fX[:, 1])
    Lab[:, 2] = 200 * (fX[:, 1] - fX[:, 2])
    return Lab
