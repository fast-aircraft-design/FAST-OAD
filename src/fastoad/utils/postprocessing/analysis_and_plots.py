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
    variables = aircraft_xml.read_variables()
    # TODO: as it has been done before, read_variables could directly return a dictionary but:
    #   - its docstring and return type should be updated accordingly
    #   - the present module should be properly unit-tested to make easily visible if a change in
    #     read_variables() break something
    #   - a better structure should be found than a dict where keys are also a property of
    #     the item values (same information twice, not DRY)
    system = {var.name: var for var in variables}

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

    plt.figure(1, figsize=(8, 5))
    plt.plot(x, y)
    plt.title('Wing geometry')
    plt.axis([0, 18, 0, 11])
    plt.show()


def wing_geometry_plot(aircraft_xml: OMXmlIO):
    variables = aircraft_xml.read_variables()
    system = {var.name: var for var in variables}

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
    variables = aircraft_xml.read_variables()
    system = {var.name: var for var in variables}

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
    variables = aircraft_xml.read_variables()
    system = {var.name: var for var in variables}

    systems = system['weight:systems:mass'].value[0]
    C11 = system['weight:systems:power:auxiliary_power_unit:mass'].value[0]
    C12 = system['weight:systems:power:electric_systems:mass'].value[0]
    C13 = system['weight:systems:power:hydraulic_systems:mass'].value[0]
    C21 = system['weight:systems:life_support:insulation:mass'].value[0]
    C22 = system['weight:systems:life_support:air_conditioning:mass'].value[0]
    C23 = system['weight:systems:life_support:de-icing:mass'].value[0]
    C24 = system['weight:systems:life_support:cabin_lighting:mass'].value[0]
    C25 = system['weight:systems:life_support:seats_crew_accommodation:mass'].value[0]
    C26 = system['weight:systems:life_support:oxygen:mass'].value[0]
    C27 = system['weight:systems:life_support:safety_equipment:mass'].value[0]
    C3 = system['weight:systems:navigation:mass'].value[0]
    C4 = system['weight:systems:transmission:mass'].value[0]
    C51 = system['weight:systems:operational:radar:mass'].value[0]
    C52 = system['weight:systems:operational:cargo_hold:mass'].value[0]
    C6 = system['weight:systems:flight_kit:mass'].value[0]

    furniture = system['weight:furniture:mass'].value[0]
    D1 = system['weight:furniture:cargo_configuration:mass'].value[0]
    D2 = system['weight:furniture:passenger_seats:mass'].value[0]
    D3 = system['weight:furniture:food_water:mass'].value[0]
    D4 = system['weight:furniture:security_kit:mass'].value[0]
    D5 = system['weight:furniture:toilets:mass'].value[0]

    crew = system['weight:crew:mass'].value[0]

    airframe = system['weight:airframe:mass'].value[0]
    wing = system['weight:airframe:wing:mass'].value[0]
    fuselage = system['weight:airframe:fuselage:mass'].value[0]
    h_tail = system['weight:airframe:horizontal_tail:mass'].value[0]
    v_tail = system['weight:airframe:vertical_tail:mass'].value[0]
    control_surface = system['weight:airframe:flight_controls:mass'].value[0]
    landing_gear_1 = system['weight:airframe:landing_gear:main:mass'].value[0]
    landing_gear_2 = system['weight:airframe:landing_gear:front:mass'].value[0]
    engine_pylon = system['weight:airframe:pylon:mass'].value[0]
    paint = system['weight:airframe:paint:mass'].value[0]

    propulsion = system['weight:propulsion:mass'].value[0]
    B1 = system['weight:propulsion:engine:mass'].value[0]
    B2 = system['weight:propulsion:fuel_lines:mass'].value[0]
    B3 = system['weight:propulsion:unconsumables:mass'].value[0]

    MTOW = system['weight:aircraft:MTOW'].value[0]
    MZFW = system['weight:aircraft:MZFW'].value[0]
    MFW = system['weight:aircraft:MFW'].value[0]
    OWE = system['weight:aircraft:OWE'].value[0]
    payload = system['weight:aircraft:payload'].value[0]
    fuel_mission = system['mission:sizing:mission:fuel'].value[0]

    # TODO: Deal with this in a more generic manner ?
    if round(MTOW, 6) == round(OWE + payload + fuel_mission, 6):
        MTOW = OWE + payload + fuel_mission

    fig = make_subplots(1, 2, specs=[[{"type": "domain"}, {"type": "domain"}]], )

    # FIXME: the first sunburst looks broken, but I don't know why
    fig.add_trace(go.Sunburst(
        labels=["MTOW", "payload", "fuel_mission", "OWE"],
        parents=["", "MTOW", "MTOW", "MTOW"],
        values=[MTOW, payload, fuel_mission, OWE],
        branchvalues='total',
    ), 1, 1)

    fig.add_trace(go.Sunburst(
        labels=["OWE", "airframe", "propulsion", "systems", "furniture", "crew",
                "wing", "fuselage", "h_tail", "v_tail", "control_surface",
                "landing_gear_1", "landing_gear_2", "engine_pylon", "paint",
                "B1", "B2", "B3",
                "C11", "C12", "C13", "C21", "C22", "C23", "C24", "C25", "C26", "C27",
                "C3", "C4", "C51", "C52", "C6",
                "D1", "D2", "D3", "D4", "D5",
                ],
        parents=["", "OWE", "OWE", "OWE", "OWE", "OWE",
                 "airframe", "airframe", "airframe", "airframe", "airframe", "airframe",
                 "airframe", "airframe", "airframe",
                 "propulsion", "propulsion", "propulsion",
                 "systems", "systems", "systems", "systems", "systems", "systems",
                 "systems", "systems", "systems", "systems", "systems", "systems",
                 "systems", "systems", "systems",
                 "furniture", "furniture", "furniture", "furniture", "furniture",
                 ],
        values=[OWE, airframe, propulsion, systems, furniture, crew,
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
