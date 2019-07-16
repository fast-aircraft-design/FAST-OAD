"""
Test module for OpenMDAO extractor
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

from tests.io.xml.data.mass_breakdown.mass_breakdown import MassBreakdown
from openmdao.api import Problem
import numpy as np

from fastoad.openmdao.types import Variable

from fastoad.openmdao.extractor import get_vars_of_unconnected_inputs, build_ivc_of_unconnected_inputs

def test_get_variables_of_unconnected_inputs():

    known_optional_var_prom = Variable('kfactors_c2:K_C24', np.array([1.]), None)
    known_mandatory_var_prom = Variable('geometry:wing_area', np.array([np.nan]), 'm**2')

    system = MassBreakdown()

    problem = Problem()
    problem.model = system
    problem.setup()
    problem.run_model()
    
    mandatory_vars_prom, optional_vars_prom = get_vars_of_unconnected_inputs(problem)

    assert (str(known_optional_var_prom) in [str(i) for i in optional_vars_prom])
    assert (str(known_mandatory_var_prom) in [str(i) for i in mandatory_vars_prom])

def test_build_ivc_of_unconnected_inputs():

    known_optional_var_prom = Variable('kfactors_c2:K_C24', np.array([1.]), None)
    known_mandatory_var_prom = Variable('geometry:wing_area', np.array([np.nan]), 'm**2')

    system = MassBreakdown()

    problem = Problem()
    problem.model = system
    problem.setup()
    problem.run_model()

    ivc_no_opt = build_ivc_of_unconnected_inputs(problem, optional_inputs=False)
    ivc_with_opt = build_ivc_of_unconnected_inputs(problem, optional_inputs=True)
    
    outputs_no_opt = []
    for (name, value, attributes) in ivc_no_opt._indep_external:  # pylint: disable=protected-access
        outputs_no_opt.append(Variable(name, value, attributes['units']))

    outputs_with_opt = []
    for (name, value, attributes) in ivc_with_opt._indep_external:  # pylint: disable=protected-access
        outputs_with_opt.append(Variable(name, value, attributes['units']))

    assert not (str(known_optional_var_prom) in [str(i) for i in outputs_no_opt])
    assert (str(known_optional_var_prom) in [str(i) for i in outputs_with_opt])
    assert (str(known_mandatory_var_prom) in [str(i) for i in outputs_no_opt])
    assert (str(known_mandatory_var_prom) in [str(i) for i in outputs_with_opt])
