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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.constants import foot

from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import RubberEngine

engine = RubberEngine(
    bypass_ratio=4.9,
    overall_pressure_ratio=32.6,
    turbine_inlet_temperature=1600,
    mto_thrust=117880,
    maximum_mach=0.85,
    design_altitude=10058.4,
    delta_t4_climb=0.0,
    delta_t4_cruise=0.0,
)

thrust = np.linspace(10.0e3, 32.0e3, 20)

flight_points = pd.DataFrame(
    FlightPoint(
        altitude=35000 * foot,
        mach=0.78,
        thrust=thrust,
        thrust_rate=0.0,
        thrust_is_regulated=True,
        engine_setting=EngineSetting.convert("CRUISE"),
    )
)

engine.compute_flight_points(flight_points)
print(flight_points)
plt.plot
