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

import numpy as np
import openmdao.api as om
from importlib_resources import path
from scipy.constants import foot

from fastoad import BundleLoader
from fastoad.base.flight_point import FlightPoint
from fastoad.models.propulsion.fuel_propulsion.base import FuelEngineSet
from . import resources
from .mission_files.mission import Mission
from .mission_files.schema import MissionDefinition


class SizingFlight(om.ExplicitComponent):
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
        self._mission_input = None
        self._mission: Mission = None

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)

        self.options.declare("mission_file_path", types=str, allow_none=True, default=None)

    def setup(self):
        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)
        self._mission_input = self.options["mission_file_path"]
        if not self._mission_input:
            with path(resources, "sizing_mission.yml") as mission_input_file:
                self._mission_input = MissionDefinition(mission_input_file)
        self._mission = Mission(self._mission_input)
        self._mission.setup(self)

        self.add_input("data:geometry:propulsion:engine:count", 2)
        self.add_input("data:geometry:wing:area", np.nan, units="m**2")
        self.add_input("data:weight:aircraft:MTOW", np.nan, units="kg")
        self.add_input("data:mission:sizing:taxi_out:fuel", np.nan, units="kg")
        self.add_input("data:mission:sizing:takeoff:altitude", np.nan, units="m")
        self.add_input("data:mission:sizing:takeoff:fuel", np.nan, units="kg")
        self.add_input("data:mission:sizing:takeoff:V2", np.nan, units="m/s")

        self.add_output("data:mission:sizing:ZFW", units="kg")

        self.declare_partials(["*"], ["*"])

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
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
            mass=inputs["data:weight:aircraft:MTOW"]
            - inputs["data:mission:sizing:takeoff:fuel"]
            - inputs["data:mission:sizing:taxi_out:fuel"],
            true_airspeed=inputs["data:mission:sizing:takeoff:V2"],
            altitude=inputs["data:mission:sizing:takeoff:altitude"] + 35 * foot,
            ground_distance=0.0,
        )

        self.flight_points = self._mission.compute(inputs, outputs, end_of_takeoff)

        # Final ================================================================
        end_of_descent = FlightPoint(
            self.flight_points.loc[self.flight_points.name == "sizing:main_route:descent"].iloc[-1]
        )
        end_of_taxi_in = FlightPoint(self.flight_points.iloc[-1])

        fuel_route = inputs["data:weight:aircraft:MTOW"] - end_of_descent.mass
        outputs["data:mission:sizing:ZFW"] = end_of_taxi_in.mass - 0.03 * fuel_route
        outputs["data:mission:sizing:fuel"] = (
            inputs["data:weight:aircraft:MTOW"] - outputs["data:mission:sizing:ZFW"]
        )

        if self.options["out_file"]:
            self.flight_points.to_csv(self.options["out_file"])
