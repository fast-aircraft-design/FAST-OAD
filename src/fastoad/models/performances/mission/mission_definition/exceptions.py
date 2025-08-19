"""Exceptions for mission definition."""

from fastoad.exceptions import FastError


class FastMissionFileMissingMissionNameError(FastError):
    """Raised when a mission definition is used without specifying the mission name."""
