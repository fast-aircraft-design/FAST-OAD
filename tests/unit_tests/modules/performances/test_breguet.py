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

import openmdao.api as om
from numpy.testing import assert_allclose

from fastoad.modules.performances.breguet import BreguetFromMTOW, BreguetFromOWE
from fastoad.modules.propulsion.fuel_engine.rubber_engine import OMRubberEngine
from tests.testing_utilities import run_system


def test_breguet_from_mtow():
    # test 1
    ivc = om.IndepVarComp()
    ivc.add_output('mission:sizing:cruise:altitude', 35000, units='ft')
    ivc.add_output('TLAR:cruise_mach', 0.78)
    ivc.add_output('TLAR:range', 500, units='NM')
    ivc.add_output('aerodynamics:aircraft:cruise:L_D_max', 16.)
    ivc.add_output('propulsion:SFC', 1e-5, units='kg/N/s')
    ivc.add_output('weight:aircraft:MTOW', 74000, units='kg')

    problem = run_system(BreguetFromMTOW(), ivc)

    assert_allclose(problem['mission:sizing:ZFW'], 65617., rtol=1e-3)
    assert_allclose(problem['mission:sizing:mission:fuel'], 8382., rtol=1e-3)

    # test 2
    ivc = om.IndepVarComp()
    ivc.add_output('mission:sizing:cruise:altitude', 35000, units='ft')
    ivc.add_output('TLAR:cruise_mach', 0.78)
    ivc.add_output('TLAR:range', 1500, units='NM')
    ivc.add_output('aerodynamics:aircraft:cruise:L_D_max', 16.)
    ivc.add_output('propulsion:SFC', 1e-5, units='kg/N/s')
    ivc.add_output('weight:aircraft:MTOW', 74000, units='kg')

    problem = run_system(BreguetFromMTOW(), ivc)

    assert_allclose(problem['mission:sizing:ZFW'], 62473., rtol=1e-3)
    assert_allclose(problem['mission:sizing:mission:fuel'], 11526., rtol=1e-3)

    # Check consistency of other outputs
    assert_allclose(problem['mission:sizing:mission:fuel'],
                    problem['mission:sizing:fuel']
                    + problem['mission:sizing:fuel_reserve']
                    , rtol=1e-3)
    assert_allclose(problem['mission:sizing:fuel'],
                    problem['mission:sizing:climb:fuel']
                    + problem['mission:sizing:cruise:fuel']
                    + problem['mission:sizing:descent:fuel']
                    , rtol=1e-3)


def test_breguet_from_mtow_with_rubber_engine():
    ivc = om.IndepVarComp()
    ivc.add_output('mission:sizing:cruise:altitude', 35000, units='ft')
    ivc.add_output('TLAR:cruise_mach', 0.78)
    ivc.add_output('TLAR:range', 500, units='NM')
    ivc.add_output('aerodynamics:aircraft:cruise:L_D_max', 16.)
    ivc.add_output('weight:aircraft:MTOW', 74000, units='kg')

    ivc.add_output('propulsion:rubber_engine:bypass_ratio', 5)
    ivc.add_output('propulsion:rubber_engine:maximum_mach', 0.95)
    ivc.add_output('propulsion:rubber_engine:design_altitude', 35000, units='ft')
    ivc.add_output('propulsion:MTO_thrust', 100000, units='N')
    ivc.add_output('propulsion:rubber_engine:overall_pressure_ratio', 30)
    ivc.add_output('propulsion:rubber_engine:turbine_inlet_temperature', 1500, units='K')

    group = om.Group()
    group.add_subsystem('breguet', BreguetFromMTOW(), promotes=['*'])
    group.add_subsystem('engine', OMRubberEngine(), promotes=['*'])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = run_system(group, ivc)

    assert_allclose(problem['mission:sizing:ZFW'], 65076., atol=1)
    assert_allclose(problem['mission:sizing:mission:fuel'], 8924., atol=1)


def test_breguet_from_owe():
    ivc = om.IndepVarComp()
    ivc.add_output('mission:sizing:cruise:altitude', 35000, units='ft')
    ivc.add_output('TLAR:cruise_mach', 0.78)
    ivc.add_output('TLAR:range', 500, units='NM')
    ivc.add_output('aerodynamics:aircraft:cruise:L_D_max', 16.)
    ivc.add_output('propulsion:SFC', 1e-5, units='kg/N/s')
    ivc.add_output('weight:aircraft:OWE', 50000, units='kg')
    ivc.add_output('weight:aircraft:payload', 15617, units='kg')

    problem = run_system(BreguetFromOWE(), ivc)

    assert_allclose(problem['weight:aircraft:MTOW'], 74000., rtol=1e-3)
    assert_allclose(problem['mission:sizing:ZFW'], 65617., rtol=1e-3)
    assert_allclose(problem['mission:sizing:mission:fuel'], 8382., rtol=1e-3)


def test_breguet_from_owe_with_rubber_engine():
    ivc = om.IndepVarComp()
    ivc.add_output('mission:sizing:cruise:altitude', 35000, units='ft')
    ivc.add_output('TLAR:cruise_mach', 0.78)
    ivc.add_output('TLAR:range', 500, units='NM')
    ivc.add_output('aerodynamics:aircraft:cruise:L_D_max', 16.)
    ivc.add_output('weight:aircraft:payload', 15076, units='kg')
    ivc.add_output('weight:aircraft:OWE', 50000, units='kg')

    ivc.add_output('propulsion:rubber_engine:bypass_ratio', 5)
    ivc.add_output('propulsion:rubber_engine:maximum_mach', 0.95)
    ivc.add_output('propulsion:rubber_engine:design_altitude', 35000, units='ft')
    ivc.add_output('propulsion:MTO_thrust', 100000, units='N')
    ivc.add_output('propulsion:rubber_engine:overall_pressure_ratio', 30)
    ivc.add_output('propulsion:rubber_engine:turbine_inlet_temperature', 1500, units='K')

    group = om.Group()

    group.add_subsystem('engine', OMRubberEngine(), promotes=['*'])
    group.add_subsystem('breguet', BreguetFromOWE(), promotes=['*'])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = run_system(group, ivc)

    assert_allclose(problem['weight:aircraft:MTOW'], 74000., atol=10)
    assert_allclose(problem['mission:sizing:ZFW'], 65076., atol=1)
    assert_allclose(problem['mission:sizing:mission:fuel'], 8924., atol=1)
