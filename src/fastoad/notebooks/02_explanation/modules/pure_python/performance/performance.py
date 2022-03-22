from .sub_components.compute_fuel_mass import compute_fuel_mission
from .sub_components.compute_new_mtow import compute_new_mtow


def compute_performance(owe, payload, mission_range, tsfc, l_d, cruise_speed):
    """
    Gather all the performances sub-functions in the main function

    :param owe: the structural mass, in kg
    :param payload: the payload mass, in kg
    :param mission_range: the mission range, in m
    :param tsfc: the thrust specific fuel consumption, in kg/N/s
    :param l_d: the lift-to-drag ratio in cruise conditions, no unit
    :param cruise_speed: Cruise speed, in m/s

    :return wing_area: Wing area, in m2
    """

    # Let's start by computing the fuel consumed during the mission
    mission_fuel = compute_fuel_mission(
        owe=owe,
        payload=payload,
        mission_range=mission_range,
        tsfc=tsfc,
        l_d=l_d,
        cruise_speed=cruise_speed,
    )

    # Let's now compute the new MTOW
    mtow_new = compute_new_mtow(owe=owe, payload=payload, mission_fuel=mission_fuel)

    return mtow_new
