from .geometry.geometry import compute_geometry
from .aerodynamics.aerodynamics import compute_aerodynamics
from .mass.mass import compute_mass
from .performance.performance import compute_performance
from .update_mtow.update_mtow import update_mtow


def mtow_and_fuel_loop(
    mtow, aspect_ratio, wing_loading, cruise_altitude, cruise_speed, mission_range, payload, tsfc
):
    """
    Gather all the module main functions in the program main function that will compute a new MTOW
    based on an old MTOW

    :param mtow: Old Max Take-Off Weight, in kg
    :param wing_loading: Wing loading, in kg/m2
    :param aspect_ratio: Wing aspect ratio, no unit
    :param cruise_speed: Cruise speed, in m/s
    :param cruise_altitude: Cruise altitude, in m
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s

    :return updated_mtow: Max Take-Off Weight computed based on the old value
    """

    # Let's start by computing the aircraft geometry
    wing_area = compute_geometry(mtow=mtow, wing_loading=wing_loading)

    # Let's now compute its aerodynamics properties
    l_d = compute_aerodynamics(
        cruise_altitude=cruise_altitude,
        cruise_speed=cruise_speed,
        mtow=mtow,
        wing_area=wing_area,
        aspect_ratio=aspect_ratio,
    )

    # We can now compute its structural mass
    owe = compute_mass(mtow=mtow, wing_area=wing_area, aspect_ratio=aspect_ratio)

    # Let's now get the mission performances
    mission_fuel = compute_performance(
        owe=owe,
        payload=payload,
        mission_range=mission_range,
        tsfc=tsfc,
        l_d=l_d,
        cruise_speed=cruise_speed,
    )

    # Finally, let's compute the new mtow
    updated_mtow = update_mtow(
        owe=owe,
        payload=payload,
        mission_fuel=mission_fuel,
    )

    return updated_mtow, mission_fuel
