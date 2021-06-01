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

import os.path as pth
from collections import OrderedDict

from ..schema import MissionDefinition

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_schema():
    obtained_dict = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))

    # As we use Python 3.7+, Python dictionaries are ordered, but they are still
    # considered equal when the order of key differs.
    # To check order, we need to convert both dictionaries to OrderedDict (recursively!)
    obtained_dict = _to_ordered_dict(obtained_dict)
    expected_dict = _to_ordered_dict(_get_expected_dict())

    assert obtained_dict == expected_dict


def _to_ordered_dict(item):
    """Returns the item with all dictionaries inside transformed to OrderedDict."""
    if isinstance(item, dict):
        ordered_dict = OrderedDict(item)
        for key, value in ordered_dict.items():
            ordered_dict[key] = _to_ordered_dict(value)
        return ordered_dict
    elif isinstance(item, list):
        for i, value in enumerate(item):
            item[i] = _to_ordered_dict(value)
    else:
        return item


def _get_expected_dict():
    return {
        "phases": {
            "initial_climb": {
                "engine_setting": "takeoff",
                "polar": {"CL": [0.0, 0.5, 1.0], "CD": [0.0, 0.03, 0.12]},
                "thrust_rate": {"value": 1.0},
                "parts": [
                    {
                        "segment": "altitude_change",
                        "target": {
                            "altitude": {"value": 400.0, "unit": "ft"},
                            "equivalent_airspeed": {"value": "constant"},
                        },
                    },
                    {
                        "segment": "speed_change",
                        "polar": {
                            "CL": "data:aerodynamics:aircraft:takeoff:CL",
                            "CD": "data:aerodynamics:aircraft:takeoff:CD",
                        },
                        "target": {"equivalent_airspeed": {"value": 250.0, "unit": "kn"}},
                    },
                    {
                        "segment": "altitude_change",
                        "polar": {
                            "CL": "data:aerodynamics:aircraft:takeoff:CL",
                            "CD": "data:aerodynamics:aircraft:takeoff:CD",
                        },
                        "target": {
                            "altitude": {"value": 1500.0, "unit": "ft"},
                            "equivalent_airspeed": {"value": "constant"},
                        },
                    },
                ],
            },
            "climb": {
                "engine_setting": "climb",
                "polar": {
                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                },
                "thrust_rate": "data:propulsion:climb:thrust_rate",
                "parts": [
                    {
                        "segment": "altitude_change",
                        "target": {
                            "altitude": {"value": 10000.0, "unit": "ft"},
                            "equivalent_airspeed": {"value": "constant"},
                        },
                    },
                    {
                        "segment": "speed_change",
                        "target": {"equivalent_airspeed": {"value": 300.0, "unit": "kn"}},
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
                        "target": {"mach": "constant", "altitude": {"value": -20000.0}},
                    },
                ],
            },
            "diversion_climb": {
                "engine_setting": "climb",
                "polar": {
                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                },
                "thrust_rate": 0.93,
                "time_step": {"value": 5.0, "unit": "s"},
                "parts": [
                    {
                        "segment": "altitude_change",
                        "target": {
                            "altitude": {"value": 10000.0, "unit": "ft"},
                            "equivalent_airspeed": "constant",
                        },
                    },
                    {
                        "segment": "speed_change",
                        "target": {"equivalent_airspeed": {"value": 300.0, "unit": "kn"}},
                    },
                    {
                        "segment": "altitude_change",
                        "target": {
                            "altitude": {"value": 22000.0, "unit": "ft"},
                            "equivalent_airspeed": "constant",
                        },
                    },
                ],
            },
            "descent": {
                "engine_setting": {"value": "idle"},
                "polar": {
                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                },
                "thrust_rate": "data:propulsion:descent:thrust_rate",
                "parts": [
                    {
                        "segment": "altitude_change",
                        "target": {
                            "equivalent_airspeed": {"value": 300.0, "unit": "kn"},
                            "mach": {"value": "constant"},
                        },
                    },
                    {
                        "segment": "altitude_change",
                        "target": {
                            "altitude": {"value": 10000.0, "unit": "ft"},
                            "equivalent_airspeed": {"value": "constant"},
                        },
                    },
                    {
                        "segment": "speed_change",
                        "target": {"equivalent_airspeed": {"value": 250.0, "unit": "kn"}},
                    },
                    {
                        "segment": "altitude_change",
                        "target": {
                            "equivalent_airspeed": {"value": "constant"},
                            "altitude": "~final_altitude",
                        },
                    },
                ],
            },
            "holding": {
                "parts": [
                    {
                        "segment": "holding",
                        "polar": {
                            "CL": "data:aerodynamics:aircraft:cruise:CL",
                            "CD": "data:aerodynamics:aircraft:cruise:CD",
                        },
                        "target": {"time": "~duration"},
                    }
                ]
            },
            "taxi_out": {
                "parts": [{"segment": "taxi", "thrust_rate": None, "target": {"time": "~duration"}}]
            },
            "taxi_in": {
                "thrust_rate": None,
                "parts": [{"segment": "taxi", "target": {"time": "~duration"}}],
            },
        },
        "routes": {
            "main": {
                "range": None,
                "climb_parts": [{"phase": "initial_climb"}, {"phase": "climb"}],
                "cruise_part": {
                    "segment": "optimal_cruise",
                    "engine_setting": "cruise",
                    "polar": {
                        "CL": "data:aerodynamics:aircraft:cruise:CL",
                        "CD": "data:aerodynamics:aircraft:cruise:CD",
                    },
                },
                "descent_parts": [{"phase": "descent"}],
            },
            "diversion": {
                "range": None,
                "climb_parts": [{"phase": "diversion_climb"}],
                "cruise_part": {
                    "segment": "cruise",
                    "engine_setting": "cruise",
                    "polar": {
                        "CL": "data:aerodynamics:aircraft:cruise:CL",
                        "CD": "data:aerodynamics:aircraft:cruise:CD",
                    },
                },
                "descent_parts": [{"phase": "descent"}],
            },
        },
        "missions": {
            "sizing": {
                "parts": [
                    {"route": "main"},
                    {"route": "diversion"},
                    {"phase": "holding"},
                    {"phase": "taxi_in"},
                ]
            },
            "operational": {
                "parts": [{"phase": "taxi_out"}, {"route": "main"}, {"phase": "taxi_in"}]
            },
        },
    }
