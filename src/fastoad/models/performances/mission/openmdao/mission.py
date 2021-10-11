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
from collections import namedtuple
from importlib.resources import path

import numpy as np
import openmdao.api as om
import pandas as pd
from scipy.constants import foot

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet, IOMPropulsionWrapper
from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterPropulsion
from . import resources
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition
from ..polar import Polar
from ..segments.cruise import BreguetCruiseSegment
from ..segments.taxi import TaxiSegment

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
            desc="If True, block fuel will fit fuel consumption during mission.\n"
            "If False, block fuel will be taken from input data.",
        )
        self.options.declare(
            "compute_TOW",
            default=False,
            types=bool,
            desc="If True, TakeOff Weight will be computed from mission block fuel and ZFW.\n"
            "If False, block fuel will be computed from TOW and ZFW.\n"
            "Not used (actually forced to True) if adjust_fuel is True.",
        )
        self.options.declare(
            "add_solver",
            default=False,
            types=bool,
            desc="Not used if compute_TOW is False.\n"
            "Otherwise, setting this option to False will deactivate the local solver.\n"
            "Useful if a global solver is used.",
        )
        self.options.declare(
            "is_sizing",
            default=False,
            types=bool,
            desc="If True, TOW will be considered equal to MTOW and mission payload will be "
            "considered equal to design payload.",
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
        mission_wrapper = MissionWrapper(self.options["mission_file_path"])
        if self.options["mission_name"] is None:
            self.options["mission_name"] = mission_wrapper.get_unique_mission_name()

        mission_name = self.options["mission_name"]

        self.add_subsystem("ZFW_computation", self._get_zfw_component(mission_name), promotes=["*"])

        if self.options["adjust_fuel"]:
            self.options["compute_TOW"] = True
            self.connect(
                "data:mission:%s:needed_onboard_fuel_at_takeoff" % mission_name,
                "data:mission:%s:onboard_fuel_at_takeoff" % mission_name,
            )
            if self.options["add_solver"]:
                self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, rtol=1.0e-4, iprint=0)
                self.linear_solver = om.DirectSolver()

        if self.options["compute_TOW"]:
            self.add_subsystem(
                "TOW_computation", self._get_tow_component(mission_name), promotes=["*"]
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
            payload_var = "data:mission:%s:payload" % mission_name

        zfw_computation = om.AddSubtractComp()
        zfw_computation.add_equation(
            "data:mission:%s:ZFW" % mission_name,
            ["data:weight:aircraft:OWE", payload_var],
            units="kg",
            desc='Zero Fuel Weight for mission "%s"' % mission_name,
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
            "data:mission:%s:TOW" % mission_name,
            [
                "data:mission:%s:ZFW" % mission_name,
                "data:mission:%s:onboard_fuel_at_takeoff" % mission_name,
            ],
            units="kg",
            desc='TakeOff Weight for mission "%s"' % mission_name,
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
            [
                "data:mission:%s:TOW" % mission_name,
                "data:mission:%s:taxi_out:fuel" % mission_name,
                "data:mission:%s:takeoff:fuel" % mission_name,
                "data:mission:%s:ZFW" % mission_name,
            ],
            units="kg",
            scaling_factors=[1, 1, 1, -1],
            desc='Loaded fuel before taxi-out for mission "%s"' % mission_name,
        )
        return block_fuel_computation


_MissionVariables = namedtuple(
    "_MissionVariables",
    [
        "TOW",
        "NEEDED_BLOCK_FUEL",
        "NEEDED_FUEL_AT_TAKEOFF",
        "TAXI_OUT_DURATION",
        "TAXI_OUT_THRUST_RATE",
        "TAXI_OUT_DISTANCE",
        "TAXI_OUT_FUEL",
        "TAKEOFF_FUEL",
        "TAKEOFF_ALTITUDE",
        "TAKEOFF_V2",
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

    def setup(self):
        self._engine_wrapper = self._get_engine_wrapper()
        self._engine_wrapper.setup(self)
        self._mission_wrapper = self.options["mission_wrapper"]
        self._mission_wrapper.setup(self, self.options["mission_name"])

        mission_name = self.options["mission_name"]

        self._mission_vars = _MissionVariables(
            TOW="data:mission:%s:TOW" % mission_name,
            NEEDED_BLOCK_FUEL="data:mission:%s:needed_block_fuel" % mission_name,
            NEEDED_FUEL_AT_TAKEOFF="data:mission:%s:needed_onboard_fuel_at_takeoff" % mission_name,
            TAXI_OUT_DURATION="data:mission:%s:taxi_out:duration" % mission_name,
            TAXI_OUT_THRUST_RATE="data:mission:%s:taxi_out:thrust_rate" % mission_name,
            TAXI_OUT_DISTANCE="data:mission:%s:taxi_out:distance" % mission_name,
            TAXI_OUT_FUEL="data:mission:%s:taxi_out:fuel" % mission_name,
            TAKEOFF_FUEL="data:mission:%s:takeoff:fuel" % mission_name,
            TAKEOFF_ALTITUDE="data:mission:%s:takeoff:altitude" % mission_name,
            TAKEOFF_V2="data:mission:%s:takeoff:V2" % mission_name,
        )

        self.add_input("data:geometry:propulsion:engine:count", 2)
        self.add_input("data:geometry:wing:area", np.nan, units="m**2")
        self.add_input(
            self._mission_vars.TOW,
            np.nan,
            units="kg",
            desc='TakeOff Weight for mission "%s"' % mission_name,
        )
        self.add_input(
            self._mission_vars.TAXI_OUT_DURATION,
            np.nan,
            units="s",
            desc='duration of taxi-out in mission "%s"' % mission_name,
        )
        self.add_input(
            self._mission_vars.TAXI_OUT_THRUST_RATE,
            np.nan,
            units=None,
            desc='thrust rate during taxi-out in mission "%s"' % mission_name,
        )
        self.add_input(
            self._mission_vars.TAKEOFF_ALTITUDE,
            np.nan,
            units="m",
            desc='altitude of airport for mission "%s"' % mission_name,
        )
        self.add_input(
            self._mission_vars.TAKEOFF_FUEL,
            np.nan,
            units="kg",
            desc='burned fuel during takeoff phase of mission "%s"' % mission_name,
        )
        self.add_input(
            self._mission_vars.TAKEOFF_V2,
            np.nan,
            units="m/s",
            desc='takeoff safety speed for mission "%s"' % mission_name,
        )
        self.add_output(
            self._mission_vars.TAXI_OUT_DISTANCE,
            units="m",
            desc='distance during taxi-out of mission "%s"' % mission_name,
        )
        self.add_output(
            self._mission_vars.TAXI_OUT_FUEL,
            units="kg",
            desc='burned fuel during taxi-out of mission "%s"' % mission_name,
        )
        self.add_output(
            self._mission_vars.NEEDED_BLOCK_FUEL,
            units="kg",
            desc='Needed fuel to complete mission "%s", including reserve fuel' % mission_name,
        )
        self.add_output(
            self._mission_vars.NEEDED_FUEL_AT_TAKEOFF,
            units="kg",
            desc='fuel quantity at instant of takeoff of mission "%s"' % mission_name,
        )

        if self.options["is_sizing"]:
            self.add_output("data:weight:aircraft:sizing_block_fuel", units="kg")
            self.add_output("data:weight:aircraft:sizing_onboard_fuel_at_takeoff", units="kg")

    def setup_partials(self):
        self.declare_partials(["*"], ["*"], method="fd")

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
        propulsion_model = FuelEngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )

        reference_area = inputs["data:geometry:wing:area"]

        self._mission_wrapper.propulsion = propulsion_model
        self._mission_wrapper.reference_area = reference_area

        self._compute_taxi_out(inputs, outputs, propulsion_model)
        end_of_takeoff = FlightPoint(
            time=0.0,
            mass=inputs[self._mission_vars.TOW],
            true_airspeed=inputs[self._mission_vars.TAKEOFF_V2],
            altitude=inputs[self._mission_vars.TAKEOFF_ALTITUDE] + 35 * foot,
            ground_distance=0.0,
        )

        self.flight_points = self._mission_wrapper.compute(inputs, outputs, end_of_takeoff)

        # Final ================================================================
        end_of_mission = FlightPoint.create(self.flight_points.iloc[-1])
        reserve = self._mission_wrapper.get_reserve(
            self.flight_points, self.options["mission_name"]
        )
        zfw = end_of_mission.mass - reserve
        reserve_name = self._mission_wrapper.get_reserve_variable_name()
        if reserve_name in outputs:
            outputs[reserve_name] = reserve
        outputs[self._mission_vars.NEEDED_BLOCK_FUEL] = (
            inputs[self._mission_vars.TOW]
            + inputs[self._mission_vars.TAKEOFF_FUEL]
            + outputs[self._mission_vars.TAXI_OUT_FUEL]
            - zfw
        )
        outputs[self._mission_vars.NEEDED_FUEL_AT_TAKEOFF] = (
            outputs[self._mission_vars.NEEDED_BLOCK_FUEL]
            - inputs[self._mission_vars.TAKEOFF_FUEL]
            - outputs[self._mission_vars.TAXI_OUT_FUEL]
        )
        if self.options["is_sizing"]:
            outputs["data:weight:aircraft:sizing_block_fuel"] = outputs[
                self._mission_vars.NEEDED_BLOCK_FUEL
            ]
            outputs["data:weight:aircraft:sizing_onboard_fuel_at_takeoff"] = outputs[
                self._mission_vars.NEEDED_FUEL_AT_TAKEOFF
            ]

        def as_scalar(value):
            if isinstance(value, np.ndarray):
                return np.asscalar(value)
            return value

        self.flight_points = self.flight_points.applymap(as_scalar)
        rename_dict = {
            field_name: "%s [%s]" % (field_name, unit)
            for field_name, unit in FlightPoint.get_units().items()
        }
        self.flight_points.rename(columns=rename_dict, inplace=True)

        if self.options["out_file"]:
            self.flight_points.to_csv(self.options["out_file"])

    def _compute_taxi_out(self, inputs, outputs, propulsion_model):
        """
        Computes the taxi-out segment.
        """
        start_of_taxi_out = FlightPoint(
            altitude=inputs[self._mission_vars.TAKEOFF_ALTITUDE],
            true_airspeed=0.0,
            # start mass is irrelevant here as long it does not get negative during computation.
            mass=inputs[self._mission_vars.TOW],
        )
        taxi_segment = TaxiSegment(
            target=FlightPoint(time=inputs[self._mission_vars.TAXI_OUT_DURATION]),
            thrust_rate=inputs[self._mission_vars.TAXI_OUT_THRUST_RATE],
            propulsion=propulsion_model,
        )
        flight_points = taxi_segment.compute_from(start_of_taxi_out)
        end_of_taxi_out = flight_points.iloc[-1]
        outputs[self._mission_vars.TAXI_OUT_DISTANCE] = (
            end_of_taxi_out.ground_distance - start_of_taxi_out.ground_distance
        )
        outputs[self._mission_vars.TAXI_OUT_FUEL] = start_of_taxi_out.mass - end_of_taxi_out.mass

    def _get_engine_wrapper(self) -> IOMPropulsionWrapper:
        """
        Overloading this method allows to define the engine without relying on the propulsion
        option.

        (useful for tests)

        :return: the engine wrapper instance
        """
        return RegisterPropulsion.get_provider(self.options["propulsion_id"])
