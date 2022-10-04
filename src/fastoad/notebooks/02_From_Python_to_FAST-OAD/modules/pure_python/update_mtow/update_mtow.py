def update_mtow(owe, payload, mission_fuel):
    """
    Updates the MTOW based on the structural weight computed, the payload and the fuel consumed
    during the design mission.

    :param owe: the structural mass, in kg
    :param payload: the payload mass, in kg
    :param mission_fuel: the fuel consumed during the designated mission, in kg

    return mtow_new: the new Maximum Take-Off Weight based on the current iteration's computation,
    in kg
    """

    # Let's simply add the weight we computed
    mtow_new = owe + payload + mission_fuel

    return mtow_new
