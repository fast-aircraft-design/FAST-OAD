def compute_wing_mass(mtow, aspect_ratio, wing_area):
    """
    Computes the wing mass based on the MTOW, its area and aspect ratio

    :param wing_area: Wing area, in m2
    :param aspect_ratio: Wing aspect ratio, no unit
    :param mtow: Max Take-Off Weight, in kg

    :return wing mass: the wing_mass, in kg
    """

    # Let's start by converting the quantities in imperial units
    mtow_lbs = mtow * 2.20462
    wing_area_ft2 = wing_area * 10.7639

    # Let's now apply the formula
    wing_mass_lbs = (
        96.948
        * (
            (5.7 * mtow_lbs / 1.0e5) ** 0.65
            * aspect_ratio ** 0.57
            * (wing_area_ft2 / 100.0) ** 0.61
            * 2.5
        )
        ** 0.993
    )

    # Converting wing mass in kg
    wing_mass = wing_mass_lbs / 2.20462

    return wing_mass
