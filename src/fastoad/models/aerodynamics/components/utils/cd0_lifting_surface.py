"""Computation of CD0 for a lifting surface."""
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

from dataclasses import dataclass

import numpy as np

from fastoad.models.aerodynamics.components.utils.friction_drag import (
    get_flat_plate_friction_drag_coefficient,
)


@dataclass
class LiftingSurfaceGeometry:
    """Minimum geometry data for computation of CD0 of lifting surfaces."""

    thickness_ratio: float  #: average thickness ratio
    MAC_length: float  #: length of Mean Aerodynamic Chord
    sweep_angle_25: float  #: sweep angle at 25% chord, in degrees
    cambered: bool  #: True if airfoil is cambered
    wet_area: float  #: wet surface area of the lifting surface
    interaction_coeff: float  #: ratio of additional drag due to interaction effects


def compute_cd0_lifting_surface(
    geometry: LiftingSurfaceGeometry,
    mach: float,
    reynolds: float,
    wing_area: float,
    lift_coefficient: float = 0.0,
):
    """
    Computes CD0 for a lifting surface.

    Friction coefficient is assessed from :cite:`raymer:1999` (Eq 12.27).
    Corrections for lifting surfaces are from :cite:`supaero:2014`.

    :param geometry: definition of lifting surface geometry
    :param mach: Mach number
    :param reynolds: Reynolds number
    :param wing_area: wing area (will be used for getting CD specific to wing area
    :param lift_coefficient: needed if wing is cambered
    :return: CD0 value
    """
    # Drag coefficient for flat plate (
    cf = get_flat_plate_friction_drag_coefficient(geometry.MAC_length, mach, reynolds)

    # Contribution of relative thickness
    thickness_contribution = (
        4.688 * geometry.thickness_ratio ** 2 + 3.146 * geometry.thickness_ratio
    )

    # Contribution of camber
    sweep_25 = np.radians(geometry.sweep_angle_25)
    if geometry.cambered:
        camber_contribution = (
            2.859 * (lift_coefficient / np.cos(sweep_25) ** 2) ** 3
            - 1.849 * (lift_coefficient / np.cos(sweep_25) ** 2) ** 2
            + 0.382 * (lift_coefficient / np.cos(sweep_25) ** 2)
            + 0.06
        )
    else:
        camber_contribution = 0.0

    # Correction from sweep angle
    sweep_correction = (
        1 - 0.000178 * geometry.sweep_angle_25 ** 2 - 0.0065 * geometry.sweep_angle_25
    )

    cd0_ht = (
        (
            (thickness_contribution + camber_contribution) * sweep_correction
            + geometry.interaction_coeff
            + 1
        )
        * cf
        * geometry.wet_area
        / wing_area
    )
    return cd0_ht
