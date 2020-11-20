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

import openmdao.api as om
import numpy as np


class StructureNodes(om.ExplicitComponent):
    """
    Computes strutural nodes locations from geometrical data
    """

    def initialize(self):
        self.options.declare("component", types=str)
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        c_type = self.options["component"]
        n_sections = self.options["number_of_sections"]
        if c_type == "wing":
            self.add_input("data:geometry:wing:span", val=np.nan)
            self.add_input("data:geometry:wing:root:y", val=np.nan)
            self.add_input("data:geometry:wing:root:z", val=0.0)
            self.add_input("data:geometry:wing:root:chord", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:front:root", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:rear:root", val=np.nan)
            self.add_input("data:geometry:wing:kink:leading_edge:x:local", val=np.nan)
            self.add_input("data:geometry:wing:kink:y", val=np.nan)
            self.add_input("data:geometry:wing:kink:z", val=0.0)
            self.add_input("data:geometry:wing:kink:chord", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:front:kink", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:rear:kink", val=np.nan)
            self.add_input("data:geometry:wing:tip:leading_edge:x:local", val=np.nan)
            self.add_input("data:geometry:wing:tip:y", val=np.nan)
            self.add_input("data:geometry:wing:tip:z", val=0.0)
            self.add_input("data:geometry:wing:tip:chord", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:front:tip", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:rear:tip", val=np.nan)
            self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
            self.add_input("data:geometry:wing:MAC:length", val=np.nan)
            self.add_input("data:geometry:wing:MAC:leading_edge:x:local", val=np.nan)
            # self.add_input("settings:aerostructural:wing:struct_sections", val=np.nan)
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":nodes",
                shape=((n_sections + 1) * 2 + 2, 3),
            )

        elif c_type == "horizontal_tail":
            self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
            self.add_input("data:geometry:horizontal_tail:sweep_0", val=np.nan, units="rad")
            self.add_input("data:geometry:horizontal_tail:span", val=np.nan)
            self.add_input("data:geometry:horizontal_tail:root:chord", val=np.nan)
            self.add_input("data:geometry:horizontal_tail:tip:chord", val=np.nan)
            self.add_input(
                "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan
            )
            self.add_input("data:geometry:horizontal_tail:MAC:at25percent:x:local", val=np.nan)
            self.add_input("data:geometry:horizontal_tail:root:z", val=np.nan)
            self.add_input("data:geometry:horizontal_tail:tip:z", val=np.nan)
            # self.add_input("settings:aerostructural:horizontal_tail:struct_sections", val=np.nan)
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":nodes",
                shape=((n_sections + 1) * 2, 3),
            )

        elif c_type == "vertical_tail":
            self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
            self.add_input("data:geometry:fuselage:maximum_width", val=np.nan)
            self.add_input("data:geometry:vertical_tail:sweep_0", val=np.nan, units="rad")
            self.add_input("data:geometry:vertical_tail:span", val=np.nan)
            self.add_input("data:geometry:vertical_tail:root:chord", val=np.nan)
            self.add_input("data:geometry:vertical_tail:tip:chord", val=np.nan)
            self.add_input(
                "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25", val=np.nan
            )
            self.add_input("data:geometry:vertical_tail:MAC:at25percent:x:local", val=np.nan)
            # self.add_input("settings:aerostructural:vertical_tail:struct_sections", val=np.nan)
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":nodes", shape=(n_sections + 1, 3)
            )
            self.add_output("data:geometry:vertical_tail:root:z", val=np.nan)
            self.add_output("data:geometry:vertical_tail:tip:z", val=np.nan)

        elif c_type == "fuselage":
            self.add_input("data:geometry:fuselage:length", val=np.nan)
            self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
            self.add_input("settings:aerostructural:fuselage:struct_sections", val=np.nan)
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":nodes", shape=(n_sections + 1, 3)
            )

        elif c_type == "strut":
            self.add_input("data:geometry:has_strut", val=0)
            self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
            self.add_input("data:geometry:strut:root:x:from_wingMAC25", val=np.nan)
            self.add_input("data:geometry:strut:root:y", val=np.nan)
            self.add_input("data:geometry:strut:root:z", val=np.nan)
            self.add_input("data:geometry:strut:junction:x", val=np.nan)
            self.add_input("data:geometry:strut:junction:y", val=np.nan)
            self.add_input("data:geometry:strut:junction:z", val=np.nan)
            self.add_input("data:geometry:strut:root:chord", val=np.nan)
            self.add_input("data:geometry:strut:junction:chord", val=np.nan)
            # self.add_input("settings:aerostructural:strut:struct_sections", val=np.nan)
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":nodes",
                shape=((n_sections + 1) * 2, 3),
            )

    def compute(self, inputs, outputs):

        c_type = self.options["component"]

        if c_type == "wing":
            x_root = (
                inputs["data:geometry:wing:MAC:at25percent:x"]
                - 0.25 * inputs["data:geometry:wing:MAC:length"]
                - inputs["data:geometry:wing:MAC:leading_edge:x:local"]
            )
            x_kink = x_root + inputs["data:geometry:wing:kink:leading_edge:x:local"]
            x_tip = x_root + inputs["data:geometry:wing:tip:leading_edge:x:local"]
            y_root = inputs["data:geometry:wing:root:y"]
            y_wing = 0.5 * inputs["data:geometry:wing:span"] - y_root
            y_kink = inputs["data:geometry:wing:kink:y"]
            y_tip = inputs["data:geometry:wing:tip:y"]
            z_root = inputs["data:geometry:wing:root:z"]
            z_kink = inputs["data:geometry:wing:kink:z"]
            z_tip = inputs["data:geometry:wing:tip:z"]
            root_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:root"]
            root_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:root"]
            kink_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:kink"]
            kink_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:kink"]
            tip_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:tip"]
            tip_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:tip"]
            root_chord = inputs["data:geometry:wing:root:chord"]
            kink_chord = inputs["data:geometry:wing:kink:chord"]
            tip_chord = inputs["data:geometry:wing:tip:chord"]

            dimensions = {
                "root_x": x_root,
                "root_y": y_root,
                "root_z": z_root,
                "kink_x": x_kink,
                "kink_y": y_kink,
                "kink_z": z_kink,
                "tip_x": x_tip,
                "tip_y": y_tip,
                "tip_z": z_tip,
                "root_front_spar_ratio": root_front_spar_ratio,
                "root_rear_spar_ratio": root_rear_spar_ratio,
                "kink_front_spar_ratio": kink_front_spar_ratio,
                "kink_rear_spar_ratio": kink_rear_spar_ratio,
                "tip_front_spar_ratio": tip_front_spar_ratio,
                "tip_rear_spar_ratio": tip_rear_spar_ratio,
                "root_chord": root_chord,
                "kink_chord": kink_chord,
                "tip_chord": tip_chord,
                "length": y_wing,
            }

        elif c_type == "fuselage":
            length = inputs["data:geometry:fuselage:length"]
            xcg = inputs["data:geometry:wing:MAC:at25percent:x"]

            dimensions = {"length": length, "x_cg": xcg}

        elif c_type == "horizontal_tail":
            x_root_h = (
                inputs["data:geometry:wing:MAC:at25percent:x"]
                + inputs["data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"]
                - inputs["data:geometry:horizontal_tail:MAC:at25percent:x:local"]
            )
            x_tip_h = x_root_h + inputs["data:geometry:horizontal_tail:span"] * 0.5 * np.tan(
                inputs["data:geometry:horizontal_tail:sweep_0"]
            )
            y_root_h = 0.0
            y_tip_h = inputs["data:geometry:horizontal_tail:span"] * 0.5
            z_root_h = inputs["data:geometry:horizontal_tail:root:z"]
            z_tip_h = inputs["data:geometry:horizontal_tail:tip:z"]
            root_chord_h = inputs["data:geometry:horizontal_tail:root:chord"]
            tip_chord_h = inputs["data:geometry:horizontal_tail:tip:chord"]
            length = inputs["data:geometry:horizontal_tail:span"] * 0.5

            dimensions = {
                "root_x": x_root_h,
                "tip_x": x_tip_h,
                "root_y": y_root_h,
                "tip_y": y_tip_h,
                "root_z": z_root_h,
                "tip_z": z_tip_h,
                "root_chord": root_chord_h,
                "tip_chord": tip_chord_h,
                "length": length,
            }

        elif c_type == "vertical_tail":
            x_root_v = (
                inputs["data:geometry:wing:MAC:at25percent:x"]
                + inputs["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"]
                - inputs["data:geometry:vertical_tail:MAC:at25percent:x:local"]
            )
            x_tip_v = x_root_v + inputs["data:geometry:vertical_tail:span"] * np.tan(
                inputs["data:geometry:vertical_tail:sweep_0"]
            )
            z_root_v = outputs["data:geometry:vertical_tail:root:z"] = (
                0.5 * inputs["data:geometry:fuselage:maximum_width"]
            )
            z_tip_v = outputs["data:geometry:vertical_tail:tip:z"] = (
                z_root_v + inputs["data:geometry:vertical_tail:span"]
            )
            root_chord_v = inputs["data:geometry:vertical_tail:root:chord"]
            tip_chord_v = inputs["data:geometry:vertical_tail:tip:chord"]
            length = inputs["data:geometry:vertical_tail:span"]

            dimensions = {
                "root_x": x_root_v,
                "tip_x": x_tip_v,
                "root_z": z_root_v,
                "tip_z": z_tip_v,
                "root_chord": root_chord_v,
                "tip_chord": tip_chord_v,
                "length": length,
            }

        elif c_type == "strut":

            x_root_s = inputs["data:geometry:strut:root:x:from_wingMAC25"]
            x_tip_s = inputs["data:geometry:strut:junction:x"]
            y_root_s = inputs["data:geometry:strut:root:y"]
            y_tip_s = inputs["data:geometry:strut:junction:y"]
            z_root_s = inputs["data:geometry:strut:root:z"]
            z_tip_s = inputs["data:geometry:strut:junction:z"]
            root_chord_s = inputs["data:geometry:strut:root:chord"]
            tip_chord_s = inputs["data:geometry:strut:junction:chord"]
            length = (
                (x_root_s - x_tip_s) ** 2 + (y_root_s - y_tip_s) ** 2 + (z_root_s - z_tip_s) ** 2
            ) ** 0.5

            dimensions = {
                "root_x": x_root_s,
                "junction_x": x_tip_s,
                "root_y": y_root_s,
                "junction_y": y_tip_s,
                "root_z": z_root_s,
                "junction_z": z_tip_s,
                "root_chord": root_chord_s,
                "tip_chord": tip_chord_s,
                "length": length,
            }

        # sections = inputs["settings:aerostructural:"+c_type+":struct_sections"]
        sections = self.options["number_of_sections"]
        outputs["data:aerostructural:structure:" + c_type + ":nodes"] = self._get_grids_loc(
            sections, c_type, dimensions
        )

    @staticmethod
    def _get_grids_loc(sections, c_type, dimensions):
        n_points = sections + 1
        comp = c_type
        comp_length = dimensions["length"]
        sections_charac = dimensions
        loc = np.linspace(0, comp_length, num=n_points)
        if comp == "wing":
            x_le_root = sections_charac["root_x"]
            y_le_root = sections_charac["root_y"]
            z_le_root = sections_charac["root_z"]
            x_box_root = (
                sections_charac["root_rear_spar_ratio"] + sections_charac["root_front_spar_ratio"]
            ) * sections_charac["root_chord"] * 0.5 + x_le_root

            x_le_kink = sections_charac["kink_x"]
            y_le_kink = sections_charac["kink_y"]
            z_le_kink = sections_charac["kink_z"]
            x_box_kink = (
                sections_charac["kink_rear_spar_ratio"] + sections_charac["kink_front_spar_ratio"]
            ) * sections_charac["kink_chord"] * 0.5 + x_le_kink

            x_le_tip = sections_charac["tip_x"]
            y_le_tip = sections_charac["tip_y"]
            z_le_tip = sections_charac["tip_z"]
            x_box_tip = (
                sections_charac["tip_rear_spar_ratio"] + sections_charac["tip_front_spar_ratio"]
            ) * sections_charac["tip_chord"] * 0.5 + x_le_tip

            # centre wing box node definition
            grid_coord = np.zeros((n_points * 2 + 2, 3))
            # Initialise centre wing-box nodes
            grid_coord[0, 0] = grid_coord[n_points + 1, 0] = x_box_root
            grid_coord[0, 2] = grid_coord[n_points + 1, 2] = z_le_root
            # Right wing nodes definition
            for i in range(0, n_points):
                loc[i] += y_le_root
                if loc[i] <= y_le_kink:
                    grid_coord[i + 1, 0] = x_box_root + (loc[i] - y_le_root) * (
                        x_box_kink - x_box_root
                    ) / (y_le_kink - y_le_root)
                    grid_coord[i + 1, 1] = loc[i]
                    grid_coord[i + 1, 2] = z_le_root + (loc[i] - y_le_root) * (
                        z_le_kink - z_le_root
                    ) / (y_le_kink - y_le_root)
                else:
                    grid_coord[i + 1, 0] = x_box_kink + (loc[i] - y_le_kink) * (
                        x_box_tip - x_box_kink
                    ) / (y_le_tip - y_le_kink)
                    grid_coord[i + 1, 1] = loc[i]
                    grid_coord[i + 1, 2] = z_le_kink + (loc[i] - y_le_kink) * (
                        z_le_tip - z_le_kink
                    ) / (y_le_tip - y_le_kink)
                # Left wing nodes definition by symmetry
                grid_coord[i + 2 + n_points, 0] = grid_coord[i + 1, 0]
                grid_coord[i + 2 + n_points, 1] = -grid_coord[i + 1, 1]
                grid_coord[i + 2 + n_points, 2] = grid_coord[i + 1, 2]
            return grid_coord

        if comp == "fuselage":
            grid_coord = np.zeros((n_points, 3))
            length = sections_charac["length"]
            xspc = sections_charac["x_cg"]
            lahead = length - xspc
            n_points1 = int(np.round(sections * lahead / length)[0])
            n_points2 = int(np.round(sections * (1 - lahead / length))[0])
            loc1 = np.linspace(0, xspc, num=n_points1 + 1)
            loc2 = np.linspace(xspc, length, num=n_points2 + 1)
            for i in range(0, n_points1):
                grid_coord[i, 0] = loc1[i]
            grid_coord[n_points1, 0] = xspc
            for i in range(0, n_points2):
                grid_coord[i + n_points1 + 1, 0] = loc2[i + 1]
            return grid_coord

        if comp == "horizontal_tail":
            grid_coord = np.zeros((n_points * 2, 3))
            x_le_root = sections_charac["root_x"]
            z_le_root = sections_charac["root_z"]
            x_box_root = x_le_root + 0.5 * sections_charac["root_chord"]
            x_le_tip = sections_charac["tip_x"]
            z_le_tip = sections_charac["tip_z"]
            x_box_tip = x_le_tip + 0.5 * sections_charac["tip_chord"]
            for i in range(0, n_points):
                grid_coord[i, 0] = x_box_root + loc[i] * (x_box_tip - x_box_root) / comp_length
                grid_coord[i, 1] = loc[i]
                grid_coord[i, 2] = z_le_root + loc[i] * (z_le_tip - z_le_root) / comp_length
                # Generate left horizontal tail by symmetry
                grid_coord[i + n_points, 0] = grid_coord[i, 0]
                grid_coord[i + n_points, 1] = -grid_coord[i, 1]
                grid_coord[i + n_points, 2] = grid_coord[i, 2]
            return grid_coord

        if comp == "vertical_tail":
            grid_coord = np.zeros((n_points, 3))
            x_le_root = sections_charac["root_x"]
            z_le_root = sections_charac["root_z"]
            x_box_root = x_le_root + 0.5 * sections_charac["root_chord"]
            x_le_tip = sections_charac["tip_x"]
            x_box_tip = x_le_tip + 0.5 * sections_charac["tip_chord"]
            for i in range(0, n_points):
                grid_coord[i, 0] = (
                    x_box_root + 0.5 * (loc[i] - z_le_root) * (x_box_tip - x_box_root) / comp_length
                )
                grid_coord[i, 2] = z_le_root + loc[i]
            return grid_coord

        if comp == "strut":
            grid_coord = np.zeros((n_points * 2, 3))
            x_root = sections_charac["root_x"]
            y_root = sections_charac["root_y"]
            z_root = sections_charac["root_z"]
            x_junc = sections_charac["junction_x"]
            z_junc = sections_charac["junction_z"]
            for i in range(0, n_points):
                grid_coord[i, 0] = x_root + loc[i] * (x_junc - x_root) / comp_length
                grid_coord[i, 1] = loc[i] + y_root
                grid_coord[i, 2] = z_root + loc[i] * (z_junc - z_root) / comp_length
                # Generate left horizontal tail by symmetry
                grid_coord[i + n_points, 0] = grid_coord[i, 0]
                grid_coord[i + n_points, 1] = -grid_coord[i, 1]
                grid_coord[i + n_points, 2] = grid_coord[i, 2]
            return grid_coord
