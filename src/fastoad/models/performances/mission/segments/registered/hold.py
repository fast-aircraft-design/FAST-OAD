"""Class for simulating hold segment."""

from dataclasses import dataclass

from fastoad.models.performances.mission.segments.base import (
    RegisterSegment,
)
from fastoad.models.performances.mission.segments.time_step_base import (
    AbstractFixedDurationSegment,
    AbstractLiftFromWeightSegment,
    AbstractRegulatedThrustSegment,
)


@RegisterSegment("holding")
@dataclass
class HoldSegment(
    AbstractRegulatedThrustSegment, AbstractFixedDurationSegment, AbstractLiftFromWeightSegment
):
    """
    Class for computing hold flight segment.

    Mach is considered constant, equal to Mach at starting point.
    Altitude is constant.
    Target is a specified time. The target definition indicates
    the time duration of the segment, independently of the initial time value.
    """
