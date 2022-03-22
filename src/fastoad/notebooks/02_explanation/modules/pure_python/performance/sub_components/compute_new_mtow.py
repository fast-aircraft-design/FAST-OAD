def compute_new_mtow(owe, payload, mission_fuel):
    """
    Computes the fuel new mtow based on the mission fuel and structural weight from previous iteration

    :param owe: the structural mass, in kg
    :param payload: the payload mass, in kg
    :param mission_fuel: the fuel consumed during the designated mission, in kg

    return mtow_new: the new Maximum Take-Off Weight based on the current iteration's computation, in kg
    """

    # Let's simply add the weight we computed
    mtow_new = owe + payload + mission_fuel

    return mtow_new
