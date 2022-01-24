"""
Test module for aerodynamics groups
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

import pytest
from pytest import approx

from fastoad._utils.testing import run_system
from fastoad.io import VariableIO
from ..aerodynamics_landing import AerodynamicsLanding


def get_indep_var_comp(var_names):
    """Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "aerodynamics_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


@pytest.mark.skip_if_no_xfoil()
def test_aerodynamics_landing_with_xfoil(xfoil_path):
    """Tests AerodynamicsHighSpeed"""
    input_list = [
        "data:TLAR:approach_speed",
        "data:mission:sizing:landing:flap_angle",
        "data:mission:sizing:landing:slat_angle",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:thickness_ratio",
        "data:geometry:wing:sweep_25",
        "data:geometry:wing:sweep_0",
        "data:geometry:wing:sweep_100_outer",
        "data:geometry:flap:chord_ratio",
        "data:geometry:flap:span_ratio",
        "data:geometry:slat:chord_ratio",
        "data:geometry:slat:span_ratio",
        "xfoil:mach",
        "tuning:aerodynamics:aircraft:landing:CL_max:landing_gear_effect:k",
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(AerodynamicsLanding(xfoil_exe_path=xfoil_path), ivc)
    # Reference values are for Windows XFOIL version, but as results can be slightly different on other
    # platforms, tolerance is extended to 1e-2
    assert problem["data:aerodynamics:aircraft:landing:CL_max_clean"] == approx(1.59359, abs=1e-2)
    assert problem["data:aerodynamics:aircraft:landing:CL_max"] == approx(2.82178, abs=1e-2)


def test_aerodynamics_landing_without_xfoil():
    """Tests AerodynamicsHighSpeed"""
    input_list = [
        "data:TLAR:approach_speed",
        "data:mission:sizing:landing:flap_angle",
        "data:mission:sizing:landing:slat_angle",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:thickness_ratio",
        "data:geometry:wing:sweep_25",
        "data:geometry:wing:sweep_0",
        "data:geometry:wing:sweep_100_outer",
        "data:geometry:flap:chord_ratio",
        "data:geometry:flap:span_ratio",
        "data:geometry:slat:chord_ratio",
        "data:geometry:slat:span_ratio",
        "xfoil:mach",
        "tuning:aerodynamics:aircraft:landing:CL_max:landing_gear_effect:k",
        "data:aerodynamics:aircraft:landing:CL_max_clean_2D",
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(AerodynamicsLanding(use_xfoil=False), ivc)
    assert problem["data:aerodynamics:aircraft:landing:CL_max_clean"] == approx(1.54978, abs=1e-5)
    assert problem["data:aerodynamics:aircraft:landing:CL_max"] == approx(2.77798, abs=1e-5)
