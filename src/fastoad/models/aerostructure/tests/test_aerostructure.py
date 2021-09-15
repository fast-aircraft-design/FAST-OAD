#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from platform import system

import numpy as np
import pytest

from fastoad.io import VariableIO
from fastoad.models.aerostructure.static_solver import StaticSolver
from tests.testing_utilities import run_system


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "aerostructure_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


@pytest.mark.skipif(system() != "Windows", reason="No AVL nor MYSTRAN executable available")
def test_aerostructure():
    input_list = [
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:leading_edge:x:local",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:wing:root:y",
        "data:geometry:wing:root:z",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:root:twist",
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:z",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:kink:twist",
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:tip:z",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:wing:tip:twist",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:spar_ratio:front:root",
        "data:geometry:wing:spar_ratio:rear:root",
        "data:geometry:wing:spar_ratio:front:kink",
        "data:geometry:wing:spar_ratio:rear:kink",
        "data:geometry:wing:spar_ratio:front:tip",
        "data:geometry:wing:spar_ratio:rear:tip",
        "data:geometry:wing:sweep_0",
        "data:geometry:wing:span",
        "data:geometry:wing:area",
        "data:geometry:horizontal_tail:MAC:at25percent:x:local",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:horizontal_tail:MAC:length",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_0",
        "data:geometry:horizontal_tail:thickness_ratio",
        "data:geometry:horizontal_tail:root:z",
        "data:geometry:horizontal_tail:tip:z",
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry: horizontal_tail:root:z",
        "data:geometry:horizontal_tail:tip:chord",
        "data:geometry: horizontal_tail:tip:z",
        "data:geometry:vertical_tail:MAC:at25percent:x:local",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:vertical_tail:MAC:length",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:sweep_0",
        "data:geometry:vertical_tail:thickness_ratio",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:front_length",
        "data:geometry:fuselage:rear_length",
        "data:geometry:fuselage:length",
        "data:aerostructural:load_case:mach",
        "data:aerostructural:load_case:d_isa",
        "data:aerostructural:load_case:weight",
        "data:aerostructural:load_case:altitude",
    ]
    comps = ["wing"]
    sects = [5]
    interp = ["linear"]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(
        StaticSolver(
            coupled_components=comps,
            aerodynamic_components_sections=sects,
            structural_components_sections=sects,
            coupled_components_interpolations=interp,
        ),
        ivc,
    )
    tz_test = np.array(
        [
            0,
            0.27501,
            1.00444,
            2.03933,
            3.23936,
            4.48776,
            0,
            0.27501,
            1.00444,
            2.03933,
            3.23936,
            4.48776,
        ]
    )
    ry_test = np.array(
        [
            0.0,
            -0.01241,
            -0.02202,
            -0.02848,
            -0.03150,
            -0.03150,
            0.0,
            -0.01241,
            -0.02202,
            -0.02848,
            -0.03150,
            -0.03150,
        ]
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:wing:displacements"][:, 2], tz_test, atol=1e-2
    )
    np.testing.assert_allclose(
        problem["data:aerostructural:structure:wing:displacements"][:, 4], ry_test, atol=1e-5
    )
