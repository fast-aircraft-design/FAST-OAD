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
    d = MissionDefinition(pth.join(DATA_FOLDER_PATH, "mission.yml"))

    assert d == {
        "missions": OrderedDict(
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
                                ],
                            )
                        ]
                    ),
                ),
            ]
        ),
        "phases": OrderedDict(
            [
                (
                    "initial_climb",
                    OrderedDict(
                        [
                            ("engine_setting", "takeoff"),
                            (
                                "polar",
                                OrderedDict([("CL", [0.0, 0.5, 1.0]), ("CD", [0.0, 0.03, 0.12])]),
                            ),
                            ("thrust_rate", OrderedDict([("value", 1.0)])),
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
                                OrderedDict(
                                    [
                                        ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                        ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                    ]
                                ),
                            ),
                            ("thrust_rate", "data:propulsion:climb:thrust_rate"),
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
                                                            OrderedDict([("value", -20000.0)]),
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
                                OrderedDict(
                                    [
                                        ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                        ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                    ]
                                ),
                            ),
                            ("thrust_rate", 0.93),
                            ("time_step", OrderedDict([("value", 5.0), ("unit", "s")])),
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
                                                                [("value", 10000.0), ("unit", "ft")]
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
                                                            "altitude",
                                                            OrderedDict(
                                                                [("value", 22000.0), ("unit", "ft")]
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
                                OrderedDict(
                                    [
                                        ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                        ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                    ]
                                ),
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
                                                        ("altitude", "~final_altitude"),
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
                                            ("target", OrderedDict([("time", "~duration")])),
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
                                            ("target", OrderedDict([("time", "~duration")])),
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
                                            ("target", OrderedDict([("time", "~duration")])),
                                        ]
                                    )
                                ],
                            ),
                        ]
                    ),
                ),
            ]
        ),
        "routes": OrderedDict(
            [
                (
                    "main",
                    OrderedDict(
                        [
                            ("range", "~"),
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
                                            OrderedDict(
                                                [
                                                    ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                                    ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                                ]
                                            ),
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
                            ("climb_parts", [OrderedDict([("phase", "diversion_climb")])]),
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
                                                    ("CL", "data:aerodynamics:aircraft:cruise:CL"),
                                                    ("CD", "data:aerodynamics:aircraft:cruise:CD"),
                                                ]
                                            ),
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
    }
