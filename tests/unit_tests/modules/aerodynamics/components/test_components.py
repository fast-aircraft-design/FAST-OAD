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
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp
from pytest import approx

from fastoad.io.xml import OMXmlIO
from fastoad.modules.aerodynamics.components.cd0 import CD0
from fastoad.modules.aerodynamics.components.cd_compressibility import CdCompressibility
from fastoad.modules.aerodynamics.components.cd_trim import CdTrim
from fastoad.modules.aerodynamics.components.compute_low_speed_aero import \
    ComputeAerodynamicsLowSpeed
from fastoad.modules.aerodynamics.components.compute_polar import ComputePolar
from fastoad.modules.aerodynamics.components.compute_reynolds import ComputeReynolds
from fastoad.modules.aerodynamics.components.high_lift_aero import ComputeDeltaHighLift
from fastoad.modules.aerodynamics.components.high_lift_drag import DeltaCDHighLift
from fastoad.modules.aerodynamics.components.high_lift_lift import DeltaCLHighLift
from fastoad.modules.aerodynamics.components.oswald import OswaldCoefficient
from fastoad.utils.physics import Atmosphere
from tests.testing_utilities import run_system


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = OMXmlIO(
        pth.join(pth.dirname(pth.dirname(__file__)), "data", "aerodynamics_inputs.xml"))
    reader.path_separator = ':'
    ivc = reader.read(only=var_names)
    return ivc


def test_high_lift_drag():
    """ Tests DeltaCDHighLift """
    input_list = ['geometry:flap:span_ratio',
                  'geometry:slat:span_ratio'
                  ]

    def get_cd(slat_angle, flap_angle):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('slat_angle', slat_angle, units='deg')
        ivc.add_output('flap_angle', flap_angle, units='deg')
        problem = run_system(DeltaCDHighLift(), ivc)
        return problem['delta_cd']

    assert get_cd(18, 0) == approx(0.01033, abs=1e-5)
    assert get_cd(18, 10) == approx(0.01430, abs=1e-5)
    assert get_cd(22, 15) == approx(0.01866, abs=1e-5)
    assert get_cd(22, 20) == approx(0.02220, abs=1e-5)
    assert get_cd(27, 35) == approx(0.04644, abs=1e-5)


def test_high_lift_lift():
    """ Tests DeltaCLHighLift """
    input_list = ['geometry:wing:sweep_0',
                  'geometry:wing:sweep_100_outer',
                  'geometry:flap:chord_ratio',
                  'geometry:flap:span_ratio',
                  'geometry:slat:chord_ratio',
                  'geometry:slat:span_ratio'
                  ]

    def get_cl(slat_angle, flap_angle, mach):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('slat_angle', slat_angle, units='deg')
        ivc.add_output('flap_angle', flap_angle, units='deg')
        ivc.add_output('mach', mach)
        problem = run_system(DeltaCLHighLift(), ivc)
        return problem['delta_cl']

    assert get_cl(18, 0, 0.2) == approx(0.062, abs=1e-3)
    assert get_cl(18, 10, 0.2) == approx(0.516, abs=1e-3)
    assert get_cl(22, 15, 0.2) == approx(0.741, abs=1e-3)
    assert get_cl(22, 20, 0.2) == approx(0.935, abs=1e-3)
    assert get_cl(27, 35, 0.2) == approx(1.344, abs=1e-3)

    assert get_cl(18, 0, 0.4) == approx(0.062, abs=1e-3)
    assert get_cl(18, 10, 0.4) == approx(0.547, abs=1e-3)
    assert get_cl(22, 15, 0.4) == approx(0.787, abs=1e-3)
    assert get_cl(22, 20, 0.4) == approx(0.994, abs=1e-3)
    assert get_cl(27, 35, 0.4) == approx(1.431, abs=1e-3)


def test_high_lift_aero():
    """ Tests ComputeDeltaHighLift """
    input_list = ['geometry:wing:sweep_0',
                  'geometry:wing:sweep_100_outer',
                  'geometry:flap:chord_ratio',
                  'geometry:flap:span_ratio',
                  'geometry:slat:chord_ratio',
                  'geometry:slat:span_ratio'
                  ]

    def get_cl_cd(slat_angle, flap_angle, mach, landing_flag):
        ivc = get_indep_var_comp(input_list)
        if landing_flag:
            ivc.add_output('sizing_mission:mission:operational:landing:slat_angle', slat_angle, units='deg')
            ivc.add_output('sizing_mission:mission:operational:landing:flap_angle', flap_angle, units='deg')
        else:
            ivc.add_output('sizing_mission:mission:operational:takeoff:slat_angle', slat_angle, units='deg')
            ivc.add_output('sizing_mission:mission:operational:takeoff:flap_angle', flap_angle, units='deg')
        ivc.add_output('xfoil:mach', mach)
        component = ComputeDeltaHighLift()
        component.options['landing_flag'] = landing_flag
        problem = run_system(component, ivc)
        if landing_flag:
            return problem['delta_cl_landing']

        return problem['delta_cl_takeoff'], problem['delta_cd_takeoff']

    cl, cd = get_cl_cd(18, 10, 0.2, False)
    assert cl == approx(0.516, abs=1e-3)
    assert cd == approx(0.01430, abs=1e-5)

    cl, cd = get_cl_cd(27, 35, 0.4, False)
    assert cl == approx(1.431, abs=1e-3)
    assert cd == approx(0.04644, abs=1e-5)

    cl = get_cl_cd(22, 20, 0.2, True)[0]
    assert cl == approx(0.935, abs=1e-3)


def test_oswald():
    """ Tests OswaldCoefficient """
    input_list = ['geometry:wing:area',
                  'geometry:wing:span',
                  'geometry:fuselage:maximum_height',
                  'geometry:fuselage:maximum_width',
                  'geometry:wing:root:chord',
                  'geometry:wing:tip:chord',
                  'geometry:wing:sweep_25',
                  ]

    def get_coeff(mach):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output('TLAR:cruise_mach', mach)
        problem = run_system(OswaldCoefficient(), ivc)
        return problem['oswald_coeff_high_speed']

    assert get_coeff(0.2) == approx(0.0465, abs=1e-4)
    assert get_coeff(0.8) == approx(0.0530, abs=1e-4)


def test_cd0():
    """ Tests CD0 (test of the group for comparison to legacy) """
    input_list = ['geometry:fuselage:maximum_height',
                  'geometry:fuselage:length',
                  'geometry:fuselage:wet_area',
                  'geometry:fuselage:maximum_width',
                  'geometry:horizontal_tail:length',
                  'geometry:horizontal_tail:sweep_25',
                  'geometry:horizontal_tail:thickness_ratio',
                  'geometry:horizontal_tail:wet_area',
                  'geometry:wing:area',
                  'geometry:propulsion:engine:count',
                  'geometry:propulsion:fan:length',
                  'geometry:propulsion:nacelle:length',
                  'geometry:propulsion:nacelle:wet_area',
                  'geometry:propulsion:pylon:length',
                  'geometry:propulsion:pylon:wet_area',
                  'geometry:aircraft:area',
                  'geometry:vertical_tail:length',
                  'geometry:vertical_tail:sweep_25',
                  'geometry:vertical_tail:thickness_ratio',
                  'geometry:vertical_tail:wet_area',
                  'geometry:wing:area',
                  'geometry:wing:MAC:length',
                  'geometry:wing:sweep_25',
                  'geometry:wing:thickness_ratio',
                  'geometry:wing:wet_area'
                  ]

    def get_cd0(alt, mach, cl):
        reynolds = Atmosphere(alt).get_unitary_reynolds(mach)

        ivc = get_indep_var_comp(input_list)
        ivc.add_output('TLAR:cruise_mach', mach)
        ivc.add_output('reynolds_high_speed', reynolds)
        ivc.add_output('cl_high_speed', 150 * [cl])  # needed because size of input array is fixed
        problem = run_system(CD0(), ivc)
        return problem['cd0_total_high_speed'][0]

    assert get_cd0(35000, 0.78, 0.5) == approx(0.01975, abs=1e-5)
    assert get_cd0(0, 0.2, 0.9) == approx(0.02727, abs=1e-5)


def test_cd_compressibility():
    """ Tests CdCompressibility """

    def get_cd_compressibility(mach, cl):
        ivc = IndepVarComp()
        ivc.add_output('cl_high_speed', 150 * [cl])  # needed because size of input array is fixed
        ivc.add_output('TLAR:cruise_mach', mach)
        problem = run_system(CdCompressibility(), ivc)
        return problem['cd_comp_high_speed'][0]

    assert get_cd_compressibility(0.78, 0.2) == approx(0.00028, abs=1e-5)
    assert get_cd_compressibility(0.78, 0.35) == approx(0.00028, abs=1e-5)
    assert get_cd_compressibility(0.78, 0.5) == approx(0.00045, abs=1e-5)
    assert get_cd_compressibility(0.84, 0.2) == approx(0.00359, abs=1e-5)
    assert get_cd_compressibility(0.84, 0.35) == approx(0.00359, abs=1e-5)
    assert get_cd_compressibility(0.84, 0.5) == approx(0.00580, abs=1e-5)
    assert get_cd_compressibility(0.2, 0.9) == approx(0.0, abs=1e-5)


def test_cd_trim():
    """ Tests CdTrim """

    def get_cd_trim(cl):
        ivc = IndepVarComp()
        ivc.add_output('cl_high_speed', 150 * [cl])  # needed because size of input array is fixed
        problem = run_system(CdTrim(), ivc)
        return problem['cd_trim_high_speed'][0]

    assert get_cd_trim(0.5) == approx(0.0002945, abs=1e-6)
    assert get_cd_trim(0.9) == approx(0.0005301, abs=1e-6)


def test_polar():
    """ Tests ComputePolar """

    # Need to plug Cd modules, Reynolds and Oswald

    input_list = ['aerodynamics:aircraft:cruise:CD:k',
                  'aerodynamics:aircraft:cruise:CD:offset',
                  'aerodynamics:aircraft:cruise:CD:winglet_effect:k',
                  'aerodynamics:aircraft:cruise:CD:winglet_effect:offset',
                  'geometry:fuselage:maximum_height',
                  'geometry:fuselage:length',
                  'geometry:fuselage:wet_area',
                  'geometry:fuselage:maximum_width',
                  'geometry:wing:area',
                  'geometry:horizontal_tail:length',
                  'geometry:horizontal_tail:sweep_25',
                  'geometry:horizontal_tail:thickness_ratio',
                  'geometry:horizontal_tail:wet_area',
                  'geometry:wing:area',
                  'geometry:propulsion:engine:count',
                  'geometry:propulsion:fan:length',
                  'geometry:propulsion:nacelle:length',
                  'geometry:propulsion:nacelle:wet_area',
                  'geometry:propulsion:pylon:length',
                  'geometry:propulsion:pylon:wet_area',
                  'geometry:wing:area',
                  'geometry:aircraft:area',
                  'geometry:vertical_tail:length',
                  'geometry:vertical_tail:sweep_25',
                  'geometry:vertical_tail:thickness_ratio',
                  'geometry:vertical_tail:wet_area',
                  'geometry:wing:MAC:length',
                  'geometry:wing:sweep_25',
                  'geometry:wing:thickness_ratio',
                  'geometry:wing:wet_area',
                  'geometry:wing:span',
                  'geometry:wing:root:chord',
                  'geometry:wing:tip:chord',
                  'TLAR:cruise_mach',
                  'sizing_mission:mission:operational:cruise:altitude'
                  ]
    group = Group()
    group.add_subsystem('reynolds', ComputeReynolds(), promotes=['*'])
    group.add_subsystem('oswald', OswaldCoefficient(), promotes=['*'])
    group.add_subsystem('cd0', CD0(), promotes=['*'])
    group.add_subsystem('cd_compressibility', CdCompressibility(), promotes=['*'])
    group.add_subsystem('cd_trim', CdTrim(), promotes=['*'])
    group.add_subsystem('polar', ComputePolar(), promotes=['*'])

    ivc = get_indep_var_comp(input_list)
    ivc.add_output('cl_high_speed', np.arange(0., 1.5, 0.01))

    problem = run_system(group, ivc)

    cd = problem['aerodynamics:ClCd'][0, :]
    cl = problem['aerodynamics:ClCd'][1, :]

    assert cd[cl == 0.] == approx(0.02030, abs=1e-5)
    assert cd[cl == 0.2] == approx(0.02209, abs=1e-5)
    assert cd[cl == 0.42] == approx(0.02897, abs=1e-5)
    assert cd[cl == 0.85] == approx(0.11781, abs=1e-5)

    assert problem['aerodynamics:Cl_opt'] == approx(0.54, abs=1e-3)
    assert problem['aerodynamics:Cd_opt'] == approx(0.03550, abs=1e-5)


def test_low_speed_aero():
    """ Tests group ComputeAerodynamicsLowSpeed """
    input_list = [
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'geometry:wing:span',
        'geometry:wing:aspect_ratio',
        'geometry:wing:tip:chord',
        'geometry:wing:sweep_25',
        'geometry:wing:root:chord',
        'geometry:wing:area',
        'geometry:wing:tip:thickness_ratio',
    ]
    ivc = get_indep_var_comp(input_list)

    problem = run_system(ComputeAerodynamicsLowSpeed(), ivc)

    assert problem['aerodynamics:aircraft:takeoff:CL_alpha'] == approx(5.0, abs=1e-1)
