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
import plotly.graph_objects as go
from fastoad.io import VariableIO
from stdatm import Atmosphere

g = 9.81


def drag_distribution_plot(
    aircraft_file_path: str,
    aircraft_mass: float,
    aircraft_altitude: float = 10668,
    low_speed_aero=False,
    CL=None,
    name=None,
    file_formatter=None,
) -> go.FigureWidget:
    """
    Returns a figure plot of the drag distribution in two situations :
        - 1) in cruise at a fixed mach number
        - 2) in low speed conditions also at a fixed mach number
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param aircraft_mass : mass of the aircraft, used to calucate Cl
    :param aircraft_altitude : altitude of the aircraft, used to calculate Cl
    :param low_speed_aero : boolean which when True computes the low speed drag
    :param CL :  value of the lift coefficient. If set to None, then CL is calulated via mass and altitude
    :param name: name to give to the trace added to the figure
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: sun distribution of the drag
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    # step 1 : Cl calculation :
    wing_area = variables["data:geometry:wing:area"].value[0]
    if not low_speed_aero:
        mach = variables["data:TLAR:cruise_mach"].value[0]
        case_string = "cruise"

    else:
        mach = variables["data:aerodynamics:aircraft:takeoff:mach"].value[0]
        case_string = "low_speed"

    if CL is None:  # CL via mass and altitude
        rho = Atmosphere(aircraft_altitude * 3.2744).density
        T = Atmosphere(aircraft_altitude * 3.2744).temperature
        CL = aircraft_mass * g / (0.5 * rho * mach ** 2 * 1.4 * 287.1 * T * wing_area)

    # step 2 : compute induced drag
    k_induced = variables[
        "data:aerodynamics:aircraft:" + case_string + ":induced_drag_coefficient"
    ].value[0]

    CDi_wing = k_induced * CL ** 2

    CL_table = np.asarray(variables["data:aerodynamics:aircraft:" + case_string + ":CL"].value)

    if CL > CL_table[-1]:
        print(
            CL,
            " > ",
            CL_table[-1],
            " CL bigger than CL_table, might be a problem for the precision",
        )
    CD_table = np.asarray(variables["data:aerodynamics:aircraft:" + case_string + ":CD"].value)
    CD_trim_table = np.asarray(
        variables["data:aerodynamics:aircraft:" + case_string + ":CD:trim"].value
    )

    CD_trim = np.interp(CL, CL_table, CD_trim_table)  # drag due to the horizontal surface

    # step 3 : retrieve the parasitic drag CDp
    CD0_fuselage_table = np.asarray(
        variables["data:aerodynamics:fuselage:" + case_string + ":CD0"].value
    )  # depend on CL
    CD0_fuselage = np.interp(CL, CL_table, CD0_fuselage_table)

    CD0_ht = variables["data:aerodynamics:horizontal_tail:" + case_string + ":CD0"].value[0]
    CD0_nacelles = variables["data:aerodynamics:nacelles:" + case_string + ":CD0"].value[0]
    CD0_pylons = variables["data:aerodynamics:pylons:" + case_string + ":CD0"].value[0]
    CD0_vt = variables["data:aerodynamics:vertical_tail:" + case_string + ":CD0"].value[0]

    CD0_wing_table = np.asarray(
        variables["data:aerodynamics:wing:" + case_string + ":CD0"].value
    )  # depend on cl
    CD0_wing = np.interp(CL, CL_table, CD0_wing_table)

    CD0 = CD0_fuselage + CD0_ht + CD0_nacelles + CD0_pylons + CD0_vt + CD0_wing

    # step 4 : retrieve drag from compressibility effects and triming of the aircraft

    CDc_wing = 0

    if not low_speed_aero:
        CDc_table = np.asarray(
            variables["data:aerodynamics:aircraft:cruise:CD:compressibility"].value
        )
        CDc_wing = np.interp(CL, CL_table, CDc_table)

    CD = CDi_wing + CD0 + CDc_wing + CD_trim

    # error calculation
    CD_estimate = np.interp(CL, CL_table, CD_table)
    # print("Error calculation : ")
    # print("CD from table", CD_estimate)
    # print("CD calculated", CD)
    # print("Error: ", CD_estimate - CD)
    # print("Error percentage : ", (CD_estimate - CD) / CD * 100, "%")

    labels = [
        "CD" + "<br>" + str("% 12.3f" % CD),
        "CDi"
        + "<br>"
        + str("% 12.3f" % CDi_wing)
        + " ("
        + str(np.round(CDi_wing / CD * 100, 1))
        + " %)",
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
        "CD_trim"
        + "<br>"
        + str("% 12.3f" % CD_trim)
        + " ("
        + str(np.round(CD_trim / CD * 100, 1))
        + " %)",
        "fuselage" + "<br>" + str("% 12.3f" % CD0_fuselage),
        "vertical tail" + "<br>" + str("% 12.3f" % CD0_vt),
        "horizontal tail" + "<br>" + str("% 12.3f" % CD0_ht),
        "wing" + "<br>" + str("% 12.3f" % CD0_wing),
        "nacelles" + "<br>" + str("% 12.3f" % CD0_nacelles),
        "pylons" + "<br>" + str("% 12.3f" % CD0_pylons),
    ]

    parents = [
        "",
        "CD" + "<br>" + str("% 12.3f" % CD),
        "CD" + "<br>" + str("% 12.3f" % CD),
        "CD" + "<br>" + str("% 12.3f" % CD),
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
        "CDp" + "<br>" + str("% 12.3f" % CD0) + " (" + str(np.round(CD0 / CD * 100, 1)) + " %)",
    ]
    values = [
        CD,
        CDi_wing,
        CD0,
        CD_trim,
        CD0_fuselage,
        CD0_vt,
        CD0_ht,
        CD0_wing,
        CD0_nacelles,
        CD0_pylons,
    ]
    if not low_speed_aero:
        labels.append(
            "CDc"
            + "<br>"
            + str("% 12.3f" % CDc_wing)
            + " ("
            + str(np.round(CDc_wing / CD * 100, 1))
            + " %)"
        )
        parents.append("CD" + "<br>" + str("% 12.3f" % CD))
        values.append(CDc_wing)

    sunburst = go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total")
    fig = go.FigureWidget()
    fig.add_trace(sunburst)

    fig.update_layout(
        title_text="Drag coefficient distribution at a mach of " + str(mach) + " : " + str(name),
        title_x=0.5,
        xaxis_title="y",
        yaxis_title="x",
        margin=dict(t=30, l=0, r=0, b=0),
    )

    return fig
