"""
Computation of lift and drag increment due to high-lift devices
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from importlib.resources import open_text

import numpy as np
import openmdao.api as om
from scipy import interpolate

from fastoad.module_management.service_registry import RegisterSubmodel
from . import resources
from ..constants import SERVICE_HIGH_LIFT

LIFT_EFFECTIVENESS_FILENAME = "interpolation of lift effectiveness.txt"


@RegisterSubmodel(SERVICE_HIGH_LIFT, "fastoad.submodel.aerodynamics.high_lift.legacy")
class ComputeDeltaHighLift(om.ExplicitComponent):
    """
    Provides lift and drag increments due to high-lift devices
    """

    def initialize(self):
        self.options.declare("landing_flag", default=False, types=bool)

    def setup(self):

        if self.options["landing_flag"]:
            self.add_input("data:mission:sizing:landing:flap_angle", val=np.nan, units="deg")
            self.add_input("data:mission:sizing:landing:slat_angle", val=np.nan, units="deg")
            self.add_input("data:aerodynamics:aircraft:landing:mach", val=np.nan)
            self.add_output("data:aerodynamics:high_lift_devices:landing:CL")
            self.add_output("data:aerodynamics:high_lift_devices:landing:CD")
        else:
            self.add_input("data:mission:sizing:takeoff:flap_angle", val=np.nan, units="deg")
            self.add_input("data:mission:sizing:takeoff:slat_angle", val=np.nan, units="deg")
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:high_lift_devices:takeoff:CL")
            self.add_output("data:aerodynamics:high_lift_devices:takeoff:CD")

        self.add_input("data:geometry:wing:sweep_0", val=np.nan, units="rad")
        self.add_input("data:geometry:wing:sweep_100_outer", val=np.nan, units="rad")
        self.add_input("data:geometry:flap:chord_ratio", val=np.nan)
        self.add_input("data:geometry:flap:span_ratio", val=np.nan)
        self.add_input("data:geometry:slat:chord_ratio", val=np.nan)
        self.add_input("data:geometry:slat:span_ratio", val=np.nan)
        self.add_input(
            "tuning:aerodynamics:high_lift_devices:landing:CD:multi_slotted_flap_effect:k", val=1.0
        )
        self.add_input(
            "tuning:aerodynamics:high_lift_devices:landing:CL:multi_slotted_flap_effect:k", val=1.0
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        if self.options["landing_flag"]:
            flap_angle = inputs["data:mission:sizing:landing:flap_angle"]
            slat_angle = inputs["data:mission:sizing:landing:slat_angle"]
            mach = inputs["data:aerodynamics:aircraft:landing:mach"]
        else:
            flap_angle = inputs["data:mission:sizing:takeoff:flap_angle"]
            slat_angle = inputs["data:mission:sizing:takeoff:slat_angle"]
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]

        k_cd_slot = inputs[
            "tuning:aerodynamics:high_lift_devices:landing:CD:multi_slotted_flap_effect:k"
        ]
        k_cl_slot = inputs[
            "tuning:aerodynamics:high_lift_devices:landing:CL:multi_slotted_flap_effect:k"
        ]
        le_sweep_angle = inputs["data:geometry:wing:sweep_0"]
        te_sweep_angle = inputs["data:geometry:wing:sweep_100_outer"]
        flap_chord_ratio = inputs["data:geometry:flap:chord_ratio"]
        flap_span_ratio = inputs["data:geometry:flap:span_ratio"]
        slat_chord_ratio = inputs["data:geometry:slat:chord_ratio"]
        slat_span_ratio = inputs["data:geometry:slat:span_ratio"]

        if self.options["landing_flag"]:
            outputs["data:aerodynamics:high_lift_devices:landing:CL"] = self._get_delta_cl(
                slat_angle,
                flap_angle,
                slat_span_ratio,
                flap_span_ratio,
                slat_chord_ratio,
                flap_chord_ratio,
                mach,
                le_sweep_angle,
                te_sweep_angle,
                k_cl_slot,
            )
            outputs["data:aerodynamics:high_lift_devices:landing:CD"] = self._get_delta_cd(
                slat_angle, flap_angle, slat_span_ratio, flap_span_ratio, k_cd_slot
            )
        else:
            outputs["data:aerodynamics:high_lift_devices:takeoff:CL"] = self._get_delta_cl(
                slat_angle,
                flap_angle,
                slat_span_ratio,
                flap_span_ratio,
                slat_chord_ratio,
                flap_chord_ratio,
                mach,
                le_sweep_angle,
                te_sweep_angle,
                k_cl_slot,
            )
            outputs["data:aerodynamics:high_lift_devices:takeoff:CD"] = self._get_delta_cd(
                slat_angle, flap_angle, slat_span_ratio, flap_span_ratio, k_cd_slot
            )

    def _get_delta_cl(
        self,
        slat_angle,
        flap_angle,
        slat_span_ratio,
        flap_span_ratio,
        slat_chord_ratio,
        flap_chord_ratio,
        mach,
        le_sweep_angle,
        te_sweep_angle,
        k_cl_slot,
    ):
        """
        Method based on Roskam book and Raymer book

        :param slat_angle: in degrees
        :param flap_angle: in degrees
        :param slat_span_ratio: the ratio of the part of wing which is equipped with slat
        :param flap_span_ratio: the ratio of the part of wing which is equipped with flap
        :param slat_chord_ratio: average ratio of slat chord to clean chord
        :param flap_chord_ratio: average ratio of flap chord to clean chord
        :param mach:
        :param le_sweep_angle: sweep angle at leading edge
        :param te_sweep_angle: sweep angle at trailing edge
        :param k_cl_slot: multiple slotted flap correction factor
        :return: increment of lift coefficient
        """

        flap_angle = np.radians(flap_angle)
        slat_angle = np.radians(slat_angle)

        #  ratio of chord with flap extended compared to clean chord
        ratio_c_flap = 1.0 + flap_chord_ratio * np.cos(flap_angle)

        alpha_flap = self._compute_alpha_flap(flap_angle * 57.3, flap_chord_ratio)

        # cl created by the flap in 2D
        delta_cl_flap = (
            2.0
            * np.pi
            / np.sqrt(1 - mach ** 2)
            * ratio_c_flap
            * alpha_flap
            * flap_angle
            * k_cl_slot
        )

        # ratio of chord with slat extended compared to clean chord
        ratio_c_slat = 1.0 + slat_chord_ratio * np.cos(slat_angle)

        # leading edge slat effectiveness
        cl_delta = (
            5.05503e-7
            + 0.00666 * slat_chord_ratio
            + 0.23758 * slat_chord_ratio ** 2
            - 4.3639 * slat_chord_ratio ** 3
            + 51.16323 * slat_chord_ratio ** 4
            - 320.10803 * slat_chord_ratio ** 5
            + 1142.23033 * slat_chord_ratio ** 6
            - 2340.75209 * slat_chord_ratio ** 7
            + 2570.35947 * slat_chord_ratio ** 8
            - 1173.73465 * slat_chord_ratio ** 9
        )

        #  cl created by the slat in 2D
        delta_cl_slat = cl_delta * slat_angle * 57.3 * ratio_c_slat

        #  cl due to flap and slat including 3D
        delta_cl_total = delta_cl_flap * flap_span_ratio * np.cos(
            te_sweep_angle
        ) + delta_cl_slat * slat_span_ratio * np.cos(
            le_sweep_angle
        )  # this equation is from ref Raymer book

        return delta_cl_total

    def _get_delta_cd(self, slat_angle, flap_angle, slat_span_ratio, flap_span_ratio, k_cd_slot):
        """

        :param slat_angle: in degrees
        :param flap_angle: in degrees
        :param slat_span_ratio: the ratio of the part of wing which is equipped with slat
        :param flap_span_ratio: the ratio of the part of wing which is equipped with flap
        :param k_cd_slot: multiple slotted flap correction factor
        :return: increment of drag coefficient
        """

        cd0_slat = (
            (
                -0.00266
                + 0.06065 * slat_angle
                - 0.03023 * slat_angle ** 2
                + 0.01055 * slat_angle ** 3
                - 0.00176 * slat_angle ** 4
                + 1.77986e-4 * slat_angle ** 5
                - 1.11754e-5 * slat_angle ** 6
                + 4.19082e-7 * slat_angle ** 7
                - 8.53492e-9 * slat_angle ** 8
                + 7.24194e-11 * slat_angle ** 9
            )
            * slat_span_ratio
            / 100
        )
        cd0_flap = (
            (
                -0.01523
                + 0.05145 * flap_angle
                - 9.53201e-4 * flap_angle ** 2
                + 7.5972e-5 * flap_angle ** 3
            )
            * k_cd_slot
            * flap_span_ratio
            / 100
        )
        total_cd0 = cd0_flap + cd0_slat

        return total_cd0

    def _compute_alpha_flap(self, flap_angle, ratio_cf_flap):
        temp_array = []
        with open_text(resources, LIFT_EFFECTIVENESS_FILENAME) as fichier:
            for line in fichier:
                temp_array.append([float(x) for x in line.split(",")])
        x1 = []
        y1 = []
        x2 = []
        y2 = []
        x3 = []
        y3 = []
        x4 = []
        y4 = []
        x5 = []
        y5 = []

        for arr in temp_array:
            x1.append(arr[0])
            y1.append(arr[1])
            x2.append(arr[2])
            y2.append(arr[3])
            x3.append(arr[4])
            y3.append(arr[5])
            x4.append(arr[6])
            y4.append(arr[7])
            x5.append(arr[8])
            y5.append(arr[9])

        tck1 = interpolate.splrep(x1, y1, s=0)
        tck2 = interpolate.splrep(x2, y2, s=0)
        tck3 = interpolate.splrep(x3, y3, s=0)
        tck4 = interpolate.splrep(x4, y4, s=0)
        tck5 = interpolate.splrep(x5, y5, s=0)
        ynew1 = interpolate.splev(flap_angle, tck1, der=0)
        ynew2 = interpolate.splev(flap_angle, tck2, der=0)
        ynew3 = interpolate.splev(flap_angle, tck3, der=0)
        ynew4 = interpolate.splev(flap_angle, tck4, der=0)
        ynew5 = interpolate.splev(flap_angle, tck5, der=0)
        zs = [0.15, 0.20, 0.25, 0.30, 0.40]
        y_final = [ynew1, ynew2, ynew3, ynew4, ynew5]
        tck6 = interpolate.splrep(zs, y_final, s=0)
        return interpolate.splev(ratio_cf_flap, tck6, der=0)
