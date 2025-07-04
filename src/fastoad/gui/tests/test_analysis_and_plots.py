"""
Tests for analysis and plots functions
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

from pathlib import Path

import pytest

from .. import (
    aircraft_geometry_plot,
    drag_polar_plot,
    mass_breakdown_bar_plot,
    mass_breakdown_sun_plot,
    payload_range_plot,
    wing_geometry_plot,
)

DATA_FOLDER_PATH = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "filename",
    [DATA_FOLDER_PATH / "problem_outputs.xml", DATA_FOLDER_PATH / "problem_outputs_updated.xml"],
)
def test_wing_geometry_plot(filename):
    """
    Basic tests for testing the plotting.
    """

    # First plot
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    fig = wing_geometry_plot(filename)

    # First plot with name
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    fig = wing_geometry_plot(filename, name="First plot")

    # Adding plots to the previous fig
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    for i in range(20):
        fig = wing_geometry_plot(filename, name=f"Plot {i}", fig=fig)


@pytest.mark.parametrize(
    "filename",
    [DATA_FOLDER_PATH / "problem_outputs.xml", DATA_FOLDER_PATH / "problem_outputs_updated.xml"],
)
def test_aircraft_geometry_plot(filename):
    """
    Basic tests for testing the plotting.
    """

    # First plot
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    fig = aircraft_geometry_plot(filename)

    # First plot with name
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    fig = aircraft_geometry_plot(filename, name="First plot")

    # Adding plots to the previous fig
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    for i in range(20):
        fig = aircraft_geometry_plot(filename, name=f"Plot {i}", fig=fig)


@pytest.mark.parametrize(
    "filename",
    [DATA_FOLDER_PATH / "problem_outputs.xml", DATA_FOLDER_PATH / "problem_outputs_updated.xml"],
)
def test_mass_breakdown_bar_plot(filename):
    """
    Basic tests for testing the plotting.
    """

    # First plot
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    fig = mass_breakdown_bar_plot(filename)

    # First plot with name
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    fig = mass_breakdown_bar_plot(filename, name="First plot")

    # Adding plots to the previous fig
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    for i in range(20):
        _ = mass_breakdown_bar_plot(filename, name=f"Plot {i}", fig=fig)


@pytest.mark.parametrize(
    "filename",
    [DATA_FOLDER_PATH / "problem_outputs.xml", DATA_FOLDER_PATH / "problem_outputs_updated.xml"],
)
def test_drag_polar_plot(filename):
    """
    Basic tests for testing the plotting.
    """

    # First plot
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    _ = drag_polar_plot(filename)


@pytest.mark.parametrize(
    "filename",
    [DATA_FOLDER_PATH / "problem_outputs.xml", DATA_FOLDER_PATH / "problem_outputs_updated.xml"],
)
def test_mass_breakdown_sun_plot(filename):
    """
    Basic tests for testing the plotting.
    """

    # First plot
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    _ = mass_breakdown_sun_plot(filename)


def test_mass_breakdown_sun_plot_specific_mission():
    """
    Test for testing the sun mass breakdown plotting for a specific mission.
    """

    filename = DATA_FOLDER_PATH / "problem_outputs_multi_mission.xml"

    mission_1 = "evaluation_mission"

    # Plot 1
    # Specific mission plot
    mass_breakdown_sun_plot(filename, mission_name=mission_1)
    # Debug
    # f = mass_breakdown_sun_plot(filename, mission_name=mission_1)  # noqa: ERA001
    # f.show()  # noqa: ERA001

    mission_2 = "MTOW_mission"

    # Plot 2
    # Specific mission plot (sizing mission)
    mass_breakdown_sun_plot(filename, mission_name=mission_2)
    # Debug
    # f = mass_breakdown_sun_plot(filename, mission_name=mission_2)  # noqa: ERA001
    # f.show()  # noqa: ERA001

    mission_3 = "not_a_mission_name"

    # Plot 3
    # Specific mission plot error
    with pytest.raises(ValueError) as exc_info:
        _ = mass_breakdown_sun_plot(filename, mission_name=mission_3)
        assert f"{mission_3}" in str(exc_info.value)


@pytest.mark.parametrize(
    "filename",
    [DATA_FOLDER_PATH / "problem_outputs.xml", DATA_FOLDER_PATH / "problem_outputs_updated.xml"],
)
def test_payload_range_plot(filename):
    """
    Basic tests for testing the plotting.
    """

    # First plot
    # This is a rudimentary test as plot are difficult to verify
    # The test will fail if an error is raised by the following line
    # Only contour
    payload_range_plot(
        filename,
        name="Payload-Range",
        mission_name="sizing",
        variable_of_interest=None,
        variable_of_interest_legend=None,
    )

    # Second plot
    # With grid
    payload_range_plot(
        filename,
        name="Payload-Range",
        mission_name="sizing",
        variable_of_interest="block_fuel",
        variable_of_interest_legend="Block fuel",
    )
