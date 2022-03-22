from .geometry.geometry import compute_geometry
from .aerodynamic.aerodynamic import compute_aerodynamic
from .mass.mass import compute_mass
from .performance.sub_components.compute_fuel_mass import compute_fuel_mission


def compute_fuel(
    mtow, aspect_ratio, wing_loading, cruise_altitude, cruise_speed, mission_range, payload, tsfc
):
    """
    Gather all the module main functions in the program main function that will compute the fuel consumed for the given
    MTOW

    :param mtow: Old Max Take-Off Weight, in kg
    :param wing_loading: Wing loading, in kg/m2
    :param aspect_ratio: Wing aspect ratio, no unit
    :param cruise_speed: Cruise speed, in m/s
    :param cruise_altitude: Cruise altitude, in m
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s

    :return fuel_mission: Max Take-Off Weight computed based on the old value
    """

    # Let's start by computing the aircraft geometry
    wing_area = compute_geometry(mtow=mtow, wing_loading=wing_loading)

    # Let's now compute its aerodynamic properties
    l_d = compute_aerodynamic(
        cruise_altitude=cruise_altitude,
        cruise_speed=cruise_speed,
        mtow=mtow,
        wing_area=wing_area,
        aspect_ratio=aspect_ratio,
    )

    # We can now compute its structural mass
    owe = compute_mass(mtow=mtow, wing_area=wing_area, aspect_ratio=aspect_ratio)

    # Let's now get the fuel consumed for the given mission
    fuel_mission = compute_fuel_mission(
        owe=owe,
        payload=payload,
        mission_range=mission_range,
        tsfc=tsfc,
        l_d=l_d,
        cruise_speed=cruise_speed,
    )

    return fuel_mission
