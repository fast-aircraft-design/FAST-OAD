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


class StructureBeamProps(om.ExplicitComponent):
    """"
    Compute Beam properties (A, I1, I2, J) from geometrical consideration and thickness information
    """

    def initialize(self):
        self.options.declare("component", types=str)
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        c_type = self.options["component"]
        n_sections = self.options["number_of_sections"]
        if c_type == "wing":
            self.add_input("data:geometry:wing:root:y", val=np.nan)
            self.add_input("data:geometry:wing:tip:y", val=np.nan)
            self.add_input("data:geometry:wing:kink:y", val=np.nan)
            self.add_input("data:geometry:wing:root:chord", val=np.nan)
            self.add_input("data:geometry:wing:root:thickness_ratio", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:front:root", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:rear:root", val=np.nan)
            self.add_input("data:geometry:wing:kink:chord", val=np.nan)
            self.add_input("data:geometry:wing:kink:thickness_ratio", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:front:kink", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:rear:kink", val=np.nan)
            self.add_input("data:geometry:wing:tip:chord", val=np.nan)
            self.add_input("data:geometry:wing:tip:thickness_ratio", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:front:tip", val=np.nan)
            self.add_input("data:geometry:wing:spar_ratio:rear:tip", val=np.nan)
            self.add_input("data:geometry:wing:skin:thicknesses", shape=(n_sections, 1))
            self.add_input("data:geometry:wing:web:thicknesses", shape=(n_sections, 1))
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":beam_properties",
                shape=((n_sections + 1) * 2, 4),
            )
        elif c_type == "fuselage":
            self.add_input("data:geometry:fuselage:length", val=np.nan)
            self.add_input("data:geometry:fuselage:front_length", val=np.nan)
            self.add_input("data:geometry:fuselage:rear_length", val=np.nan)
            self.add_input("data:geometry:fuselage:maximum_width", val=np.nan)
            self.add_input("data:geometry:fuselage:skin:thicknesses", shape=(n_sections,))
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":beam_properties",
                shape=(n_sections, 4),
            )

        elif c_type in ("horizontal_tail", "strut"):
            self.add_input("data:geometry:" + c_type + ":span", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":root:chord", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":tip:chord", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":thickness_ratio", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":skin:thicknesses", shape=(n_sections, 1))
            self.add_input("data:geometry:" + c_type + ":web:thicknesses", shape=(n_sections, 1))
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":beam_properties",
                shape=(n_sections * 2, 4),
            )

        elif c_type == "vertical_tail":
            self.add_input("data:geometry:" + c_type + ":root:z", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":tip:z", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":root:chord", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":tip:chord", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":thickness_ratio", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":skin:thicknesses", shape=(n_sections, 1))
            self.add_input("data:geometry:" + c_type + ":web:thicknesses", shape=(n_sections, 1))
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":beam_properties",
                shape=(n_sections, 4),
            )

        elif c_type == "strut":
            self.add_input("data:geometry:" + c_type + ":root:y", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":tip:y", val=np.nan)
            self.add_input("data:geometry:" + c_type + "vertical_tail" ":root:chord", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":tip:chord", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":thickness_ratio", val=np.nan)
            self.add_input("data:geometry:" + c_type + ":skin:thicknesses", shape=(n_sections, 1))
            self.add_output(
                "data:aerostructural:structure:" + c_type + ":beam_properties",
                shape=(n_sections * 2, 4),
            )

        # self.add_input("setting:aerostructural:"+c_type+":struct_sections", val=1)
        self.add_input("settings:aerostructural:" + c_type + ":n_spar", val=0.0)
        self.add_input("data:geometry:" + c_type + ":spar_area", val=0.0)
        self.add_input("data:aerostructural:structure:" + c_type + ":nodes", shape_by_conn=True)

        # self.add_output("data:aerostructural:structure:"+c_type+":beam_properties", )

    def compute(self, inputs, outputs):
        c_type = self.options["component"]

        if c_type == "wing":
            root_y = inputs["data:geometry:wing:root:y"]
            kink_y = inputs["data:geometry:wing:kink:y"]
            tip_y = inputs["data:geometry:wing:tip:y"]
            root_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:root"]
            root_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:root"]
            kink_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:kink"]
            kink_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:kink"]
            tip_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:tip"]
            tip_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:tip"]
            root_thickness_ratio = inputs["data:geometry:wing:root:thickness_ratio"]
            kink_thickness_ratio = inputs["data:geometry:wing:kink:thickness_ratio"]
            tip_thickness_ratio = inputs["data:geometry:wing:tip:thickness_ratio"]
            thicknesses = np.hstack(
                (
                    inputs["data:geometry:wing:skin:thicknesses"],
                    inputs["data:geometry:wing:web:thicknesses"],
                )
            )
            root_chord = inputs["data:geometry:wing:root:chord"]
            kink_chord = inputs["data:geometry:wing:kink:chord"]
            tip_chord = inputs["data:geometry:wing:tip:chord"]

            dimensions = {
                "root_y": root_y,
                "tip_y": tip_y,
                "kink_y": kink_y,
                "root_front_spar_ratio": root_front_spar_ratio,
                "root_rear_spar_ratio": root_rear_spar_ratio,
                "kink_front_spar_ratio": kink_front_spar_ratio,
                "kink_rear_spar_ratio": kink_rear_spar_ratio,
                "tip_front_spar_ratio": tip_front_spar_ratio,
                "tip_rear_spar_ratio": tip_rear_spar_ratio,
                "root_thickness_ratio": root_thickness_ratio,
                "kink_thickness_ratio": kink_thickness_ratio,
                "tip_thickness_ratio": tip_thickness_ratio,
                "root_chord": root_chord,
                "kink_chord": kink_chord,
                "tip_chord": tip_chord,
            }

        elif c_type == "horizontal_tail":
            root_y = 0.0
            tip_y = inputs["data:geometry:" + c_type + ":span"]
            root_chord = inputs["data:geometry:" + c_type + ":root:chord"]
            tip_chord = inputs["data:geometry:" + c_type + ":tip:chord"]
            thickness_ratio = inputs["data:geometry:" + c_type + ":thickness_ratio"]
            thicknesses = np.hstack(
                (
                    inputs["data:geometry:" + c_type + ":skin:thicknesses"],
                    inputs["data:geometry:" + c_type + ":web:thicknesses"],
                )
            )
            dimensions = {
                "root_y": root_y,
                "tip_y": tip_y,
                "root_chord": root_chord,
                "tip_chord": tip_chord,
                "thickness_ratio": thickness_ratio,
            }

        elif c_type == "vertical_tail":
            root_z = inputs["data:geometry:" + c_type + ":root:z"]
            tip_z = inputs["data:geometry:" + c_type + ":tip:z"]
            root_chord = inputs["data:geometry:" + c_type + ":root:chord"]
            tip_chord = inputs["data:geometry:" + c_type + ":tip:chord"]
            thickness_ratio = inputs["data:geometry:" + c_type + ":thickness_ratio"]
            thicknesses = np.hstack(
                (
                    inputs["data:geometry:" + c_type + ":skin:thicknesses"],
                    inputs["data:geometry:" + c_type + ":web:thicknesses"],
                )
            )
            dimensions = {
                "root_z": root_z,
                "tip_z": tip_z,
                "root_chord": root_chord,
                "tip_chord": tip_chord,
                "thickness_ratio": thickness_ratio,
            }

        elif c_type == "strut":
            root_y = inputs["data:geometry:" + c_type + ":root:y"]
            junction_y = inputs["data:geometry:" + c_type + ":junction:y"]
            root_chord = inputs["data:geometry:" + c_type + ":root:chord"]
            junction_chord = inputs["data:geometry:" + c_type + ":junction:chord"]
            thickness_ratio = inputs["data:geometry:" + c_type + ":thickness_ratio"]
            thicknesses = inputs["data:geometry:" + c_type + ":skin:thicknesses"]

            dimensions = {
                "root_y": root_y,
                "junction_y": junction_y,
                "root_chord": root_chord,
                "junction_chord": junction_chord,
                "thickness_ratio": thickness_ratio,
            }

        elif c_type == "fuselage":
            rear_length = inputs["data:geometry:fuselage:rear_length"]
            front_length = inputs["data:geometry:fuselage:front_length"]
            length = inputs["data:geometry:fuselage:length"]
            maximum_width = inputs["data:geometry:fuselage:maximum_width"]
            thicknesses = inputs["data:geometry:fuselage:skin:thicknesses"]

            dimensions = {
                "rear_length": rear_length,
                "front_length": front_length,
                "length": length,
                "maximum_width": maximum_width,
            }

        sections = self.options["number_of_sections"]
        n_spar = inputs["settings:aerostructural:" + c_type + ":n_spar"]
        spar_area = inputs["data:geometry:" + c_type + ":spar_area"]
        nodes = inputs["data:aerostructural:structure:" + c_type + ":nodes"]

        outputs[
            "data:aerostructural:structure:" + c_type + ":beam_properties"
        ] = self._prop_definition(
            c_type, sections, nodes, dimensions, n_spar, spar_area, thicknesses
        )

    @staticmethod
    def _prop_definition(c_type, sections, nodes, dimensions, n_spar, spar_area, thicknesses):
        grids = nodes.astype(np.float)
        if c_type == "wing":
            sections = sections + 1
            thicknesses = np.vstack((thicknesses[0, :], thicknesses))

        if c_type == "wing":
            props = np.zeros((sections * 2, 4))
            c_box_root = (
                dimensions["root_rear_spar_ratio"] - dimensions["root_front_spar_ratio"]
            ) * dimensions["root_chord"]
            h_box_root = dimensions["root_thickness_ratio"] * dimensions["root_chord"]
            c_box_kink = (
                dimensions["kink_rear_spar_ratio"] - dimensions["kink_front_spar_ratio"]
            ) * dimensions["kink_chord"]
            h_box_kink = dimensions["kink_thickness_ratio"] * dimensions["kink_chord"]
            c_box_tip = (
                dimensions["tip_rear_spar_ratio"] - dimensions["tip_front_spar_ratio"]
            ) * dimensions["tip_chord"]
            h_box_tip = dimensions["tip_thickness_ratio"] * dimensions["tip_chord"]
            for i in range(0, sections):
                if grids[i, 1] <= dimensions["kink_y"]:
                    c_box = c_box_root + (grids[i, 1] - dimensions["root_y"]) * (
                        c_box_kink - c_box_root
                    ) / (dimensions["kink_y"] - dimensions["root_y"])
                    h_box = h_box_root + (grids[i, 1] - dimensions["root_y"]) * (
                        h_box_kink - h_box_root
                    ) / (dimensions["kink_y"] - dimensions["root_y"])
                    if n_spar > 1:
                        d_spar = c_box / (n_spar - 1)
                        d2 = np.zeros(n_spar)
                        for j in range(0, n_spar):
                            d2[j] = (d_spar * j - c_box / 2) ** 2
                        s2 = np.sum(d2)
                    else:
                        s2 = 0
                    t_s = thicknesses[i, 0]
                    t_w = thicknesses[i, 1]
                    props[i, 0] = props[i + sections, 0] = (
                        2 * c_box * t_s + 2 * h_box * t_w + n_spar * spar_area
                    )  # A
                    props[i, 1] = props[i + sections, 1] = 2 * (
                        (t_w * h_box ** 3) / 12
                        + (t_s * c_box * h_box ** 2) / 4
                        + (n_spar * spar_area * h_box ** 2) / 4
                    )  # I1
                    props[i, 2] = props[i + sections, 2] = 2 * (
                        (t_s * c_box ** 3) / 12
                        + (t_w * h_box * c_box ** 2) / 4
                        + s2 * spar_area * 2
                    )
                    props[i, 3] = props[i + sections, 3] = (
                        2 * (c_box ** 2 * h_box ** 2 * t_s * t_w) / (c_box * t_w + h_box * t_s)
                    )

                else:
                    c_box = c_box_kink + (grids[i, 1] - dimensions["kink_y"]) * (
                        c_box_tip - c_box_kink
                    ) / (dimensions["tip_y"] - dimensions["kink_y"])
                    h_box = h_box_kink + (grids[i, 1] - dimensions["kink_y"]) * (
                        h_box_tip - h_box_kink
                    ) / (dimensions["tip_y"] - dimensions["kink_y"])
                    if n_spar > 1:
                        d_spar = c_box / (n_spar - 1)
                        d2 = np.zeros(n_spar)
                        for j in range(0, n_spar):
                            d2[j] = (d_spar * j - c_box / 2) ** 2
                        s2 = np.sum(d2)
                    else:
                        s2 = 0
                    t_s = thicknesses[i, 0]
                    t_w = thicknesses[i, 1]
                    props[i, 0] = props[i + sections, 0] = (
                        2 * c_box * t_s + 2 * h_box * t_w + n_spar * spar_area
                    )  # A
                    props[i, 1] = props[i + sections, 1] = 2 * (
                        (t_w * h_box ** 3) / 12
                        + (t_s * c_box * h_box ** 2) / 4
                        + (n_spar * spar_area * h_box ** 2) / 4
                    )  # I1
                    props[i, 2] = props[i + sections, 2] = 2 * (
                        (t_s * c_box ** 3) / 12
                        + (t_w * h_box * c_box ** 2) / 4
                        + s2 * spar_area * 2
                    )
                    props[i, 3] = props[i + sections, 3] = (
                        2 * (c_box ** 2 * h_box ** 2 * t_s * t_w) / (c_box * t_w + h_box * t_s)
                    )

        if c_type == "horizontal_tail":
            props = np.zeros((sections * 2, 4))
            c_box_root = 0.5 * dimensions["root_chord"]
            h_box_root = dimensions["thickness_ratio"] * dimensions["root_chord"]
            c_box_tip = 0.5 * dimensions["tip_chord"]
            h_box_tip = dimensions["thickness_ratio"] * dimensions["tip_chord"]
            for i in range(0, sections):
                c_box = c_box_root + (grids[i, 1] - dimensions["root_y"]) * (
                    c_box_tip - c_box_root
                ) / (dimensions["tip_y"] - dimensions["root_y"])
                h_box = h_box_root + (grids[i, 1] - dimensions["root_y"]) * (
                    h_box_tip - h_box_root
                ) / (dimensions["tip_y"] - dimensions["root_y"])
                if n_spar > 1:
                    d_spar = c_box / (n_spar - 1)
                    d2 = np.zeros(n_spar)
                    for j in range(0, n_spar):
                        d2[j] = (d_spar * j - c_box / 2) ** 2
                    s2 = np.sum(d2)
                else:
                    s2 = 0
                t_s = thicknesses[i, 0]
                t_w = thicknesses[i, 1]
                props[i, 0] = props[i + sections, 0] = (
                    2 * c_box * t_s + 2 * h_box * t_w + n_spar * spar_area
                )
                props[i, 1] = props[i + sections, 1] = 2 * (
                    (t_w * h_box ** 3) / 12
                    + (t_s * c_box * h_box ** 2) / 4
                    + (n_spar * spar_area * h_box ** 2) / 4
                )  # I1
                props[i, 2] = props[i + sections, 2] = 2 * (
                    (t_s * c_box ** 3) / 12 + (t_w * h_box * c_box ** 2) / 4 + s2 * spar_area * 2
                )  # I2
                props[i, 3] = props[i + sections, 3] = (
                    2 * (c_box ** 2 * h_box ** 2 * t_s * t_w) / (c_box * t_w + h_box * t_s)
                )  # J

        if c_type == "strut":
            props = np.zeros((sections * 2, 4))
            h_box_root = dimensions["thickness_ratio"] * dimensions["root_chord"]
            h_box_tip = dimensions["thickness_ratio"] * dimensions["junction_chord"]
            for i in range(0, sections):
                h_box = h_box_root + (grids[i, 1] - dimensions["root_y"]) * (
                    h_box_tip - h_box_root
                ) / (dimensions["junction_y"] - dimensions["root_y"])
                t_s = thicknesses[i]
                props[i, 0] = props[i + sections, 0] = 2 * np.pi * t_s * h_box  # A
                props[i, 1] = props[i + sections, 1] = np.pi * h_box ** 3 * t_s / 4  # I1
                props[i, 2] = props[i + sections, 2] = np.pi * h_box ** 3 * t_s / 4  # I2
                props[i, 3] = props[i + sections, 3] = np.pi * h_box ** 3 * t_s / 2  # J

        if c_type == "vertical_tail":
            props = np.zeros((sections, 4))
            c_box_root = 0.5 * dimensions["root_chord"]
            h_box_root = dimensions["thickness_ratio"] * dimensions["root_chord"]
            c_box_tip = 0.5 * dimensions["tip_chord"]
            h_box_tip = dimensions["thickness_ratio"] * dimensions["tip_chord"]
            for i in range(0, sections):
                c_box = c_box_root + (grids[i, 2] - dimensions["root_z"]) * (
                    c_box_tip - c_box_root
                ) / (dimensions["tip_z"] - dimensions["root_z"])
                h_box = h_box_root + (grids[i, 2] - dimensions["root_z"]) * (
                    h_box_tip - h_box_root
                ) / (dimensions["tip_z"] - dimensions["root_z"])
                if n_spar > 1:
                    d_spar = c_box / (n_spar - 1)
                    d2 = np.zeros(n_spar)
                    for j in range(0, n_spar):
                        d2[j] = (d_spar * j - c_box / 2) ** 2
                    s2 = np.sum(d2)
                else:
                    s2 = 0
                t_s = thicknesses[i, 0]
                t_w = thicknesses[i, 1]
                props[i, 0] = 2 * c_box * t_s + 2 * h_box * t_w + n_spar * spar_area  # A
                props[i, 1] = 2 * (
                    (t_w * h_box ** 3) / 12
                    + (t_s * c_box * h_box ** 2) / 4
                    + (n_spar * spar_area * h_box ** 2) / 4
                )  # I1
                props[i, 2] = 2 * (
                    (t_s * c_box ** 3) / 12 + (t_w * h_box * c_box ** 2) / 4 + s2 * spar_area * 2
                )  # I2
                props[i, 3] = (
                    2 * (c_box ** 2 * h_box ** 2 * t_s * t_w) / (c_box * t_w + h_box * t_s)
                )  # J

        if c_type == "fuselage":
            props = np.zeros((sections, 4))
            w_fuse = dimensions["maximum_width"]
            l_fuse = dimensions["length"]
            x_front = dimensions["front_length"]  # Location of end of front non-cylindrical part
            l_rear = dimensions["rear_length"]
            x_rear = l_fuse - l_rear

            for i in range(0, sections):
                t_s = thicknesses[i]
                if grids[i, 0] <= x_front:
                    r = w_fuse * 0.25 + grids[i, 0] * (w_fuse * 0.25 / x_front)
                    props[i, 0] = 2 * np.pi * t_s * r  # A
                    props[i, 1] = np.pi * r ** 3 * t_s / 4  # I1
                    props[i, 2] = np.pi * r ** 3 * t_s / 4  # I2
                    props[i, 3] = np.pi * r ** 3 * t_s / 2  # J
                elif x_front < grids[i, 0] <= x_rear:
                    r = w_fuse * 0.5
                    props[i, 0] = 2 * np.pi * t_s * r  # A
                    props[i, 1] = np.pi * r ** 3 * t_s / 4  # I1
                    props[i, 2] = np.pi * r ** 3 * t_s / 4  # I2
                    props[i, 3] = np.pi * r ** 3 * t_s / 2  # J
                else:
                    r = w_fuse * 0.5 - (grids[i, 0] - x_rear) * (w_fuse * 0.25) / l_rear
                    props[i, 0] = 2 * np.pi * t_s * r  # A
                    props[i, 1] = np.pi * r ** 3 * t_s / 4  # I1
                    props[i, 2] = np.pi * r ** 3 * t_s / 4  # I2
                    props[i, 3] = np.pi * r ** 3 * t_s / 2  # J

        return props
