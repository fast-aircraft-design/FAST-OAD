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
from scipy.constants import g, degree

from fastoad.utils.physics import Atmosphere as Atm
from fastoad.models.aerostructure.aerodynamic.external.AVL import avl336
import fastoad.models.aerodynamics.external.xfoil.resources as xfoil_resources
from fastoad.utils.resource_management.copy import copy_resource
from . import ressources
from .utils.avl_components_classes import AvlGeometryComponents
from .utils.avl_components_dict import AVL_COMPONENT_NAMES


OPTION_RESULT_AVL_FILENAME = "result_avl_filename"
OPTION_RESULT_FOLDER_PATH = "result_folder_path"
OPTION_AVL_EXE_PATH = "avl_exe_path"
_AVL_EXE_NAME = "avl.exe"
_AVL_GEOM_NAME = "data.avl"
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
        self.options.declare(OPTION_RESULT_AVL_FILENAME, default="results.out", types=str)
        self.options.declare(OPTION_RESULT_FOLDER_PATH, default="", types=str)
        self.options.declare(OPTION_AVL_EXE_PATH, default="", types=str, allow_none=True)

    def setup(self):
        comps = self.options["components"]
        sects = self.options["components_sections"]
        self.add_input("data:geometry:wing:area", val=np.nan)
        self.add_input("data:geometry:wing:span", val=np.nan)
        self.add_input("data:geometry:wing:MAC:length", val=np.nan)
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input("data:geometry:wing:sweep_0", val=np.nan, units="rad")
        self.add_input("data:aerostructural:load_case:mach", val=np.nan)
        self.add_input("data:aerostructural:load_case:weight", val=np.nan)
        self.add_input("data:aerostructural:load_case:load_factor", val=1.0)
        self.add_input("data:aerostructural:load_case:altitude", val=np.nan, units="ft")
        self.add_input("tuning:aerostructural:aerodynamic:chordwise_spacing:k", val=1.0)

        for comp, n_sect in zip(comps, sects):
            self.add_input(
                "data:aerostructural:aerodynamic:" + comp + ":nodes",
                val=np.nan,
                shape_by_conn=True,
            )
            self.add_input(
                "data:aerostructural:aerodynamic:" + comp + ":displacements",
                val=np.nan,
                copy_shape="data:aerostructural:aerodynamic:" + comp + ":nodes",
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

            size = n_sect  # Default number of section for non symmetrical components
            if comp in ("wing", "horizontal_tail", "strut"):
                size = n_sect * 2  # Number of section doubled for symmetrical components
            elif comp == "fuselage":
                size = 4

            self.add_output(
                "data:aerostructural:aerodynamic:" + comp + ":forces", val=0.0, shape=(size, 6)
            )

        # self.add_output("data:aerostructural:aerodynamic:forces", val=np.nan, shape=(size, 6))
        self.add_output("data:aerostructural:aerodynamic:CDi", val=0.0)
        self.add_output("data:aerostructural:aerodynamic:CL", val=0.0)
        self.add_output("data:aerostructural:aerodynamic:Oswald_Coeff", val=0.0)

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):

        # Results Folder creation if needed --------------------------------------------------------
        result_folder_path = self.options[OPTION_RESULT_FOLDER_PATH]
        if result_folder_path != "":
            os.makedirs(result_folder_path, exist_ok=True)

        # Creation of the temporary directory ------------------------------------------------------
        tmp_dir = TemporaryDirectory()
        if self.options[OPTION_AVL_EXE_PATH] != "":
            copy_resource(xfoil_resources, _PROFILE_FILE_NAME, tmp_dir.name)
            self.options["command"] = [self.options[OPTION_AVL_EXE_PATH]]
        else:
            copy_resource(avl336, _AVL_EXE_NAME, tmp_dir.name)
            copy_resource(xfoil_resources, _PROFILE_FILE_NAME, tmp_dir.name)
            self.options["command"] = [pth.join(tmp_dir.name, _AVL_EXE_NAME)]

        self.stdin = pth.join(tmp_dir.name, _STDIN_FILE_NANE)
        self.stdout = pth.join(tmp_dir.name, _STDOUT_FILE_NAME)
        self.stderr = pth.join(tmp_dir.name, _STDERR_FILE_NAME)

        # AVL geometry file (.avl) creation --------------------------------------------------------
        input_geom_file = pth.join(tmp_dir.name, _AVL_GEOM_NAME)
        profile_file = pth.join(tmp_dir.name, _PROFILE_FILE_NAME)
        self._get_avl_geom_file(inputs, input_geom_file, _PROFILE_FILE_NAME)

        # AVL session file creation ----------------------------------------------------------------

        s_ref = inputs["data:geometry:wing:area"]
        b_ref = inputs["data:geometry:wing:span"]
        c_ref = inputs["data:geometry:wing:MAC:length"]
        mach = inputs["data:aerostructural:load_case:mach"]
        alt = inputs["data:aerostructural:load_case:altitude"]
        rho = Atm(alt).density
        vtas = Atm(alt).speed_of_sound * mach
        q = 0.5 * rho * vtas ** 2

        m_lc = inputs["data:aerostructural:load_case:weight"]
        nz = inputs["data:aerostructural:load_case:load_factor"]
        cl = nz * m_lc * g / (q * s_ref)

        tmp_result_file = pth.join(tmp_dir.name, self.options[OPTION_RESULT_AVL_FILENAME])
        parser = InputFileGenerator()
        with path(ressources, _STDIN_FILE_NANE) as stdin_template:
            parser.set_template_file(stdin_template)
            parser.set_generated_file(self.stdin)

            # Update session file with target values:
            parser.mark_anchor("LOAD")
            parser.transfer_var(input_geom_file, 1, 1)
            parser.mark_anchor("OPER")
            parser.transfer_var(float(cl), 1, 3)
            parser.mark_anchor("M")
            parser.transfer_var(float(mach), 1, 2)
            parser.transfer_var(float(vtas), 2, 2)
            parser.transfer_var(float(rho), 3, 2)
            parser.mark_anchor("W")
            parser.transfer_var(tmp_result_file, 1, 1)

            parser.generate()

        # Check for input and output file presence -------------------------------------------------
        self.options["external_input_files"] = [
            self.stdin,
            input_geom_file,
            profile_file,
        ]
        self.options["external_output_files"] = [tmp_result_file]

        # Launch AVL -------------------------------------------------------------------------------
        super().compute(inputs, outputs)

        # Gather results ---------------------------------------------------------------------------
        parser_out = FileParser()
        parser_out.set_file(tmp_result_file)
        parser_out.mark_anchor("Alpha =")
        aoa = parser_out.transfer_var(0, 3)
        parser_out.mark_anchor("CLtot =")
        outputs["data:aerostructural:aerodynamic:CL"] = parser_out.transfer_var(0, 3)
        parser_out.mark_anchor("CDind =")
        outputs["data:aerostructural:aerodynamic:CDi"] = parser_out.transfer_var(0, 6)
        outputs["data:aerostructural:aerodynamic:Oswald_Coeff"] = parser_out.transfer_var(2, 6)
        for (comp, sect) in zip(self.options["components"], self.options["components_sections"]):
            size = sect  # default number of section for non symmetric components
            if comp in ("wing", "horizontal_tail", "strut"):
                size = sect * 2  # number of sections doubled for symmetric components
            elif comp == "fuselage":
                size = 4  # particular case for fuselage due to specific VLM modelling
            avl_comp = AVL_COMPONENT_NAMES[comp]
            parser_out.mark_anchor(avl_comp)
            comp_coef = parser_out.transfer_2Darray(0, 3, size - 1, 8)
            #  Reorganise result array to have coefficient in direct axis order
            comp_coef[:, :] = comp_coef[:, [1, 3, 0, 5, 2, 4]]
            #  Comvert coefficients into forces and moments
            comp_coef[:, :3] *= q * s_ref
            comp_coef[:, [3, 5]] *= q * s_ref * b_ref
            comp_coef[:, 4] *= q * s_ref * c_ref
            #  Change forces and moment from aerodynamic to body axis
            r_mat = self._get_rotation_matrix(aoa * degree, axis="y")
            comp_coef[:, :3] = np.dot(comp_coef[:, :3], r_mat)
            comp_coef[:, 3:] = np.dot(comp_coef[:, 3:], r_mat)  # Moments in std axis ie X fwd
            outputs["data:aerostructural:aerodynamic:" + comp + ":forces"] = comp_coef
        # outputs["data:aerostructural:aerodynamic:forces"] = q * s_ref * surface_coef

        # Store input and result files if necessary ------------------------------------------------
        if self.options[OPTION_RESULT_FOLDER_PATH]:
            if pth.exists(tmp_result_file):
                forces_file = pth.join(result_folder_path, self.options[OPTION_RESULT_AVL_FILENAME])
                shutil.move(tmp_result_file, forces_file)
            if pth.exists(input_geom_file):
                geometry_file = pth.join(result_folder_path, _AVL_GEOM_NAME)
                shutil.move(input_geom_file, geometry_file)
            if pth.exists(self.stdin):
                stdin_path = pth.join(result_folder_path, _STDIN_FILE_NANE)
                shutil.move(self.stdin, stdin_path)
            if pth.exists(self.stdout):
                stdout_path = pth.join(result_folder_path, _STDOUT_FILE_NAME)
                shutil.move(self.stdout, stdout_path)
            if pth.exists(self.stderr):
                stderr_path = pth.join(result_folder_path, _STDERR_FILE_NAME)
                shutil.move(self.stderr, stderr_path)
        tmp_dir.cleanup()

    def _get_avl_geom_file(self, inputs: dict, geom_file_path: str, profile_file_name: str):
        """
        Generate AVL geometry file(*.avl) from om.ExternalCodeComp inputs and stores it in the
        temporary directory.
        :param inputs: Dictionary of om.ExternalCodeComp inputs
        :param geom_file_path: temporary directory where are stored avl computation files
        :param profile_file_name: Wing profile file name
        :return:
        """
        with open(geom_file_path, "w") as data_file:
            lines = self._get_geom_file_header(inputs)

            # Sections definitions for each component
            count = 0
            k_chords = inputs["tuning:aerostructural:aerodynamic:chordwise_spacing:k"][0]

            for comp in self.options["components"]:
                count += 1
                geom_gen_class = AvlGeometryComponents[comp.upper()].value
                geom_gen = geom_gen_class()
                geom_gen.index = count
                geom_gen.k_c = k_chords
                geom_gen.nodes = (
                    inputs["data:aerostructural:aerodynamic:" + comp + ":nodes"]
                    + inputs["data:aerostructural:aerodynamic:" + comp + ":displacements"]
                )
                geom_gen.chords = inputs["data:aerostructural:aerodynamic:" + comp + ":chords"]
                if comp == "wing":
                    geom_gen.twist = inputs["data:aerostructural:aerodynamic:wing:twist"]
                    geom_gen.thickness_ratios = inputs[
                        "data:aerostructural:aerodynamic:wing:thickness_ratios"
                    ]
                    geom_gen.profile = profile_file_name
                lines += geom_gen.get_component_geom()

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
        mach_ref = (
            np.cos(inputs["data:geometry:wing:sweep_0"])
            * inputs["data:aerostructural:load_case:mach"]
        )
        # First lines of the input file
        lines = [
            "AVL geometry FAST-OAD \n",
            str(mach_ref[0]) + "\n",
            "0 0 0.0 \n",
            str(s_ref[0]) + " " + str(c_ref[0]) + " " + str(b_ref[0]) + "\n",
            str(x_ref[0]) + " 0.0 0.0 \n",
        ]
        return lines

    @staticmethod
    def _get_rotation_matrix(angle, axis="y"):
        c = np.cos(angle)
        s = np.sin(angle)
        if axis == "x":
            r_mat = np.array([[1, 0, 0], [0, c, s], [0, -s, c]])
        elif axis == "y":
            r_mat = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        else:
            r_mat = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        return r_mat
