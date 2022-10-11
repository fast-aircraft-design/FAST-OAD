import scipy.constants as sc


def compute_wing_mass(mtow, aspect_ratio, wing_area):
    """
    Computes the wing mass based on the MTOW, its area and aspect ratio

    :param wing_area: Wing area, in m2
    :param aspect_ratio: Wing aspect ratio, no unit
    :param mtow: Max Take-Off Weight, in kg

    :return wing mass: the wing_mass, in kg
    """

    # Let's start by converting the quantities in imperial units
    mtow_lbm = mtow / sc.lb
    wing_area_ft2 = wing_area / sc.foot ** 2.0

    # Let's now apply the formula
    wing_mass_lbm = (
        96.948
        * (
            (5.7 * mtow_lbm / 1.0e5) ** 0.65
            * aspect_ratio ** 0.57
            * (wing_area_ft2 / 100.0) ** 0.61
            * 2.5
        )
        ** 0.993
    )

    # Converting wing mass in kg
    wing_mass = wing_mass_lbm * sc.lb

    return wing_mass
