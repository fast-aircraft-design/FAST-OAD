"""
Defines the analysis and plotting functions for postprocessing
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fastoad.io.xml import OMXmlIO


def wing_geometry_plot_matplotlib(aircraft_xml: OMXmlIO):
    system = aircraft_xml.read_variables()

    wing_x4 = system['geometry:wing_x4'].value[0]
    wing_y2 = system['geometry:wing_y2'].value[0]
    wing_y3 = system['geometry:wing_y3'].value[0]
    wing_y4 = system['geometry:wing_y4'].value[0]
    wing_l2 = system['geometry:wing_l2'].value[0]
    wing_l4 = system['geometry:wing_l4'].value[0]

    x = [0, wing_y2, wing_y4,
         wing_y4, wing_y3,
         wing_y2, 0, 0]
    y = [0, 0, wing_x4, wing_x4 + wing_l4,
         wing_l2, wing_l2, wing_l2, 0]

    plt.figure(1, figsize=(8, 5))
    plt.plot(x, y)
    plt.title('Wing geometry')
    plt.axis([0, 18, 0, 11])
    plt.show()


def wing_geometry_plot(aircraft_xml: OMXmlIO):
    system = aircraft_xml.read_variables()

    wing_x4 = system['geometry:wing:tip:leading_edge:x'].value[0]
    wing_y2 = system['geometry:wing:root:y'].value[0]
    wing_y3 = system['geometry:wing:kink:y'].value[0]
    wing_y4 = system['geometry:wing:tip:y'].value[0]
    wing_l2 = system['geometry:wing:root:chord'].value[0]
    wing_l4 = system['geometry:wing:tip:chord'].value[0]

    x = [0, wing_y2, wing_y4,
         wing_y4, wing_y3,
         wing_y2, 0, 0]
    y = [0, 0, wing_x4, wing_x4 + wing_l4,
         wing_l2, wing_l2, wing_l2, 0]

    scatter = go.Scatter(x=x, y=y,
                         mode='lines+markers')

    layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    data = [scatter]
    fig = go.FigureWidget(data=data, layout=layout)
    fig.layout.title = 'Wing Geometry'
    return fig


def wing_geometry_symetric_plot(aircraft_xml: OMXmlIO):
    system = aircraft_xml.read_variables()

    wing_x4 = system['geometry:wing:tip:leading_edge:x'].value[0]
    wing_y2 = system['geometry:wing:root:y'].value[0]
    wing_y3 = system['geometry:wing:kink:y'].value[0]
    wing_y4 = system['geometry:wing:tip:y'].value[0]
    wing_l2 = system['geometry:wing:root:chord'].value[0]
    wing_l4 = system['geometry:wing:tip:chord'].value[0]

    x = [0, wing_y2, wing_y4,
         wing_y4, wing_y3,
         wing_y2, 0, 0]

    x = [-x_i for x_i in x] + x
    y = [0, 0, wing_x4, wing_x4 + wing_l4,
         wing_l2, wing_l2, wing_l2, 0]

    y = y + y

    scatter = go.Scatter(x=x, y=y,
                         mode='lines+markers')

    layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    data = [scatter]
    fig = go.FigureWidget(data=data, layout=layout)
    fig.layout.title = 'Wing Geometry'
    return fig


def mass_breakdown(aircraft_xml: OMXmlIO):
    system = aircraft_xml.read_variables()

    systems = system['weight_systems:C'].value[0]
    C11 = system['weight_systems:C11'].value[0]
    C12 = system['weight_systems:C12'].value[0]
    C13 = system['weight_systems:C13'].value[0]
    C21 = system['weight_systems:C21'].value[0]
    C22 = system['weight_systems:C22'].value[0]
    C23 = system['weight_systems:C23'].value[0]
    C24 = system['weight_systems:C24'].value[0]
    C25 = system['weight_systems:C25'].value[0]
    C26 = system['weight_systems:C26'].value[0]
    C27 = system['weight_systems:C27'].value[0]
    C3 = system['weight_systems:C3'].value[0]
    C4 = system['weight_systems:C4'].value[0]
    C51 = system['weight_systems:C51'].value[0]
    C52 = system['weight_systems:C52'].value[0]
    C6 = system['weight_systems:C6'].value[0]

    furniture = system['weight_furniture:D'].value[0]
    D1 = system['weight_furniture:D1'].value[0]
    D2 = system['weight_furniture:D2'].value[0]
    D3 = system['weight_furniture:D3'].value[0]
    D4 = system['weight_furniture:D4'].value[0]
    D5 = system['weight_furniture:D5'].value[0]

    crew = system['weight_crew:E'].value[0]

    airframe = system['weight_airframe:A'].value[0]
    wing = system['weight_airframe:A1'].value[0]
    fuselage = system['weight_airframe:A2'].value[0]
    h_tail = system['weight_airframe:A31'].value[0]
    v_tail = system['weight_airframe:A32'].value[0]
    control_surface = system['weight_airframe:A4'].value[0]
    landing_gear_1 = system['weight_airframe:A51'].value[0]
    landing_gear_2 = system['weight_airframe:A52'].value[0]
    engine_pylon = system['weight_airframe:A6'].value[0]
    paint = system['weight_airframe:A7'].value[0]

    propulsion = system['weight_propulsion:B'].value[0]
    B1 = system['weight_propulsion:B1'].value[0]
    B2 = system['weight_propulsion:B2'].value[0]
    B3 = system['weight_propulsion:B3'].value[0]

    MTOW = system['weight:MTOW'].value[0]
    MZFW = system['weight:MZFW'].value[0]
    MFW = system['weight:MFW'].value[0]
    OEW = system['weight:OEW'].value[0]
    max_payload = system['weight:Max_PL'].value[0]

    # TODO: Deal with when mass loop is not solved
    MTOW = MZFW + MFW

    fig = make_subplots(1, 2, specs=[[{"type": "domain"}, {"type": "domain"}]], )

    fig.add_trace(go.Sunburst(
        labels=["MTOW", "MFW", "MZFW", "max_payload", "OEW"],
        parents=["", "MTOW", "MTOW", "MZFW", "MZFW"],
        values=[MTOW, MFW, MZFW, max_payload, OEW],
        branchvalues='total',
    ), 1, 1)

    fig.add_trace(go.Sunburst(
        labels=["OEW", "airframe", "propulsion", "systems", "furniture", "crew",
                "wing", "fuselage", "h_tail", "v_tail", "control_surface",
                "landing_gear_1", "landing_gear_2", "engine_pylon", "paint",
                "B1", "B2", "B3",
                "C11", "C12", "C13", "C21", "C22", "C23", "C24", "C25", "C26", "C27",
                "C3", "C4", "C51", "C52", "C6",
                "D1", "D2", "D3", "D4", "D5",
                ],
        parents=["", "OEW", "OEW", "OEW", "OEW", "OEW",
                 "airframe", "airframe", "airframe", "airframe", "airframe", "airframe",
                 "airframe", "airframe", "airframe",
                 "propulsion", "propulsion", "propulsion",
                 "systems", "systems", "systems", "systems", "systems", "systems",
                 "systems", "systems", "systems", "systems", "systems", "systems",
                 "systems", "systems", "systems",
                 "furniture", "furniture", "furniture", "furniture", "furniture",
                 ],
        values=[OEW, airframe, propulsion, systems, furniture, crew,
                wing, fuselage, h_tail, v_tail, control_surface,
                landing_gear_1, landing_gear_2, engine_pylon, paint,
                B1, B2, B3,
                C11, C12, C13, C21, C22, C23, C24, C25, C26, C27,
                C3, C4, C51, C52, C6,
                D1, D2, D3, D4, D5,
                ],
        branchvalues='total',
    ), 1, 2)

    fig.update_layout(margin=dict(t=10, b=10, r=10, l=10))

    fig.layout.title = 'Mass Breakdown'

    return fig
