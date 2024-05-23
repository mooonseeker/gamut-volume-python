import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import cgats
import get_volume


def plot_rings(file, ref_file=None):
    # Read the CGATS files
    color_data = cgats.readCGATS(file)

    # Calculate the d and C* values for the given L* and h* steps
    Lsteps = 100
    hsteps = 360
    _, _, volmap = get_volume.get_d_C(color_data, Lsteps, hsteps)
    x, y, _, vol = calc_rings(volmap)

    # Plot the figure
    x_selected = x[9::10, :]
    x_closed = np.hstack((x_selected, x_selected[:, [0]])).T
    y_selected = y[9::10, :]
    y_closed = np.hstack((y_selected, y_selected[:, [0]])).T
    plt.plot(x_closed, y_closed, "k")

    # Add labels for L* 10, 50 and 100
    for n in [10, 50, 100]:
        plt.text(x[n - 1, -1], y[n - 1, -1], f"L*={n}", color=[0.5, 0.3, 0])

    # Add a central marker
    plt.plot(0, 0, "+", markersize=20)

    # If a reference is supplied, add a dotted outline
    if ref_file is not None:
        ref_cgats = cgats.readCGATS(ref_file)
        _, _, volmap_ref = get_volume.get_d_C(ref_cgats, Lsteps, hsteps)
        x, y, _, _ = calc_rings(volmap_ref)
        x = np.hstack((x[-1, :], x[-1, 0]))
        y = np.hstack((y[-1, :], y[-1, 0]))
        plt.plot(x.T, y.T, "--k")

    # Add a little padding to the axis range
    plt.axis(np.array(plt.axis()) * 1.05)

    # Make the axes equal
    plt.axis("equal")

    # Add the title
    title = "CIELab gamut rings\nVolume = {}".format(vol)
    plt.title(title)

    # Add the axis labels
    plt.xlabel("a*_{RSS}")
    plt.ylabel("b*_{RSS}")

    plt.show()


def calc_rings(volmap):
    Lsteps = volmap.shape[0]
    hsteps = volmap.shape[1]
    dH = 2 * np.pi / hsteps
    dL = 100 / Lsteps

    # Get the map of the volume in cylindrical coordinates
    volmap = volmap * dL * dH / 2
    # Get the accumulated volume sum (the final cols will be the total)
    # and calculate the radius required to represent that volume
    rings = (2 * np.cumsum(volmap, axis=0) / dH) ** 0.5

    # Plot against the mid-point of the angle ranges
    midH = np.arange(dH / 2, 2 * np.pi, dH)
    # Calculate x and y using broadcasting
    x = np.sin(midH).reshape(1, hsteps) * rings
    y = np.cos(midH).reshape(1, hsteps) * rings
    vol = np.sum(volmap)
    return x, y, rings, vol
