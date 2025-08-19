"""
Classes for simulating flight segments.

Be sure to import this package before interpreting a mission input file.
"""


# flake8: noqa

# With these imports, importing only the current package ensures to have all
# these segments available when interpreting a mission input file
from . import (
    altitude_change,
    cruise,
    ground_speed_change,
    hold,
    mass_input,
    speed_change,
    start,
    takeoff,
    taxi,
    transition,
)
