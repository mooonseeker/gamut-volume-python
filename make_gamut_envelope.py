import numpy as np
import colour
import cgats


def make_gamut_envelope(input_file, output_file):
    color_data = cgats.readCGATS(input_file)

    # Build the XYZ and RGB arrays
    XYZ = color_data[["XYZ_X", "XYZ_Y", "XYZ_Z"]].values
    RGB = color_data[["RGB_R", "RGB_G", "RGB_B"]].values

    # Find the reference max RGB
    RGBmax = np.max(RGB)
    # Find the white point
    XYZn = XYZ[np.all(RGB == RGBmax, axis=1)][0]

    # Get a D50 white point of equivalent luminance
    D50 = np.array([0.9642, 1, 0.8249]) * XYZn[1]

    # Chromatically adapt CIE XYZ to D50 using CIECAM02 CAT
    XYZ_adapted = colour.adaptation.chromatic_adaptation(
        XYZ, XYZn, D50, transform="Bradford"
    )

    # Calculate CIELAB
    CIELAB = colour.XYZ_to_Lab(XYZ_adapted, illuminant=D50)

    # Assign the LAB values to the appropriate property
    color_data["LAB_L"] = CIELAB[:, 0]
    color_data["LAB_A"] = CIELAB[:, 1]
    color_data["LAB_B"] = CIELAB[:, 2]

    # Change the list of values to output - excluding XYZ, including LAB
    if "SampleID" in color_data.columns:
        fmt_cols = ["SampleID", "RGB_R", "RGB_G", "RGB_B", "LAB_L", "LAB_A", "LAB_B"]
    else:
        fmt_cols = ["RGB_R", "RGB_G", "RGB_B", "LAB_L", "LAB_A", "LAB_B"]

    color_data = color_data[fmt_cols]
    cgats.writeCGATS(color_data, output_file)
    return CIELAB
