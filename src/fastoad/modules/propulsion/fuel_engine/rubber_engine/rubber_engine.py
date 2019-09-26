"""
Parametric turbofan engine
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import math
from enum import Enum
from typing import Union, Sequence, Tuple

import numpy as np

from fastoad.utils.physics import Atmosphere
from .constants import ALPHA, BETA, A_MS, B_MS, C_MS, E_MS, D_MS, A_FM, D_FM, E_FM, B_FM, C_FM

# Logger for this module
_LOGGER = logging.getLogger(__name__)

ATM_SEA_LEVEL = Atmosphere(0)
ATM_TROPOPAUSE = Atmosphere(11000, altitude_in_feet=False)


class FlightPhase(Enum):
    """ Enumeration of flight phases"""
    TAKEOFF = 'Takeoff'
    CLIMB = 'Climb'
    IDLE = 'Fight Idle'
    CRUISE = 'Cruise'


class RubberEngine:
    """
    Parametric turbofan engine

    Computes engine characteristics using analytical model from following sources:

    .. bibliography:: ../refs.bib

    :param bypass_ratio:
    :param overall_pressure_ratio:
    :param turbine_inlet_temperature: (unit=K) also noted T4
    :param delta_t4_climb: (unit=K) difference between T4 during climb and design T4 in K
    :param delta_t4_cruise: (unit=K) difference between T4 during cruise and design T4
    :param mto_thrust: (unit=N) Maximum TakeOff thrust, i.e. maximum thrust
                       on ground at speed 0, also noted F0
    :param maximum_mach:
    :param design_altitude: (unit=m)

    """

    def __init__(self,
                 bypass_ratio: float,
                 overall_pressure_ratio: float,
                 turbine_inlet_temperature: float,
                 delta_t4_climb: float,
                 delta_t4_cruise: float,
                 mto_thrust: float,
                 maximum_mach: float,
                 design_altitude: float):
        # pylint: disable=too-many-arguments  # they define the engine
        """ constructor """

        self.bypass_ratio = bypass_ratio
        self.overall_pressure_ratio = overall_pressure_ratio
        self.t_4 = turbine_inlet_temperature
        self.f_0 = mto_thrust
        self.mach_max = maximum_mach
        self.design_alt = design_altitude

        # This dictionary is expected to have a dT4 value for all FlightPhase values
        self.dt4_values = {
            FlightPhase.TAKEOFF: 0.,
            FlightPhase.CLIMB: delta_t4_climb,
            FlightPhase.CRUISE: delta_t4_cruise,
            FlightPhase.IDLE: delta_t4_cruise
        }

        # ... so check that all FlightPhase values are in dict
        assert any([key in self.dt4_values.keys() for key in FlightPhase])

    def compute_manual(self, mach: Union[float, Sequence[float]],
                       altitude: Union[float, Sequence[float]],
                       thrust_rate: Union[float, Sequence[float]] = None,
                       phase: Union[FlightPhase, Sequence[FlightPhase]] = FlightPhase.TAKEOFF) \
            -> Tuple[Union[float, Sequence[float]],
                     Union[float, Sequence[float]]]:
        """
        Computes Specific Fuel Consumption according to provided conditions.

        :param mach:
        :param altitude: (unit=m)
        :param thrust_rate:
        :param phase:
        :return: SFC (in kg/s/N), thrust (in N)
        """
        sfc, _, thrust = self.compute(mach, altitude, self._get_delta_t4(phase),
                                      thrust_rate=thrust_rate)
        return sfc, thrust

    def compute_regulated(self, mach: Union[float, Sequence[float]],
                          altitude: Union[float, Sequence[float]],
                          drag: Union[float, Sequence[float]] = None,
                          phase: Union[FlightPhase, Sequence[FlightPhase]] = FlightPhase.CRUISE) \
            -> Tuple[Union[float, Sequence[float]],
                     Union[float, Sequence[float]]]:
        """
        Computes Specific Fuel Consumption according to provided conditions.
        Thrust rate is adjusted to compensate provided drag

        :param mach:
        :param altitude: (unit=m)
        :param drag: (unit=N)
        :param phase:
        :return: SFC (in kg/s/N), needed thrust rate
        """
        sfc, thrust_rate, _ = self.compute(mach, altitude, self._get_delta_t4(phase), thrust=drag)
        return sfc, thrust_rate

    def compute(self,
                mach: Union[float, Sequence[float]],
                altitude: Union[float, Sequence[float]],
                delta_t4: Union[float, Sequence[float]],
                thrust_rate: Union[float, Sequence[float]] = None,
                thrust: Union[float, Sequence[float]] = None) \
            -> Tuple[Union[float, Sequence[float]],
                     Union[float, Sequence[float]],
                     Union[float, Sequence[float]]]:
        # pylint: disable=too-many-arguments  # they define the engine
        """
        Computes Specific Fuel Consumption according to provided conditions.

        Inputs can be floats, lists or arrays.
        Inputs that are not floats must all have the same size.

        *thrust_rate* and *thrust* are linked, so only one is required (it
        thrust_rate is provided, thrust is ignored)

        :param mach:
        :param altitude: (unit=m)
        :param delta_t4: (unit=K)
        :param thrust_rate: between 0.0 and 1.0. If None, thrust should be provided.
        :param thrust: (unit=N) if None, thrust_rate should be provided.
        :return: SFC (in kg/s/N), thrust rate, thrust (in N)
        """
        atmosphere = Atmosphere(altitude, altitude_in_feet=False)

        max_thrust = self.max_thrust(atmosphere, mach, delta_t4)

        if thrust_rate is None:
            thrust_rate = thrust / max_thrust
        else:
            thrust = thrust_rate * max_thrust

        sfc_0 = self.sfc_at_max_thrust(atmosphere, mach)
        sfc = sfc_0 * self.sfc_ratio(altitude, thrust_rate)

        # FIXME: As model can diverge at a specific altitude, SFC value is limited.
        #        The model should be fixed.
        sfc = np.minimum(sfc, 2.0 / 36000.0)

        return sfc, thrust_rate, thrust

    def sfc_at_max_thrust(self, atmosphere: Atmosphere, mach: Union[float, Sequence[float]]):
        """
        Computation of Specific Fuel Consumption at maximum thrust

        Uses model described in :cite:`roux:2005`, p.41.

        :param atmosphere: Atmosphere instance at intended altitude
        :param mach: Mach number(s)
        :return: SFC (in kg/s/N)
        """

        altitude = atmosphere.get_altitude(False)
        mach = np.asarray(mach)

        # Check definition domain
        if np.any(altitude > 20000):
            _LOGGER.warning(
                "MAX THRUST SFC computation for altitude above 20000 may be unreliable.")
        if self.bypass_ratio < 3.0:
            _LOGGER.warning(
                "MAX THRUST SFC computation for bypass ratio below 3.0 may be unreliable.")
        if self.overall_pressure_ratio < 20.0:
            _LOGGER.warning(
                "MAX THRUST SFC computation for overall pressure ratio below 20 may be unreliable.")
        if self.overall_pressure_ratio > 40.0:
            _LOGGER.warning(
                "MAX THRUST SFC computation for overall pressure ratio above 40 may be unreliable.")

        # pylint: disable=invalid-name  # coefficients are named after model

        # Following coefficients are constant for alt<=0 and alt >=11000m.
        # We use numpy to implement that so we are safe if altitude is a sequence.
        bound_altitude = np.minimum(11000, np.maximum(0, altitude))
        a1 = -7.44e-13 * bound_altitude + 6.54e-7
        a2 = -3.32e-10 * bound_altitude + 8.54e-6
        b1 = -3.47e-11 * bound_altitude - 6.58e-7
        b2 = 4.23e-10 * bound_altitude + 1.32e-5
        c = - 1.05e-7

        theta = atmosphere.temperature / ATM_SEA_LEVEL.temperature
        sfc = mach * (a1 * self.bypass_ratio + a2) + \
              (b1 * self.bypass_ratio + b2) * np.sqrt(theta) + \
              ((7.4e-13 * (self.overall_pressure_ratio - 30) * altitude) + c) * (
                      self.overall_pressure_ratio - 30)

        return sfc

    def sfc_ratio(self,
                  altitude: Union[float, Sequence[float]],
                  thrust_rate: Union[float, Sequence[float]],
                  mach: Union[float, Sequence[float]] = 0.8
                  ) -> Union[float, Sequence[float]]:
        """
        Computation of ratio :math:`\\frac{SFC(F)}{SFC(Fmax)}`, given altitude
        and thrust_rate :math:`\\frac{F}{Fmax}`.

        Uses model described in :cite:`roux:2002`, p.85.

        Warning: this model is very limited

        :param altitude:
        :param thrust_rate:
        :param mach: only used for logger checks as model is made for Mach~0.8
        :return: SFC ratio
        """

        altitude = np.asarray(altitude)
        thrust_rate = np.asarray(thrust_rate)
        mach = np.asarray(mach)

        # Check definition domain
        if np.any(thrust_rate < 0.5):
            _LOGGER.warning("SFC RATIO computation for thrust rate below 50% may be unreliable.")
        if np.any(mach < 0.75) or np.any(mach > 0.85):
            _LOGGER.warning(
                "SFC RATIO computation for Mach number other than Mach 0.8 may be unreliable.")

        delta_h = altitude - self.design_alt
        thrust_ratio_at_min_sfc_ratio = -9.6e-5 * delta_h + 0.85  # =Fi in model

        min_sfc_ratio = np.minimum(0.998, -3.385e-5 * delta_h + 0.995)  # CSRmin in the model

        coeff = (1 - min_sfc_ratio) / (1 - thrust_ratio_at_min_sfc_ratio) ** 2  # =a in the model
        return coeff * (thrust_rate - thrust_ratio_at_min_sfc_ratio) ** 2 + min_sfc_ratio

    def max_thrust(self, atmosphere: Atmosphere,
                   mach: Union[float, Sequence[float]],
                   delta_t4: Union[float, Sequence[float]]) -> Union[float, Sequence[float]]:
        """
        Computation of maximum thrust

        Uses model described in :cite:`roux:2005`, p.57-58

        :param atmosphere: Atmosphere instance at intended altitude (should be <=20km)
        :param mach: Mach number(s) (should be between 0.05 and 1.0)
        :param delta_t4: (unit=K) difference between operational and design values of
                         turbine inlet temperature in K
        :return: maximum thrust (in N)
        """
        # pylint: disable=too-many-statements  # the model is complex and separated in 3 local
        #                                        functions, so I guess it is acceptable

        altitude = atmosphere.get_altitude(altitude_in_feet=False)
        mach = np.asarray(mach)
        delta_t4 = np.asarray(delta_t4)

        # Check definition domain
        if np.any(altitude > 20000):
            _LOGGER.warning("MAX THRUST computation for altitude above 20000 may be unreliable.")
        if np.any(mach < 0.05):
            _LOGGER.warning("MAX THRUST computation for Mach number below 0.05 may be unreliable.")
        if np.any(mach > 1.):
            _LOGGER.warning("MAX THRUST computation for Mach number above 1.0 may be unreliable.")
        if self.bypass_ratio < 3.0:
            _LOGGER.warning("MAX THRUST computation for bypass ratio below 3.0 may be unreliable.")
        if self.bypass_ratio > 6.0:
            _LOGGER.warning("MAX THRUST computation for bypass ratio above 6.0 may be unreliable.")
        if self.t_4 < 1400:
            _LOGGER.warning("MAX THRUST computation for T4 below 1400K may be unreliable.")
        if self.t_4 > 1500:
            _LOGGER.warning("MAX THRUST computation for T4 above 1600K may be unreliable.")
        if self.overall_pressure_ratio < 20.0:
            _LOGGER.warning(
                "MAX THRUST computation for overall pressure ratio below 20 may be unreliable.")
        if self.overall_pressure_ratio > 40.0:
            _LOGGER.warning(
                "MAX THRUST computation for overall pressure ratio above 40 may be unreliable.")
        if np.any(delta_t4 < -100):
            _LOGGER.warning("MAX THRUST computation for Delta_T4 below -100K may be unreliable.")
        if np.any(delta_t4 > 0):
            _LOGGER.warning("MAX THRUST computation for Delta_T4 above 0K may be unreliable.")

        def _mach_effect():
            """ Computation of Mach effect """
            vect = [(self.overall_pressure_ratio - 30) ** 2, (self.overall_pressure_ratio - 30), 1.,
                    self.t_4, delta_t4]

            def _calc_coef(a_coeffs, b_coeffs):
                # We don't use np.dot because delta_t4 can be a sequence
                return (a_coeffs[0] * vect[0] + a_coeffs[1] * vect[1] +
                        a_coeffs[2] + a_coeffs[3] * vect[3] + a_coeffs[4] * vect[
                            4]) * self.bypass_ratio + \
                       (b_coeffs[0] * vect[0] + b_coeffs[1] * vect[1] +
                        b_coeffs[2] + b_coeffs[3] * vect[3] + b_coeffs[4] * vect[4])

            f_ms = _calc_coef(ALPHA[0], BETA[0])
            g_ms = _calc_coef(ALPHA[1], BETA[1])
            f_fm = _calc_coef(ALPHA[2], BETA[2])
            g_fm = _calc_coef(ALPHA[3], BETA[3])

            ms_11000 = A_MS * self.t_4 + B_MS * self.bypass_ratio + C_MS * (
                    self.overall_pressure_ratio - 30) + D_MS * delta_t4 + E_MS

            fm_11000 = A_FM * self.t_4 + B_FM * self.bypass_ratio + C_FM * (
                    self.overall_pressure_ratio - 30) + D_FM * delta_t4 + E_FM

            # Following coefficients are constant for alt >=11000m.
            # We use numpy to implement that so we are safe if altitude is a sequence.
            bound_altitude = np.minimum(11000, altitude)

            m_s = ms_11000 + f_ms * (bound_altitude - 11000) ** 2 + g_ms * (bound_altitude - 11000)
            f_m = fm_11000 + f_fm * (bound_altitude - 11000) ** 2 + g_fm * (bound_altitude - 11000)

            alpha_mach_effect = (1 - f_m) / (m_s * m_s)

            return alpha_mach_effect * (mach - m_s) ** 2 + f_m

        def _altitude_effect():
            """ Computation of altitude effect """
            # pylint: disable=invalid-name  # coefficients are named after model
            k = 1 + 1.2e-3 * delta_t4
            nf = 0.98 + 8e-4 * delta_t4

            def _troposhere_effect(density, altitude, k, nf):
                return k * ((density / ATM_SEA_LEVEL.density) ** nf) * \
                       (1 / (1 - (0.04 * np.sin((np.pi * altitude) / 11000))))

            def _stratosphere_effect(density, k, nf):
                return k * ((ATM_TROPOPAUSE.density / ATM_SEA_LEVEL.density) ** nf) \
                       * density / ATM_TROPOPAUSE.density

            if np.shape(altitude) == ():
                if altitude <= 11000:
                    h = _troposhere_effect(atmosphere.density, altitude, k, nf)
                else:
                    h = _stratosphere_effect(atmosphere.density, k, nf)
            else:
                h = np.empty(np.shape(altitude))
                idx = altitude <= 11000
                if np.shape(delta_t4) == ():
                    h[idx] = _troposhere_effect(atmosphere.density[idx], altitude[idx], k, nf)
                    idx = np.logical_not(idx)
                    h[not idx] = _stratosphere_effect(atmosphere.density[idx], k, nf)
                else:
                    h[idx] = _troposhere_effect(atmosphere.density[idx], altitude[idx],
                                                k[idx], nf[idx])
                    idx = np.logical_not(idx)
                    h[idx] = _stratosphere_effect(atmosphere.density[idx], k[idx], nf[idx])

            return h

        def _residuals():
            """ Computation of residuals """
            return -4.51e-3 * self.bypass_ratio + 2.19e-5 * self.t_4 - 3.09e-4 * (
                    self.overall_pressure_ratio - 30) + 0.945

        return self.f_0 * _mach_effect() * _altitude_effect() * _residuals()

    def installed_weight(self) -> float:
        """
        Computes weight of installed engine, depending on MTO thrust (F0)

        Uses model described in :cite:`roux:2005`, p.74

        :return: installed weight (in kg)
        """
        installation_factor = 1.2

        if self.f_0 < 80000:
            weight = 22.2e-3 * self.f_0
        else:
            weight = 14.1e-3 * self.f_0 + 648

        installed_weight = installation_factor * weight

        return installed_weight

    def length(self):
        # TODO: update model reference with last edition of Raymer
        """
        Computes engine length from MTO thrust and maximum Mach

        Model from :cite:`raymer:1999`, p.74

        :return: engine length (in m)
        """
        length = 0.49 * (self.f_0 / 1000) ** 0.4 * self.mach_max ** 0.2

        return length

    def nacelle_diameter(self):
        # TODO: update model reference with last edition of Raymer
        """
        Computes nacelle diameter from MTO thrust and bypass ratio

        Model of engine diameter from :cite:`raymer:1999`, p.235.
        Nacelle diameter is considered 10% greater (:cite:`kroo:2001`)

        :return: nacelle diameter (in m)
        """
        engine_diameter = 0.15 * (self.f_0 / 1000) ** 0.5 * math.exp(0.04 * self.bypass_ratio)
        nacelle_diameter = engine_diameter * 1.1
        return nacelle_diameter

    def _get_delta_t4(self, phase: Union[FlightPhase, Sequence[FlightPhase]]) \
            -> Union[float, Sequence[float]]:
        """
        :param phase:
        :return: DeltaT4 according to phase
        """

        if np.shape(phase) == ():  # phase is a scalar
            return self.dt4_values[phase]

        # Here phase is a sequence. Ensure now it is a numpy array
        phase_array = np.asarray(phase)

        delta_t4 = np.empty(phase_array.shape)
        for phase_value, dt4_value in self.dt4_values.items():
            delta_t4[phase_array == phase_value] = dt4_value

        return delta_t4
