"""
Test module for XFOIL component
"""
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

# pylint: disable=redefined-outer-name  # needed for fixtures

import os.path as pth
import shutil
from platform import system

import pytest
from openmdao.core.indepvarcomp import IndepVarComp

from tests.testing_utilities import run_system
from tests.xfoil_exe.get_xfoil import get_xfoil_path
from ..xfoil_polar import XfoilPolar, DEFAULT_2D_CL_MAX

XFOIL_RESULTS = pth.join(pth.dirname(__file__), "results")

xfoil_path = None if system() == "Windows" else get_xfoil_path()


@pytest.mark.skipif(
    system() != "Windows" and xfoil_path is None, reason="No XFOIL executable available"
)
def test_compute():
    """ Tests a simple XFOIL run"""

    if pth.exists(XFOIL_RESULTS):
        shutil.rmtree(XFOIL_RESULTS)

    ivc = IndepVarComp()
    ivc.add_output("xfoil:reynolds", 18000000)
    ivc.add_output("xfoil:mach", 0.20)
    ivc.add_output("data:geometry:wing:thickness_ratio", 0.1284)

    xfoil_comp = XfoilPolar(
        alpha_start=15.0, alpha_end=25.0, iter_limit=20, xfoil_exe_path=xfoil_path
    )
    problem = run_system(xfoil_comp, ivc)
    assert problem["xfoil:CL_max_2D"] == pytest.approx(1.94, 1e-2)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil_comp = XfoilPolar(
        alpha_start=12.0, alpha_end=20.0, iter_limit=20, xfoil_exe_path=xfoil_path
    )  # will stop before real max CL
    problem = run_system(xfoil_comp, ivc)
    assert problem["xfoil:CL_max_2D"] == pytest.approx(1.92, 1e-2)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil_comp = XfoilPolar(
        alpha_start=50.0, alpha_end=55.0, iter_limit=2, xfoil_exe_path=xfoil_path
    )  # will not converge
    problem = run_system(xfoil_comp, ivc)
    assert problem["xfoil:CL_max_2D"] == pytest.approx(DEFAULT_2D_CL_MAX, 1e-2)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil_comp = XfoilPolar(
        iter_limit=20, result_folder_path=XFOIL_RESULTS, xfoil_exe_path=xfoil_path
    )
    problem = run_system(xfoil_comp, ivc)
    assert problem["xfoil:CL_max_2D"] == pytest.approx(1.94, 1e-2)
    assert pth.exists(XFOIL_RESULTS)
    assert pth.exists(pth.join(XFOIL_RESULTS, "polar_result.txt"))


@pytest.mark.skipif(
    system() != "Windows" and xfoil_path is None, reason="No XFOIL executable available"
)
def test_compute_with_provided_path():
    """ Test that option "use_exe_path" works """
    ivc = IndepVarComp()
    ivc.add_output("xfoil:reynolds", 18000000)
    ivc.add_output("xfoil:mach", 0.20)
    ivc.add_output("data:geometry:wing:thickness_ratio", 0.1284)

    xfoil_comp = XfoilPolar(alpha_start=18.0, alpha_end=21.0, iter_limit=20)
    xfoil_comp.options["xfoil_exe_path"] = "Dummy"  # bad name
    with pytest.raises(ValueError):
        problem = run_system(xfoil_comp, ivc)

    xfoil_comp.options["xfoil_exe_path"] = (
        xfoil_path
        if xfoil_path
        else pth.join(pth.dirname(__file__), pth.pardir, "xfoil699", "xfoil.exe")
    )
    problem = run_system(xfoil_comp, ivc)
    assert problem["xfoil:CL_max_2D"] == pytest.approx(1.94, 1e-2)
