#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURpositiveE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
import plotly.graph_objects as go
from fastoad.io import VariableIO


def v_n_diagram_drawing_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the V-n diagram of the aircraft for the MTOW and the MZFW.
    Different designs can be superpositiveed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: wing plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    ## Diagram parameters
    mtow = float(variables["data:weight:aircraft:MTOW"].value[0])
    mzfw = float(variables["data:weight:aircraft:MZFW"].value[0])

    # Speeds that are invariables between the MZFW and the MTOW
    v_cruising = float(variables["data:performance:V-n_diagram:v_cruising"].value[0])
    v_dive = float(variables["data:performance:V-n_diagram:v_dive"].value[0])

    # MTOW
    v_stall_mtow = float(variables["data:performance:V-n_diagram:v_stall"].value[0])
    v_manoeuvre_positive_mtow = float(
        variables["data:performance:V-n_diagram:MTOW:v_manoeuvre"].value[0]
    )  # manoeuvre speed at maximum positive load factor
    v_manoeuvre_negative_mtow = float(
        variables["data:performance:V-n_diagram:MTOW:v_manoeuvre_negative"].value[0]
    )  # manoeuvre speed at maximum negative load factor
    v_maneouvre_positive_vector_mtow = np.linspace(0, v_manoeuvre_positive_mtow, 100)
    v_manoeuvre_negative_vector_mtow = np.linspace(0, v_manoeuvre_negative_mtow, 100)

    n_v_c_positive_mtow = float(
        variables["data:performance:V-n_diagram:MTOW:n_v_c_positive"].value[0]
    )  # load factor at cruising speed for a gust of 50 ft/s
    n_v_c_negative_mtow = float(
        variables["data:performance:V-n_diagram:MTOW:n_v_c_negative"].value[0]
    )  # load factor at cruising speed for a gust of -50 ft/s
    n_v_d_positive_mtow = float(
        variables["data:performance:V-n_diagram:MTOW:n_v_d_positive"].value[0]
    )  # load factor at diving speed for a gust of 25 ft/s
    n_v_d_negative_mtow = float(
        variables["data:performance:V-n_diagram:MTOW:n_v_d_negative"].value[0]
    )  # load factor at diving speed for a gust of -25 ft/s

    v_1g_negative_mtow = float(
        variables["data:performance:V-n_diagram:v_1g_negative"].value[0]
    )  # speed at which the load factor is equal to -1

    # MZFW
    v_manoeuvre_positive_mzfw = float(
        variables["data:performance:V-n_diagram:MZFW:v_manoeuvre"].value[0]
    )  # manoeuvre speed at maximum positive load factor
    v_manoeuvre_negative_mzfw = float(
        variables["data:performance:V-n_diagram:MZFW:v_manoeuvre_negative"].value[0]
    )  # manoeuvre speed at maximum negative load factor

    v_manoeuvre_vector_mzfw = np.linspace(0, v_manoeuvre_positive_mzfw, 100)
    v_manoeuvre_negative_vector_mzfw = np.linspace(0, v_manoeuvre_negative_mzfw, 100)

    n_v_c_positive_mzfw = float(
        variables["data:performance:V-n_diagram:MZFW:n_v_c_positive"].value[0]
    )  # load factor at cruising speed for a gust of 50 ft/s
    n_v_c_negative_mzfw = float(
        variables["data:performance:V-n_diagram:MZFW:n_v_c_negative"].value[0]
    )  # load factor at cruising speed for a gust of -50 ft/s
    n_v_d_positive_mzfw = float(
        variables["data:performance:V-n_diagram:MZFW:n_v_d_positive"].value[0]
    )  # load factor at diving speed for a gust of 25 ft/s
    n_v_d_negative_mzfw = float(
        variables["data:performance:V-n_diagram:MZFW:n_v_d_negative"].value[0]
    )  # load factor at diving speed for a gust of -25 ft/s

    mass_correction_factor = np.sqrt(
        mzfw / mtow
    )  # correction factor to take into account the modification of mass
    v_stall_mzfw = v_stall_mtow * mass_correction_factor
    v_1g_negative_mzfw = (
        v_1g_negative_mtow * mass_correction_factor
    )  # speed at which the load factor is equal to -1

    ## MTOW Computation
    n_from_0_to_n_max = np.zeros_like(
        v_maneouvre_positive_vector_mtow
    )  # load factor vector between 0 and the maximum load factor (parabolic curve)
    for i in range(len(v_maneouvre_positive_vector_mtow)):
        n_from_0_to_n_max[i] = (v_maneouvre_positive_vector_mtow[i] / v_stall_mtow) * (
            v_maneouvre_positive_vector_mtow[i] / v_stall_mtow
        )
        if n_from_0_to_n_max[i] > 1 and n_from_0_to_n_max[i - 1] < 1:
            n_from_0_to_n_max[i] = 1
            v_maneouvre_positive_vector_mtow[i] = v_stall_mtow

    n_negative_vector = np.zeros_like(
        v_manoeuvre_negative_vector_mtow
    )  # load factor vector between 0 and the maximum load factor (parabolic curve)
    for i in range(len(v_manoeuvre_negative_vector_mtow)):
        n_negative_vector[i] = -(v_manoeuvre_negative_vector_mtow[i] / v_1g_negative_mtow) * (
            v_manoeuvre_negative_vector_mtow[i] / v_1g_negative_mtow
        )
        if n_negative_vector[i] <= -1 and n_negative_vector[i - 1] > -1:
            n_negative_vector[i] = -1
            v_manoeuvre_negative_vector_mtow[i] = v_1g_negative_mtow

    v_remaining = np.array(
        [
            v_manoeuvre_positive_mtow,
            v_dive,
            v_dive,
            v_cruising,
            v_manoeuvre_negative_mtow,
        ]
    )  # Value of speed that permit to close the manoeuvre envelope
    n_remaining = np.array(
        [
            n_from_0_to_n_max[-1],
            n_from_0_to_n_max[-1],
            0,
            n_negative_vector[-1],
            n_negative_vector[-1],
        ]
    )  # Value of load factor that permit to close the manoeuvre envelope

    n_manoeuvre_envelope_mtow = np.append(
        n_from_0_to_n_max, np.append(n_remaining, n_negative_vector[::-1])
    )
    v_manoeuvre_envelope_mtow = np.append(
        v_maneouvre_positive_vector_mtow,
        np.append(v_remaining, v_manoeuvre_negative_vector_mtow[::-1]),
    )

    # Flight envelope computation
    # This envelope is computed by taking into account the manoeuvre envelope and the gust envelope
    v_flight_envelope_mtow = np.where(
        v_maneouvre_positive_vector_mtow >= v_stall_mtow,
        v_maneouvre_positive_vector_mtow,
        v_stall_mtow,
    )  # Speed vector containing the speeds of the flight envelope

    # Below, the different cases dealt between the gust envelope and the manoeuvre envelope
    if n_v_c_positive_mtow > n_from_0_to_n_max[-1]:
        n_flight_envelope_mtow = np.append(
            n_from_0_to_n_max,
            np.array(
                [
                    n_from_0_to_n_max[-1],
                    n_v_c_positive_mtow,
                ]
            ),
        )
        v_flight_envelope_mtow = np.append(
            v_flight_envelope_mtow,
            np.array(
                [
                    FindVMeeting(0, 1, v_cruising, n_v_c_positive_mtow, n_from_0_to_n_max[-1]),
                    v_cruising,
                ]
            ),
        )
        if n_v_d_positive_mtow > n_from_0_to_n_max[-1]:
            n_flight_envelope_mtow = np.append(
                n_flight_envelope_mtow,
                np.array(
                    [
                        n_v_d_positive_mtow,
                        n_from_0_to_n_max[-1],
                        np.minimum(n_v_d_negative_mtow, 0),
                    ]
                ),
            )
            v_flight_envelope_mtow = np.append(
                v_flight_envelope_mtow,
                np.array(
                    [
                        v_dive,
                        v_dive,
                        v_dive,
                    ]
                ),
            )

        else:
            n_flight_envelope_mtow = np.append(
                n_flight_envelope_mtow,
                np.array(
                    [
                        n_from_0_to_n_max[-1],
                        n_from_0_to_n_max[-1],
                        np.minimum(n_v_d_negative_mtow, 0),
                    ]
                ),
            )
            v_flight_envelope_mtow = np.append(
                v_flight_envelope_mtow,
                np.array(
                    [
                        FindVMeeting(
                            v_cruising,
                            n_v_c_positive_mtow,
                            v_dive,
                            n_v_d_positive_mtow,
                            n_from_0_to_n_max[-1],
                        ),
                        v_dive,
                        v_dive,
                    ]
                ),
            )

    else:
        if n_v_d_positive_mtow < n_from_0_to_n_max[-1]:
            v_flight_envelope_mtow = np.append(v_flight_envelope_mtow, np.array([v_dive, v_dive]))
            n_flight_envelope_mtow = np.append(
                n_from_0_to_n_max,
                np.array([n_from_0_to_n_max[-1], np.minimum(n_v_d_negative_mtow, 0)]),
            )
        else:
            v_flight_envelope_mtow = np.append(
                v_flight_envelope_mtow,
                np.array(
                    [
                        FindVMeeting(0, 1, v_dive, n_v_d_positive_mtow, n_from_0_to_n_max[-1]),
                        v_dive,
                        v_dive,
                    ]
                ),
            )
            n_flight_envelope_mtow = np.append(
                n_from_0_to_n_max,
                np.array(
                    [n_from_0_to_n_max[-1], n_v_d_positive_mtow, np.minimum(n_v_d_negative_mtow, 0)]
                ),
            )

    if n_v_d_negative_mtow > 0 and n_v_c_negative_mtow > n_negative_vector[-1]:
        n_flight_envelope_mtow = np.append(
            n_flight_envelope_mtow,
            np.array([n_negative_vector[-1], n_negative_vector[-1], -1, 0, 0]),
        )
        v_flight_envelope_mtow = np.append(
            v_flight_envelope_mtow,
            np.array(
                [
                    v_cruising,
                    v_manoeuvre_negative_mtow,
                    v_1g_negative_mtow,
                    v_1g_negative_mtow,
                    v_stall_mtow,
                ]
            ),
        )
    elif n_v_d_negative_mtow < 0 and n_v_c_negative_mtow > n_negative_vector[-1]:
        n_flight_envelope_mtow = np.append(
            n_flight_envelope_mtow,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mtow,
                        v_dive,
                        n_v_d_negative_mtow,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[1],
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    -1,
                    0,
                    0,
                ]
            ),
        )
        v_flight_envelope_mtow = np.append(
            v_flight_envelope_mtow,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mtow,
                        v_dive,
                        n_v_d_negative_mtow,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[0],
                    v_cruising,
                    v_manoeuvre_negative_mtow,
                    v_1g_negative_mtow,
                    v_1g_negative_mtow,
                    v_stall_mtow,
                ]
            ),
        )
    elif n_v_d_negative_mtow < 0 and n_v_c_negative_mtow < n_negative_vector[-1]:
        n_flight_envelope_mtow = np.append(
            n_flight_envelope_mtow,
            np.array(
                [
                    n_v_c_negative_mtow,
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    -1,
                    0,
                    0,
                ]
            ),
        )
        v_flight_envelope_mtow = np.append(
            v_flight_envelope_mtow,
            np.array(
                [
                    v_cruising,
                    FindVMeeting(0, 1, v_cruising, n_v_c_negative_mtow, n_negative_vector[-1]),
                    v_manoeuvre_positive_mtow,
                    v_manoeuvre_negative_mtow,
                    v_1g_negative_mtow,
                    v_1g_negative_mtow,
                    v_stall_mtow,
                ]
            ),
        )
    else:
        n_flight_envelope_mtow = np.append(
            n_flight_envelope_mtow,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mtow,
                        v_dive,
                        n_v_d_negative_mtow,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[1],
                    n_v_c_negative_mtow,
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    -1,
                    0,
                    0,
                ]
            ),
        )
        v_flight_envelope_mtow = np.append(
            v_flight_envelope_mtow,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mtow,
                        v_dive,
                        n_v_d_negative_mtow,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[0],
                    v_cruising,
                    FindVMeeting(0, 1, v_cruising, n_v_c_negative_mtow, n_negative_vector[-1]),
                    v_manoeuvre_negative_mtow,
                    v_1g_negative_mtow,
                    v_1g_negative_mtow,
                    v_stall_mtow,
                ]
            ),
        )

    ## MZFW Computation
    v_remaining_mzfw = np.array(
        [
            v_manoeuvre_positive_mzfw,
            v_dive,
            v_dive,
            v_cruising,
            v_manoeuvre_negative_mzfw,
        ]
    )  # Value of speed that permit to close the manoeuvre envelope
    n_remaining_mzfw = np.array(
        [
            n_from_0_to_n_max[-1],
            n_from_0_to_n_max[-1],
            0,
            n_negative_vector[-1],
            n_negative_vector[-1],
        ]
    )  # Value of load factor that permit to close the manoeuvre envelope

    n_manoeuvre_envelope_mzfw = np.append(
        n_from_0_to_n_max, np.append(n_remaining_mzfw, n_negative_vector[::-1])
    )
    v_manoeuvre_envelope_mzfw = np.append(
        v_manoeuvre_vector_mzfw, np.append(v_remaining_mzfw, v_manoeuvre_negative_vector_mzfw[::-1])
    )

    # Flight envelope computation
    # This envelope is computed by taking into account the manoeuvre envelope and the gust envelope
    v_flight_envelope_mzfw = np.where(
        v_manoeuvre_vector_mzfw >= v_stall_mzfw,
        v_manoeuvre_vector_mzfw,
        v_stall_mzfw,
    )  # Speed vector containing the speeds of the flight envelope

    # Below, the different cases dealt between the gust envelope and the manoeuvre envelope
    if n_v_c_positive_mzfw > n_from_0_to_n_max[-1]:
        n_flight_envelope_mzfw = np.append(
            n_from_0_to_n_max,
            np.array(
                [
                    n_from_0_to_n_max[-1],
                    n_v_c_positive_mzfw,
                ]
            ),
        )
        v_flight_envelope_mzfw = np.append(
            v_flight_envelope_mzfw,
            np.array(
                [
                    FindVMeeting(0, 1, v_cruising, n_v_c_positive_mzfw, n_from_0_to_n_max[-1]),
                    v_cruising,
                ]
            ),
        )
        if n_v_d_positive_mzfw > n_from_0_to_n_max[-1]:
            n_flight_envelope_mzfw = np.append(
                n_flight_envelope_mzfw,
                np.array(
                    [
                        n_v_d_positive_mzfw,
                        n_from_0_to_n_max[-1],
                        np.minimum(n_v_d_negative_mzfw, 0),
                    ]
                ),
            )
            v_flight_envelope_mzfw = np.append(
                v_flight_envelope_mzfw,
                np.array(
                    [
                        v_dive,
                        v_dive,
                        v_dive,
                    ]
                ),
            )

        else:
            n_flight_envelope_mzfw = np.append(
                n_flight_envelope_mzfw,
                np.array(
                    [
                        n_from_0_to_n_max[-1],
                        n_from_0_to_n_max[-1],
                        np.minimum(n_v_d_negative_mzfw, 0),
                    ]
                ),
            )
            v_flight_envelope_mzfw = np.append(
                v_flight_envelope_mzfw,
                np.array(
                    [
                        FindVMeeting(
                            v_cruising,
                            n_v_c_positive_mzfw,
                            v_dive,
                            n_v_d_positive_mzfw,
                            n_from_0_to_n_max[-1],
                        ),
                        v_dive,
                        v_dive,
                    ]
                ),
            )

    else:
        if n_v_d_positive_mzfw < n_from_0_to_n_max[-1]:
            v_flight_envelope_mzfw = np.append(v_flight_envelope_mzfw, np.array([v_dive, v_dive]))
            n_flight_envelope_mzfw = np.append(
                n_from_0_to_n_max,
                np.array([n_from_0_to_n_max[-1], np.minimum(n_v_d_negative_mzfw, 0)]),
            )
        else:
            v_flight_envelope_mzfw = np.append(
                v_flight_envelope_mzfw,
                np.array(
                    [
                        FindVMeeting(0, 1, v_dive, n_v_d_positive_mzfw, n_from_0_to_n_max[-1]),
                        v_dive,
                        v_dive,
                    ]
                ),
            )
            n_flight_envelope_mzfw = np.append(
                n_from_0_to_n_max,
                np.array(
                    [n_from_0_to_n_max[-1], n_v_d_positive_mzfw, np.minimum(n_v_d_negative_mzfw, 0)]
                ),
            )

    if n_v_d_negative_mzfw > 0 and n_v_c_negative_mzfw > n_negative_vector[-1]:
        n_flight_envelope_mzfw = np.append(
            n_flight_envelope_mzfw,
            np.array([n_negative_vector[-1], n_negative_vector[-1], -1, 0, 0]),
        )
        v_flight_envelope_mzfw = np.append(
            v_flight_envelope_mzfw,
            np.array(
                [
                    v_cruising,
                    v_manoeuvre_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_stall_mzfw,
                ]
            ),
        )
    elif n_v_d_negative_mzfw < 0 and n_v_c_negative_mzfw > n_negative_vector[-1]:
        n_flight_envelope_mzfw = np.append(
            n_flight_envelope_mzfw,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mzfw,
                        v_dive,
                        n_v_d_negative_mzfw,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[1],
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    -1,
                    0,
                    0,
                ]
            ),
        )
        v_flight_envelope_mzfw = np.append(
            v_flight_envelope_mzfw,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mzfw,
                        v_dive,
                        n_v_d_negative_mzfw,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[0],
                    v_cruising,
                    v_manoeuvre_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_stall_mzfw,
                ]
            ),
        )
    elif n_v_d_negative_mzfw < 0 and n_v_c_negative_mzfw < n_negative_vector[-1]:
        n_flight_envelope_mzfw = np.append(
            n_flight_envelope_mzfw,
            np.array(
                [
                    n_v_c_negative_mzfw,
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    -1,
                    0,
                    0,
                ]
            ),
        )
        v_flight_envelope_mzfw = np.append(
            v_flight_envelope_mzfw,
            np.array(
                [
                    v_cruising,
                    FindVMeeting(0, 1, v_cruising, n_v_c_negative_mzfw, n_negative_vector[-1]),
                    v_manoeuvre_positive_mzfw,
                    v_manoeuvre_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_stall_mzfw,
                ]
            ),
        )
    else:
        n_flight_envelope_mzfw = np.append(
            n_flight_envelope_mzfw,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mzfw,
                        v_dive,
                        n_v_d_negative_mzfw,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[1],
                    n_v_c_negative_mzfw,
                    n_negative_vector[-1],
                    n_negative_vector[-1],
                    -1,
                    0,
                    0,
                ]
            ),
        )
        v_flight_envelope_mzfw = np.append(
            v_flight_envelope_mzfw,
            np.array(
                [
                    FindVandNMeeting(
                        v_cruising,
                        n_v_c_negative_mzfw,
                        v_dive,
                        n_v_d_negative_mzfw,
                        v_cruising,
                        n_negative_vector[-1],
                        v_dive,
                        0,
                    )[0],
                    v_cruising,
                    FindVMeeting(0, 1, v_cruising, n_v_c_negative_mzfw, n_negative_vector[-1]),
                    v_manoeuvre_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_1g_negative_mzfw,
                    v_stall_mzfw,
                ]
            ),
        )

    # Plot the results
    fig = go.Figure()

    # MTOW
    scatter_v_c_positive_mtow = go.Scatter(
        x=np.array([1, v_cruising]),
        y=np.array([1, n_v_c_positive_mtow]),
        legendgroup="group",
        line=dict(color="#ff7f0e", dash="dash", width=2),
        name="50 ft/s gust",
        visible="legendonly",
    )  # gust line for 50 ft/s
    scatter_v_c_negative_mtow = go.Scatter(
        x=np.array([1, v_cruising]),
        y=np.array([1, n_v_c_negative_mtow]),
        legendgroup="group",
        line=dict(color="#ff7f0e", dash="dash", width=2),
        showlegend=False,
        visible="legendonly",
    )  # gust line for -50 ft/s
    scatter_v_d_positive_mtow = go.Scatter(
        x=np.array([1, v_dive]),
        y=np.array([1, n_v_d_positive_mtow]),
        legendgroup="group",
        line=dict(color="#00cc96", dash="dash", width=2),
        showlegend=False,
        visible="legendonly",
    )  # gust line for 25 ft/s
    scatter_v_d_negative_mtow = go.Scatter(
        x=np.array([1, v_dive]),
        y=np.array([1, n_v_d_negative_mtow]),
        legendgroup="group",
        line=dict(color="#00cc96", dash="dash", width=2),
        name="25 ft/s gust",
        visible="legendonly",
    )  # gust line for -25 ft/s
    scatter_v_n_manoeuvre_envelope_mtow = go.Scatter(
        x=v_manoeuvre_envelope_mtow,
        y=n_manoeuvre_envelope_mtow,
        legendgroup="group",
        legendgrouptitle_text="MTOW",
        line=dict(color="#636efa", dash="dash"),
        name="manoeuvre envelope",
        visible="legendonly",
    )
    scatter_stall_vertical_mtow = go.Scatter(
        x=np.array([v_stall_mtow, v_stall_mtow]),
        y=np.array([0, 1]),
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )
    scatter_1g_negative_vertical_mtow = go.Scatter(
        x=np.array([v_1g_negative_mtow, v_1g_negative_mtow]),
        y=np.array([0, -1]),
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )  # vertical line at speed at which the load factor is equal to -1
    scatter_manoeuvre_positive_vertical_mtow = go.Scatter(
        x=np.array([v_manoeuvre_positive_mtow, v_manoeuvre_positive_mtow]),
        y=np.array([0, n_from_0_to_n_max[-1]]),
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )  # vertical line at manoeuvre speed for maximum positive load factor
    scatter_manoeuvre_negative_vertical_mtow = go.Scatter(
        x=np.array([v_manoeuvre_negative_mtow, v_manoeuvre_negative_mtow]),
        y=np.array([0, n_negative_vector[-1]]),
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )  # vertical line at manoeuvre speed for maximum negative load factor
    scatter_flight_envelope_mtow = go.Scatter(
        x=v_flight_envelope_mtow,
        y=n_flight_envelope_mtow,
        legendgroup="group",
        line=dict(
            color="black",
        ),
        mode="lines",
        name="flight envelope : n_max = %3f"
        % np.maximum(n_v_c_positive_mtow, n_from_0_to_n_max[-1]),
        visible="legendonly",
    )

    # MZFW
    scatter_v_c_positive_mzfw = go.Scatter(
        x=np.array([1, v_cruising]),
        y=np.array([1, n_v_c_positive_mzfw]),
        legendgroup="group2",
        legendgrouptitle_text="MZFW",
        line=dict(color="red", dash="dash", width=1),
        name="50 ft/s gust",
    )  # gust line for 50 ft/s
    scatter_v_c_negative_mzfw = go.Scatter(
        x=np.array([1, v_cruising]),
        y=np.array([1, n_v_c_negative_mzfw]),
        legendgroup="group2",
        line=dict(color="red", dash="dash", width=1),
        showlegend=False,
    )  # gust line for -50 ft/s
    scatter_v_d_positive_mzfw = go.Scatter(
        x=np.array([1, v_dive]),
        y=np.array([1, n_v_d_positive_mzfw]),
        legendgroup="group2",
        line=dict(color="green", dash="dash", width=1),
        showlegend=False,
    )  # gust line for 25 ft/s
    scatter_v_d_negative_mzfw = go.Scatter(
        x=np.array([1, v_dive]),
        y=np.array([1, n_v_d_negative_mzfw]),
        legendgroup="group2",
        line=dict(color="green", dash="dash", width=1),
        name="25 ft/s gust",
    )  # gust line for -25 ft/s
    scatter_v_n_manoeuvre_envelope_mzfw = go.Scatter(
        x=v_manoeuvre_envelope_mzfw,
        y=n_manoeuvre_envelope_mzfw,
        legendgroup="group2",
        legendgrouptitle_text="MZFW",
        line=dict(color="blue", dash="dash"),
        name="manoeuvre envelope",
    )
    scatter_stall_vertical_mzfw = go.Scatter(
        x=np.array([v_stall_mzfw, v_stall_mzfw]),
        y=np.array([0, 1]),
        legendgroup="group2",
        line=dict(color="blue", dash="dot", width=1),
        showlegend=False,
    )
    scatter_minus_1g_vertical_mzfw = go.Scatter(
        x=np.array([v_1g_negative_mzfw, v_1g_negative_mzfw]),
        y=np.array([0, -1]),
        legendgroup="group2",
        line=dict(color="blue", dash="dot", width=1),
        showlegend=False,
    )  # vertical line at speed at which the load factor is equal to -1
    scatter_manoeuvre_positive_vertical_mzfw = go.Scatter(
        x=np.array([v_manoeuvre_positive_mzfw, v_manoeuvre_positive_mzfw]),
        y=np.array([0, n_from_0_to_n_max[-1]]),
        legendgroup="group2",
        line=dict(color="blue", dash="dot", width=1),
        showlegend=False,
    )  # vertical line at manoeuvre speed for maximum positive load factor
    scatter_manoeuvre_negative_vertical_mzfw = go.Scatter(
        x=np.array([v_manoeuvre_negative_mzfw, v_manoeuvre_negative_mzfw]),
        y=np.array([0, n_negative_vector[-1]]),
        legendgroup="group2",
        line=dict(color="blue", dash="dot", width=1),
        showlegend=False,
    )  # vertical line at manoeuvre speed for maximum negative load factor
    scatter_flight_envelope_mzfw = go.Scatter(
        x=v_flight_envelope_mzfw,
        y=n_flight_envelope_mzfw,
        legendgroup="group2",
        line=dict(
            color="black",
        ),
        mode="lines",
        name="flight envelope : n_max = %3f"
        % np.maximum(n_v_c_positive_mzfw, n_from_0_to_n_max[-1]),
    )

    scatter_cruising_vertical_mtow = go.Scatter(
        x=np.array([v_cruising, v_cruising]),
        y=np.array([n_negative_vector[-1], n_from_0_to_n_max[-1]]),
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
    )
    scatter_dive_vertical_mtow = go.Scatter(
        x=np.array([v_dive, v_dive]),
        y=np.array([0, n_from_0_to_n_max[-1]]),
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
    )
    scatter_cruising_vertical_mzfw = go.Scatter(
        x=np.array([v_cruising, v_cruising]),
        y=np.array([n_negative_vector[-1], n_from_0_to_n_max[-1]]),
        legendgroup="group2",
        line=dict(
            color="blue",
            dash="dot",
        ),
        showlegend=False,
    )
    scatter_dive_vertical_mzfw = go.Scatter(
        x=np.array([v_dive, v_dive]),
        y=np.array([0, n_from_0_to_n_max[-1]]),
        legendgroup="group2",
        line=dict(
            color="blue",
            dash="dot",
        ),
        showlegend=False,
    )

    fig.add_trace(scatter_cruising_vertical_mtow)
    fig.add_trace(scatter_dive_vertical_mtow)
    fig.add_trace(scatter_cruising_vertical_mzfw)
    fig.add_trace(scatter_dive_vertical_mzfw)

    # MZFW
    fig.add_trace(scatter_v_n_manoeuvre_envelope_mzfw)
    fig.add_trace(scatter_manoeuvre_positive_vertical_mzfw)
    fig.add_trace(scatter_manoeuvre_negative_vertical_mzfw)
    fig.add_trace(scatter_stall_vertical_mzfw)
    fig.add_trace(scatter_minus_1g_vertical_mzfw)

    fig.add_trace(scatter_v_c_positive_mzfw)
    fig.add_trace(scatter_v_c_negative_mzfw)
    fig.add_trace(scatter_v_d_positive_mzfw)
    fig.add_trace(scatter_v_d_negative_mzfw)
    fig.add_trace(scatter_flight_envelope_mzfw)

    # MTOW
    fig.add_trace(scatter_v_n_manoeuvre_envelope_mtow)
    fig.add_trace(scatter_manoeuvre_positive_vertical_mtow)
    fig.add_trace(scatter_manoeuvre_negative_vertical_mtow)
    fig.add_trace(scatter_stall_vertical_mtow)
    fig.add_trace(scatter_1g_negative_vertical_mtow)

    fig.add_trace(scatter_v_c_positive_mtow)
    fig.add_trace(scatter_v_c_negative_mtow)
    fig.add_trace(scatter_v_d_positive_mtow)
    fig.add_trace(scatter_v_d_negative_mtow)
    fig.add_trace(scatter_flight_envelope_mtow)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=750,
        width=900,
        # title_text="V-n maoeuvre diagram",
        title_x=0.5,
        xaxis_title="Equivalent Air Speed [m/s]",
        yaxis_title="Load factor [-]",
    )
    return fig


# Function which returns the x-value (speed) of the meeting point between an horizontal line and another line
def FindVMeeting(x1, y1, x2, y2, n_max):

    # Equation of the line : y = mx + p
    m = (y2 - y1) / (x2 - x1)
    p = y2 - m * x2
    x_meeting = (n_max - p) / m
    return x_meeting


# Function which returns the x-value (speed) and the y-value (load factor)  of the meeting point between two lines
def FindVandNMeeting(xA1, yA1, xA2, yA2, xB1, yB1, xB2, yB2):

    mA = (yA2 - yA1) / (xA2 - xA1)
    mB = (yB2 - yB1) / (xB2 - xB1)

    pA = yA1 - mA * xA1
    pB = yB1 - mB * xB1

    x_meeting = (pB - pA) / (mA - mB)
    y_meeting = mA * x_meeting + pA
    return x_meeting, y_meeting
