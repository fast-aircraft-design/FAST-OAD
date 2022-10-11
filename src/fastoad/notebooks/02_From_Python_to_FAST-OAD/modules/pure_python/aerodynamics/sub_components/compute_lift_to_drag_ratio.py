import scipy.constants as sc

from fastoad.model_base.atmosphere import Atmosphere


def compute_l_d(cruise_altitude, cruise_speed, cd0, k, mtow, wing_area):
    """
    Computes the lift to drag ratio considering a lift equilibrium in cruise and a simple quadratic model

    :param cruise_altitude: Cruise altitude, in m
    :param cruise_speed: Cruise speed, in m/s
    :param cd0: Profile drag, no unit
    :param k: Lift induced drag coefficient, no unit
    :param mtow: Max Take-Off Weight, in kg
    :param wing_area: Wing area, in m2

    :return l_d: Lift-to-drag ratio in cruise conditions, no unit
    """

    # Air density at cruise level, to compute it, we will use the Atmosphere model available in
    # FAST-OAD, so we will create an Atmosphere instance using the cruise altitude and extract
    # its density attribute
    atm = Atmosphere(altitude=cruise_altitude, altitude_in_feet=False)
    rho = atm.density

    # Computation of the cruise lift coefficient using a simple equilibrium
    cl = (mtow * sc.g) / (0.5 * rho * cruise_speed ** 2.0 * wing_area)

    # Computation of the cruise drag coefficient using the simple quadratic model
    cd = cd0 + k * cl ** 2

    # Computation of the ratio
    l_d = cl / cd

    return l_d
