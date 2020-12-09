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


AVL_RESULTS = pth.join(pth.dirname(__file__), "results")

AVL_PATH = None


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
        nodes = np.zeros((sect * 2, 3))
        nodes[:, 0] = np.linspace(11.5, 19.42, sect * 2)
        nodes[:sect, 1] = np.linspace(1.96, 17.5, sect * 2)
        nodes[sect:, 1] = -nodes[:sect, 1]
    if comp == "horizontal_tail":
        nodes = np.zeros((sect * 2, 3))
        nodes[:, 0] = np.linspace(32.4, 36.44, sect)
        nodes[:sect, 1] = np.linspace(0, 6.15, sect)
        nodes[sect:, 1] = -nodes[:sect, 1]
        nodes[:, 2] = 1.02
    if comp == "vertical_tail":
        nodes = np.zeros((sect, 3))
        nodes[:, 0] = np.linspace(30.5, 36.4, sect)
        nodes[:, 2] = np.linspace(2.03, 8.93, sect)
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
        chords = np.linspace(6.20, 2.3, sect)
    if comp == "horizontal_tail":
        chords = np.linspace(4.4, 1.3, sect)
    if comp == "vertical_tail":
        chords = np.linspace(6.0, 1.8, sect)
    if comp == "fuselage":
        chords = np.zeros(12)
        chords[0] = chords[3] = chords[6] = chords[9] = 37.5
        chords[1] = chords[4] = chords[10] = 37.5 - 3.45 - 7.3
        chords[2] = chords[5] = chords[11] = 37.5 - 6.9 - 14.6
        chords[7] = 37.5 - 3.45
        chords[8] = 37.5 - 6.9
    return chords


@pytest.mark.skipif(
    system() != "Windows" and AVL_PATH is None, reason="No XFOIL executable available"
)
def test_compute():
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
    ]

    def get_cl_cdi_forces(components, sections):
        ivc = get_indep_var_comp(input_list)
        ivc.add_output("data:aerostructural:load_case:weight", 60000, units="kg")
        for comp, sect in zip(components, sections):
            nodes = _get_nodes(comp, sect)
            ivc.add_output("data:aerostructural:aerodynamic:" + comp + "nodes", nodes)
            chords = _get_chords(comp, sect)
            ivc.add_output("data:aerostructural:aerodynamic:" + comp + "chord", chords)
            if comp == "wing":
                twist = np.linspace(3, -1, sect)
                t_c = np.linspace(0.12, 0.1, sect)
                ivc.add_output("data:aerostructural:aerodynamic:wing:twist", twist)
                ivc.add_output("data:aerostructural:aerodynamic:wing:thickness_ratios", t_c)

        avl_comp = AVL(components=components, components_sections=sections, sizing=False)
        problem = run_system(avl_comp, ivc)
        cl = problem["data:aerostructural:aerodynamic:CL"]
        cdi = problem["data:aerostructural:aerodynamic:CDi"]
        oswald = problem["data:aerostructural:aerodynamic:Oswald_Coeff"]
        forces = problem["data:aerostructural:aerodynamic:forces"]
        return cl, cdi, oswald, forces

    assert get_cl_cdi_forces(["wing", "fuselage"], [12, 3])[0] == approx(0.37, abs=1e-3)
    assert get_cl_cdi_forces(["wing", "fuselage"], [12, 3])[1] == approx(0.01274, abs=1e-5)
    assert get_cl_cdi_forces(["wing", "fuselage"], [12, 3])[2] == approx(0.6573, abs=1e-4)

    # Test with only wing and fuselage
