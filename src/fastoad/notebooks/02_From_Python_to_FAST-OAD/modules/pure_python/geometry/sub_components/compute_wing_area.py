def compute_wing_area(mtow, wing_loading):
    """
    Computes the wing area based on the provided MTOW and wing loading

    :param mtow: Max Take-Off Weight, in kg
    :param wing_loading: Wing loading, in kg/m2

    :return wing_area: Wing area, in m2
    """

    # Computation of the wing area
    wing_area = mtow / wing_loading

    return wing_area
