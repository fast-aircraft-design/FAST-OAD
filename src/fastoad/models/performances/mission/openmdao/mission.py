"""
OpenMDAO component for time-step computation of missions.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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

import logging
from enum import Enum
from importlib.resources import path

import numpy as np
import openmdao.api as om
import pandas as pd
from scipy.constants import foot

from fastoad import BundleLoader
from fastoad.base.flight_point import FlightPoint
from fastoad.models.propulsion import IOMPropulsionWrapper
from fastoad.models.propulsion.fuel_propulsion.base import FuelEngineSet
from fastoad.utils.physics import AtmosphereSI
from . import resources
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition
from ..polar import Polar
from ...breguet import Breguet

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class Mission(om.Group):
    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)
        self.options.declare("breguet_iterations", default=1, types=int)
        self.options.declare(
            "mission_file_path", default=None, types=(str, MissionDefinition), allow_none=True
        )
        self.options.declare("compute_TOW", default=True, types=bool)
        self.options.declare("add_solver", default=True, types=bool)

    def setup(self):

        if not self.options["mission_file_path"]:
            # If no mission_file_path provided, the default mission is applied
            self.options["mission_file_path"] = "::sizing_mission"
        if "::" in self.options["mission_file_path"]:
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            i = self.options["mission_file_path"].index("::")
            file_name = self.options["mission_file_path"][i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                self.options["mission_file_path"] = MissionDefinition(mission_input_file)
        mission_wrapper = MissionWrapper(self.options["mission_file_path"])

        mission_name = mission_wrapper.mission_name

        self.set_input_defaults("data:weight:aircraft:OWE", np.nan, units="kg")
        self.set_input_defaults("data:mission:%s:payload" % mission_name, np.nan, units="kg")

        zfw_computation = om.AddSubtractComp()
        zfw_computation.add_equation(
            "data:mission:%s:ZFW" % mission_name,
            ["data:weight:aircraft:OWE", "data:mission:%s:payload" % mission_name],
            units="kg",
        )
        self.add_subsystem("ZFW_computation", zfw_computation, promotes=["*"])

        if self.options["compute_TOW"]:
            tow_computation = om.AddSubtractComp()
            tow_computation.add_equation(
                "data:mission:%s:TOW" % mission_name,
                [
                    "data:mission:%s:ZFW" % mission_name,
                    "data:mission:%s:needed_block_fuel" % mission_name,
                ],
                units="kg",
            )

            self.add_subsystem("TOW_computation", tow_computation, promotes=["*"])

            if self.options["add_solver"]:
                self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, rtol=5.0e-4)
                self.linear_solver = om.DirectSolver()

        mission_options = dict(self.options.items())
        del mission_options["compute_TOW"]
        del mission_options["add_solver"]
        del mission_options["mission_file_path"]
        mission_options["mission_wrapper"] = mission_wrapper
        self.add_subsystem(
            "mission_computation", MissionComponent(**mission_options), promotes=["*"]
        )

        block_fuel_computation = om.AddSubtractComp()
        block_fuel_computation.add_equation(
            "data:mission:%s:block_fuel" % mission_name,
            ["data:mission:%s:TOW" % mission_name, "data:mission:%s:ZFW" % mission_name,],
            units="kg",
            scaling_factors=[1, -1],
        )
        self.add_subsystem("block_fuel_computation", block_fuel_computation, promotes=["*"])

    @property
    def flight_points(self) -> pd.DataFrame:
        return self.mission_computation.flight_points


class MissionComponent(om.ExplicitComponent):
    def __init__(self, **kwargs):
        """
        Computes thrust, SFC and thrust rate by direct call to engine model.

        Options:
          - propulsion_id: (mandatory) the identifier of the propulsion wrapper.
          - out_file: if provided, a csv file will be written at provided path with all computed
                      flight points. If path is relative, it will be resolved from working
                      directory
        """
        super().__init__(**kwargs)
        self.flight_points = None
        self._engine_wrapper = None
        self._mission: MissionWrapper = None
        self._mission_vars: type = None

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)
        self.options.declare("breguet_iterations", default=2, types=int)
        self.options.declare("mission_wrapper", types=MissionWrapper)

    def setup(self):
        self._engine_wrapper = self._get_engine_wrapper()
        self._engine_wrapper.setup(self)
        self._mission = self.options["mission_wrapper"]
        self._mission.setup(self)

        mission_name = self._mission.mission_name

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

        self.declare_partials(["*"], ["*"])

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        if self.iter_count_without_approx < self.options["breguet_iterations"]:
            _LOGGER.info("Using Breguet for computing sizing mission.")
            self.compute_breguet(inputs, outputs)
        else:
            _LOGGER.info("Using time-step integration for computing sizing mission.")
            self.compute_mission(inputs, outputs)

    def compute_breguet(self, inputs, outputs):
        """
        Computes mission using simple Breguet formula at altitude==10000m

        Useful for initiating the computation.

        :param inputs: OpenMDAO input vector
        :param outputs: OpenMDAO output vector
        """
        propulsion_model = FuelEngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )
        high_speed_polar = Polar(
            inputs["data:aerodynamics:aircraft:cruise:CL"],
            inputs["data:aerodynamics:aircraft:cruise:CD"],
        )

        distance = np.sum(self._mission.get_route_ranges(inputs))
        cruise_speed_param, cruise_speed_value = self._mission.get_route_cruise_speeds(inputs)[0]
        altitude = 10000.0

        cruise_mach = 0.8  # next lines should overwrite this value
        if cruise_speed_param == "mach":
            cruise_mach = cruise_speed_value
        else:
            atm = AtmosphereSI(altitude)
            if cruise_speed_param == "true_airspeed":
                cruise_mach = cruise_speed_value / atm.speed_of_sound
            elif cruise_speed_param == "equivalent_airspeed":
                cruise_mach = atm.get_true_airspeed(cruise_speed_value) / atm.speed_of_sound

        breguet = Breguet(
            propulsion_model,
            max(
                10.0, high_speed_polar.optimal_cl / high_speed_polar.cd(high_speed_polar.optimal_cl)
            ),
            cruise_mach,
            altitude,
        )
        breguet.compute(
            inputs[self._mission_vars.TOW.value], distance,
        )

        outputs[self._mission_vars.BLOCK_FUEL.value] = breguet.mission_fuel

    def compute_mission(self, inputs, outputs):
        """
        Computes mission using time-step integration.

        :param inputs: OpenMDAO input vector
        :param outputs: OpenMDAO output vector
        """
        propulsion_model = FuelEngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )

        reference_area = inputs["data:geometry:wing:area"]

        self._mission.propulsion = propulsion_model
        self._mission.reference_area = reference_area

        end_of_takeoff = FlightPoint(
            time=0.0,
            # FIXME: legacy FAST was considering that aircraft was at MTOW before taxi out,
            #  though it supposed to be at MTOW at takeoff. We keep this logic for sake of
            #  non-regression, but it should be corrected later.
            mass=inputs[self._mission_vars.TOW.value]
            - inputs[self._mission_vars.TAKEOFF_FUEL.value]
            - inputs[self._mission_vars.TAXI_OUT_FUEL.value],
            true_airspeed=inputs[self._mission_vars.TAKEOFF_V2.value],
            altitude=inputs[self._mission_vars.TAKEOFF_ALTITUDE.value] + 35 * foot,
            ground_distance=0.0,
        )

        self.flight_points = self._mission.compute(inputs, outputs, end_of_takeoff)

        # Final ================================================================
        end_of_descent = FlightPoint.create(
            self.flight_points.loc[
                self.flight_points.name == "%s:main_route:descent" % self._mission.mission_name
            ].iloc[-1]
        )
        end_of_taxi_in = FlightPoint.create(self.flight_points.iloc[-1])

        fuel_route = inputs[self._mission_vars.TOW.value] - end_of_descent.mass
        zfw = end_of_taxi_in.mass - 0.03 * fuel_route
        outputs[self._mission_vars.BLOCK_FUEL.value] = inputs[self._mission_vars.TOW.value] - zfw

        if self.options["out_file"]:
            self.flight_points.to_csv(self.options["out_file"])

    def _get_engine_wrapper(self) -> IOMPropulsionWrapper:
        """
        Overloading this method allows to define the engine without relying on the propulsion
        option.

        (useful for tests)

        :return: the engine wrapper instance
        """
        return BundleLoader().instantiate_component(self.options["propulsion_id"])
