import numpy as np


def make_tesselation(gsv):
    N = len(gsv)

    # Build the reference RGB table
    J, K = np.meshgrid(gsv, gsv)
    J = J.flatten()
    K = K.flatten()
    Lower = np.zeros_like(J) + gsv[0]
    Upper = np.zeros_like(J) + gsv[-1]

    # on the bottom surface the order must be rotations of Lower,J,K
    # on the top surface the order must be rotations of Upper,K,J
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
