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
    return OrderedDict(
        [
            (
                "phases",
                OrderedDict(
                    [
                        (
                            "initial_climb",
                            OrderedDict(
                                [
                                    ("engine_setting", "takeoff"),
                                    ("polar", OrderedDict([("CL", None), ("CD", None)])),
                                    (
                                        "thrust_rate",
                                        OrderedDict(
                                            [
                                                (
                                                    "value",
                                                    "data:propulsion:initial_climb:thrust_rate",
                                                ),
                                                ("default", 1.0),
                                            ]
                                        ),
                                    ),
                                    ("parts", None),
                                ]
                            ),
                        ),
                        (
                            "climb",
                            OrderedDict(
                                [
                                    ("engine_setting", "climb"),
                                    (
                                        "polar",
                                        OrderedDict(
                                            [
                                                ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                                ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                            ]
                                        ),
                                    ),
                                    ("thrust_rate", "data:propulsion:climb:thrust_rate"),
                                    ("parts", None),
                                ]
                            ),
                        ),
                        (
                            "diversion_climb",
                            OrderedDict(
                                [
                                    ("engine_setting", "climb"),
                                    (
                                        "polar",
                                        OrderedDict(
                                            [
                                                ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                                ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                            ]
                                        ),
                                    ),
                                    ("thrust_rate", 0.93),
                                    ("time_step", OrderedDict([("value", 5.0), ("unit", "s")])),
                                    ("parts", None),
                                ]
                            ),
                        ),
                        (
                            "descent",
                            OrderedDict(
                                [
                                    ("engine_setting", OrderedDict([("value", "idle")])),
                                    (
                                        "polar",
                                        OrderedDict(
                                            [
                                                ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                                ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                            ]
                                        ),
                                    ),
                                    ("thrust_rate", "data:propulsion:descent:thrust_rate"),
                                    ("parts", None),
                                ]
                            ),
                        ),
                        ("holding", OrderedDict([("parts", None)])),
                        ("taxi_out", OrderedDict([("parts", None)])),
                        ("taxi_in", OrderedDict([("thrust_rate", None), ("parts", None)])),
                    ]
                ),
            ),
            (
                "routes",
                OrderedDict(
                    [
                        (
                            "main",
                            OrderedDict(
                                [
                                    ("range", None),
                                    ("distance_accuracy", 500),
                                    ("climb_parts", None),
                                    (
                                        "cruise_part",
                                        OrderedDict(
                                            [
                                                ("segment", "optimal_cruise"),
                                                ("engine_setting", "cruise"),
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
                                            ]
                                        ),
                                    ),
                                    ("descent_parts", None),
                                ]
                            ),
                        ),
                        (
                            "diversion",
                            OrderedDict(
                                [
                                    ("range", None),
                                    (
                                        "distance_accuracy",
                                        OrderedDict([("value", 0.1), ("unit", "km")]),
                                    ),
                                    ("climb_parts", None),
                                    (
                                        "cruise_part",
                                        OrderedDict(
                                            [
                                                ("segment", "cruise"),
                                                ("engine_setting", "cruise"),
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
                                            ]
                                        ),
                                    ),
                                    ("descent_parts", None),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "missions",
                OrderedDict(
                    [
                        ("sizing", OrderedDict([("parts", None)])),
                        ("operational", OrderedDict([("parts", None)])),
                    ]
                ),
            ),
        ]
    )
