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
import shutil
from tempfile import TemporaryDirectory

import numpy as np
import openmdao.api as om
from pyNastran.bdf.bdf import BDF, CaseControlDeck

from fastoad._utils.resource_management.copy import copy_resource
from fastoad.models.aerostructure.structure.external.mystran import mystran112
from fastoad.models.aerostructure.structure.external.mystran.utils.constant import basis_id
from fastoad.models.aerostructure.structure.external.mystran.utils.read_f06 import readf06

OPTION_MYSTRAN_EXE_PATH = "mystran_exe_path"
OPTION_RESULT_FOLDER_PATH = "result_folder_path"

_TMP_INPUT_FILE_NAME = "run.dat"
_TMP_OUTPUT_FILE_NAME = "run.F06"
_TMP_BDF_FILE_NAME = "run.bdf"
_STDERR_FILE_NAME = "run.ERR"
_STDOUT_FILE_NAME = "mystran.log"
MYSTRAN_EXE_NAME = "MYSTRAN.exe"


class MystranStatic(om.ExternalCodeComp):
    """
    Runs linear static analysis using MYSTRAN and returns displacements and stresses
    for each structural component e.g. wing, fuselage, horizontal tail, vertical tail
    """

    def initialize(self):
        self.options.declare("structural_components", types=list)
        self.options.declare("structural_components_sections", types=list)
        self.options.declare(OPTION_MYSTRAN_EXE_PATH, default="", types=str, allow_none=True)
        self.options.declare(OPTION_RESULT_FOLDER_PATH, default="", types=str, allow_none=True)
        self.options.declare("coupling_iterations", types=bool, default=True)
        self.options.declare("has_vertical_strut", types=bool, default=False)

    def setup(self):
        comps = self.options["structural_components"]
        nsects = self.options["structural_components_sections"]
        coupling = self.options["coupling_iterations"]
        # System inputs ---------------------------------------------------------------------------
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:aerostructural:load_case:load_factor", val=1.0)
        for comp, nsect in zip(comps, nsects):
            if comp in ("wing", "horizontal_tail", "strut"):
                n_nodes = (nsect + 1) * 2
            else:
                n_nodes = nsect + 1

            self.add_input(
                "data:aerostructural:structure:" + comp + ":nodes", val=np.nan, shape_by_conn=True
            )
            self.add_input(
                "data:aerostructural:structure:" + comp + ":beam_properties",
                val=np.nan,
                shape_by_conn=True,
            )
            # By default no external loads are considered, to work for non coupled structural
            # Components. The force will be non zero for coupled components as aero is computed
            # first.
            self.add_input(
                "data:aerostructural:structure:" + comp + ":forces", val=0.0, shape=(n_nodes, 6),
            )
            self.add_input("data:aerostructural:structure:" + comp + ":material:E", val=70e9)
            self.add_input("data:aerostructural:structure:" + comp + ":material:nu", val=0.33)
            self.add_input(
                "data:aerostructural:structure:" + comp + ":material:density", val=2810.0
            )

            self.add_output(
                "data:aerostructural:structure:" + comp + ":displacements",
                val=0.0,
                shape=(n_nodes, 6),
                ref=1e-2,
                res_ref=1e-5,
            )

            self.add_output(
                "data:aerostructural:structure:" + comp + ":stresses",
                val=0.0,
                units="Pa",
                ref=100e6,
            )

            # Initialisation of the MYSTRAN (NASTRAN) input file ----------------------------
        self.input_file = ""

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        result_folder_path = self.options[OPTION_RESULT_FOLDER_PATH]
        coupling = self.options["coupling_iterations"]
        if result_folder_path != "":
            os.makedirs(result_folder_path, exist_ok=True)

        components = self.options["structural_components"]
        nsects = self.options["structural_components_sections"]

        # Prepare input file ----------------------------------------------------------------------
        tmp_dir = TemporaryDirectory()
        self.input_file = pth.join(tmp_dir.name, _TMP_BDF_FILE_NAME)
        if self.options[OPTION_MYSTRAN_EXE_PATH]:
            # if a path for MYSTRAN has been provided, simply use it
            self.options["command"] = [self.options[OPTION_MYSTRAN_EXE_PATH], self.input_file]
        else:
            # otherwise, copy the embedded resource in tmp dir
            copy_resource(mystran112, MYSTRAN_EXE_NAME, tmp_dir.name)
            self.options["command"] = [pth.join(tmp_dir.name, MYSTRAN_EXE_NAME), self.input_file]

        # Input BDF file generation ---------------------------------------------------------------
        # get_nastran_bdf(self.input_file, strg, sol="static", nz=nz)
        bdf_file = pth.join(tmp_dir.name, _TMP_BDF_FILE_NAME)
        self._prepare_bdf(inputs, components, bdf_file)
        self.sderr = pth.join(tmp_dir.name, _STDERR_FILE_NAME)
        self.stdout = pth.join(tmp_dir.name, _STDOUT_FILE_NAME)
        # Run MYSTRAN -----------------------------------------------------------------------------
        result_file = pth.join(tmp_dir.name, _TMP_OUTPUT_FILE_NAME)

        super().compute(inputs, outputs)

        # Post-processing -------------------------------------------------------------------------
        displacements, stresses = readf06(result_file)
        for i, comp in enumerate(components):
            comp_id = (i + 1) * 1000000
            outputs[
                "data:aerostructural:structure:" + comp + ":displacements"
            ] = self._get_component_matrix(displacements, comp_id)

            outputs["data:aerostructural:structure:" + comp + ":stresses"] = np.max(
                self._get_component_matrix(stresses, comp_id)
            )

        # Getting output files if needed ----------------------------------------------------------
        if self.options[OPTION_RESULT_FOLDER_PATH]:
            if pth.exists(result_file):
                f06_file_path = pth.join(result_folder_path, _TMP_OUTPUT_FILE_NAME)
                shutil.move(result_file, f06_file_path)

            if pth.exists(self.input_file):
                bdf_file_path = pth.join(result_folder_path, _TMP_INPUT_FILE_NAME)
                shutil.move(self.input_file, bdf_file_path)

            if pth.exists(bdf_file):
                bdf_file_path = pth.join(result_folder_path, _TMP_BDF_FILE_NAME)
                shutil.move(bdf_file, bdf_file_path)

        tmp_dir.cleanup()

    @staticmethod
    def _get_component_matrix(matrix, basis_id):
        """
        This function split a FEM results matrix into structural component matrices e.g.
        displacements for the wing.
        :param matrix: FEM results matrix
        :param comps: list of structural components
        :param nsects: number of section (elements) per components
        :param type: "grid" or "element" whether the results is grid-wise or element-wise.
        :return:
        """
        indices_component_sup = np.where(basis_id <= matrix[:, 0])
        indices_component_inf = np.where(basis_id + 1000000 > matrix[:, 0])
        indices_component = np.intersect1d(indices_component_inf, indices_component_sup)
        matrix_comp = matrix[indices_component, 1:]
        return matrix_comp

    @staticmethod
    def _get_component_stress(stress_matrix, comps, nsects):

        split_sections = np.zeros(len(nsects), dtype=int)

        for idx, comp in enumerate(comps):
            if comp in ("wing", "horizontal_tail", "strut"):
                n_nodes = nsects[idx] * 2
            else:
                n_nodes = nsects[idx]
            if idx != 0:
                split_sections[idx] = int(n_nodes) + split_sections[idx - 1]
            else:
                split_sections[idx] = int(n_nodes)
        return np.split(stress_matrix, split_sections)

    @staticmethod
    def _prepare_bdf(inputs, components, bdf_filename):
        bdf = BDF()
        bdf.sol = 1  # corresponds to SOL101 in Nastran (Linear static solution)
        case_control = CaseControlDeck(
            [
                "TITLE = STATIC WING SIZING",
                "DISP = ALL",
                "STRESS = ALL",
                "SPCFORCE = ALL",
                "SPC = 1",
                "LOAD = 2",
            ]
        )
        bdf.case_control_deck = case_control

        nz = inputs["data:aerostructural:load_case:load_factor"][0]

        for i, comp in enumerate(components):
            comp_id = (i + 1) * 1000000
            if comp == "strut":
                id_strut = comp_id
            if comp == "wing":
                id_wing = comp_id
            nodes = inputs["data:aerostructural:structure:" + comp + ":nodes"]
            properties = inputs["data:aerostructural:structure:" + comp + ":beam_properties"]
            forces = inputs["data:aerostructural:structure:" + comp + ":forces"]
            material_E = inputs["data:aerostructural:structure:" + comp + ":material:E"][0]
            material_nu = inputs["data:aerostructural:structure:" + comp + ":material:nu"][0]
            material_rho = inputs["data:aerostructural:structure:" + comp + ":material:density"][0]
            material_G = material_E / (2 + 2 * material_nu)
            mat_id = basis_id[comp] + 111000
            ident_matrix = np.identity(6)

            # Mat card -----------------------------------------------------------------------------
            bdf.add_mat1(mat_id, material_E, material_G, material_nu, rho=material_rho)

            # GRID FORCE and MOMENT cards ----------------------------------------------------------
            for idx, node in enumerate(nodes):
                bdf.add_grid(comp_id + idx, node)
                # RBE card to join symmetric parts
                if (
                    comp in ["wing", "strut", "horizontal_tail"]
                    and idx == np.size(nodes, axis=0) / 2
                ):
                    bdf.add_rbe2(comp_id + 10000000, comp_id, "123456", [comp_id + idx])

                # FORCE and MOMENT cards
                for j in [0, 1, 2]:
                    bdf.add_force(11, comp_id + idx, forces[idx, j], ident_matrix[j, :3])
                    bdf.add_moment(11, comp_id + idx, forces[idx, j + 3], ident_matrix[j + 3, 3:])

            # CBAR and PBAR cards ------------------------------------------------------------------
            for idx, prop in enumerate(properties):
                id1 = idx
                id2 = idx + 1
                elem_id = idx + 1000 + comp_id
                prop_id = idx + 11000 + comp_id

                if (
                    comp in ["wing", "horizontal_tail", "strut"]
                    and idx >= np.size(properties, axis=0) / 2
                ):
                    id1 = idx + 1
                    id2 = idx + 2

                dir_vect = nodes[id2, :] - nodes[id1, :]  # Direction vector of the beam element
                normal_vect = list(
                    np.cross(np.array([1.0, 0.0, 0.0]), dir_vect)
                )  # Normal vector to (x, dir_vect) plan
                bdf.add_cbar(
                    elem_id, prop_id, [id1 + comp_id, id2 + comp_id], x=normal_vect, g0=None
                )

                # PBAR cards
                bdf.add_pbar(
                    prop_id,
                    mat_id,
                    A=prop[0],
                    i1=prop[1],
                    i2=prop[2],
                    j=prop[3],
                    c1=prop[4],
                    c2=prop[5],
                    d1=prop[6],
                    d2=prop[7],
                    e1=prop[8],
                    e2=prop[9],
                    f1=prop[10],
                    f2=prop[11],
                )

            # Clamping card ------------------------------------------------------------------------
            bdf.add_spc1(i + 2, "123456", comp_id)

        # GRAV card --------------------------------------------------------------------------------
        bdf.add_grav(12, 9.806, [0.0, 0.0, -1.0])

        # LOAD card --------------------------------------------------------------------------------
        bdf.add_load(2, 1.0, [1.0, nz], [11, 12])

        # SPCADD card (to create problem boundary conditions) --------------------------------------
        bdf.add_spcadd(1, np.arange(2, 2 + len(components), 1, dtype=int))

        # Joining strut and wing if a strut exist --------------------------------------------------
        if "strut" in components:
            strut_nodes = inputs["data:aerostructural:structure:strut:nodes"]
            wing_nodes = inputs["data:aerostructural:structure:wing:nodes"]
            id_connect_right = np.where(wing_nodes[:, 1] == -strut_nodes[-1, 1])[0][0]
            id_connect_left = np.where(wing_nodes[:, 1] == strut_nodes[-1, 1])[0][0]
            bdf.add_rbe2(
                id_strut + 10000001,
                id_wing + id_connect_left,
                "123456",
                [id_strut + int(np.size(strut_nodes, axis=0) - 1)],
            )
            bdf.add_rbe2(
                id_strut + 10000002,
                id_wing + id_connect_right,
                "123456",
                [id_strut + int(np.size(strut_nodes, axis=0) / 2 - 1)],
            )
        bdf.add_param("GRIDSEQ", "GRID")
        bdf.write_bdf(bdf_filename, enddata=True)
