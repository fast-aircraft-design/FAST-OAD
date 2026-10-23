#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

import numpy as np
import pytest
from numpy.testing import assert_allclose

from fastoad.model_base.flight_point import FlightPoint
from fastoad.models.performances.mission.exceptions import FastUnknownMissionElementError
from fastoad.models.performances.mission.polar import Polar
from fastoad.models.performances.mission.polar_modifier import (
    AbstractPolarModifier,
    GroundEffectRaymer,
    RegisterPolarModifier,
    UnchangedPolar,
)


@pytest.fixture
def polar() -> Polar:
    """Returns a simple polar for testing."""
    cl = np.array([0.5, 1.0, 1.5])
    cd = np.array([0.01, 0.035, 0.07])
    alpha = np.array([0.0, 0.1, 0.2])
    return Polar(cl, cd, alpha)


@pytest.fixture
def flight_point() -> FlightPoint:
    """Returns a flight point at low altitude."""
    return FlightPoint(altitude=1.0)


def test_modify_polar_unaffected_by_altitude(polar):
    """UnchangedPolar should not modify polar regardless of altitude."""
    modifier = UnchangedPolar()
    for altitude in [0.0, 1000.0, 10000.0]:
        fp = FlightPoint(altitude=altitude)
        result = modifier.modify_polar(polar, fp)
        assert result is polar
        assert_allclose(
            result.definition_cd,
            polar.definition_cd,
        )


def _ground_effect_modifier():
    """Return a GroundEffectRaymer instance with standard test parameters."""
    return GroundEffectRaymer(
        span=34.5,
        landing_gear_height=2.5,
        induced_drag_coefficient=0.034,
        k_winglet=1.0,
        k_cd=1.0,
    )


def test_modify_polar_computes_drag_increase(polar, flight_point):
    """GroundEffectRaymer should compute drag per Raymer's formula.

    Reference: 'Aircraft Design A conceptual approach', D. Raymer p304.
    """
    modifier = _ground_effect_modifier()
    result = modifier.modify_polar(polar, flight_point)

    # Manually compute expected values using the same formula
    span = modifier.span
    h_b = (
        span * 0.1
        + modifier.landing_gear_height
        + flight_point.altitude
        - modifier.ground_altitude
    ) / span
    k_ground = 33.0 * h_b**1.5 / (1 + 33.0 * h_b**1.5)
    cd_ground = (
        modifier.induced_drag_coefficient
        * polar.definition_cl**2
        * modifier.k_winglet
        * modifier.k_cd
        * (k_ground - 1)
    )
    expected_cd = polar.definition_cd + cd_ground

    assert_allclose(result.definition_cl, polar.definition_cl)
    assert_allclose(result.definition_alpha, polar.definition_alpha)
    assert_allclose(result.definition_cd, expected_cd)


def test_modify_polar_high_altitude_near_zero_effect(polar):
    """At high altitude, ground effect vanishes and CD approaches original values."""
    modifier = _ground_effect_modifier()
    fp_high = FlightPoint(altitude=1000.0)
    result = modifier.modify_polar(polar, fp_high)

    h_b = (
        modifier.span * 0.1
        + modifier.landing_gear_height
        + fp_high.altitude
        - modifier.ground_altitude
    ) / modifier.span
    k_ground = 33.0 * h_b**1.5 / (1 + 33.0 * h_b**1.5)
    cd_ground = (
        modifier.induced_drag_coefficient
        * polar.definition_cl**2
        * modifier.k_winglet
        * modifier.k_cd
        * (k_ground - 1)
    )
    expected_cd = polar.definition_cd + cd_ground

    assert_allclose(result.definition_cl, polar.definition_cl)
    assert_allclose(result.definition_cd, expected_cd, rtol=1e-10)
    # rtol=1e-10: verifying exact reproduction of the analytical formula
    # CD should be very close to original at high altitude
    assert_allclose(result.definition_cd, polar.definition_cd, rtol=1e-3)
    # rtol=1e-3: ground effect is negligible at 1000m altitude


def test_modify_polar_returns_new_polar_object(polar, flight_point):
    """modify_polar should return a new Polar instance, not modify the original."""
    modifier = _ground_effect_modifier()
    original_cd = polar.definition_cd.copy()
    result = modifier.modify_polar(polar, flight_point)
    assert result is not polar
    # Original polar should be unchanged
    assert_allclose(polar.definition_cd, original_cd)


def test_modify_polar_with_ground_altitude(polar):
    """ground_altitude parameter should shift the effective ground level."""
    modifier_no_ground = GroundEffectRaymer(
        span=34.5,
        landing_gear_height=2.5,
        induced_drag_coefficient=0.034,
        k_winglet=1.0,
        k_cd=1.0,
        ground_altitude=0.0,
    )
    modifier_with_ground = GroundEffectRaymer(
        span=34.5,
        landing_gear_height=2.5,
        induced_drag_coefficient=0.034,
        k_winglet=1.0,
        k_cd=1.0,
        ground_altitude=5.0,
    )
    fp_ground = FlightPoint(altitude=0.0)
    result_ground = modifier_with_ground.modify_polar(polar, fp_ground)
    result_no_ground = modifier_no_ground.modify_polar(polar, fp_ground)
    # Results should differ because ground_altitude changes h_b
    assert not np.allclose(
        result_ground.definition_cd,
        result_no_ground.definition_cd,
        rtol=1e-3,
        atol=1e-3,
    )
    modifier_high_ground = GroundEffectRaymer(
        span=34.5,
        landing_gear_height=2.5,
        induced_drag_coefficient=0.034,
        k_winglet=1.0,
        k_cd=1.0,
        ground_altitude=1000.0,
    )
    fp_altitude = FlightPoint(altitude=1000.0)
    result_ground = modifier_high_ground.modify_polar(polar, fp_altitude)
    # At high altitude, ground altitude difference should not impact the polar
    assert_allclose(
        result_ground.definition_cd,
        result_no_ground.definition_cd,
        rtol=1e-10,
        atol=1e-10,
    )


class TestRegister:
    """Tests for polar modifier registration and retrieval."""

    def test_register_and_get_class(self):
        """Registered polar modifiers should be retrievable by keyword."""
        none_class = RegisterPolarModifier.get_class("none")
        assert none_class is not None
        assert issubclass(none_class, AbstractPolarModifier)

        ground_class = RegisterPolarModifier.get_class("ground_effect_raymer")
        assert ground_class is not None
        assert issubclass(ground_class, AbstractPolarModifier)

    def test_get_classes_contains_all(self):
        """get_classes should return all registered polar modifiers."""
        classes = RegisterPolarModifier.get_classes()
        assert "none" in classes
        assert "ground_effect_raymer" in classes

    def test_get_unknown_class_raises(self):
        """get_class should raise FastUnknownMissionElementError for unknown keyword."""
        with pytest.raises(FastUnknownMissionElementError):
            RegisterPolarModifier.get_class("nonexistent_modifier")

    def test_register_decorator(self):
        """The @RegisterPolarModifier decorator should register the class."""

        @RegisterPolarModifier("test_modifier")
        class TestModifier(AbstractPolarModifier):
            def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
                return polar

        retrieved = RegisterPolarModifier.get_class("test_modifier")
        assert retrieved is TestModifier


class TestBoundaryCases:
    """Tests for boundary and edge-case inputs."""

    def test_modify_polar_zero_span_raises_zero_division(self, polar):
        """Zero span must raise ZeroDivisionError due to h_b computation (h_b = .../span)."""
        modifier = GroundEffectRaymer(
            span=0.0,
            landing_gear_height=2.5,
            induced_drag_coefficient=0.034,
            k_winglet=1.0,
            k_cd=1.0,
        )
        fp = FlightPoint(altitude=1.0)
        with pytest.raises(ZeroDivisionError):
            modifier.modify_polar(polar, fp)

    def test_modify_polar_negative_altitude_nan_effect(self, polar):
        """Robust to negative altitude values."""
        modifier = GroundEffectRaymer(
            span=34.5,
            landing_gear_height=2.5,
            induced_drag_coefficient=0.034,
            k_winglet=1.0,
            k_cd=1.0,
            ground_altitude=1000.0,
        )
        fp = FlightPoint(altitude=-10.0)
        result = modifier.modify_polar(polar, fp)

        assert not np.any(np.isnan(result.definition_cd))

    def test_modify_polar_negative_cl(self, polar, flight_point):
        """Negative CL squared yields same ground effect as positive CL of same magnitude."""
        modifier = _ground_effect_modifier()
        polar_neg_cl = Polar(
            np.array([-0.5, -1.0, -1.5]),
            polar.definition_cd,
            polar.definition_alpha,
        )
        result_neg = modifier.modify_polar(polar_neg_cl, flight_point)
        polar_pos_cl = Polar(
            np.array([0.5, 1.0, 1.5]),
            polar.definition_cd,
            polar.definition_alpha,
        )
        result_pos = modifier.modify_polar(polar_pos_cl, flight_point)
        # cd_ground is proportional to CL**2, so negative and positive CL of same
        # magnitude should produce the same result
        assert_allclose(
            result_neg.definition_cd,
            result_pos.definition_cd,
            rtol=1e-10,
        )
