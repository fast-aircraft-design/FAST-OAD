#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
from collections import OrderedDict
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot, knot

from fastoad.model_base.propulsion import IPropulsion
from fastoad.models.performances.mission.base import FlightSequence
from fastoad.models.performances.mission.segments.altitude_change import AltitudeChangeSegment
from fastoad.models.performances.mission.segments.hold import HoldSegment
from fastoad.models.performances.mission.segments.speed_change import SpeedChangeSegment
from fastoad.models.performances.mission.segments.taxi import TaxiSegment
from ..exceptions import FastMissionFileMissingMissionNameError
from ..mission_builder import MissionBuilder
from ..schema import MissionDefinition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_initialization():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )

    assert mission_builder._structure == OrderedDict(
        [
            (
                "sizing",
                OrderedDict(
                    [
                        ("mission", "sizing"),
                        (
                            "parts",
                            [
                                OrderedDict(
                                    [
                                        ("route", "main"),
                                        ("range", None),
                                        ("distance_accuracy", 500),
                                        (
                                            "climb_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        ("phase", "initial_climb"),
                                                        ("engine_setting", "takeoff"),
                                                        (
                                                            "polar",
                                                            {
                                                                "CD": [0.0, 0.03, 0.12],
                                                                "CL": [0.0, 0.5, 1.0],
                                                            },
                                                        ),
                                                        ("thrust_rate", {"value": 1.0}),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 400.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "polar": OrderedDict(
                                                                        [
                                                                            (
                                                                                "CL",
                                                                                "data:aerodynamics:aircraft:takeoff:CL",
                                                                            ),
                                                                            (
                                                                                "CD",
                                                                                "data:aerodynamics:aircraft:takeoff:CD",
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 250,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "polar": {
                                                                        "CD": "data:aerodynamics:aircraft:takeoff:CD",
                                                                        "CL": "data:aerodynamics:aircraft:takeoff:CL",
                                                                    },
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 1500.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                                OrderedDict(
                                                    [
                                                        ("phase", "climb"),
                                                        ("engine_setting", "climb"),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        "data:aerodynamics:aircraft:cruise:CL",
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        "data:aerodynamics:aircraft:cruise:CD",
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            "data:propulsion:climb:thrust_rate",
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 10000.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 300.0,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": "constant",
                                                                        "mach": "data:TLAR:cruise_mach",
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "value": -20000.0
                                                                        },
                                                                        "mach": "constant",
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                        (
                                            "cruise_part",
                                            {
                                                "engine_setting": "cruise",
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            "data:aerodynamics:aircraft:cruise:CL",
                                                        ),
                                                        (
                                                            "CD",
                                                            "data:aerodynamics:aircraft:cruise:CD",
                                                        ),
                                                    ]
                                                ),
                                                "segment": "optimal_cruise",
                                            },
                                        ),
                                        (
                                            "descent_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        ("phase", "descent"),
                                                        ("engine_setting", {"value": "idle"}),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        "data:aerodynamics:aircraft:cruise:CL",
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        "data:aerodynamics:aircraft:cruise:CD",
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            "data:propulsion:descent:thrust_rate",
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 300,
                                                                        },
                                                                        "mach": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 10000.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 250.0,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": "~final_altitude",
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("route", "diversion"),
                                        ("range", None),
                                        ("distance_accuracy", {"unit": "km", "value": 0.1}),
                                        (
                                            "climb_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        ("phase", "diversion_climb"),
                                                        ("engine_setting", "climb"),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        "data:aerodynamics:aircraft:cruise:CL",
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        "data:aerodynamics:aircraft:cruise:CD",
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        ("thrust_rate", 0.93),
                                                        ("time_step", {"unit": "s", "value": 5.0}),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 10000.0,
                                                                        },
                                                                        "equivalent_airspeed": "constant",
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 300.0,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 22000.0,
                                                                        },
                                                                        "equivalent_airspeed": "constant",
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                        (
                                            "cruise_part",
                                            {
                                                "engine_setting": "cruise",
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            "data:aerodynamics:aircraft:cruise:CL",
                                                        ),
                                                        (
                                                            "CD",
                                                            "data:aerodynamics:aircraft:cruise:CD",
                                                        ),
                                                    ]
                                                ),
                                                "segment": "cruise",
                                            },
                                        ),
                                        (
                                            "descent_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        ("phase", "descent"),
                                                        ("engine_setting", {"value": "idle"}),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        "data:aerodynamics:aircraft:cruise:CL",
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        "data:aerodynamics:aircraft:cruise:CD",
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            "data:propulsion:descent:thrust_rate",
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 300,
                                                                        },
                                                                        "mach": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 10000.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 250.0,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": "~final_altitude",
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("phase", "holding"),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "polar": OrderedDict(
                                                        [
                                                            (
                                                                "CL",
                                                                "data:aerodynamics:aircraft:cruise:CL",
                                                            ),
                                                            (
                                                                "CD",
                                                                "data:aerodynamics:aircraft:cruise:CD",
                                                            ),
                                                        ]
                                                    ),
                                                    "segment": "holding",
                                                    "target": {"delta_time": "~duration"},
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("phase", "taxi_in"),
                                        ("thrust_rate", None),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": "taxi",
                                                    "target": {"delta_time": "~duration"},
                                                    "true_airspeed": 0.0,
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                {"reserve": {"multiplier": 0.03, "ref": "main"}},
                            ],
                        ),
                    ]
                ),
            ),
            (
                "operational",
                OrderedDict(
                    [
                        ("mission", "operational"),
                        (
                            "parts",
                            [
                                OrderedDict(
                                    [
                                        ("phase", "taxi_out"),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": "taxi",
                                                    "target": {"delta_time": "~duration"},
                                                    "thrust_rate": None,
                                                    "true_airspeed": 0.0,
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("route", "main"),
                                        ("range", None),
                                        ("distance_accuracy", 500),
                                        (
                                            "climb_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        ("phase", "initial_climb"),
                                                        ("engine_setting", "takeoff"),
                                                        (
                                                            "polar",
                                                            {
                                                                "CD": [0.0, 0.03, 0.12],
                                                                "CL": [0.0, 0.5, 1.0],
                                                            },
                                                        ),
                                                        ("thrust_rate", {"value": 1.0}),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 400.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "polar": OrderedDict(
                                                                        [
                                                                            (
                                                                                "CL",
                                                                                "data:aerodynamics:aircraft:takeoff:CL",
                                                                            ),
                                                                            (
                                                                                "CD",
                                                                                "data:aerodynamics:aircraft:takeoff:CD",
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 250,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "polar": {
                                                                        "CD": "data:aerodynamics:aircraft:takeoff:CD",
                                                                        "CL": "data:aerodynamics:aircraft:takeoff:CL",
                                                                    },
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 1500.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                                OrderedDict(
                                                    [
                                                        ("phase", "climb"),
                                                        ("engine_setting", "climb"),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        "data:aerodynamics:aircraft:cruise:CL",
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        "data:aerodynamics:aircraft:cruise:CD",
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            "data:propulsion:climb:thrust_rate",
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 10000.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 300.0,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": "constant",
                                                                        "mach": "data:TLAR:cruise_mach",
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "value": -20000.0
                                                                        },
                                                                        "mach": "constant",
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                        (
                                            "cruise_part",
                                            {
                                                "engine_setting": "cruise",
                                                "polar": OrderedDict(
                                                    [
                                                        (
                                                            "CL",
                                                            "data:aerodynamics:aircraft:cruise:CL",
                                                        ),
                                                        (
                                                            "CD",
                                                            "data:aerodynamics:aircraft:cruise:CD",
                                                        ),
                                                    ]
                                                ),
                                                "segment": "optimal_cruise",
                                            },
                                        ),
                                        (
                                            "descent_parts",
                                            [
                                                OrderedDict(
                                                    [
                                                        ("phase", "descent"),
                                                        ("engine_setting", {"value": "idle"}),
                                                        (
                                                            "polar",
                                                            OrderedDict(
                                                                [
                                                                    (
                                                                        "CL",
                                                                        "data:aerodynamics:aircraft:cruise:CL",
                                                                    ),
                                                                    (
                                                                        "CD",
                                                                        "data:aerodynamics:aircraft:cruise:CD",
                                                                    ),
                                                                ]
                                                            ),
                                                        ),
                                                        (
                                                            "thrust_rate",
                                                            "data:propulsion:descent:thrust_rate",
                                                        ),
                                                        (
                                                            "parts",
                                                            [
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 300,
                                                                        },
                                                                        "mach": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": {
                                                                            "unit": "ft",
                                                                            "value": 10000.0,
                                                                        },
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "speed_change",
                                                                    "target": {
                                                                        "equivalent_airspeed": {
                                                                            "unit": "kn",
                                                                            "value": 250.0,
                                                                        }
                                                                    },
                                                                },
                                                                {
                                                                    "segment": "altitude_change",
                                                                    "target": {
                                                                        "altitude": "~final_altitude",
                                                                        "equivalent_airspeed": {
                                                                            "value": "constant"
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("phase", "taxi_in"),
                                        ("thrust_rate", None),
                                        (
                                            "parts",
                                            [
                                                {
                                                    "segment": "taxi",
                                                    "target": {"delta_time": "~duration"},
                                                    "true_airspeed": 0.0,
                                                }
                                            ],
                                        ),
                                    ]
                                ),
                                {"reserve": {"multiplier": 0.02, "ref": "main"}},
                            ],
                        ),
                    ]
                ),
            ),
        ]
    )


def test_inputs():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )
    with pytest.raises(FastMissionFileMissingMissionNameError):
        mission_builder.get_input_variables()

    assert mission_builder.get_input_variables("sizing") == {
        "data:TLAR:cruise_mach": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CL": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CL": (None, "Input defined by the mission."),
        "data:mission:sizing:diversion:descent:final_altitude": (
            "m",
            "Input defined by the mission.",
        ),
        "data:mission:sizing:diversion:range": ("m", "Input defined by the mission."),
        "data:mission:sizing:holding:duration": ("s", "Input defined by the mission."),
        "data:mission:sizing:main:descent:final_altitude": (
            "m",
            "Input defined by the mission.",
        ),
        "data:mission:sizing:main:range": ("m", "Input defined by the mission."),
        "data:mission:sizing:taxi_in:duration": ("s", "Input defined by the mission."),
        "data:mission:sizing:taxi_in:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:climb:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:descent:thrust_rate": (None, "Input defined by the mission."),
    }
    assert mission_builder.get_input_variables("operational") == {
        "data:TLAR:cruise_mach": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:cruise:CL": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CD": (None, "Input defined by the mission."),
        "data:aerodynamics:aircraft:takeoff:CL": (None, "Input defined by the mission."),
        "data:mission:operational:main:descent:final_altitude": (
            "m",
            "Input defined by the mission.",
        ),
        "data:mission:operational:main:range": ("m", "Input defined by the mission."),
        "data:mission:operational:taxi_in:duration": ("s", "Input defined by the mission."),
        "data:mission:operational:taxi_in:thrust_rate": (None, "Input defined by the mission."),
        "data:mission:operational:taxi_out:duration": ("s", "Input defined by the mission."),
        "data:mission:operational:taxi_out:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:climb:thrust_rate": (None, "Input defined by the mission."),
        "data:propulsion:descent:thrust_rate": (None, "Input defined by the mission."),
    }


def test_build():
    mission_definition = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))
    mission_builder = MissionBuilder(
        mission_definition, propulsion=Mock(IPropulsion), reference_area=100.0
    )

    cl = np.linspace(0.0, 1.0, 11)
    cd = 0.5 * cl ** 2

    inputs = {
        "data:TLAR:cruise_mach": 0.78,
        "data:mission:sizing:main:range": 8000.0e3,
        "data:mission:sizing:diversion:range": 926.0e3,
        "initial_climb:final_altitude": 500,
        "initial_climb:final_equivalent_airspeed": 130.0,
        "data:aerodynamics:aircraft:cruise:CD": cd,
        "data:aerodynamics:aircraft:cruise:CL": cl,
        "data:aerodynamics:aircraft:low_speed:CD": cd,
        "data:aerodynamics:aircraft:low_speed:CL": cl,
        "data:aerodynamics:aircraft:takeoff:CD": cd,
        "data:aerodynamics:aircraft:takeoff:CL": cl,
        "data:mission:sizing:climb:thrust_rate": 0.9,
        "data:mission:sizing:descent:thrust_rate": 0.5,
        "data:mission:sizing:holding:duration": 2000.0,
        "data:mission:sizing:taxi_in:duration": 300.0,
        "data:mission:sizing:taxi_in:thrust_rate": 0.5,
    }
    mission = mission_builder.build(inputs, mission_name="sizing")

    assert len(mission.flight_sequence) == 4
    assert mission.flight_sequence[0].name == "sizing:main"
    assert mission.flight_sequence[1].name == "sizing:diversion"
    assert mission.flight_sequence[2].name == "sizing:holding"
    assert mission.flight_sequence[3].name == "sizing:taxi_in"

    main_route = mission.flight_sequence[0]
    assert isinstance(main_route, FlightSequence)
    assert len(main_route.flight_sequence) == 4
    assert main_route.distance_accuracy == 500.0
    assert main_route.flight_sequence[0].name == "sizing:main:initial_climb"
    assert main_route.flight_sequence[1].name == "sizing:main:climb"
    assert main_route.flight_sequence[2].name == "sizing:main:cruise"
    assert main_route.flight_sequence[3].name == "sizing:main:descent"

    initial_climb = main_route.flight_sequence[0]
    assert isinstance(initial_climb, FlightSequence)
    assert len(initial_climb.flight_sequence) == 3
    assert_allclose([segment.thrust_rate for segment in initial_climb.flight_sequence], 1.0)

    climb1 = initial_climb.flight_sequence[0]
    assert isinstance(climb1, AltitudeChangeSegment)
    assert climb1.target.altitude == pytest.approx(400 * foot)
    assert climb1.target.equivalent_airspeed == "constant"
    assert_allclose(climb1.polar.definition_cl, [0.0, 0.5, 1.0])
    assert_allclose(climb1.polar.cd(), [0.0, 0.03, 0.12])

    acceleration = initial_climb.flight_sequence[1]
    assert isinstance(acceleration, SpeedChangeSegment)
    assert acceleration.target.equivalent_airspeed == pytest.approx(250 * knot)
    assert_allclose(acceleration.polar.definition_cl, cl)
    assert_allclose(acceleration.polar.cd(), cd)

    climb2 = initial_climb.flight_sequence[2]
    assert isinstance(climb2, AltitudeChangeSegment)
    assert_allclose(climb2.polar.definition_cl, cl)
    assert_allclose(climb2.polar.cd(), cd)

    holding_phase = mission.flight_sequence[2]
    assert isinstance(holding_phase, FlightSequence)
    assert len(holding_phase.flight_sequence) == 1
    holding = holding_phase.flight_sequence[0]
    assert isinstance(holding, HoldSegment)

    taxi_in_phase = mission.flight_sequence[3]
    assert isinstance(taxi_in_phase, FlightSequence)
    assert len(taxi_in_phase.flight_sequence) == 1
    taxi_in = taxi_in_phase.flight_sequence[0]
    assert isinstance(taxi_in, TaxiSegment)


def test_get_route_ranges():
    mission_definition = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))
    mission_builder = MissionBuilder(
        mission_definition, propulsion=Mock(IPropulsion), reference_area=100.0
    )

    cl = np.linspace(0.0, 1.0, 11)
    cd = 0.5 * cl ** 2

    inputs = {
        "data:TLAR:cruise_mach": 0.78,
        "data:mission:sizing:main:range": 8000.0e3,
        "data:mission:operational:main:range": 500.0e3,
        "data:mission:sizing:diversion:range": 926.0e3,
        "initial_climb:final_altitude": 500,
        "initial_climb:final_equivalent_airspeed": 130.0,
        "data:aerodynamics:aircraft:cruise:CD": cd,
        "data:aerodynamics:aircraft:cruise:CL": cl,
        "data:aerodynamics:aircraft:low_speed:CD": cd,
        "data:aerodynamics:aircraft:low_speed:CL": cl,
        "data:aerodynamics:aircraft:takeoff:CD": cd,
        "data:aerodynamics:aircraft:takeoff:CL": cl,
        "data:mission:sizing:climb:thrust_rate": 0.9,
        "data:mission:sizing:descent:thrust_rate": 0.5,
        "data:mission:sizing:holding:duration": 2000.0,
        "data:mission:operational:taxi_out:duration": 300.0,
        "data:mission:operational:taxi_out:thrust_rate": 0.5,
        "data:mission:operational:taxi_in:duration": 300.0,
        "data:mission:operational:taxi_in:thrust_rate": 0.5,
        "data:mission:sizing:taxi_in:duration": 300.0,
        "data:mission:sizing:taxi_in:thrust_rate": 0.5,
    }

    assert_allclose(mission_builder.get_route_ranges(inputs, "sizing"), [8000.0e3, 926.0e3])
    assert_allclose(mission_builder.get_route_ranges(inputs, "operational"), [500.0e3])


def test_get_reserve():
    mission_builder = MissionBuilder(
        pth.join(DATA_FOLDER_PATH, "mission.yml"),
        propulsion=Mock(IPropulsion),
        reference_area=100.0,
    )

    flight_points = pd.DataFrame(
        dict(
            mass=[70000, 65000, 55000, 45000],
            name=[
                "data:mission:sizing:main:start",
                "data:mission:sizing:main:climb",
                "data:mission:sizing:other:start",
                "data:mission:sizing:other:climb",
            ],
        )
    )
    assert_allclose(mission_builder.get_reserve(flight_points, "sizing"), 5000 * 0.03)

    flight_points.name = [
        "data:mission:sizing:main:start",
        "data:mission:sizing:main:climb",
        "data:mission:sizing:main:cruise",
        "data:mission:sizing:main:cruise",
    ]
    assert_allclose(mission_builder.get_reserve(flight_points, "sizing"), 25000 * 0.03)
