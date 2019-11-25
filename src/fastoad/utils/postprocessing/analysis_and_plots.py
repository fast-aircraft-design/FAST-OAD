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

    scatter = go.Scatter(x=x, y=y,
                         mode='lines+markers')

    layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    data = [scatter]
    fig = go.FigureWidget(data=data, layout=layout)
    fig.layout.title = 'Wing Geometry'
    return fig
