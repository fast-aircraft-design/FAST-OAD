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

import math
from typing import Union, Sequence

import numpy as np

from fastoad.utils.physics import Atmosphere
from .constants import ALPHA, BETA, A_MS, B_MS, C_MS, E_MS, D_MS, A_FM, D_FM, E_FM, B_FM, C_FM

ATM_SEA_LEVEL = Atmosphere(0)
ATM_TROPOPAUSE = Atmosphere(11000, altitude_in_feet=False)


class RubberEngine(object):
    """
    Parametric turbofan engine

    Computes engine characteristics using analytical model from following sources:

    .. bibliography:: ../refs.bib
       :list: bullet
    """

    def __init__(self, bpr, opr, t4, d_t4_cl, d_t4_cr, f0, mach_max, hm):
        self.bpr, self.opr, self.t4, self.d_t4_cl, self.d_t4_cr = bpr, opr, t4, d_t4_cl, d_t4_cr
        self.f0, self.mach_max, self.hm = f0, mach_max, hm
        self.altitude = None
        self.temperature = None
        self.altitude = None
        self.density = None
        self.mach = None
        self.delta_t_4 = None

    def compute_manual(self, mach, altitude, thrust_rate, phase='MTO'):
        _, fc, sfc = self.compute(mach, altitude, phase, thrust_rate=thrust_rate)
        return fc, sfc

    def compute_regulated(self, mach, altitude, drag, phase='CRZ'):

        thrust_rate, _, sfc = self.compute(mach, altitude, phase, fc=drag)
        return sfc, thrust_rate

    def compute(self, mach, altitude, phase, thrust_rate=None, fc=None):
        """
        #----------------------------------------------------------------
        # DEFINITION OF THE sfc CALCULATION FUNCTION
        #----------------------------------------------------------------
        # from Elodie Roux [see her PhD Thesis]
        #
        #----------------------------------------------------------------
        # INPUTS
        #    -mach number
        #    -Flight altitude [m]
        #    -Flight temperature [K]
        #    -Overall Pressure Ratio
        #    -By-Pass Ratio
        #
        # OUTPUTS
        #    -sfc in [kg/s/N]
        #----------------------------------------------------------------
        """
        atmosphere = Atmosphere(altitude)

        self.altitude = altitude * 0.3048
        self.mach = mach
        self.temperature, self.density, _, _ = self._atmosphere(self.altitude)

        # Initialisation de la temperature turbine pour la phase courante
        # FIXME: use enums. Raise a better Exception
        if phase == 'MTO':
            self.delta_t_4 = 0
        elif phase == 'CLIMB':
            self.delta_t_4 = self.d_t4_cl
        elif phase == 'FI':
            self.delta_t_4 = self.d_t4_cr
        elif phase == 'CRZ':
            self.delta_t_4 = self.d_t4_cr
        else:
            raise RuntimeError()

        # Calcul de poussee max (fonction MaxThrust du modele ER)
        fmax_0 = self.max_thrust(atmosphere, self.mach, self.delta_t_4)

        if thrust_rate is None:
            thrust_rate = fc / fmax_0
        else:
            fc = thrust_rate * fmax_0

        # Calcul de conso specifique a poussee max
        sfc_0 = self._sfc_calc_at_max_thrust()

        # Calcul de conso specifique en regime reduit
        delta_h = self.altitude - self.hm
        fi = -9.6e-5 * delta_h + 0.85
        if delta_h < -89:
            csrmin = 0.998
        else:
            csrmin = -3.385e-5 * delta_h + 0.995

        adir = (1 - csrmin) / (1 - fi) ** 2
        csr = adir * (thrust_rate - fi) ** 2 + csrmin

        sfc = sfc_0 * csr
        if sfc > 2.0 / 36000.0:
            sfc = 2.0 / 36000.0

        return thrust_rate, fc, sfc

    def _sfc_calc_at_max_thrust(self):
        global a1, a2, b1, b2, c

        if self.altitude == 0:
            a1 = 6.54e-7
            a2 = 8.54e-6
            b1 = -6.58e-7
            b2 = 1.32e-5
            c = -1.05e-7

        if self.altitude > 0:
            if self.altitude <= 11000:
                a1 = -(7.44e-13) * self.altitude + 6.54e-7
                a2 = -(3.32e-10) * self.altitude + 8.54e-6
                b1 = -(3.47e-11) * self.altitude - 6.58e-7
                b2 = (4.23e-10) * self.altitude + 1.32e-5
                c = - 1.05e-7
            else:
                a1 = 6.45e-7
                a2 = 4.89e-6
                b1 = -1.04e-6
                b2 = 1.79e-5
                c = -1.05e-7

        sfc = self.mach * (a1 * self.bpr + a2) + math.sqrt(self.temperature / 288.15) \
              * (b1 * self.bpr + b2) + (self.opr - 30) * ((7.4e-13
                                                           * (self.opr - 30) * self.altitude) + c)

        return sfc

    def max_thrust(self, atmosphere: Atmosphere,
                   mach: Union[float, Sequence[float]],
                   delta_t4: float) -> Union[float, Sequence[float]]:
        """
        Computation of maximum thrust

        Uses model described in :cite:`roux:2005`, p.57-58


        :param atmosphere: Atmosphere instance at intended altitude (should be <=20km)
        :param mach: Mach number(s) (should be between 0.05 and 1.0)
        :param delta_t4: difference between operational and design values of
                         temperature at turbine input in K
        :return: maximum thrust in N
        """
        altitude = atmosphere.get_altitude(altitude_in_feet=False)

        def _mach_effect():
            """ Computation of Mach effect """
            vect = [(self.opr - 30) ** 2, (self.opr - 30), 1., self.t4, delta_t4]

            f_ms = np.dot(vect, ALPHA[0]) * self.bpr + np.dot(vect, BETA[0])
            g_ms = np.dot(vect, ALPHA[1]) * self.bpr + np.dot(vect, BETA[1])
            f_fm = np.dot(vect, ALPHA[2]) * self.bpr + np.dot(vect, BETA[2])
            g_fm = np.dot(vect, ALPHA[3]) * self.bpr + np.dot(vect, BETA[3])

            ms_11000 = A_MS * self.t4 + B_MS * self.bpr + C_MS * (self.opr - 30) + \
                       D_MS * delta_t4 + E_MS

            fm_11000 = A_FM * self.t4 + B_FM * self.bpr + C_FM * (self.opr - 30) + \
                       D_FM * delta_t4 + E_FM

            # Following coefficients are constant for alt >=11000m.
            # We use numpy to implement that so we are safe if altitude is a sequence.
            bound_altitude = np.minimum(11000, altitude)

            m_s = ms_11000 + f_ms * (bound_altitude - 11000) ** 2 + g_ms * (bound_altitude - 11000)
            f_m = fm_11000 + f_fm * (bound_altitude - 11000) ** 2 + g_fm * (bound_altitude - 11000)

            alpha_mach_effect = (1 - f_m) / (m_s * m_s)

            return alpha_mach_effect * (mach - m_s) ** 2 + f_m

        def _altitude_effect():
            """ Computation of altitude effect """
            k = 1 + 1.2e-3 * delta_t4
            nf = 0.98 + 8e-4 * delta_t4

            if altitude <= 11000:
                return k * ((atmosphere.density / ATM_SEA_LEVEL.density) ** nf) * \
                       (1 / (1 - (0.04 * math.sin((math.pi * altitude) / 11000))))
            return k * ((ATM_TROPOPAUSE.density / ATM_SEA_LEVEL.density) ** nf) \
                   * atmosphere.density / ATM_TROPOPAUSE.density

        def _residuals():
            """ Computation of residuals """
            return -4.51e-3 * self.bpr + 2.19e-5 * self.t4 - 3.09e-4 * (self.opr - 30) + 0.945

        return self.f0 * _mach_effect() * _altitude_effect() * _residuals()

    def installed_weight(self):
        """
        #        #TORENBEEK MODEL with CORRECTION by EROUX
        #        #---------------------------------------------------
        #        #see PhD p. 69 and 72 (correction of the model)
        #        #---------------------------------------------------
        #
        #        #---------------------------------------------------
        #        #Constant definition
        #        #---------------------------------------------------
        #        T_0 = 288.15
        #        Gamma_heat = 1.4
        #
        #        Eta_c = 0.85
        #        Eta_f = 0.85
        #        Eta_t = 0.88
        #        Eta_n = 0.97
        #
        #        Eta_tf = Eta_t * Eta_f
        #
        #        installation_factor = 1.2
        #
        #        C1 = (self.t4/T_0)-((self.opr**((Gamma_heat-1)/Gamma_heat)-1)/Eta_c)
        #
        #        C2 = 1-(((self.opr**((Gamma_heat-1)/Gamma_heat))-1) / (self.t4/T_0*Eta_c*Eta_t) )
        #
        #        C3 = 1-(1.01/(self.opr**((Gamma_heat-1)/Gamma_heat)*C2))
        #
        #        G0 = C1 * C3
        #
        #        C4 = (10*self.opr**(1/4))/(340.43*(math.sqrt(5*Eta_n*(1+Eta_tf*self.bpr)*G0)))
        #
        #        C5 = C4 + (0.0122 * (1-(1/math.sqrt(1+0.75*self.bpr))))
        #
        #        weight = self.f0 * C5
        #
        #        installed_weight = installation_factor * weight
        #
        #        #installed_weight = self.f0 *  installation_factor * (C4+(0.0122*
        #
        #        #Correction factor from EROUX
        #
        #        #installed_weight =  installed_weight /
        #                                    (1+(((7.26e-3)/100)*installed_weight)-20.8/100)
        # Model by EROUX
        #---------------------------------------------------
        # see PhD p. 69 and 72 (correction of the model)
        #---------------------------------------------------
        """
        installation_factor = 1.2

        if self.f0 < 80000:
            weight = 22.2e-3 * self.f0
        else:
            weight = 14.1e-3 * self.f0 + 648

        installed_weight = installation_factor * weight

        return installed_weight

    def length(self):
        """
        # Model by Raymer
        #---------------------------------------------------
        # see 3rd edition of the conceptual design book p. 235
        #---------------------------------------------------
        """
        length = 0.49 * (self.f0 / 1000) ** 0.4 * self.mach_max ** 0.2

        return length

    def nacelle_diameter(self):
        """
        # Model by Raymer
        #---------------------------------------------------
        # see 3rd edition of the conceptual design book p. 235
        #---------------------------------------------------
        """
        diameter = 0.15 * (self.f0 / 1000) ** 0.5 * math.exp(0.04 * self.bpr)

        # Nacelle size is derived from Kroo notes
        # https://web.archive.org/web/20010307121417/http://adg.stanford.edu/aa241/propulsion/nacelledesign.html
        nacelle_diameter = diameter * 1.1

        return nacelle_diameter

    # FIXME: use atmosphere module
    @staticmethod
    def _atmosphere(altitude):
        """
        #----------------------------------------------------------------
        # DEFINITION OF THE ATMOSPHERE FUNCTION
        #----------------------------------------------------------------
        # Valid for an altitude between 0 and 15000 m
        #
        #----------------------------------------------------------------
        # INPUTS
        #    -altitude (m)
        #
        # OUTPUTS
        #    -temperature [deg K]
        #    -Densityt [kg/m3]
        #    -viscosity [
        #    -sos [m/s]
        #----------------------------------------------------------------
        """
        if altitude <= 11000:
            temperature = (288.15 - 0.0065 * altitude)
            density = ((temperature / (288.15)) ** -((9.81 / -0.0065 / 287) + 1) * 1.225)
            viscosity = ((0.000001458) * temperature ** (3 / 2)) * (1 / (temperature + 110.4))
            sos = (1.4 * 287 * temperature) ** 0.5
        else:
            temperature = 216.65
            density = math.exp(-(9.81 / 287 / temperature) * (altitude - 11000)) * 0.364
            viscosity = ((0.000001458) * temperature ** (3 / 2)) * (1 / (temperature + 110.4))
            sos = (1.4 * 287 * temperature) ** 0.5

        return temperature, density, viscosity, sos
