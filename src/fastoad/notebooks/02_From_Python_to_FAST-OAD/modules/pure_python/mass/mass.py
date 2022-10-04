from .sub_components.compute_wing_mass import compute_wing_mass
from .sub_components.compute_owe import compute_owe


def compute_mass(mtow, wing_area, aspect_ratio):
    """
    Gather all the mass sub-functions in the main function

    :param mtow: Max Take-Off Weight, in kg
    :param wing_area: Wing area, in m2
    :param aspect_ratio: Wing aspect ratio, no unit

    :return owe: the structural mass, in kg
    """

    # Let's start by computing the wing mass
    wing_mass = compute_wing_mass(mtow=mtow, aspect_ratio=aspect_ratio, wing_area=wing_area)

    # Let's now compute the owe
    owe = compute_owe(
        wing_mass=wing_mass,
        mtow=mtow,
    )

    return owe
