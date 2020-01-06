"""
Tests for postprocessing functions
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

import os.path as pth

import pytest

from fastoad.io.xml import OMXmlIO
from fastoad.utils.postprocessing.analysis_and_plots import \
    wing_geometry_plot, drag_polar_plot, mass_breakdown_plot

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')

def test_wing_geometry_plot():
    """
    Basic tests for testing the plotting.
    """

    filename = pth.join(DATA_FOLDER_PATH, 'problem_outputs.xml')

    xml = OMXmlIO(filename)

    # First plot
    fig = wing_geometry_plot(xml)

    # First plot with name
    fig = wing_geometry_plot(xml, name='First plot')

    # Adding a plot to the previous fig
    fig = wing_geometry_plot(xml, name='Second plot', fig=fig)


def test_drag_polar_plot():
    """
    Basic tests for testing the plotting.
    """

    filename = pth.join(DATA_FOLDER_PATH, 'problem_outputs.xml')

    xml = OMXmlIO(filename)

    # First plot
    fig = drag_polar_plot(xml)


def test_mass_breakdown_plot():
    """
    Basic tests for testing the plotting.
    """

    filename = pth.join(DATA_FOLDER_PATH, 'problem_outputs.xml')

    xml = OMXmlIO(filename)

    # First plot
    fig = mass_breakdown_plot(xml)

