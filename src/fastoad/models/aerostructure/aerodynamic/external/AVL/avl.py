"""
Module to launch Vortex Lattice Method computations via AVL
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

import os
import os.path as pth
from tempfile import TemporaryDirectory
from importlib.resources import path
import shutil

from openmdao.api import ExternalCodeComp
from openmdao.utils.file_wrap import InputFileGenerator
from openmdao.utils.file_wrap import FileParser
import numpy as np
from scipy.constants import g

from fastoad.utils.physics import Atmosphere as Atm
from fastoad.models.aerostructure.aerodynamic.external.AVL import avl336
import fastoad.models.aerodynamics.external.xfoil.resources as xfoil_resources
from fastoad.utils.resource_management.copy import copy_resource
from . import ressources
from .utils.avl_components_classes import AvlGeometryComponents


OPTION_RESULT_AVL_FILENAME = "result_avl_filename"
OPTION_RESULT_FOLDER_PATH = "result_folder_path"
OPTION_AVL_EXE_PATH = "avl_exe_path"
_AVL_EXE_NAME = "avl.exe"
_AVL_GEOM_NAME = "data.avl"
_AVL_RESULT_NAME = "results.out"
_PROFILE_FILE_NAME = "BACJ.txt"
_STDIN_FILE_NANE = "avl_session.txt"
_STDOUT_FILE_NAME = "avl.log"
_STDERR_FILE_NAME = "avl.err"


class AVL(ExternalCodeComp):
    """
    Computes aerodynamic loads and performances with AVL
    """

    def initialize(self):
        self.options.declare("components", types=list)
        self.options.declare("components_sections", types=list)
        self.options.declare("sizing", default=True, types=bool)
        self.options.declare(OPTION_RESULT_AVL_FILENAME, types=str)
        self.options.declare(OPTION_RESULT_FOLDER_PATH, types=str)
        self.options.declare(OPTION_AVL_EXE_PATH, types=str)

    def setup(self):
        comps = self.options["components"]
        sects = self.options["components_sections"]
        self.add_input("data:geometry:wing:area", val=np.nan)
        self.add_input("data:geometry:wing:span", val=np.nan)
        self.add_input("data:geometry:wing:MAC:length", val=np.nan)
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:wing:sweep_0", val=np.nan, units="rad")
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:aerostructural:load_case:weight", val=np.nan)
        self.add_input("data:aerostructural:load_case:load_factor", val=1.0)

        size = 0
        for comp, n_sect in zip(comps, sects):
            self.add_input(
                "data:aerostructural:aerodynamic:" + comp + ":nodes", val=np.nan, shape_by_conn=True
            )
            self.add_input(
                "data:aerostructural:aerodynamic:" + comp + ":chords",
                val=np.nan,
                shape_by_conn=True,
            )
            if comp == "wing":
                self.add_input(
                    "data:aerostructural:aerodynamic:wing:thickness_ratios",
                    val=np.nan,
                    shape_by_conn=True,
                )
                self.add_input(
                    "data:aerostructural:aerodynamic:wing:twist", val=np.nan, shape_by_conn=True
                )
            if comp in ("wing", "horizontal_tail", "strut"):
                size += n_sect * 2
            else:
                size += n_sect

        self.add_output("data:aerostructural:aerodynamic:forces", val=np.nan, shape=(size, 3))
        if not self.options["sizing"]:
            self.add_output("data:aerostructural:aerodynamic:CDi", val=np.nan)
            self.add_output("data:aerostructural:aerodynamic:CL", val=np.nan)
            self.add_output("data:aerostructural:aerodynamic:Oswald_Coeff", val=np.nan)

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):

        # Results Folder creation if needed --------------------------------------------------------
        result_folder_path = self.options[OPTION_RESULT_FOLDER_PATH]
        if result_folder_path != "":
            os.mkdirs(result_folder_path, exist_ok=True)

        # Creation of the temporary directory ------------------------------------------------------
        tmp_dir = TemporaryDirectory()
        if self.options[OPTION_AVL_EXE_PATH] != "":
            self.options["command"] = [self.options[OPTION_AVL_EXE_PATH]]
        else:
            copy_resource(avl336, _AVL_EXE_NAME, tmp_dir.name)
            copy_resource(xfoil_resources, _PROFILE_FILE_NAME, tmp_dir.name)
            self.options["command"] = [pth.join(tmp_dir.name, _AVL_EXE_NAME)]

        self.stdin = pth.join(tmp_dir.name, _STDIN_FILE_NANE)
        self.stdout = pth.join(tmp_dir.name, _STDOUT_FILE_NAME)
        self.stderr = pth.join(tmp_dir.name, _STDERR_FILE_NAME)

        # AVL session file creation ----------------------------------------------------------------

        s_ref = inputs["data:geometry:wing:area"]
        mach = inputs["data:TLAR:cruise_mach"]
        rho = Atm(0).density
        vtas = Atm(0).speed_of_sound * mach
        q = 0.5 * rho * vtas ** 2

        m_lc = inputs["data:aerostructural:load_case:weight"]
        nz = inputs["data:aerostructural:sizing_load_factor"]
        cl = nz * m_lc * g / (q * s_ref)

        tmp_result_file = pth.joint(tmp_dir.name, _AVL_RESULT_NAME)
        parser = InputFileGenerator()
        with path(ressources, _STDIN_FILE_NANE) as stdin_template:
            parser.set_template_file(stdin_template)
            parser.set_generated_file(self.stdin)

            # Update session file with target values:
            parser.mark_anchor(".OPER")
            parser.transfer_var(float(cl), 1, 3)
            parser.mark_anchor("M")
            parser.transfer_var(float(mach), 1, 2)
            parser.transfer_var(float(vtas), 2, 2)
            parser.transfer_var(float(rho), 3, 2)

        # AVL geometry file (.avl) creation --------------------------------------------------------
        input_geom_file = pth.join(tmp_dir.name, _AVL_GEOM_NAME)
        self._get_avl_geom_file(inputs, tmp_dir.name)

        # Check for input and output file presence -------------------------------------------------
        self.options["external_input_file"] = [
            self.stdin,
            input_geom_file,
            pth.join(tmp_dir.name, _PROFILE_FILE_NAME),
        ]
        self.options["external_output_file"] = [tmp_result_file]

        # Launch AVL -------------------------------------------------------------------------------
        super().compute(inputs, outputs)

        # Gather results ---------------------------------------------------------------------------
        size = 0
        for (comp, sect,) in zip(self.options["components"], self.options["components_sections"]):
            if comp in ("wing", "horizontal_tail", "strut"):
                size += sect * 2
            else:
                size += sect
        parser_out = FileParser()
        parser_out.set_file(tmp_result_file)
        parser_out.mark_anchor("CZtot")
        outputs["data:aerostructural:aerodynamic:CL"] = parser_out.transfer_var(2, 3)
        outputs["data:aerostructural:aerodynamic:CDi"] = parser_out.transfer_var(4, 6)
        outputs["data:aerostructural:aerodynamic:Oswald_Coeff"] = parser_out.transfer_var(6, 6)
        parser_out.mark_anchor("Surface Forces", 1)
        surface_coef = parser_out.transfer_2Darray(7, 3, size, 6)
        outputs["data:aerostructural:aerodynamic:forces"] = q * s_ref * surface_coef

        # Store input and result files if necessary ------------------------------------------------
        if self.options[OPTION_RESULT_FOLDER_PATH]:
            if path.exist(tmp_result_file):
                forces_file = pth.join(result_folder_path, _AVL_RESULT_NAME)
                shutil.move(tmp_result_file, forces_file)
            if path.exist(input_geom_file):
                geometry_file = pth.join(result_folder_path, _AVL_GEOM_NAME)
                shutil.move(input_geom_file, geometry_file)

    def _get_avl_geom_file(self, inputs: dict, dir_path: str):
        """
        Generate AVL geometry file(*.avl) from om.ExternalCodeComp inputs and stores it in the
        temporary directory.
        :param inputs: Dictionary of om.ExternalCodeComp inputs
        :param dir_path: temporary directory where are stored avl computation files
        :return:
        """
        with open(pth.join(dir_path, _AVL_GEOM_NAME)) as data_file:
            lines = self._get_geom_file_header(inputs)

            # Sections definitions for each component
            count = 0
            k_chords = inputs["tuning:aerostructural:aerodynamic:chordwise_spacing:k"]

            for comp in self.options["components"]:
                nodes = inputs["data:aerostructural:aerodynamic:" + comp + "nodes"]
                chords = inputs["data:aerostructural:aerodynamic" + comp + "chords"]
                count += 1
                geom_generator = AvlGeometryComponents[comp.upper()].value
                geom_generator.index = count
                if comp == "wing":
                    geom_generator.twist = inputs["data:aerostructural:aerodynamic:wing:twist"]
                    geom_generator.thickness_ratios = inputs[
                        "data:aerostructural:aerodynamic:wing:thickness_ratios"
                    ]
                    geom_generator.profile = pth.join(dir_path, _PROFILE_FILE_NAME)
                lines += geom_generator.get_component_geom(nodes, chords, k_chords)

            data_file.writelines(lines)

    @staticmethod
    def _get_geom_file_header(inputs):
        """
        Generates header of the AVL geometry file (*.avl) from wing geometry characteristics.
        :param inputs: Dictionary of om.ExternalCodeComp inputs
        :return:
        """
        s_ref = inputs["data:geometry:wing:area"]
        c_ref = inputs["data:geometry:wing:MAC:length"]
        b_ref = inputs["data:geometry:wing:span"]
        x_ref = inputs["data:geometry:wing:MAC:at25percent:x"]
        # Mach for Prandtl-Glauert correction
        mach_ref = np.cos(inputs["data:geometry:wing:sweep_0"]) * inputs["data:TLAR:cruise_mach"]
        # First lines of the input file
        lines = [
            "AVL geometry FAST-OAD \n",
            str(mach_ref[0]) + "\n",
            "0 0 0.0 \n",
            str(s_ref[0]) + " " + str(c_ref[0]) + " " + str(b_ref[0]) + "\n",
            str(x_ref[0]) + "0.0 0.0 \n",
        ]
        return lines
