"""
Test module for OpenMDAO versions of RubberEngine
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

import openmdao.api as om
import pytest

from fastoad.constants import FlightPhase
from fastoad.modules.propulsion.fuel_engine.rubber_engine.openmdao import ManualRubberEngine, \
    RegulatedRubberEngine
from tests.testing_utilities import run_system


def test_ManualRubberEngine():
    """ Tests ManualRubberEngine component """
    # Same test as in test_rubber_engine.test_compute_manual
    engine = ManualRubberEngine(flight_point_count=5)

    ivc = om.IndepVarComp()
    ivc.add_output('bypass_ratio', 5)
    ivc.add_output('overall_pressure_ratio', 30)
    ivc.add_output('turbine_inlet_temperature', 1500, units='K')
    ivc.add_output('mto_thrust', 1, units='N')
    ivc.add_output('maximum_mach', 0.95)
    ivc.add_output('design_altitude', 10000, units='m')

    ivc.add_output('mach', [0, 0.3, 0.3, 0.8, 0.8], )
    ivc.add_output('altitude', [0, 0, 0, 10000, 13000], units='m')
    ivc.add_output('thrust_rate', [0.8, 0.5, 0.5, 0.4, 0.7])
    ivc.add_output('phase', [FlightPhase.TAKEOFF, FlightPhase.TAKEOFF,
                             FlightPhase.CLIMB, FlightPhase.IDLE,
                             FlightPhase.CRUISE.value])

    problem = run_system(engine, ivc)

    expected_thrust = [0.955 * 0.8, 0.389, 0.357, 0.0967, 0.113]
    expected_sfc = [0.993e-5, 1.35e-5, 1.35e-5, 1.84e-5, 1.60e-5]

    assert problem['thrust'] == pytest.approx(expected_thrust, rel=1e-2)
    assert problem['SFC'] == pytest.approx(expected_sfc, rel=1e-2)


def test_RegulatedRubberEngine():
    """ Tests RegulatedRubberEngine component """
    # Same test as in test_rubber_engine.test_compute_regulated
    engine = RegulatedRubberEngine(flight_point_count=5)

    ivc = om.IndepVarComp()
    ivc.add_output('bypass_ratio', 5)
    ivc.add_output('overall_pressure_ratio', 30)
    ivc.add_output('turbine_inlet_temperature', 1500, units='K')
    ivc.add_output('mto_thrust', 1, units='N')
    ivc.add_output('maximum_mach', 0.95)
    ivc.add_output('design_altitude', 10000, units='m')

    ivc.add_output('mach', [0, 0.3, 0.3, 0.8, 0.8], )
    ivc.add_output('altitude', [0, 0, 0, 10000, 13000], units='m')
    ivc.add_output('thrust', [0.955 * 0.8, 0.389, 0.357, 0.0967, 0.113], units='N')
    ivc.add_output('phase', [FlightPhase.TAKEOFF, FlightPhase.TAKEOFF,
                             FlightPhase.CLIMB, FlightPhase.IDLE,
                             FlightPhase.CRUISE.value])

    problem = run_system(engine, ivc)

    expected_thrust = [0.8, 0.5, 0.5, 0.4, 0.7]
    expected_sfc = [0.993e-5, 1.35e-5, 1.35e-5, 1.84e-5, 1.60e-5]

    assert problem['thrust_rate'] == pytest.approx(expected_thrust, rel=1e-2)
    assert problem['SFC'] == pytest.approx(expected_sfc, rel=1e-2)
