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

# %%
"""
<div class="row">
  <div class="column">
    <img src="../../img/logo-onera.png" width="200">
  </div>
  <div class="column">
    <img src="../../img/logo-ISAE_SUPAERO.png" width="200">
  </div>
</div>
"""

# %%
import logging
import os.path as pth
from os import mkdir
from shutil import rmtree

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.constants import foot
from scipy.constants import nautical_mile

from fastoad import api
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.io import VariableIO
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import RubberEngine
from fastoad.utils.postprocessing.analysis_and_plots import (
    mass_breakdown_sun_plot,
    wing_geometry_plot,
)

# %%

engine = RubberEngine(
    bypass_ratio=4.5,
    overall_pressure_ratio=35.2,
    turbine_inlet_temperature=1600,
    mto_thrust=140550,
    maximum_mach=0.85,
    design_altitude=10058.4,
    delta_t4_climb=-50.0,
    delta_t4_cruise=-100.0,
)

thrust = np.linspace(10.0e3, 32.0e3, 20)

bucket_points = pd.DataFrame(
    [
        FlightPoint(
            altitude=35000 * foot,
            mach=0.78,
            thrust=thrust,
            thrust_rate=0.0,
            thrust_is_regulated=True,
            engine_setting=EngineSetting.convert("CRUISE"),
        )
        for thrust in np.linspace(10.0e3, 32.0e3, 20)
    ]
)


engine.compute_flight_points(bucket_points)

fig = px.line(bucket_points, x="thrust", y="sfc", width=800, height=350)
fig.update_xaxes(title_text="Thrust per engine [N]", range=[5000, 35000])
fig.update_yaxes(title_text="SFC [kg/s/N]", range=[1.4e-5, 2.0e-5])
fig.update_layout(margin=dict(l=265, r=145, t=20, b=20),)
fig.show()

# %%

mission_name = "R7408_PL18000"

A321LR_INPUT_FILE = pth.join(pth.pardir, pth.pardir, "reference_data.xml")

WORK_FOLDER_PATH = mission_name
OAD_SIZING_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "oad_sizing.toml")

OUTPUT_FOLDER_PATH = pth.join(WORK_FOLDER_PATH, "outputs")
rmtree(OUTPUT_FOLDER_PATH, ignore_errors=True)
mkdir(OUTPUT_FOLDER_PATH)
OAD_SIZING_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "oad_sizing.csv")

# %%
input_file = api.generate_inputs(OAD_SIZING_CONFIGURATION_FILE, A321LR_INPUT_FILE, overwrite=True)
api.variable_viewer(input_file, editable=False)

# %%
