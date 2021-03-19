"""
OpenMDAO component for time-step computation of missions.
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

import logging
from enum import Enum
from importlib.resources import path

import numpy as np
import openmdao.api as om
import pandas as pd
from scipy.constants import foot

from fastoad.base.flight_point import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet, IOMPropulsionWrapper
from fastoad.module_management.service_registry import RegisterPropulsion
from . import resources
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition
from ..polar import Polar
from ..segments.cruise import BreguetCruiseSegment

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class Mission(om.Group):
    """
    Computes a mission as specified in mission input file.

    Options:
      - propulsion_id: (mandatory) the identifier of the propulsion wrapper.
      - out_file: if provided, a csv file will be written at provided path with all computed
                  flight points.
      - mission_file_path: the path to file that defines the mission.
                           If can also begin with two colons "::" to use pre-defined missions:
                               - "::sizing_mission" : design mission for CeRAS-01
                               - "::breguet" : a simple mission with Breguet formula for cruise, and
                                               input coefficients for fuel reserve and fuel
                                               consumption during climb and descent
      - mission_name: the mission name. Required if mission file defines several missions.
      - use_initializer_iteration: During first solver loop, a complete mission computation can
                                   fail or consume useless CPU-time. When activated, this option
                                   ensures the first iteration is done using a simple, dummy,
                                   formula instead of the specified mission.
                                   Set this option to False if you do expect this model to be
                                   computed only once.
      - adjust_fuel: if True, block fuel will fit fuel consumption during mission.
      - compute_TOW: if True, TakeOff Weight will be computed from mission block fuel and ZFW.
                     If False, block fuel will be computed from TOW and ZFW.
                     Not used (actually forced to True) if adjust_fuel is True.
      - add_solver: not used if compute_TOW is False. Otherwise, setting this option to False will
                    deactivate the local solver. Useful if a global solver is used.
      - is_sizing: if True, TOW will be considered equal to MTOW and mission payload will be
                   considered equal to design payload.
    """

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)
        self.options.declare(
            "mission_file_path",
            default="::sizing_mission",
            types=(str, MissionDefinition),
            allow_none=True,
        )
        self.options.declare("mission_name", default=None, types=str, allow_none=True)
        self.options.declare("use_initializer_iteration", default=True, types=bool)
        self.options.declare("adjust_fuel", default=True, types=bool)
        self.options.declare("compute_TOW", default=False, types=bool)
        self.options.declare("add_solver", default=False, types=bool)
        self.options.declare("is_sizing", default=False, types=bool)

    def setup(self):
        if "::" in self.options["mission_file_path"]:
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            i = self.options["mission_file_path"].index("::")
            file_name = self.options["mission_file_path"][i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                self.options["mission_file_path"] = MissionDefinition(mission_input_file)
        mission_wrapper = MissionWrapper(self.options["mission_file_path"])
        if self.options["mission_name"] is None:
            self.options["mission_name"] = mission_wrapper.get_unique_mission_name()

        mission_name = self.options["mission_name"]

        self.add_subsystem("ZFW_computation", self._get_zfw_component(mission_name), promotes=["*"])

        if self.options["adjust_fuel"]:
            self.options["compute_TOW"] = True
            self.connect(
                "data:mission:%s:needed_block_fuel" % mission_name,
                "data:mission:%s:block_fuel" % mission_name,
            )
            if self.options["add_solver"]:
                self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, rtol=1.0e-4, iprint=0)
                self.linear_solver = om.DirectSolver()

        if self.options["compute_TOW"]:
            self.add_subsystem(
                "TOW_computation", self._get_tow_component(mission_name), promotes=["*"]
            )
        else:
            self.add_subsystem(
                "block_fuel_computation",
                self._get_block_fuel_component(mission_name),
                promotes=["*"],
            )

        mission_options = dict(self.options.items())
        del mission_options["adjust_fuel"]
        del mission_options["compute_TOW"]
        del mission_options["add_solver"]
        del mission_options["mission_file_path"]
        mission_options["mission_wrapper"] = mission_wrapper
        mission_options["mission_name"] = mission_name
        self.add_subsystem(
            "mission_computation", MissionComponent(**mission_options), promotes=["*"]
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
            payload_var = "data:mission:%s:payload" % mission_name

        zfw_computation = om.AddSubtractComp()
        zfw_computation.add_equation(
            "data:mission:%s:ZFW" % mission_name,
            ["data:weight:aircraft:OWE", payload_var],
            units="kg",
        )
        return zfw_computation

    @staticmethod
    def _get_tow_component(mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes TakeOff Weight from ZFW and needed block fuel
        """
        tow_computation = om.AddSubtractComp()
        tow_computation.add_equation(
            "data:mission:%s:TOW" % mission_name,
            ["data:mission:%s:ZFW" % mission_name, "data:mission:%s:block_fuel" % mission_name,],
            units="kg",
        )
        return tow_computation

    @staticmethod
    def _get_block_fuel_component(mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes initial block fuel from TOW and ZFW
        """
        block_fuel_computation = om.AddSubtractComp()
        block_fuel_computation.add_equation(
            "data:mission:%s:block_fuel" % mission_name,
            ["data:mission:%s:TOW" % mission_name, "data:mission:%s:ZFW" % mission_name],
            units="kg",
            scaling_factors=[1, -1],
        )
        return block_fuel_computation


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
        """
        super().__init__(**kwargs)
        self.flight_points = None
        self._engine_wrapper = None
        self._mission_wrapper: MissionWrapper = None
        self._mission_vars: type = None

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)
        self.options.declare("use_initializer_iteration", default=True, types=bool)
        self.options.declare("mission_wrapper", types=MissionWrapper)
        self.options.declare("mission_name", types=str)
        self.options.declare("is_sizing", default=False, types=bool)

    def setup(self):
        self._engine_wrapper = self._get_engine_wrapper()
        self._engine_wrapper.setup(self)
        self._mission_wrapper = self.options["mission_wrapper"]
        self._mission_wrapper.setup(self, self.options["mission_name"])

        mission_name = self.options["mission_name"]

        class MissionVars(Enum):
            TOW = "data:mission:%s:TOW" % mission_name
            BLOCK_FUEL = "data:mission:%s:needed_block_fuel" % mission_name
            TAXI_OUT_FUEL = "data:mission:%s:taxi_out:fuel" % mission_name
            TAKEOFF_FUEL = "data:mission:%s:takeoff:fuel" % mission_name
            TAKEOFF_ALTITUDE = "data:mission:%s:takeoff:altitude" % mission_name
            TAKEOFF_V2 = "data:mission:%s:takeoff:V2" % mission_name

        self._mission_vars = MissionVars

        self.add_input("data:geometry:propulsion:engine:count", 2)
        self.add_input("data:geometry:wing:area", np.nan, units="m**2")
        self.add_input(self._mission_vars.TOW.value, np.nan, units="kg")
        self.add_input(self._mission_vars.TAXI_OUT_FUEL.value, np.nan, units="kg")
        self.add_input(self._mission_vars.TAKEOFF_ALTITUDE.value, np.nan, units="m")
        self.add_input(self._mission_vars.TAKEOFF_FUEL.value, np.nan, units="kg")
        self.add_input(self._mission_vars.TAKEOFF_V2.value, np.nan, units="m/s")

        self.add_output(self._mission_vars.BLOCK_FUEL.value, units="kg")
        if self.options["is_sizing"]:
            self.add_output("data:weight:aircraft:sizing_block_fuel", units="kg")

        self.declare_partials(["*"], ["*"])

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        iter_count = self.iter_count_without_approx
        message_prefix = "Mission computation - iteration %i : " % iter_count
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
        propulsion_model = FuelEngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )

        high_speed_polar = self._get_initial_polar(inputs)
        distance = np.asscalar(
            np.sum(self._mission_wrapper.get_route_ranges(inputs, self.options["mission_name"]))
        )

        altitude = 100.0
        cruise_mach = 0.1

        breguet = BreguetCruiseSegment(
            FlightPoint(ground_distance=distance),
            propulsion=propulsion_model,
            polar=high_speed_polar,
            use_max_lift_drag_ratio=True,
        )
        start_point = FlightPoint(
            mass=inputs[self._mission_vars.TOW.value], altitude=altitude, mach=cruise_mach
        )
        flight_points = breguet.compute_from(start_point)
        end_point = FlightPoint.create(flight_points.iloc[-1])
        outputs[self._mission_vars.BLOCK_FUEL.value] = start_point.mass - end_point.mass

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
        propulsion_model = FuelEngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )

        reference_area = inputs["data:geometry:wing:area"]

        self._mission_wrapper.propulsion = propulsion_model
        self._mission_wrapper.reference_area = reference_area

        end_of_takeoff = FlightPoint(
            time=0.0,
            mass=inputs[self._mission_vars.TOW.value],
            true_airspeed=inputs[self._mission_vars.TAKEOFF_V2.value],
            altitude=inputs[self._mission_vars.TAKEOFF_ALTITUDE.value] + 35 * foot,
            ground_distance=0.0,
        )

        self.flight_points = self._mission_wrapper.compute(inputs, outputs, end_of_takeoff)

        # Final ================================================================
        end_of_mission = FlightPoint.create(self.flight_points.iloc[-1])
        zfw = end_of_mission.mass - self._mission_wrapper.get_reserve(
            self.flight_points, self.options["mission_name"]
        )
        outputs[self._mission_vars.BLOCK_FUEL.value] = (
            inputs[self._mission_vars.TOW.value]
            + inputs[self._mission_vars.TAKEOFF_FUEL.value]
            + inputs[self._mission_vars.TAXI_OUT_FUEL.value]
            - zfw
        )
        if self.options["is_sizing"]:
            outputs["data:weight:aircraft:sizing_block_fuel"] = outputs[
                self._mission_vars.BLOCK_FUEL.value
            ]

        def as_scalar(value):
            if isinstance(value, np.ndarray):
                return np.asscalar(value)
            return value

        self.flight_points = self.flight_points.applymap(as_scalar)
        if self.options["out_file"]:
            self.flight_points.to_csv(self.options["out_file"])

    def _get_engine_wrapper(self) -> IOMPropulsionWrapper:
        """
        Overloading this method allows to define the engine without relying on the propulsion
        option.

        (useful for tests)

        :return: the engine wrapper instance
        """
        return RegisterPropulsion.get_provider(self.options["propulsion_id"])
