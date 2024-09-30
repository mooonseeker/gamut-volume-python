import numpy as np
import cgats
import get_volume


def coverage(file, ref_file):
    color_data = cgats.readCGATS(file)
    color_ref = cgats.readCGATS(ref_file)

    _, _, volmap = get_volume.get_d_C(color_data, 100, 360)
    _, _, volmap_ref = get_volume.get_d_C(color_ref, 100, 360)
    volmap_coverage = np.minimum(volmap, volmap_ref)

    dH = 2 * np.pi / 360
    volmap_coverage = volmap_coverage * dH / 2
    volmap_ref = volmap_ref * dH / 2

    vol_coverage = np.sum(volmap_coverage)
    vol_ref = np.sum(volmap_ref)
    coverage_ratio = vol_coverage / vol_ref

    return vol_coverage, coverage_ratio


# TODO: Implementation based on code from IDMS isn't available
# def intersect_d_Cs(d1, C1, d2, C2):
#     results = [
#         intersect(d1_elem, C1_elem, d2_elem, C2_elem)
#         for d1_elem, C1_elem, d2_elem, C2_elem in zip(d1, C1, d2, C2)
#     ]
#     # Unzip results safely
#     di, Ci = zip(*results) if results else ([], [])
#     return list(di), list(Ci)


# def intersect(d1, C1, d2, C2):
#     # Concatenate all d and C values
#     di = np.concatenate((d1, d2))
#     Ci = np.concatenate((C1, C2))
#     # Prepare dt for tracking inside/outside
#     dt = np.block([[d1, np.zeros_like(d1)], [np.zeros_like(d2), d2]])
#     # Get the indices of descending sorted C values
#     sorted_indices = np.argsort(Ci)[::-1]
#     # Cumulative sum to determine inside/outside
#     t = np.min(np.cumsum(dt[sorted_indices, :], axis=1), axis=1)
#     # Calculate indices to keep
#     unique_indices = np.where(np.diff(t, prepend=np.nan) != 0)[0]
#     di = di[unique_indices]
#     Ci = Ci[unique_indices]
#     return di, Ci
