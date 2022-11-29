from .sub_components.compute_profile_drag import compute_cd0
from .sub_components.compute_induced_drag_coefficient import compute_k
from .sub_components.compute_lift_to_drag_ratio import compute_l_d


def compute_aerodynamics(cruise_altitude, cruise_speed, mtow, wing_area, aspect_ratio):
    """
    Gather all the aerodynamics sub-functions in the main function

    :param cruise_altitude: Cruise altitude, in m
    :param cruise_speed: Cruise speed, in m/s
    :param mtow: Max Take-Off Weight, in kg
    :param wing_area: Wing area; in m2
    :param aspect_ratio: Wing aspect ratio, no unit

    :return wing_area: Wing area, in m2
    """

    # Let's start by computing the profile drag coefficient
    cd0 = compute_cd0(wing_area=wing_area)

    # Let's now compute the lift induced drag coefficient
    k = compute_k(aspect_ratio=aspect_ratio)

    # We can now compute the lift-to-drag ratio
    l_d = compute_l_d(
        cruise_altitude=cruise_altitude,
        cruise_speed=cruise_speed,
        cd0=cd0,
        k=k,
        mtow=mtow,
        wing_area=wing_area,
    )

    return l_d
