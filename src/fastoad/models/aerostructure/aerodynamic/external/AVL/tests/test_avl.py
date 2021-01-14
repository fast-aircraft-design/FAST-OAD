"""
Test module for AVL component
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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
import shutil
from platform import system


import numpy as np

import pytest
from pytest import approx
from fastoad.io import VariableIO
from fastoad.models.aerostructure.aerodynamic.external.AVL.avl import AVL
from tests.testing_utilities import run_system
from tests.avl_exe.get_avl import get_avl_path


AVL_RESULTS = pth.join(pth.dirname(__file__), "results")
AVL_PATH = None if system() == "Windows" else get_avl_path()


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "avl_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def _get_nodes(comp, sect):
    """
    Gives nodes coordinates for simplified geometry depending on the number of sections
    :param comp: component names
    :param sect: number of section for the component
    :return nodes: array containing sections leading edge nodes coordinates
    """
    nodes = np.nan
    if comp == "wing":
        nodes = np.zeros(((sect + 1) * 2, 3))
        nodes[: sect + 1, 0] = nodes[sect + 1 :, 0] = np.linspace(11.5, 19.44, sect + 1)
        nodes[: sect + 1, 1] = np.linspace(1.96, 17.5, sect + 1)
        nodes[sect + 1 :, 1] = -nodes[: sect + 1, 1]
    if comp == "horizontal_tail":
        nodes = np.zeros(((sect + 1) * 2, 3))
        nodes[: sect + 1, 0] = nodes[sect + 1 :, 0] = np.linspace(32.4, 36.44, sect + 1)
        nodes[: sect + 1, 1] = np.linspace(0, 6.15, sect + 1)
        nodes[sect + 1 :, 1] = -nodes[: sect + 1, 1]
        nodes[:, 2] = 1.02
    if comp == "vertical_tail":
        nodes = np.zeros((sect + 1, 3))
        nodes[:, 0] = np.linspace(30.5, 36.4, sect + 1)
        nodes[:, 2] = np.linspace(2.03, 8.93, sect + 1)
    if comp == "fuselage":
        nodes = np.zeros((12, 3))
        nodes[:3, 0] = nodes[3:6, 0] = nodes[6:9, 0] = nodes[9:12, 0] = np.linspace(0.0, 6.9, 3)
        nodes[:3, 1] = np.linspace(0.0, 1.96, 3)
        nodes[3:6, 1] = -nodes[:3, 1]
        nodes[6:9, 2] = np.linspace(0.0, 2.03, 3)
        nodes[9:12, 2] = -nodes[6:9, 2]
    return nodes


def _get_chords(comp, sect):
    """
    Gives length of each section of each component for simplified geometry (rectangular wing).
    :param comp: component's name
    :param sect: number of section of the component
    :return chords: array of section length for a given component
    """
    chords = np.nan
    if comp == "wing":
        chords = np.tile(np.linspace(6.20, 2.3, sect + 1), 2)
    if comp == "horizontal_tail":
        chords = np.tile(np.linspace(4.4, 1.3, sect + 1), 2)
    if comp == "vertical_tail":
        chords = np.linspace(6.0, 1.8, sect + 1)
    if comp == "fuselage":
        chords = np.zeros(12)
        chords[0] = chords[3] = chords[6] = chords[9] = 37.5
        chords[1] = chords[4] = chords[10] = 37.5 - 3.45 - 7.3
        chords[2] = chords[5] = chords[11] = 37.5 - 6.9 - 14.6
        chords[7] = 37.5 - 3.45
        chords[8] = 37.5 - 6.9
    return chords


def get_ivc_for_components(
    components: list, sections: list, input_list: list, load_case: dict,
):
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:aerostructural:load_case:weight", load_case["weight"], units="kg")
    ivc.add_output("data:aerostructural:load_case:altitude", load_case["altitude"], units="ft")
    ivc.add_output("data:aerostructural:load_case:load_factor", load_case["load_factor"])
    ivc.add_output("data:aerostructural:load_case:mach", load_case["mach"])
    for comp, sect in zip(components, sections):
        nodes = _get_nodes(comp, sect)
        ivc.add_output("data:aerostructural:aerodynamic:" + comp + ":nodes", nodes)
        chords = _get_chords(comp, sect)
        ivc.add_output("data:aerostructural:aerodynamic:" + comp + ":chords", chords)
        if comp == "wing":
            twist = np.tile(np.linspace(3, -1, sect + 1), 2)
            t_c = np.tile(np.linspace(0.12, 0.1, sect + 1), 2)
            ivc.add_output("data:aerostructural:aerodynamic:wing:twist", twist)
            ivc.add_output("data:aerostructural:aerodynamic:wing:thickness_ratios", t_c)
    return ivc


@pytest.mark.skipif(
    system() != "Windows" and AVL_PATH is None, reason="No AVL executable available"
)
def test_avl_design():
    """
    Test simple AVL computation without sizing option (nz=1.0) and simplified rectangular swept wing
    """
    if pth.exists(AVL_RESULTS):
        shutil.rmtree(AVL_RESULTS)
    input_list = [
        "data:geometry:wing:span",
        "data:geometry:wing:area",
        "data:geometry:wing:sweep_0",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:at25percent:x",
        "tuning:aerostructural:aerodynamic:chordwise_spacing:k",
    ]

    # Test with only wing and fuselage -------------------------------------------------------------
    load_case = {"weight": 60000, "altitude": 35000, "mach": 0.78, "load_factor": 1.0}
    components = ["wing", "fuselage"]
    sections = [11, 12]
    ivc = get_ivc_for_components(components, sections, input_list, load_case)

    avl_comp = AVL(components=components, components_sections=sections)
    problem = run_system(avl_comp, ivc)
    assert problem["data:aerostructural:aerodynamic:CL"][0] == approx(0.37, abs=1e-3)
    assert problem["data:aerostructural:aerodynamic:CDi"][0] == approx(0.011373, abs=1e-5)
    assert problem["data:aerostructural:aerodynamic:Oswald_Coeff"][0] == approx(0.6678, abs=1e-4)
    assert not pth.exists(pth.join(pth.dirname(__file__), "results"))
    # Test for complete aircraft (wing, fuselage, tails) -------------------------------------------
    components = ["wing", "horizontal_tail", "vertical_tail", "fuselage"]
    sections = [11, 11, 5, 12]
    ivc = get_ivc_for_components(components, sections, input_list, load_case)

    avl_comp = AVL(components=components, components_sections=sections)
    problem = run_system(avl_comp, ivc)
    assert problem["data:aerostructural:aerodynamic:CL"][0] == approx(0.37, abs=1e-3)
    assert problem["data:aerostructural:aerodynamic:CDi"][0] == approx(0.0097103, abs=1e-5)
    assert problem["data:aerostructural:aerodynamic:Oswald_Coeff"][0] == approx(0.7766, abs=1e-4)
    assert not pth.exists(pth.join(pth.dirname(__file__), "results"))
    # Test with results directory provided ---------------------------------------------------------
    components = ["wing", "horizontal_tail", "vertical_tail", "fuselage"]
    sections = [11, 11, 5, 12]
    ivc = get_ivc_for_components(components, sections, input_list, load_case)

    avl_comp = AVL(
        components=components, components_sections=sections, result_folder_path=AVL_RESULTS
    )
    problem = run_system(avl_comp, ivc)
    assert problem["data:aerostructural:aerodynamic:CL"][0] == approx(0.37, abs=1e-3)
    assert problem["data:aerostructural:aerodynamic:CDi"][0] == approx(0.0097103, abs=1e-5)
    assert problem["data:aerostructural:aerodynamic:Oswald_Coeff"][0] == approx(0.7766, abs=1e-4)
    assert pth.exists(AVL_RESULTS)
    assert pth.exists(pth.join(AVL_RESULTS, "results.out"))


@pytest.mark.skipif(
    system() != "Windows" and AVL_PATH is None, reason="No AVL executable available"
)
def test_avl_sizing():
    """
    Test simple AVL computation with sizing option (nz=2.5) and simplified rectangular swept wing
    """
    if pth.exists(AVL_RESULTS):
        shutil.rmtree(AVL_RESULTS)
    input_list = [
        "data:geometry:wing:span",
        "data:geometry:wing:area",
        "data:geometry:wing:sweep_0",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:at25percent:x",
        "tuning:aerostructural:aerodynamic:chordwise_spacing:k",
    ]

    # Test with only wing and fuselage -------------------------------------------------------------
    load_case = {"weight": 78000, "altitude": 30000, "mach": 0.84, "load_factor": 2.5}
    components = ["wing", "fuselage"]
    sections = [11, 12]
    ivc = get_ivc_for_components(components, sections, input_list, load_case)
    avl_comp = AVL(components=components, components_sections=sections)
    problem = run_system(avl_comp, ivc)

    forces_test = np.loadtxt(
        pth.join(pth.dirname(__file__), "data", "forces_results_wing_fuse_2p5g"), skiprows=1
    )
    f_test_w = forces_test[:-4, :]  # Remove fuselage surfaces forces
    f_test_f = forces_test[-4:, :]  # Remove wings surfaces forces
    for f_fast, f_test in zip(problem["data:aerostructural:aerodynamic:wing:forces"], f_test_w):
        assert f_fast[0] == approx(f_test[0], rel=1e-3)
        assert f_fast[1] == approx(f_test[1], rel=1e-3)
        assert f_fast[2] == approx(f_test[2], rel=1e-3)
        assert f_fast[4] == approx(f_test[4], rel=1e-2)
        assert f_fast[5] == approx(f_test[5], rel=1e-2)
    for f_fast, f_test in zip(problem["data:aerostructural:aerodynamic:fuselage:forces"], f_test_f):
        assert f_fast[0] == approx(f_test[0], rel=1e-3)
        assert f_fast[1] == approx(f_test[1], rel=1e-3)
        assert f_fast[2] == approx(f_test[2], rel=1e-3)
        assert f_fast[4] == approx(f_test[4], rel=1e-2)
        assert f_fast[5] == approx(f_test[5], rel=1e-2)

    # Test for complete aircraft (wing, fuselage, tails) -------------------------------------------
    components = ["wing", "horizontal_tail", "vertical_tail", "fuselage"]
    sections = [11, 11, 5, 12]
    ivc = get_ivc_for_components(components, sections, input_list, load_case)

    avl_comp = AVL(components=components, components_sections=sections)
    problem = run_system(avl_comp, ivc)
    forces_test = np.loadtxt(
        pth.join(pth.dirname(__file__), "data", "forces_results_full_2p5g"), skiprows=1
    )
    f_test_w = forces_test[:22, :]  # Wings surface forces & moments
    f_test_h = forces_test[22:44, :]  # Horizontal tails surface forces & moments
    f_test_v = forces_test[44:49, :]  # Vertical tail surface forces & moments
    f_test_f = forces_test[49:, :]  # Fuselage surface forces & moments

    for f_fast, f_test in zip(problem["data:aerostructural:aerodynamic:wing:forces"], f_test_w):
        assert f_fast[0] == approx(f_test[0], rel=1e-3)
        assert f_fast[1] == approx(f_test[1], rel=1e-3)
        assert f_fast[2] == approx(f_test[2], rel=1e-3)
        assert f_fast[4] == approx(f_test[4], rel=1e-2)
        assert f_fast[5] == approx(f_test[5], rel=1e-2)
    for f_fast, f_test in zip(
        problem["data:aerostructural:aerodynamic:horizontal_tail:forces"], f_test_h
    ):
        assert f_fast[0] == approx(f_test[0], rel=1e-3)
        assert f_fast[1] == approx(f_test[1], rel=1e-3)
        assert f_fast[2] == approx(f_test[2], rel=1e-3)
        assert f_fast[4] == approx(f_test[4], rel=1e-2)
        assert f_fast[5] == approx(f_test[5], rel=1e-2)
    for f_fast, f_test in zip(
        problem["data:aerostructural:aerodynamic:vertical_tail:forces"], f_test_v
    ):
        assert f_fast[0] == approx(f_test[0], rel=1e-3)
        assert f_fast[1] == approx(f_test[1], rel=1e-3)
        assert f_fast[2] == approx(f_test[2], rel=1e-3)
        assert f_fast[4] == approx(f_test[4], rel=1e-2)
        assert f_fast[5] == approx(f_test[5], rel=1e-2)
    for f_fast, f_test in zip(problem["data:aerostructural:aerodynamic:fuselage:forces"], f_test_f):
        assert f_fast[0] == approx(f_test[0], rel=1e-3)
        assert f_fast[1] == approx(f_test[1], rel=1e-3)
        assert f_fast[2] == approx(f_test[2], rel=1e-3)
        assert f_fast[4] == approx(f_test[4], rel=1e-2)
        assert f_fast[5] == approx(f_test[5], rel=1e-2)


@pytest.mark.skipif(
    system() != "Windows" and AVL_PATH is None, reason="No AVL executable available"
)
def test_avl_path():
    """
    Tests AVL with a specified exe path.
    :return:
    """
    if pth.exists(AVL_RESULTS):
        shutil.rmtree(AVL_RESULTS)
    input_list = [
        "data:geometry:wing:span",
        "data:geometry:wing:area",
        "data:geometry:wing:sweep_0",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:at25percent:x",
        "tuning:aerostructural:aerodynamic:chordwise_spacing:k",
    ]

    # Test with only wing and fuselage -------------------------------------------------------------
    load_case = {"weight": 60000, "altitude": 35000, "mach": 0.78, "load_factor": 1.0}
    components = ["wing", "fuselage"]
    sections = [11, 12]
    ivc = get_ivc_for_components(components, sections, input_list, load_case)

    avl_comp = AVL(components=components, components_sections=sections)

    avl_comp.options["avl_exe_path"] = "Dummy"  # bad name
    with pytest.raises(ValueError):
        problem = run_system(avl_comp, ivc)

    avl_comp.options["avl_exe_path"] = (
        AVL_PATH if AVL_PATH else pth.join(pth.dirname(__file__), pth.pardir, "avl336", "avl.exe")
    )
    problem = run_system(avl_comp, ivc)
    assert problem["data:aerostructural:aerodynamic:CL"] == approx(0.37, abs=1e-3)
    assert problem["data:aerostructural:aerodynamic:CDi"] == approx(0.011373, abs=1e-5)
    assert problem["data:aerostructural:aerodynamic:Oswald_Coeff"] == approx(0.6678, abs=1e-4)
