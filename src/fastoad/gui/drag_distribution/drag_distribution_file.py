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

from typing import Dict

import numpy as np

import plotly
import plotly.graph_objects as go
from fastoad.io import VariableIO
from fastoad.model_base import FlightPoint
import os.path as pth
from stdatm import Atmosphere

g = 9.81


def drag_distribution_plot(
        aircraft_file_path: str,
        aircraft_mass: float,
        aircraft_mach: float,
        aircraft_altitude: float,
        name=None,
        fig=None,
        file_formatter=None,
        low_speed_aero=False,
) -> go.FigureWidget:
    """
    Returns a figure plot of the drag distribution at a certain flight point
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: sun distribution of the drag
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    # step 1 : Cl calculation :
    wing_area = variables["data:geometry:wing:area"].value[0]
    rho = Atmosphere(aircraft_altitude * 3.2744).density
    T = Atmosphere(aircraft_altitude * 3.2744).temperature
    CL = aircraft_mass * g / (0.5 * rho * aircraft_mach ** 2 * 1.4 * 287.1 * T * wing_area)

    # step 2 : compute induced drag
    k_induced = variables["data:aerodynamics:aircraft:cruise:induced_drag_coefficient"].value[0]
    CDi_wing = k_induced * CL ** 2

    # step 3 : retrieve the parasitic drag CDp
    CDp_fuselage = variables["data:aerodynamics:fuselage:cruise:CD0"].value[0]
    CDp_ht = variables["data:aerodynamics:horizontal_tail:cruise:CD0"].value[0]
    CDp_nacelles = variables["data:aerodynamics:nacelles:cruise:CD0"].value[0]
    CDp_pylons = variables["data:aerodynamics:pylons:cruise:CD0"].value[0]
    CDp_vt = variables["data:aerodynamics:vertical_tail:cruise:CD0"].value[0]
    CDp_wing = variables["data:aerodynamics:wing:cruise:CD0"].value[0]


    CDp = CDp_fuselage + CDp_ht + CDp_nacelles + CDp_pylons + CDp_vt + CDp_wing

    #step 4 : retriev drag from compressibility effects and triming of the aircraft
    CL_table =  np.asarray(variables["data:aerodynamics:aircraft:cruise:CL"].value)
    CD_table =   np.asarray(variables["data:aerodynamics:aircraft:cruise:CD"].value)
    CD0_table = np.asarray(variables["data:aerodynamics:aircraft:cruise:CD0"].value)
    CD_compressibility = np.asarray(variables["data:aerodynamics:aircraft:cruise:CD:compressibility"].value)
    CD_table_trim =  np.asarray(variables["data:aerodynamics:aircraft:cruise:CD:trim"].value)
    CDc_wing = np.interp(CL,CL_table,CD_compressibility)
    CD_trim = np.interp(CL,CL_table,CD_table_trim)




    CD = CDi_wing + CDp+ CDc_wing + CD_trim
    CDp_estimate = np.interp(CL,CL_table,CD0_table)
    print("CDp_estimate",CDp_estimate)
    print("CDp",CDp)
    print("error: ",CDp-CDp_estimate)

    CD_estimate = np.interp(CL,CL_table,CD_table)
    print("CD_estimate",CD_estimate)
    print("CD",CD)
    print("error: ",CD-CD_estimate)





    if fig is None:
        fig = go.Figure()

    sunburst = go.Sunburst(
        labels=[
            "CD" + "<br>" + str('% 12.3f'%CD),

            "CDi" + "<br>" + str('% 12.3f' % CDi_wing) + " (" + str(np.round(CDi_wing/CD*100,1)) + " %)",
            "CDp" + "<br>" + str('% 12.3f'%CDp) + " (" + str(np.round(CDp/CD*100,1)) + " %)",
            "CDc" + "<br>" + str('% 12.3f'%CDc_wing) + " (" + str(np.round(CDc_wing/CD*100,1)) + " %)",
            "CD_trim" + "<br>" + str('% 12.3f'%CD_trim)+ " (" + str(np.round(CD_trim/CD*100,1)) + " %)",

            "fuselage" + "<br>" + str('% 12.3f'%CDp_fuselage),
            "vertical tail" + "<br>" + str('% 12.3f'%CDp_vt),
            "horizontal tail" + "<br>" + str('% 12.3f' % CDp_ht),
            "wing" + "<br>" + str('% 12.3f'%CDp_wing),
            "nacelles"+ "<br>" + str('% 12.3f'%CDp_nacelles),
            "nacelles" + "<br>" + str('% 12.3f' % CDp_pylons),
        ],
        parents=[
            "",

            "CD" + "<br>" + str('% 12.3f'%CD),
            "CD" + "<br>" + str('% 12.3f'%CD),
            "CD" + "<br>" + str('% 12.3f' % CD),
            "CD" + "<br>" + str('% 12.3f' % CD),

            "CDp" + "<br>" + str('% 12.3f' % CDp) + " (" + str(np.round(CDp / CD * 100, 1)) + " %)",
            "CDp" + "<br>" + str('% 12.3f' % CDp) + " (" + str(np.round(CDp / CD * 100, 1)) + " %)",
            "CDp" + "<br>" + str('% 12.3f' % CDp) + " (" + str(np.round(CDp / CD * 100, 1)) + " %)",
            "CDp" + "<br>" + str('% 12.3f' % CDp) + " (" + str(np.round(CDp / CD * 100, 1)) + " %)",
            "CDp" + "<br>" + str('% 12.3f' % CDp) + " (" + str(np.round(CDp / CD * 100, 1)) + " %)",
            "CDp" + "<br>" + str('% 12.3f' % CDp) + " (" + str(np.round(CDp / CD * 100, 1)) + " %)",
        ],
        values=[CD, CDi_wing, CDp,CDc_wing, CD_trim, CDp_fuselage,CDp_vt,CDp_ht,CDp_wing,CDp_nacelles,CDp_pylons],
        branchvalues="total"
    )


    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig.add_trace(sunburst)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text="Drag coefficient distribution", title_x=0.5, xaxis_title="y", yaxis_title="x"
    )

    return fig
