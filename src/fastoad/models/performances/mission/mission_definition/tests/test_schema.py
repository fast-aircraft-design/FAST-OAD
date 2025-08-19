from collections import OrderedDict
from pathlib import Path

from ..schema import MissionDefinition

DATA_FOLDER_PATH = Path(__file__).parent / "data"


def test_schema():
    obtained_dict = MissionDefinition(DATA_FOLDER_PATH / "mission.yml")

    # As we use Python 3.7+, Python dictionaries are ordered, but they are still
    # considered equal when the order of key differs.
    # To check order, we need to convert both dictionaries to OrderedDict (recursively!)
    obtained_dict = _to_ordered_dict(obtained_dict)
    expected_dict = _get_expected_dict()

    assert obtained_dict == expected_dict


def _to_ordered_dict(item):
    """Returns the item with all dictionaries inside transformed to OrderedDict."""
    if isinstance(item, dict):
        ordered_dict = OrderedDict(item)
        for key, value in ordered_dict.items():
            ordered_dict[key] = _to_ordered_dict(value)
        return ordered_dict
    else:
        if isinstance(item, list):
            for i, value in enumerate(item):
                item[i] = _to_ordered_dict(value)
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
                                    (
                                        "polar",
                                        OrderedDict(
                                            [("CL", [0.0, 0.5, 1.0]), ("CD", [0.0, 0.03, 0.12])]
                                        ),
                                    ),
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
                                    (
                                        "time_step",
                                        OrderedDict(
                                            [("value", "settings:mission:~"), ("unit", "s")]
                                        ),
                                    ),
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 400.0),
                                                                            ("unit", "ft"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [("value", "constant")]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "speed_change"),
                                                    (
                                                        "polar",
                                                        "data:aerodynamics:aircraft:takeoff",
                                                    ),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 250),
                                                                            ("unit", "kn"),
                                                                        ]
                                                                    ),
                                                                )
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "polar",
                                                        OrderedDict(
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
                                                    ),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 1500.0),
                                                                            ("unit", "ft"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [("value", "constant")]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
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
                                        "data:aerodynamics:aircraft:cruise",
                                    ),
                                    ("thrust_rate", "data:propulsion:climb:thrust_rate"),
                                    ("time_step", OrderedDict([("value", "~"), ("unit", "s")])),
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 10000.0),
                                                                            ("unit", "ft"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [("value", "constant")]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "speed_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 300.0),
                                                                            ("unit", "kn"),
                                                                        ]
                                                                    ),
                                                                )
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                ("equivalent_airspeed", "constant"),
                                                                ("mach", "data:TLAR:cruise_mach"),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                ("mach", "constant"),
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [("value", -20000.0)]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
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
                                        "data:aerodynamics:aircraft:cruise",
                                    ),
                                    ("thrust_rate", 0.93),
                                    (
                                        "time_step",
                                        OrderedDict(
                                            [("value", "settings:mission~t_step"), ("unit", "s")]
                                        ),
                                    ),
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 10000.0),
                                                                            ("unit", "ft"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                ("equivalent_airspeed", "constant"),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "speed_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 300.0),
                                                                            ("unit", "kn"),
                                                                        ]
                                                                    ),
                                                                )
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 22000.0),
                                                                            ("unit", "ft"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                ("equivalent_airspeed", "constant"),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
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
                                        "data:aerodynamics:aircraft:cruise",
                                    ),
                                    ("thrust_rate", "data:propulsion:descent:thrust_rate"),
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 300),
                                                                            ("unit", "kn"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                (
                                                                    "mach",
                                                                    OrderedDict(
                                                                        [("value", "constant")]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "altitude",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 10000.0),
                                                                            ("unit", "ft"),
                                                                        ]
                                                                    ),
                                                                ),
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [("value", "constant")]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "speed_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", 250.0),
                                                                            ("unit", "kn"),
                                                                        ]
                                                                    ),
                                                                )
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            OrderedDict(
                                                [
                                                    ("segment", "altitude_change"),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                (
                                                                    "equivalent_airspeed",
                                                                    OrderedDict(
                                                                        [("value", "constant")]
                                                                    ),
                                                                ),
                                                                ("altitude", "~:final_altitude"),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                        (
                            "holding",
                            OrderedDict(
                                [
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "holding"),
                                                    (
                                                        "polar",
                                                        "data:aerodynamics:aircraft:cruise",
                                                    ),
                                                    (
                                                        "target",
                                                        OrderedDict([("delta_time", "~duration")]),
                                                    ),
                                                ]
                                            )
                                        ],
                                    )
                                ]
                            ),
                        ),
                        (
                            "taxi_out",
                            OrderedDict(
                                [
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "taxi"),
                                                    ("thrust_rate", "~"),
                                                    ("true_airspeed", 0.0),
                                                    (
                                                        "target",
                                                        OrderedDict(
                                                            [
                                                                ("delta_time", "~:duration"),
                                                                (
                                                                    "mass",
                                                                    OrderedDict(
                                                                        [
                                                                            ("value", "~TOW"),
                                                                            ("unit", "kg"),
                                                                        ]
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ],
                                    )
                                ]
                            ),
                        ),
                        (
                            "taxi_in",
                            OrderedDict(
                                [
                                    ("thrust_rate", "~"),
                                    (
                                        "parts",
                                        [
                                            OrderedDict(
                                                [
                                                    ("segment", "taxi"),
                                                    ("true_airspeed", 0.0),
                                                    (
                                                        "target",
                                                        OrderedDict([("delta_time", "~duration")]),
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                ]
                            ),
                        ),
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
                                    ("range", "~"),
                                    ("distance_accuracy", 500),
                                    (
                                        "climb_parts",
                                        [
                                            OrderedDict([("phase", "initial_climb")]),
                                            OrderedDict([("phase", "climb")]),
                                        ],
                                    ),
                                    (
                                        "cruise_part",
                                        OrderedDict(
                                            [
                                                ("segment", "optimal_cruise"),
                                                ("engine_setting", "cruise"),
                                                (
                                                    "polar",
                                                    "data:aerodynamics:aircraft:cruise",
                                                ),
                                            ]
                                        ),
                                    ),
                                    ("descent_parts", [OrderedDict([("phase", "descent")])]),
                                ]
                            ),
                        ),
                        (
                            "diversion",
                            OrderedDict(
                                [
                                    ("range", "~"),
                                    (
                                        "distance_accuracy",
                                        OrderedDict([("value", 0.1), ("unit", "km")]),
                                    ),
                                    ("climb_parts", [OrderedDict([("phase", "diversion_climb")])]),
                                    (
                                        "cruise_part",
                                        OrderedDict(
                                            [
                                                ("segment", "cruise"),
                                                ("engine_setting", "cruise"),
                                                (
                                                    "polar",
                                                    "data:aerodynamics:aircraft:cruise",
                                                ),
                                            ]
                                        ),
                                    ),
                                    ("descent_parts", [OrderedDict([("phase", "descent")])]),
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
                        (
                            "sizing",
                            OrderedDict(
                                [
                                    (
                                        "parts",
                                        [
                                            OrderedDict([("route", "main")]),
                                            OrderedDict([("route", "diversion")]),
                                            OrderedDict([("phase", "holding")]),
                                            OrderedDict([("phase", "taxi_in")]),
                                            OrderedDict(
                                                [
                                                    (
                                                        "reserve",
                                                        OrderedDict(
                                                            [("ref", "main"), ("multiplier", 0.03)]
                                                        ),
                                                    )
                                                ]
                                            ),
                                        ],
                                    )
                                ]
                            ),
                        ),
                        (
                            "operational",
                            OrderedDict(
                                [
                                    (
                                        "parts",
                                        [
                                            OrderedDict([("phase", "taxi_out")]),
                                            OrderedDict([("route", "main")]),
                                            OrderedDict([("phase", "taxi_in")]),
                                            OrderedDict(
                                                [
                                                    (
                                                        "reserve",
                                                        OrderedDict(
                                                            [("ref", "main"), ("multiplier", 0.02)]
                                                        ),
                                                    )
                                                ]
                                            ),
                                        ],
                                    )
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
