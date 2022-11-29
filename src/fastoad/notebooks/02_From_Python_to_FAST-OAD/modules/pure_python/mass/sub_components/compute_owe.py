import numpy as np


def compute_owe(wing_mass, mtow):
    """
    Computes the aircraft structural mass based on its MTOW and wing mass

    :param wing_mass: Wing mass, in kg
    :param mtow: Max Take-Off Weight, in kg

    :return owe: the structural mass, in kg
    """

    # Let's start by computing the weight of the aircraft without the wings
    owe_without_wing = mtow * (0.43 + 0.0066 * np.log(mtow))

    # Let's now add the wing mass to get the structural weight
    owe = owe_without_wing + wing_mass

    return owe
