from .sub_components.compute_wing_area import compute_wing_area


def compute_geometry(mtow, wing_loading):
    """
    Gather all the geometry sub-functions in the main function

    :param mtow: Max Take-Off Weight, in kg
    :param wing_loading: Wing loading, in kg/m2

    :return wing_area: Wing area, in m2
    """

    wing_area = compute_wing_area(mtow=mtow, wing_loading=wing_loading)

    return wing_area
