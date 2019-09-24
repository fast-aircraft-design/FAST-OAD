"""
    Estimation of vertical tail lift coefficient
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
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeVTClalpha(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail lift coefficient estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('tlar:cruise_Mach', val=np.nan)
        self.add_input('geometry:vt_aspect_ratio', val=np.nan)
        self.add_input('geometry:vt_sweep_25', val=np.nan, units='deg')
        self.add_input('k_ar_effective', val=np.nan)

        self.add_output('aerodynamics:Cl_alpha_vt')

        self.declare_partials('aerodynamics:Cl_alpha_vt', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        cruise_mach = inputs['tlar:cruise_Mach']
        k_ar_effective = inputs['k_ar_effective']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        lambda_vt = inputs['geometry:vt_aspect_ratio']

        beta = math.sqrt(1 - cruise_mach ** 2)
        lambda_vt *= k_ar_effective
        cl_alpha_vt = 0.8 * 2 * math.pi * lambda_vt / \
                      (2 + math.sqrt(4 + lambda_vt ** 2 * beta ** 2 / 0.95 ** \
                       2 * (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 \
                       / beta ** 2)))

        outputs['aerodynamics:Cl_alpha_vt'] = cl_alpha_vt

    def compute_partials(self, inputs, partials):
        cruise_mach = inputs['tlar:cruise_Mach']
        k_ar_effective = inputs['k_ar_effective']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        lambda_vt = inputs['geometry:vt_aspect_ratio']

        beta = math.sqrt(1 - cruise_mach ** 2)
        lambda_eff = lambda_vt * k_ar_effective

        dbeta_dm = - 2 * cruise_mach / (2. * beta)
        dlambda_dlambda = k_ar_effective
        dlambda_dk = lambda_vt

        num = 0.8 * 2 * math.pi * lambda_eff
        den = 2 + math.sqrt(4 + lambda_eff ** 2 * beta ** 2 / 0.95 ** 2 *
                            (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 / beta ** 2))

        dnum_dlambda = 0.8 * 2 * math.pi * dlambda_dlambda
        dnum_dk = 0.8 * 2 * math.pi * dlambda_dk

        dden_dlambda = 0.5 * 2 * dlambda_dlambda * lambda_eff * beta ** 2 / 0.95 ** 2 * \
                       (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 / beta ** 2) / (den - 2)
        dden_dk = 0.5 * 2 * dlambda_dk * lambda_eff * beta ** 2 / 0.95 ** 2 * \
                  (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 / beta ** 2) / (den - 2)
        dden_dsweep = 0.5 * lambda_eff ** 2 / 0.95 ** 2 * 2 * math.pi / 180. / (
            math.cos(sweep_25_vt / 180. * math.pi)) ** 2 * \
                      math.tan(sweep_25_vt / 180. * math.pi) / \
                      math.sqrt(4 + lambda_eff ** 2 * beta ** 2 / 0.95 ** 2 * \
                      (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 / beta ** 2))
        dden_dm = 0.5 * lambda_eff ** 2 / 0.95 ** 2 * 2 * beta * dbeta_dm / \
                  math.sqrt(4 + lambda_eff ** 2 * beta ** 2 / 0.95 ** 2 * (
                              1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 / beta ** 2))

        partials['aerodynamics:Cl_alpha_vt', 'geometry:vt_aspect_ratio'] = \
            (dnum_dlambda * den - num * dden_dlambda) / den ** 2
        partials['aerodynamics:Cl_alpha_vt', 'k_ar_effective'] = \
            (dnum_dk * den - num * dden_dk) / den ** 2
        partials['aerodynamics:Cl_alpha_vt', 'geometry:vt_sweep_25'] = num * (-dden_dsweep)  \
                                                                       / den ** 2
        partials['aerodynamics:Cl_alpha_vt', 'tlar:cruise_Mach'] = num * (-dden_dm) / den ** 2
