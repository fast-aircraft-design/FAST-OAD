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


import os
import os.path as pth
from tempfile import TemporaryDirectory
import shutil

import openmdao.api as om
import numpy as np

from fastoad.models.aerostructure.structure.external.mystran.utils.read_f06 import readf06
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import get_nodes_cards
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import get_props_cards
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import get_mat_cards
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import (
    get_rbe_junction_cards,
)
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import get_forces_cards
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import get_bc_cards
from fastoad.models.aerostructure.structure.external.mystran.utils.get_cards import get_nastran_bdf
from fastoad.utils.resource_management.copy import copy_resource

from fastoad.models.aerostructure.structure.external.mystran import mystran112

OPTION_MYSTRAN_EXE_PATH = "mystran_exe_path"
OPTION_RESULT_FOLDER_PATH = "result_folder_path"

_TMP_INPUT_FILE_NAME = "run.dat"
_TMP_OUTPUT_FILE_NAME = "run.F06"
_STDERR_FILE_NAME = "run.ERR"
MYSTRAN_EXE_NAME = "MYSTRAN.exe"


class MystranStatic(om.ExternalCodeComp):
    """
    Runs linear static analysis using MYSTRAN and returns displacements and stresses
    for each structural component e.g. wing, fuselage, horizontal tail, vertical tail
    """

    def initialize(self):
        self.options.declare("components", types=list)
        self.options.declare("components_sections", types=list)
        self.options.declare(OPTION_MYSTRAN_EXE_PATH, default="", types=str, allow_none=True)
        self.options.declare(OPTION_RESULT_FOLDER_PATH, default="", types=str, allow_none=True)

    def setup(self):
        comps = self.options["components"]
        nsects = self.options["components_sections"]

        # System inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:aerostructural:load_case:load_factor", val=1.0)
        for comp, nsect in zip(comps, nsects):
            if comp == "wing":
                n_nodes = (nsect + 1) * 2 + 2
                n_props = (nsect + 1) * 2
            elif comp in ("horizontal_tail", "strut"):
                n_nodes = (nsect + 1) * 2
                n_props = nsect * 2
            else:
                n_nodes = nsect + 1
                n_props = nsect
            self.add_input("data:aerostructural:structure:" + comp + ":nodes", shape_by_conn=True)
            self.add_input(
                "data:aerostructural:structure:" + comp + ":beam_properties", shape_by_conn=True
            )
            self.add_input(
                "data:aerostructural:structure:" + comp + ":nodal_forces_moments",
                shape_by_conn=True,
            )
            self.add_input("data:aerostructural:structure:" + comp + ":material:E", val=70e9)
            self.add_input("data:aerostructural:structure:" + comp + ":material:mu", val=0.33)
            self.add_input(
                "data:aerostructural:structure:" + comp + ":material:density", val=2810.0
            )

            self.add_output(
                "data:aerostructural:structure:" + comp + ":displacements", shape=(n_nodes, 6)
            )

            self.add_output(
                "data:aerostructural:structure:" + comp + ":stresses", shape=(n_props, 4)
            )

            # Initialisation of the MYSTRAN (NASTRAN) input file (.dat) ----------------------------
        self.input_file = ""

    def compute(self, inputs, outputs):
        result_folder_path = self.options[OPTION_RESULT_FOLDER_PATH]
        if result_folder_path != "":
            os.makedirs(result_folder_path, exist_ok=True)

        components = self.options["components"]
        nsects = self.options["components_sections"]

        # Prepare input file ----------------------------------------------------------------------
        cg_loc = inputs["data:geometry:wing:MAC:at25percent:x"]
        nz = inputs["data:aerostructural:load_case:load_factor"]
        strg = []
        for comp in components:
            mat_prop = np.zeros(3)
            nodes = inputs["data:aerostructural:structure:" + comp + ":nodes"]
            props = inputs["data:aerostructural:structure:" + comp + ":beam_properties"]
            forces = inputs["data:aerostructural:structure:" + comp + ":nodal_forces_moments"]
            mat_prop[0] = inputs["data:aerostructural:structure:" + comp + ":material:E"]
            mat_prop[1] = inputs["data:aerostructural:structure:" + comp + ":material:mu"]
            mat_prop[2] = inputs["data:aerostructural:structure:" + comp + ":material:density"]
            strg += get_nodes_cards(comp, nodes)
            strg += get_props_cards(comp, props)
            strg += get_mat_cards(comp, mat_prop)
            strg += get_rbe_junction_cards(comp, nodes)
            strg += get_forces_cards(comp, forces)
            if comp != "strut":
                master = "fuselage"
                master_nodes = inputs["data:aerostructural:structure:fuselage:nodes"]
                strg += get_bc_cards(comp, master, master_nodes, nodes, cg_loc)
            if comp == "strut":
                master = "fuselage"
                master_nodes = inputs["data:aerostructural:structure:fuselage:nodes"]
                strg += get_bc_cards(comp, master, master_nodes, nodes, cg_loc)
                master = "wing"
                master_nodes = inputs["data:aerostructural:structure:wing:nodes"]
                strg += get_bc_cards(comp, master, master_nodes, nodes, cg_loc)

        tmp_dir = TemporaryDirectory()
        self.input_file = pth.join(tmp_dir.name, _TMP_INPUT_FILE_NAME)
        if self.options[OPTION_MYSTRAN_EXE_PATH]:
            # if a path for MYSTRAN has been provided, simply use it
            self.options["command"] = [self.options[OPTION_MYSTRAN_EXE_PATH], self.input_file]
        else:
            # otherwise, copy the embedded resource in tmp dir
            copy_resource(mystran112, MYSTRAN_EXE_NAME, tmp_dir.name)
            self.options["command"] = [pth.join(tmp_dir.name, MYSTRAN_EXE_NAME), self.input_file]

        # Input BDF file generation ---------------------------------------------------------------
        get_nastran_bdf(self.input_file, strg, sol="static", nz=nz)
        self.sderr = pth.join(tmp_dir.name, _STDERR_FILE_NAME)
        # Run MYSTRAN -----------------------------------------------------------------------------
        result_file = pth.join(tmp_dir.name, _TMP_OUTPUT_FILE_NAME)
        # self.options["external_input_files"] = [input_file]
        # self.options["external_output_files"] = [result_file]

        super().compute(inputs, outputs)

        # Post-processing -------------------------------------------------------------------------
        displacements, stresses = readf06(result_file)
        # split displacements and stresses matrices for each component
        splited_disp = self._get_component_disp(displacements, components, nsects)
        splited_stresses = self._get_component_stress(stresses, components, nsects)
        for i, comp in enumerate(components):
            outputs["data:aerostructural:structure:" + comp + ":displacements"] = splited_disp[i]
            outputs["data:aerostructural:structure:" + comp + ":stresses"] = splited_stresses[i]

        # Getting output files if needed ----------------------------------------------------------
        if self.options[OPTION_RESULT_FOLDER_PATH]:
            if pth.exists(result_file):
                f06_file_path = pth.join(result_folder_path, _TMP_OUTPUT_FILE_NAME)
                shutil.move(result_file, f06_file_path)

            if pth.exists(self.input_file):
                bdf_file_path = pth.join(result_folder_path, _TMP_INPUT_FILE_NAME)
                shutil.move(self.input_file, bdf_file_path)

        tmp_dir.cleanup()

    @staticmethod
    def _get_component_disp(disp_matrix, comps, nsects):

        split_sections = np.zeros(len(nsects), dtype=int)

        for i in range(0, len(comps)):
            if comps[i] == "wing":
                n_nodes = (nsects[i] + 1) * 2 + 2
            elif comps[i] == "horizontal_tail" or comps[i] == "strut":
                n_nodes = (nsects[i] + 1) * 2
            else:
                n_nodes = nsects[i] + 1
            if i != 0:
                split_sections[i] = int(n_nodes) + split_sections[i - 1]
            else:
                split_sections[i] = int(n_nodes)
        return np.split(disp_matrix, split_sections)

    @staticmethod
    def _get_component_stress(stress_matrix, comps, nsects):

        split_sections = np.zeros(len(nsects), dtype=int)

        for i in range(0, len(comps)):
            if comps[i] == "wing":
                n_nodes = (nsects[i] + 1) * 2
            elif comps[i] == "horizontal_tail" or comps[i] == "strut":
                n_nodes = nsects[i] * 2
            else:
                n_nodes = nsects[i]
            if i != 0:
                split_sections[i] = int(n_nodes) + split_sections[i - 1]
            else:
                split_sections[i] = int(n_nodes)
        return np.split(stress_matrix, split_sections)
