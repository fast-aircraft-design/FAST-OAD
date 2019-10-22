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
from typing import Union, Sequence, Tuple, Optional

import numpy as np

from fastoad.constants import FlightPhase
from fastoad.modules.propulsion import IEngine
from fastoad.modules.propulsion.fuel_engine.rubber_engine.exceptions import \
    FastRubberEngineInconsistentInputParametersError
from fastoad.utils.physics import Atmosphere
from .constants import ALPHA, BETA, A_MS, B_MS, C_MS, E_MS, D_MS, A_FM, D_FM, E_FM, B_FM, C_FM, \
    MAX_SFC_RATIO_COEFF, ATM_SEA_LEVEL, ATM_TROPOPAUSE

# Logger for this module
_LOGGER = logging.getLogger(__name__)


class RubberEngine(IEngine):
    """
    Parametric turbofan engine

    Computes engine characteristics using analytical model from following sources:

    .. bibliography:: ../refs.bib

    :param bypass_ratio:
    :param overall_pressure_ratio:
    :param turbine_inlet_temperature: (unit=K) also noted T4
    :param mto_thrust: (unit=N) Maximum TakeOff thrust, i.e. maximum thrust
                       on ground at speed 0, also noted F0
    :param maximum_mach:
    :param design_altitude: (unit=m)
    :param delta_t4_climb: (unit=K) difference between T4 during climb and design T4 in K
    :param delta_t4_cruise: (unit=K) difference between T4 during cruise and design T4
    """

    def __init__(self,
                 bypass_ratio: float,
                 overall_pressure_ratio: float,
                 turbine_inlet_temperature: float,
                 mto_thrust: float,
                 maximum_mach: float,
                 design_altitude: float,
                 delta_t4_climb: float = -50,
                 delta_t4_cruise: float = -100,
                 ):
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

    def compute_flight_points(self,
                              mach: Union[float, Sequence],
                              altitude: Union[float, Sequence],
                              phase: Union[FlightPhase, Sequence],
                              use_thrust_rate: Optional[Union[bool, Sequence]] = None,
                              thrust_rate: Optional[Union[float, Sequence]] = None,
                              thrust: Optional[Union[float, Sequence]] = None) \
            -> Tuple[Union[float, Sequence],
                     Union[float, Sequence],
                     Union[float, Sequence]]:
        # pylint: disable=too-many-arguments  # they define the trajectory
        """
        see :meth:`fastoad.modules.propulsion.engine.IEngine.compute_flight_points` for more info


        :param mach: Mach number
        :param altitude: (unit=m) altitude w.r.t. to sea level
        :param phase: flight phase
        :param use_thrust_rate: tells if thrust_rate or thrust should be used (works element-wise)
        :param thrust_rate: thrust rate (unit=none)
        :param thrust: required thrust (unit=N)
        :return: SFC (in kg/s/N), thrust rate, thrust (in N)
        """
        return self.compute_flight_points_from_dt4(mach, altitude, self._get_delta_t4(phase),
                                                   use_thrust_rate, thrust_rate, thrust)

    def compute_flight_points_from_dt4(self,
                                       mach: Union[float, Sequence],
                                       altitude: Union[float, Sequence],
                                       delta_t4: Union[float, Sequence],
                                       use_thrust_rate: Optional[Union[bool, Sequence]] = None,
                                       thrust_rate: Optional[Union[float, Sequence]] = None,
                                       thrust: Optional[Union[float, Sequence]] = None) \
            -> Tuple[Union[float, Sequence],
                     Union[float, Sequence],
                     Union[float, Sequence]]:
        # pylint: disable=too-many-arguments  # they define the trajectory
        """
        Same as :meth:`compute_flight_points` except that delta_t4 is used directly
        instead of specifying flight phase.

        :param mach: Mach number
        :param altitude: (unit=m) altitude w.r.t. to sea level
        :param delta_t4: (unit=K) difference between operational and design values of
                         turbine inlet temperature in K
        :param use_thrust_rate: tells if thrust_rate or thrust should be used (works element-wise)
        :param thrust_rate: thrust rate (unit=none)
        :param thrust: required thrust (unit=N)
        :return: SFC (in kg/s/N), thrust rate, thrust (in N)
        """
        mach = np.asarray(mach)
        altitude = np.asarray(altitude)
        delta_t4 = np.asarray(delta_t4)

        use_thrust_rate, thrust_rate, thrust = self._check_thrust_inputs(use_thrust_rate,
                                                                         thrust_rate, thrust)

        use_thrust_rate = np.asarray(use_thrust_rate, dtype=bool)
        thrust_rate = np.asarray(thrust_rate)
        thrust = np.asarray(thrust)

        atmosphere = Atmosphere(altitude, altitude_in_feet=False)

        max_thrust = self.max_thrust(atmosphere, mach, delta_t4)

        # We compute thrust values from thrust rates when needed
        idx = use_thrust_rate
        if np.size(max_thrust) == 1:
            maximum_thrust = max_thrust
            out_thrust_rate = thrust_rate
            out_thrust = thrust
        else:
            out_thrust_rate = np.full(np.shape(max_thrust), thrust_rate.item()) if np.size(
                thrust_rate) == 1 else thrust_rate
            out_thrust = np.full(np.shape(max_thrust), thrust.item()) if np.size(
                thrust) == 1 else thrust

            maximum_thrust = max_thrust[idx]

        out_thrust[idx] = out_thrust_rate[idx] * maximum_thrust

        # thrust_rate is obtained from entire thrust vector (could be optimized if needed,
        # as some thrust rates that are computed may have been provided as input)
        out_thrust_rate = thrust / max_thrust

        # Now SFC can be computed
        sfc_0 = self.sfc_at_max_thrust(atmosphere, mach)
        sfc = sfc_0 * self.sfc_ratio(altitude, out_thrust_rate)

        return sfc, out_thrust_rate, out_thrust

    @staticmethod
    def _check_thrust_inputs(use_thrust_rate, thrust_rate, thrust):
        """ Checks that inputs are consistent and return them in proper shape """
        # Check inputs: if use_thrust_rate is None, we will use the provided input between
        # thrust_rate and thrust
        if use_thrust_rate is None:
            if thrust_rate is not None:
                use_thrust_rate = True
                thrust = np.empty_like(thrust_rate)
            elif thrust is not None:
                use_thrust_rate = False
                thrust_rate = np.empty_like(thrust)
            else:
                raise FastRubberEngineInconsistentInputParametersError(
                    'When use_thrust_rate is None, either thrust_rate or thrust should be provided.'
                )

        elif np.size(use_thrust_rate) == 1:
            # Check inputs: if use_thrust_rate is a scalar, the matching input(thrust_rate or
            # thrust) must be provided.
            if use_thrust_rate:
                if thrust_rate is None:
                    raise FastRubberEngineInconsistentInputParametersError(
                        'When use_thrust_rate is True, thrust_rate should be provided.'
                    )
                thrust = np.empty_like(thrust_rate)
            else:
                if thrust is None:
                    raise FastRubberEngineInconsistentInputParametersError(
                        'When use_thrust_rate is False, thrust should be provided.'
                    )
                thrust_rate = np.empty_like(thrust)

        else:
            # Check inputs: if use_thrust_rate is not a scalar, both thrust_rate and thrust must be
            # provided and have the same shape as use_thrust_rate
            if thrust_rate is None or thrust is None:
                raise FastRubberEngineInconsistentInputParametersError(
                    'When use_thrust_rate is a sequence, both thrust_rate and thrust should be '
                    'provided.'
                )
            if np.shape(thrust_rate) != np.shape(use_thrust_rate) or np.shape(thrust) != np.shape(
                    use_thrust_rate):
                raise FastRubberEngineInconsistentInputParametersError(
                    'When use_thrust_rate is a sequence, both thrust_rate and thrust should have '
                    'same shape as use_thrust_rate'
                )

        return use_thrust_rate, thrust_rate, thrust

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

        self._check_definition_domain('SFC at MAX THRUST computation',
                                      {'altitude': (altitude, None, 20000),
                                       'Mach number': (mach, 0.05, 1.0),
                                       'overall pressure ratio': (
                                           self.overall_pressure_ratio, 20.0, 40.0),
                                       'bypass ratio': (self.bypass_ratio, 3.0, None)
                                       })

        # Following coefficients are constant for alt<=0 and alt >=11000m.
        # We use numpy to implement that so we are safe if altitude is a sequence.
        bound_altitude = np.minimum(11000, np.maximum(0, altitude))

        # pylint: disable=invalid-name  # coefficients are named after model
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

        Uses a patched version of model described in :cite:`roux:2002`, p.85.

        Warning: this model is very limited

        :param altitude:
        :param thrust_rate:
        :param mach: only used for logger checks as model is made for Mach~0.8
        :return: SFC ratio
        """

        altitude = np.asarray(altitude)
        thrust_rate = np.asarray(thrust_rate)
        mach = np.asarray(mach)

        self._check_definition_domain('SFC RATIO computation',
                                      {'altitude': (altitude, None, 20000),
                                       'Mach number': (mach, 0.75, 0.85),
                                       'thrust rate': (thrust_rate, 0.5, 1.0),
                                       })

        delta_h = altitude - self.design_alt
        thrust_ratio_at_min_sfc_ratio = -9.6e-5 * delta_h + 0.85  # =Fi in model

        min_sfc_ratio = np.minimum(0.998, -3.385e-5 * delta_h + 0.995)

        # Get sfc_ratio_min closer to 1 when Fi closes to 1, to
        # respect coeff<=MAX_SFC_RATIO_COEFF
        # pylint: disable=unsupported-assignment-operation  # pylint is wrong
        min_sfc_ratio = np.maximum(min_sfc_ratio, 1 - MAX_SFC_RATIO_COEFF * (
                1 - thrust_ratio_at_min_sfc_ratio) ** 2)
        coeff = (1 - min_sfc_ratio) / (1 - thrust_ratio_at_min_sfc_ratio) ** 2

        # When thrust_ratio_at_min_sfc_ratio==1. (so min_sfc_ratio==1 also),
        # coeff has to be affected by hand
        if np.size(coeff) != 1:
            min_sfc_ratio[thrust_ratio_at_min_sfc_ratio == 1.0] = 1.0
            coeff[thrust_ratio_at_min_sfc_ratio == 1.0] = MAX_SFC_RATIO_COEFF
        elif thrust_ratio_at_min_sfc_ratio == 1.0:
            min_sfc_ratio = 1.0
            coeff = MAX_SFC_RATIO_COEFF

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

        altitude = atmosphere.get_altitude(altitude_in_feet=False)
        mach = np.asarray(mach)
        delta_t4 = np.asarray(delta_t4)

        self._check_definition_domain('MAX THRUST computation',
                                      {'altitude': (altitude, None, 20000),
                                       'Mach number': (mach, 0.05, 1.0),
                                       'overall pressure ratio': (
                                           self.overall_pressure_ratio, 20.0, 40.0),
                                       'bypass ratio': (self.bypass_ratio, 3.0, 6.0),
                                       'T4': (self.t_4, 1400.0, 1600.0),
                                       'Delta_T4': (delta_t4, -100.0, 0.0),
                                       })

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

            if np.size(altitude) == 1:
                if altitude <= 11000:
                    h = _troposhere_effect(atmosphere.density, altitude, k, nf)
                else:
                    h = _stratosphere_effect(atmosphere.density, k, nf)
            else:
                h = np.empty(np.shape(altitude))
                idx = altitude <= 11000
                if np.size(delta_t4) == 1:
                    h[idx] = _troposhere_effect(atmosphere.density[idx], altitude[idx], k, nf)
                    idx = np.logical_not(idx)
                    h[idx] = _stratosphere_effect(atmosphere.density[idx], k, nf)
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

    @staticmethod
    def _check_definition_domain(operation_name: str, arrays: dict):
        """
        Checks that provided arrays have values inside limits.
        Logs a warning for each array that does not respect a limit.

        The *arrays* dictionary is expected to have following structure:
            - key : name of the variable as it should appear in logger message
            - value = tuple with 3 members:
                - the actual variable (numpy array, sequence or scalar)
                - the lower limit of the domain definition
                - the upper limit of the domain definition

        :param operation_name: for logging
        :param arrays: see description above
        :return: True if all bounds are respected. False otherwise
        """

        msg_lower_limit = operation_name + ' for %s below %s may be unreliable.'
        msg_upper_limit = operation_name + ' for %s above %s may be unreliable.'

        status = True

        for identifier, (values, low_limit, high_limit) in arrays.items():
            # Check bounds
            if low_limit is not None and np.any(values < low_limit):
                _LOGGER.warning(msg_lower_limit, identifier, low_limit)
                status = False
            if high_limit is not None and np.any(values > high_limit):
                _LOGGER.warning(msg_upper_limit, identifier, high_limit)
                status = False

        return status
