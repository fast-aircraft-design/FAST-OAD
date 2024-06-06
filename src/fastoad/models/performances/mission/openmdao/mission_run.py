#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import logging
from os import PathLike
from typing import Optional

import numpy as np
from openmdao import api as om

from fastoad._utils.files import make_parent_dir
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IOMPropulsionWrapper
from fastoad.module_management.service_registry import RegisterPropulsion
from .base import BaseMissionComp
from ..polar import Polar
from ..segments.registered.cruise import BreguetCruiseSegment

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class MissionComp(om.ExplicitComponent, BaseMissionComp):
    """
    Computes a mission as specified in mission input file.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flight_points = None
        self._input_weight_variable_name = ""
        self._engine_wrapper = None

    def initialize(self):
        super().initialize()
        self.options.declare(
            "out_file",
            default="",
            types=(str, PathLike),
            desc="if provided, a csv file will be written at provided path with "
            "all computed flight points.",
        )

    def setup(self):
        super().setup()

        self._engine_wrapper = self.get_engine_wrapper()
        self._engine_wrapper.setup(self)

        self._mission_wrapper.setup(self)

        self._input_weight_variable_name = self._mission_wrapper.get_input_weight_variable_name(
            self.mission_name
        )

        try:
            self.add_input(self.options["reference_area_variable"], np.nan, units="m**2")
        except ValueError:
            pass

        # Global mission outputs
        self.add_output(
            self.name_provider.NEEDED_BLOCK_FUEL.value,
            units="kg",
            desc=f'Needed fuel to complete mission "{self.mission_name}", including reserve fuel',
        )
        self.add_output(
            self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
            units="kg",
            desc=f'consumed fuel quantity before target mass defined for "{self.mission_name}",'
            f" if any (e.g. TakeOff Weight)",
        )

    def setup_partials(self):
        self.declare_partials(["*"], ["*"], method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        propulsion_model = self._engine_wrapper.get_model(inputs)
        reference_area = inputs[self.options["reference_area_variable"]]

        self._mission_wrapper.propulsion = propulsion_model
        self._mission_wrapper.reference_area = reference_area

        # This is the default start point, that can be overridden by using the "start"
        # segment in the mission definition.
        start_flight_point = FlightPoint(
            altitude=0.0, mass=inputs[self._input_weight_variable_name], true_airspeed=0.0
        )

        self.flight_points = self._mission_wrapper.compute(start_flight_point, inputs, outputs)

        self._compute_outputs(outputs, self.flight_points)

        self._postprocess_flight_points(self.flight_points)

    def _postprocess_flight_points(self, flight_points):
        def as_scalar(value):
            if isinstance(value, np.ndarray):
                return value.item()
            return value

        flight_points = flight_points.applymap(as_scalar)
        rename_dict = {
            field_name: f"{field_name} [{unit}]"
            for field_name, unit in FlightPoint.get_units().items()
        }
        flight_points.rename(columns=rename_dict, inplace=True)
        if self.options["out_file"]:
            make_parent_dir(self.options["out_file"])
            flight_points.to_csv(self.options["out_file"])

        return flight_points

    def _compute_outputs(self, outputs, flight_points):
        # Final ================================================================
        end_of_mission = FlightPoint.create(flight_points.iloc[-1])
        outputs[self.name_provider.NEEDED_BLOCK_FUEL.value] = end_of_mission.consumed_fuel
        reserve_var_name = self._mission_wrapper.get_reserve_variable_name()
        if reserve_var_name in outputs:
            outputs[self.name_provider.NEEDED_BLOCK_FUEL.value] += outputs[
                self._mission_wrapper.get_reserve_variable_name()
            ]
        outputs[
            self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value
        ] = self._mission_wrapper.consumed_fuel_before_input_weight

    def get_engine_wrapper(self) -> Optional[IOMPropulsionWrapper]:
        """
        Overloading this method allows to define the engine without relying on the propulsion
        option.

        (useful for tests)

        :return: the engine wrapper instance
        """
        if self.options["propulsion_id"]:
            return RegisterPropulsion.get_provider(self.options["propulsion_id"])

        return None


class AdvancedMissionComp(MissionComp):
    """
    Computes a mission as specified in mission input file.

    Compared to :class:`MissionComp`, it allows:
        - to use an initializer iteration (simple Breguet) at first call.
        - to use the mission as the design mission for the sizing process.
    """

    def initialize(self):
        super().initialize()
        self.options.declare("use_initializer_iteration", default=True, types=bool)
        self.options.declare("is_sizing", default=False, types=bool)

    def setup(self):
        super().setup()

        if self.options["is_sizing"]:
            self.add_output("data:weight:aircraft:sizing_block_fuel", units="kg")
            self.add_output("data:weight:aircraft:sizing_onboard_fuel_at_input_weight", units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        iter_count = self.iter_count_without_approx
        message_prefix = f"Mission computation - iteration {iter_count:d} : "
        if iter_count == 0 and self.options["use_initializer_iteration"]:
            _LOGGER.info(
                "%sUsing initializer computation. OTHER ITERATIONS NEEDED.", message_prefix
            )
            self._compute_breguet(inputs, outputs)
        else:
            _LOGGER.info("%sUsing mission definition.", message_prefix)
            super().compute(inputs, outputs, discrete_inputs, discrete_outputs)
            if self.options["is_sizing"]:
                outputs["data:weight:aircraft:sizing_block_fuel"] = outputs[
                    self.name_provider.NEEDED_BLOCK_FUEL.value
                ]
                outputs["data:weight:aircraft:sizing_onboard_fuel_at_input_weight"] = (
                    outputs[self.name_provider.NEEDED_BLOCK_FUEL.value]
                    - self._mission_wrapper.consumed_fuel_before_input_weight
                )

    def _compute_breguet(self, inputs, outputs):
        """
        Computes mission using simple Breguet formula at altitude==100m and Mach 0.1
        (but max L/D ratio is assumed anyway)

        Useful only for initiating the computation.

        :param inputs: OpenMDAO input vector
        :param outputs: OpenMDAO output vector
        """
        propulsion_model = self._engine_wrapper.get_model(inputs)

        high_speed_polar = self._get_initial_polar(inputs)
        distance = np.sum(self._mission_wrapper.get_route_ranges(inputs)).item()

        altitude = 100.0
        cruise_mach = 0.1

        breguet = BreguetCruiseSegment(
            target=FlightPoint(ground_distance=distance),
            propulsion=propulsion_model,
            polar=high_speed_polar,
            use_max_lift_drag_ratio=True,
        )
        start_point = FlightPoint(
            mass=inputs[self._input_weight_variable_name],
            altitude=altitude,
            mach=cruise_mach,
        )
        flight_points = breguet.compute_from(start_point)
        end_point = FlightPoint.create(flight_points.iloc[-1])
        outputs[self.name_provider.NEEDED_BLOCK_FUEL.value] = start_point.mass - end_point.mass

    @staticmethod
    def _get_initial_polar(inputs) -> Polar:
        """
        At computation start, polar may be irrelevant and give a very low lift/drag ratio.

        In that case, this method returns a fake polar that has 10.0 as max lift drag ratio.
        Otherwise, the actual cruise polar is returned.
        """
        high_speed_polar = Polar(
            inputs["data:aerodynamics:aircraft:cruise:CL"],
            inputs["data:aerodynamics:aircraft:cruise:CD"],
        )
        use_minimum_l_d_ratio = False
        try:
            if (
                high_speed_polar.optimal_cl / high_speed_polar.cd(high_speed_polar.optimal_cl)
                < 10.0
            ):
                use_minimum_l_d_ratio = True
        except ZeroDivisionError:
            use_minimum_l_d_ratio = True
        if use_minimum_l_d_ratio:
            # We replace by a polar that has at least 10.0 as max L/D ratio
            high_speed_polar = Polar(np.array([0.0, 0.5, 1.0]), np.array([0.1, 0.05, 1.0]))

        return high_speed_polar
