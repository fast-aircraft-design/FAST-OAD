"""
test module for modules in aerodynamics/components
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

import os.path as pth

import numpy as np
import pytest

from fastoad.io.xml import OpenMdaoXmlIO
from fastoad.modules.aerodynamics.components.cd0 import CD0
from fastoad.modules.aerodynamics.components.high_lift_aero import ComputeDeltaHighLift
from fastoad.modules.aerodynamics.components.high_lift_drag import DeltaCDHighLift
from fastoad.modules.aerodynamics.components.high_lift_lift import DeltaCLHighLift
from fastoad.modules.aerodynamics.components.oswald import OswaldCoefficient
from tests.testing_utilities import run_system


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = OpenMdaoXmlIO(pth.join(pth.dirname(__file__), "data", "aerodynamics_inputs.xml"))
    reader.path_separator = ':'
    ivc = reader.read(only=var_names)
    return ivc


def test_high_lift_drag():
    """ Tests DeltaCDHighLift """
    input_list = ['geometry:flap_span_ratio',
                  'geometry:slat_span_ratio'
                  ]

    def get_cd(slat_angle, flap_angle):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('slat_angle', slat_angle, units='deg')
        ivc.add_output('flap_angle', flap_angle, units='deg')
        problem = run_system(DeltaCDHighLift(), ivc)
        return problem['delta_cd']

    assert get_cd(18, 0) == pytest.approx(0.01033, abs=1e-5)
    assert get_cd(18, 10) == pytest.approx(0.01430, abs=1e-5)
    assert get_cd(22, 15) == pytest.approx(0.01866, abs=1e-5)
    assert get_cd(22, 20) == pytest.approx(0.02220, abs=1e-5)
    assert get_cd(27, 35) == pytest.approx(0.04644, abs=1e-5)


def test_high_lift_drag():
    """ Tests DeltaCLHighLift """
    input_list = ['geometry:wing_sweep_0',
                  'geometry:wing_sweep_100_outer',
                  'geometry:flap_chord_ratio',
                  'geometry:flap_span_ratio',
                  'geometry:slat_chord_ratio',
                  'geometry:slat_span_ratio'
                  ]

    def get_cl(slat_angle, flap_angle, mach):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('slat_angle', slat_angle, units='deg')
        ivc.add_output('flap_angle', flap_angle, units='deg')
        ivc.add_output('mach', mach)
        problem = run_system(DeltaCLHighLift(), ivc)
        return problem['delta_cl']

    assert get_cl(18, 0, 0.2) == pytest.approx(0.062, abs=1e-3)
    assert get_cl(18, 10, 0.2) == pytest.approx(0.516, abs=1e-3)
    assert get_cl(22, 15, 0.2) == pytest.approx(0.741, abs=1e-3)
    assert get_cl(22, 20, 0.2) == pytest.approx(0.935, abs=1e-3)
    assert get_cl(27, 35, 0.2) == pytest.approx(1.344, abs=1e-3)

    assert get_cl(18, 0, 0.4) == pytest.approx(0.062, abs=1e-3)
    assert get_cl(18, 10, 0.4) == pytest.approx(0.547, abs=1e-3)
    assert get_cl(22, 15, 0.4) == pytest.approx(0.787, abs=1e-3)
    assert get_cl(22, 20, 0.4) == pytest.approx(0.994, abs=1e-3)
    assert get_cl(27, 35, 0.4) == pytest.approx(1.431, abs=1e-3)


def test_high_lift_aero():
    """ Tests ComputeDeltaHighLift """
    input_list = ['geometry:wing_sweep_0',
                  'geometry:wing_sweep_100_outer',
                  'geometry:flap_chord_ratio',
                  'geometry:flap_span_ratio',
                  'geometry:slat_chord_ratio',
                  'geometry:slat_span_ratio'
                  ]

    def get_cl_cd(slat_angle, flap_angle, mach, landing_flag):
        id = 'landing' if landing_flag else 'to'

        ivc = get_indep_var_comp(input_list)
        ivc.add_output('sizing_mission:slat_angle_%s' % id, slat_angle, units='deg')
        ivc.add_output('sizing_mission:flap_angle_%s' % id, flap_angle, units='deg')
        ivc.add_output('xfoil:mach', mach)
        component = ComputeDeltaHighLift()
        component.options['landing_flag'] = landing_flag
        problem = run_system(component, ivc)
        if landing_flag:
            return problem['delta_cl_landing']
        else:
            return problem['delta_cl_takeoff'], problem['delta_cd_takeoff']

    cl_cd = get_cl_cd(18, 10, 0.2, False)
    assert cl_cd[0] == pytest.approx(0.516, abs=1e-3)
    assert cl_cd[1] == pytest.approx(0.01430, abs=1e-5)

    cl_cd = get_cl_cd(27, 35, 0.4, False)
    assert cl_cd[0] == pytest.approx(1.431, abs=1e-3)
    assert cl_cd[1] == pytest.approx(0.04644, abs=1e-5)

    cl = get_cl_cd(22, 20, 0.2, True)[0]
    assert cl == pytest.approx(0.935, abs=1e-3)


def test_oswald():
    """ Tests OswaldCoefficient """
    input_list = ['geometry:wing_area',
                  'geometry:wing_span',
                  'geometry:fuselage_height_max',
                  'geometry:fuselage_width_max',
                  'geometry:wing_l2',
                  'geometry:wing_l4',
                  'geometry:wing_sweep_25',
                  ]

    def get_coeff(mach):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('tlar:cruise_Mach', mach)
        problem = run_system(OswaldCoefficient(), ivc)
        return problem['oswald_coeff']

    assert get_coeff(0.2) == pytest.approx(0.0465, abs=1e-4)
    assert get_coeff(0.8) == pytest.approx(0.0530, abs=1e-4)


def test_cd0():
    """ Tests CD0 (test of the group for comparison to legacy) """
    input_list = ['geometry:fuselage_height_max',
                  'geometry:fuselage_length',
                  'geometry:fuselage_wet_area',
                  'geometry:fuselage_width_max',
                  'geometry:wing_area',
                  'geometry:ht_length',
                  'geometry:ht_sweep_25',
                  'geometry:ht_toc',
                  'geometry:ht_wet_area',
                  'geometry:wing_area',
                  'geometry:engine_number',
                  'geometry:fan_length',
                  'geometry:nacelle_length',
                  'geometry:nacelle_wet_area',
                  'geometry:pylon_length',
                  'geometry:pylon_wet_area',
                  'geometry:wing_area',
                  'geometry:S_total',
                  'geometry:vt_length',
                  'geometry:vt_sweep_25',
                  'geometry:vt_toc',
                  'geometry:vt_wet_area',
                  'geometry:wing_area',
                  'geometry:wing_area',
                  'geometry:wing_l0',
                  'geometry:wing_sweep_25',
                  'geometry:wing_toc_aero',
                  'geometry:wing_wet_area'
                  ]

    def get_cd0(static_pressure, temperature, mach):
        reynolds = 47899 * (
                static_pressure * mach * ((1 + 0.126 * mach ** 2) * temperature + 110.4)) / (
                           temperature ** 2 * (1 + 0.126 * mach ** 2) ** (5 / 2))
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('tlar:cruise_Mach', mach)
        ivc.add_output('reynolds_high_speed', reynolds)
        cl = np.arange(150) / 150.
        ivc.add_output('cl_high_speed', cl)
        problem = run_system(CD0(), ivc)
        return problem['cd0_total_high_speed']

    assert get_cd0(24000, 219, 0.78)[75] == pytest.approx(0.01973, abs=1e-4)  # CL = 0.5
    assert get_cd0(101325, 288, 0.2)[140] == pytest.approx(0.02822, abs=1e-4)  # CL = 0.933
