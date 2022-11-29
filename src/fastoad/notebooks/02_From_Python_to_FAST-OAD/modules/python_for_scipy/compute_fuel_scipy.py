from ..pure_python.geometry.geometry import compute_geometry
from ..pure_python.aerodynamics.aerodynamics import compute_aerodynamics
from ..pure_python.mass.mass import compute_mass
from ..pure_python.performance.performance import compute_fuel_mission


def compute_fuel_scipy(
    x, wing_loading, cruise_altitude, cruise_speed, mission_range, payload, tsfc
):
    """
    Gather all the module main functions in the program main function that will compute the fuel consumed for the given
    MTOW

    :param x: Tuple containing the Old Max Take-Off Weight, in kg and the aspect ration with no unit
    :param wing_loading: Wing loading, in kg/m2
    :param cruise_speed: Cruise speed, in m/s
    :param cruise_altitude: Cruise altitude, in m
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s

    :return fuel_mission: Max Take-Off Weight computed based on the old value
    """

    # Let's unpack the tuple containing the two values that will be used for the optimization
    mtow = x[0]
    aspect_ratio = x[1]

    # Let's start by computing the aircraft geometry
    wing_area = compute_geometry(mtow=mtow, wing_loading=wing_loading)

    # Let's now compute its aerodynamic properties
    l_d = compute_aerodynamics(
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
