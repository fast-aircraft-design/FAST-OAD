"""
OpenMDAO component for time-step computation of missions.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
import os.path as pth
from collections import namedtuple
from importlib.resources import path
from os import makedirs

import numpy as np
import openmdao.api as om
import pandas as pd

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IOMPropulsionWrapper
from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterPropulsion
from . import resources
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition
from ..polar import Polar
from ..segments.cruise import BreguetCruiseSegment

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@RegisterOpenMDAOSystem("fastoad.performances.mission", domain=ModelDomain.PERFORMANCE)
class Mission(om.Group):
    """
    Computes a mission as specified in mission input file.
    """

    def initialize(self):
        self.options.declare(
            "propulsion_id",
            default="",
            types=str,
            desc="(mandatory) The identifier of the propulsion wrapper.",
        )
        self.options.declare(
            "out_file",
            default="",
            types=str,
            desc="If provided, a csv file will be written at provided path with all computed "
            "flight points.",
        )
        self.options.declare(
            "mission_file_path",
            default="::sizing_mission",
            types=(str, MissionDefinition),
            allow_none=True,
            desc="The path to file that defines the mission.\n"
            'If can also begin with two colons "::" to use pre-defined missions:\n'
            '  - "::sizing_mission" : design mission for CeRAS-01\n'
            '  - "::breguet" : a simple mission with Breguet formula for cruise, and input\n'
            "    coefficients for fuel reserve and fuel consumption during climb and descent",
        )
        self.options.declare(
            "mission_name",
            default=None,
            types=str,
            allow_none=True,
            desc="The mission name. Required if mission file defines several missions.",
        )
        self.options.declare(
            "use_initializer_iteration",
            default=True,
            types=bool,
            desc="During first solver loop, a complete mission computation can fail or consume "
            "useless CPU-time.\n"
            "When activated, this option ensures the first iteration is done using a simple,\n"
            "dummy, formula instead of the specified mission.\n"
            "Set this option to False if you do expect this model to be computed only once.",
        )
        self.options.declare(
            "adjust_fuel",
            default=True,
            types=bool,
            desc="If True, block fuel will fit fuel consumption during mission. In that case, a "
            "solver (local or global) will be needed. (see `add_solver` option for more"
            "information)\n"
            "If False, block fuel will be taken from input data.",
        )
        self.options.declare(
            "compute_TOW",
            default=False,
            types=bool,
            desc="If True, TakeOff Weight will be computed from onboard fuel at takeoff and ZFW.\n"
            "If False, block fuel will be computed from ramp weight and ZFW.\n"
            "Not used (actually forced to True) if adjust_fuel is True.",
        )
        self.options.declare(
            "add_solver",
            default=False,
            types=bool,
            desc="If True, a local solver is set for the mission computation.\n"
            "It is useful if `adjust_fuel` is set to True, or to ensure consistency between "
            "ramp weight and takeoff weight + taxi-out fuel.\n"
            "If a global solver is used, using a local solver or not should be only a question"
            "of CPU time consumption and is not expected to modify the results.",
        )
        self.options.declare(
            "is_sizing",
            default=False,
            types=bool,
            desc="If True, TOW will be considered equal to MTOW and mission payload will be "
            "considered equal to design payload.",
        )
        self.options.declare(
            "reference_area_variable",
            default="data:geometry:wing:area",
            types=str,
            desc="Defines the name of the variable for providing aircraft reference surface area.",
        )

    def setup(self):
        if "::" in self.options["mission_file_path"]:
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            i = self.options["mission_file_path"].index("::")
            file_name = self.options["mission_file_path"][i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                self.options["mission_file_path"] = MissionDefinition(mission_input_file)
        self._mission_wrapper = MissionWrapper(self.options["mission_file_path"])
        if self.options["mission_name"] is None:
            self.options["mission_name"] = self._mission_wrapper.get_unique_mission_name()

        mission_name = self.options["mission_name"]

        self.add_subsystem("ZFW_computation", self._get_zfw_component(mission_name), promotes=["*"])
        self.add_subsystem(
            "ramp_weight_computation",
            self._get_ramp_weight_component(mission_name),
            promotes=["*"],
        )

        if self.options["adjust_fuel"]:
            self.options["compute_TOW"] = True
            self.connect(
                f"data:mission:{mission_name}:needed_onboard_fuel_at_takeoff",
                f"data:mission:{mission_name}:onboard_fuel_at_takeoff",
            )
        if self.options["add_solver"]:
            self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, rtol=1.0e-4, iprint=0)
            self.linear_solver = om.DirectSolver()

        if self.options["compute_TOW"]:
            self.add_subsystem(
                "TOW_computation", self._get_tow_component(mission_name), promotes=["*"]
            )
        # Needed when TOW should be defined as input in the mission definition file:
        self.set_input_defaults(f"data:mission:{mission_name}:TOW", np.nan, "kg")

        mission_options = dict(self.options.items())
        del mission_options["adjust_fuel"]
        del mission_options["compute_TOW"]
        del mission_options["add_solver"]
        del mission_options["mission_file_path"]
        mission_options["mission_wrapper"] = self._mission_wrapper
        mission_options["mission_name"] = mission_name

        self.add_subsystem(
            "mission_computation", MissionComponent(**mission_options), promotes=["*"]
        )
        self.add_subsystem(
            "block_fuel_computation", self._get_block_fuel_component(mission_name), promotes=["*"]
        )

    @property
    def flight_points(self) -> pd.DataFrame:
        """Dataframe that lists all computed flight point data."""
        return self.mission_computation.flight_points

    def _get_zfw_component(self, mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes Zero Fuel Weight from OWE and mission payload
        """
        if self.options["is_sizing"]:
            payload_var = "data:weight:aircraft:payload"
        else:
            payload_var = f"data:mission:{mission_name}:payload"

        zfw_computation = om.AddSubtractComp()
        zfw_computation.add_equation(
            f"data:mission:{mission_name}:ZFW",
            ["data:weight:aircraft:OWE", payload_var],
            units="kg",
            desc=f'Zero Fuel Weight for mission "{mission_name}"',
        )
        return zfw_computation

    @staticmethod
    def _get_tow_component(mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes TakeOff Weight from ZFW and loaded fuel at takeoff
        """
        tow_computation = om.AddSubtractComp()
        tow_computation.add_equation(
            f"data:mission:{mission_name}:TOW",
            [
                f"data:mission:{mission_name}:ZFW",
                f"data:mission:{mission_name}:onboard_fuel_at_takeoff",
            ],
            units="kg",
            desc=f'TakeOff Weight for mission "{mission_name}"',
        )
        return tow_computation

    def _get_ramp_weight_component(self, mission_name: str):
        """

        :param mission_name:
        :return: component that computes Ramp Weight from TakeOff Weight and (possibly) Taxi-out
                 fuel
        """
        # Using ExecComp is the only way I found to set a variable equal to another one.
        # (group.connect() will work only if TOW is an output in the group, and AddSubtractComp
        # requires at least 2 inputs)
        # And since our variable names won't be parsed by ExecComp, we use promotion aliases
        # in a Group.
        # And when taxi-out fuel has to be used, an AddSubtractComp would do, but it's better
        # to keep the same logic.

        operation = "a=b"
        promotions = [
            ("a", f"data:mission:{mission_name}:ramp_weight"),
            ("b", f"data:mission:{mission_name}:TOW"),
        ]
        if self._mission_wrapper.has_taxi_out(mission_name):
            operation += "+c"
            promotions.append(("c", f"data:mission:{mission_name}:taxi_out:fuel"))

        ramp_weight_computation = om.Group()
        ramp_weight_computation.add_subsystem(
            "equality",
            om.ExecComp(operation, units="kg"),
            promotes=promotions,
        )

        return ramp_weight_computation

    @staticmethod
    def _get_block_fuel_component(mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes block fuel from ramp weight and ZFW
        """
        block_fuel_computation = om.AddSubtractComp()
        block_fuel_computation.add_equation(
            output_name=f"data:mission:{mission_name}:block_fuel",
            input_names=[
                f"data:mission:{mission_name}:ramp_weight",
                f"data:mission:{mission_name}:ZFW",
            ],
            units="kg",
            scaling_factors=[1, -1],
            desc=f'Loaded fuel at beginning for mission "{mission_name}"',
        )

        return block_fuel_computation


_MissionVariables = namedtuple(
    "_MissionVariables",
    [
        "START_ALTITUDE",
        "START_TAS",
        "RAMP_WEIGHT",
        "TOW",
        "NEEDED_BLOCK_FUEL",
        "NEEDED_FUEL_AT_TAKEOFF",
        "TAXI_OUT_FUEL",
    ],
)


class MissionComponent(om.ExplicitComponent):
    def __init__(self, **kwargs):
        """
        Computes a mission as specified in mission input file

        Options:
          - propulsion_id: (mandatory) the identifier of the propulsion wrapper.
          - out_file: if provided, a csv file will be written at provided path with all computed
                      flight points.
          - mission_wrapper: the MissionWrapper instance that defines the mission.
          - use_initializer_iteration: During first solver loop, a complete mission computation can
                                       fail or consume useless CPU-time. When activated, this option
                                       ensures the first iteration is done using a simple, dummy,
                                       formula instead of the specified mission.
                                       Set this option to False if you do expect this model to be
                                       computed only once.
          - is_sizing: if True, TOW will be considered equal to MTOW and mission payload will be
                       considered equal to design payload.
          - reference_area_variable: Defines the name of the variable for providing aircraft
                                     reference surface area.
        """
        super().__init__(**kwargs)
        self.flight_points = None
        self._engine_wrapper = None
        self._mission_wrapper: MissionWrapper = None
        self._mission_vars: _MissionVariables = None

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)
        self.options.declare("use_initializer_iteration", default=True, types=bool)
        self.options.declare("mission_wrapper", types=MissionWrapper)
        self.options.declare("mission_name", types=str)
        self.options.declare("is_sizing", default=False, types=bool)
        self.options.declare(
            "reference_area_variable", default="data:geometry:wing:area", types=str
        )

    def setup(self):
        self._engine_wrapper = self._get_engine_wrapper()
        self._engine_wrapper.setup(self)
        self._mission_wrapper = self.options["mission_wrapper"]
        self._mission_wrapper.setup(self, self.options["mission_name"])

        mission_name = self.options["mission_name"]

        self._mission_vars = _MissionVariables(
            START_ALTITUDE=f"data:mission:{mission_name}:start:altitude",
            START_TAS=f"data:mission:{mission_name}:start:true_airspeed",
            RAMP_WEIGHT=f"data:mission:{mission_name}:ramp_weight",
            TOW=f"data:mission:{mission_name}:TOW",
            NEEDED_BLOCK_FUEL=f"data:mission:{mission_name}:needed_block_fuel",
            NEEDED_FUEL_AT_TAKEOFF=f"data:mission:{mission_name}:needed_onboard_fuel_at_takeoff",
            TAXI_OUT_FUEL=f"data:mission:{mission_name}:taxi_out:fuel",
        )
        try:
            self.add_input(
                self._mission_vars.TOW,
                np.nan,
                units="kg",
                desc='TakeOff Weight for mission "%s"' % mission_name,
            )
        except ValueError:
            pass

        try:
            self.add_input(self.options["reference_area_variable"], np.nan, units="m**2")
        except ValueError:
            pass

        # Mission start inputs
        self.add_input(
            self._mission_vars.START_ALTITUDE,
            0.0,
            units="ft",
            desc=f'Starting altitude for mission "{mission_name}"',
        )
        self.add_input(
            self._mission_vars.START_TAS,
            0.0,
            units="m/s",
            desc=f'Starting speed for mission "{mission_name}"',
        )
        if self._mission_wrapper.need_start_mass(mission_name):
            self.add_input(
                self._mission_vars.RAMP_WEIGHT,
                np.nan,
                units="kg",
                desc=f'Starting mass for mission "{mission_name}"',
            )

        # Global mission outputs
        self.add_output(
            self._mission_vars.NEEDED_BLOCK_FUEL,
            units="kg",
            desc=f'Needed fuel to complete mission "{mission_name}", including reserve fuel',
        )
        self.add_output(
            self._mission_vars.NEEDED_FUEL_AT_TAKEOFF,
            units="kg",
            desc=f'fuel quantity at instant of takeoff of mission "{mission_name}"',
        )

        if self.options["is_sizing"]:
            self.add_output("data:weight:aircraft:sizing_block_fuel", units="kg")
            self.add_output("data:weight:aircraft:sizing_onboard_fuel_at_takeoff", units="kg")

    def setup_partials(self):
        self.declare_partials(["*"], ["*"], method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        iter_count = self.iter_count_without_approx
        message_prefix = f"Mission computation - iteration {iter_count:d} : "
        if iter_count == 0 and self.options["use_initializer_iteration"]:
            _LOGGER.info(message_prefix + "Using initializer computation. OTHER ITERATIONS NEEDED.")
            self._compute_breguet(inputs, outputs)
        else:
            _LOGGER.info(message_prefix + "Using mission definition.")
            self._compute_mission(inputs, outputs)

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
        distance = np.sum(
            self._mission_wrapper.get_route_ranges(inputs, self.options["mission_name"])
        ).item()

        altitude = 100.0
        cruise_mach = 0.1

        breguet = BreguetCruiseSegment(
            target=FlightPoint(ground_distance=distance),
            propulsion=propulsion_model,
            polar=high_speed_polar,
            use_max_lift_drag_ratio=True,
        )
        start_point = FlightPoint(
            mass=inputs[self._mission_vars.TOW], altitude=altitude, mach=cruise_mach
        )
        flight_points = breguet.compute_from(start_point)
        end_point = FlightPoint.create(flight_points.iloc[-1])
        outputs[self._mission_vars.NEEDED_BLOCK_FUEL] = start_point.mass - end_point.mass

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

    def _compute_mission(self, inputs, outputs):
        """
        Computes mission using time-step integration.

        :param inputs: OpenMDAO input vector
        :param outputs: OpenMDAO output vector
        """
        propulsion_model = self._engine_wrapper.get_model(inputs)
        reference_area = inputs[self.options["reference_area_variable"]]

        self._mission_wrapper.propulsion = propulsion_model
        self._mission_wrapper.reference_area = reference_area

        start_flight_point = FlightPoint(
            altitude=inputs[self._mission_vars.START_ALTITUDE],
            true_airspeed=inputs[self._mission_vars.START_TAS],
            mass=(
                inputs[self._mission_vars.RAMP_WEIGHT]
                if self._mission_vars.RAMP_WEIGHT in inputs
                else 0.0
            ),
        )

        self.flight_points = self._mission_wrapper.compute(start_flight_point, inputs, outputs)

        # Final ================================================================
        start_of_mission = FlightPoint.create(self.flight_points.iloc[0])
        end_of_mission = FlightPoint.create(self.flight_points.iloc[-1])
        reserve = self._mission_wrapper.get_reserve(
            self.flight_points, self.options["mission_name"]
        )
        reserve_name = self._mission_wrapper.get_reserve_variable_name()
        if reserve_name in outputs:
            outputs[reserve_name] = reserve
        outputs[self._mission_vars.NEEDED_BLOCK_FUEL] = (
            start_of_mission.mass - end_of_mission.mass + reserve
        )
        outputs[self._mission_vars.NEEDED_FUEL_AT_TAKEOFF] = outputs[
            self._mission_vars.NEEDED_BLOCK_FUEL
        ]
        if self._mission_vars.TAXI_OUT_FUEL in outputs:
            outputs[self._mission_vars.NEEDED_FUEL_AT_TAKEOFF] -= outputs[
                self._mission_vars.TAXI_OUT_FUEL
            ]

        if self.options["is_sizing"]:
            outputs["data:weight:aircraft:sizing_block_fuel"] = outputs[
                self._mission_vars.NEEDED_BLOCK_FUEL
            ]
            outputs["data:weight:aircraft:sizing_onboard_fuel_at_takeoff"] = outputs[
                self._mission_vars.NEEDED_FUEL_AT_TAKEOFF
            ]

        def as_scalar(value):
            if isinstance(value, np.ndarray):
                return value.item()
            return value

        self.flight_points = self.flight_points.applymap(as_scalar)
        rename_dict = {
            field_name: f"{field_name} [{unit}]"
            for field_name, unit in FlightPoint.get_units().items()
        }
        self.flight_points.rename(columns=rename_dict, inplace=True)

        if self.options["out_file"]:
            makedirs(pth.dirname(self.options["out_file"]), exist_ok=True)
            self.flight_points.to_csv(self.options["out_file"])

    def _get_engine_wrapper(self) -> IOMPropulsionWrapper:
        """
        Overloading this method allows to define the engine without relying on the propulsion
        option.

        (useful for tests)

        :return: the engine wrapper instance
        """
        return RegisterPropulsion.get_provider(self.options["propulsion_id"])
