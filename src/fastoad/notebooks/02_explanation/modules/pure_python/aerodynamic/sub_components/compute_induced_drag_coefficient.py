import numpy as np


def compute_k(aspect_ratio):
    """
    Computes the induced drag coefficient based on the aspect ratio

    :param aspect_ratio: Wing aspect ratio, no unit

    :return k: induced drag coefficient, no unit
    """

    # Computation of the Oswald efficiency factor
    e = 1.78 * (1.0 - 0.045 * aspect_ratio ** 0.68) - 0.64

    # Computation of the lift induced drag coefficient
    k = 1.0 / (np.pi * aspect_ratio * e)

    return k
