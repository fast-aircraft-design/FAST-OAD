#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
    d = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))

    assert d == {
        "mission": OrderedDict(
            [
                ("name", "sizing"),
                (
                    "steps",
                    [
                        OrderedDict([("route", "main")]),
                        OrderedDict([("route", "diversion")]),
                        OrderedDict([("phase", "holding")]),
                        OrderedDict([("phase", "taxi_in")]),
                    ],
                ),
            ]
        ),
        "phase_definitions": OrderedDict(
            [
                (
                    "initial_climb",
                    OrderedDict(
                        [
                            ("engine_setting", "takeoff"),
                            (
                                "polar",
                                {
                                    "CD": "data:aerodynamics:aircraft:takeoff:CD",
                                    "CL": "data:aerodynamics:aircraft:takeoff:CL",
                                },
                            ),
                            ("thrust_rate", "data:mission:sizing:climb:thrust_rate"),
                            (
                                "steps",
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
                                                                [("value", 400.0), ("unit", "ft")]
                                                            ),
                                                        ),
                                                        (
                                                            "equivalent_airspeed",
                                                            OrderedDict([("value", "constant")]),
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
                                                                [("value", 250.0), ("unit", "kn")]
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
                                                                [("value", 1500.0), ("unit", "ft")]
                                                            ),
                                                        ),
                                                        (
                                                            "equivalent_airspeed",
                                                            OrderedDict([("value", "constant")]),
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
                                {
                                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                                },
                            ),
                            ("thrust_rate", "data:mission:sizing:climb:thrust_rate"),
                            (
                                "steps",
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
                                                                [("value", 10000.0), ("unit", "ft")]
                                                            ),
                                                        ),
                                                        (
                                                            "equivalent_airspeed",
                                                            OrderedDict([("value", "constant")]),
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
                                                                [("value", 300.0), ("unit", "kn")]
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
                                                            OrderedDict([("value", "constant")]),
                                                        ),
                                                        (
                                                            "altitude",
                                                            OrderedDict([("value", -20000.0)]),
                                                        ),
                                                    ]
                                                ),
                                            ),
                                            ("maximum_mach", "data:TLAR:cruise_mach"),
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
                            ("engine_setting", "idle"),
                            (
                                "polar",
                                {
                                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                                },
                            ),
                            ("thrust_rate", "data:mission:sizing:descent:thrust_rate"),
                            (
                                "steps",
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
                                                                [("value", 300.0), ("unit", "kn")]
                                                            ),
                                                        ),
                                                        (
                                                            "mach",
                                                            OrderedDict([("value", "constant")]),
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
                                                                [("value", 10000.0), ("unit", "ft")]
                                                            ),
                                                        ),
                                                        (
                                                            "equivalent_airspeed",
                                                            OrderedDict([("value", "constant")]),
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
                                                                [("value", 250.0), ("unit", "kn")]
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
                                                            OrderedDict([("value", "constant")]),
                                                        ),
                                                        (
                                                            "altitude",
                                                            OrderedDict(
                                                                [("value", 1500.0), ("unit", "ft")]
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
                    "holding",
                    OrderedDict(
                        [
                            (
                                "steps",
                                [
                                    OrderedDict(
                                        [
                                            ("segment", "holding"),
                                            (
                                                "polar",
                                                {
                                                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                                                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                                                },
                                            ),
                                            (
                                                "target",
                                                OrderedDict(
                                                    [
                                                        (
                                                            "time",
                                                            "data:mission:sizing:holding:duration",
                                                        )
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
                            (
                                "steps",
                                [
                                    OrderedDict(
                                        [
                                            ("segment", "taxi"),
                                            (
                                                "thrust_rate",
                                                "data:mission:sizing:taxi_in:thrust_rate",
                                            ),
                                            (
                                                "target",
                                                OrderedDict(
                                                    [
                                                        (
                                                            "time",
                                                            "data:mission:sizing:taxi_in:duration",
                                                        )
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
            ]
        ),
        "route_definitions": OrderedDict(
            [
                (
                    "main",
                    OrderedDict(
                        [
                            ("range", "data:TLAR:range"),
                            (
                                "steps",
                                [
                                    OrderedDict([("phase", "initial_climb")]),
                                    OrderedDict([("phase", "climb")]),
                                    OrderedDict(
                                        [
                                            ("segment", "cruise"),
                                            ("engine_setting", "cruise"),
                                            (
                                                "polar",
                                                {
                                                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                                                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                                                },
                                            ),
                                        ]
                                    ),
                                    OrderedDict([("phase", "descent")]),
                                ],
                            ),
                        ]
                    ),
                ),
                (
                    "diversion",
                    OrderedDict(
                        [
                            ("range", "data:mission:sizing:diversion:distance"),
                            (
                                "steps",
                                [
                                    OrderedDict(
                                        [
                                            ("phase", "climb"),
                                            (
                                                "target",
                                                OrderedDict(
                                                    [
                                                        (
                                                            "altitude",
                                                            OrderedDict(
                                                                [("value", 22000.0), ("unit", "ft")]
                                                            ),
                                                        ),
                                                        (
                                                            "equivalent_airspeed",
                                                            OrderedDict([("value", "constant")]),
                                                        ),
                                                    ]
                                                ),
                                            ),
                                        ]
                                    ),
                                    OrderedDict(
                                        [
                                            ("segment", "cruise"),
                                            ("engine_setting", "cruise"),
                                            (
                                                "polar",
                                                {
                                                    "CD": "data:aerodynamics:aircraft:cruise:CD",
                                                    "CL": "data:aerodynamics:aircraft:cruise:CL",
                                                },
                                            ),
                                        ]
                                    ),
                                    OrderedDict([("phase", "descent")]),
                                ],
                            ),
                        ]
                    ),
                ),
            ]
        ),
    }
