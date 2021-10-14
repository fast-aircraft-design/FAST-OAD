"""
Management of 2D wing profiles
"""
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

import operator
from collections import namedtuple
from typing import Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

Coordinates2D = namedtuple("Coordinates2D", ["x", "y"])

X = "x"
Z = "z"
THICKNESS = "thickness"


class Profile:
    """Class for managing 2D wing profiles
    :param chord_length:
    :param x:
    :param y:
    """

    # pylint: disable=invalid-name  # X and Z are valid names in this context

    def __init__(self, chord_length: float = 0.0):

        self._rel_mean_line_and_thickness = pd.DataFrame(columns=[X, Z, THICKNESS])
        """
        Data of mean line and thickness, computed after inputs of :meth:`set_points`_.

        DataFrame keys are 'x', 'z' and 'thickness'.
        - 'x' and 'z' are relative to chord_length
        - 'thickness' is relative to max thickness (and given according to 'x')
        """

        self.chord_length: float = chord_length
        """ in meters """

        self._max_relative_thickness: float = 0.0
        """ max thickness / chord length"""

    @property
    def thickness_ratio(self) -> float:
        """thickness-to-chord ratio"""
        return self._max_relative_thickness

    @thickness_ratio.setter
    def thickness_ratio(self, value: float):

        # FIXME: mean line is modified accordingly to conform to legacy algorithm, but it
        #        is questionable
        if self._max_relative_thickness != 0.0:
            coeff = value / self._max_relative_thickness
            self._rel_mean_line_and_thickness[Z] *= coeff
        self._max_relative_thickness = value

    def set_points(
        self,
        x: Sequence,
        z: Sequence,
        keep_chord_length: bool = True,
        keep_relative_thickness: bool = True,
    ):
        """
        Sets points of the 2D profile.

        Provided points are expected to be in order around the profile (clockwise
        or anti-clockwise).

        :param x: in meters
        :param z: in meters
        :param keep_relative_thickness:
        :param keep_chord_length:
        """

        x = np.asarray(x)

        # Separate upper surface from lower surface (easier for computation
        # of thickness and mean line)
        upper, lower = self._create_upper_lower_sides(x, z)

        # Upper and lower sides are defined, we can compute mean line and thickness
        chord_length, max_thickness = self._compute_mean_line_and_thickness(upper, lower)

        if not keep_chord_length or self.chord_length == 0.0:
            self.chord_length = chord_length
        if not keep_relative_thickness or self.thickness_ratio == 0.0:
            self.thickness_ratio = max_thickness / chord_length

    def get_mean_line(self) -> pd.DataFrame:
        """Point set of mean line of the profile.

        DataFrame keys are 'x' and 'z', given in meters.
        """
        mean_line = self._rel_mean_line_and_thickness[[X, Z]] * self.chord_length
        return mean_line

    def get_relative_thickness(self) -> pd.DataFrame:
        """Point set of relative thickness of the profile.

        DataFrame keys are 'x' and 'thickness' and are relative to chord_length.
        'x' is from 0. to 1.
        """
        return self._rel_mean_line_and_thickness[[X, THICKNESS]] * [1.0, self.thickness_ratio]

    def get_upper_side(self) -> pd.DataFrame:
        """Point set of upper side of the profile.

        DataFrame keys are 'x' and 'z', given in meters.
        """
        return self._get_side_points(operator.add)

    def get_lower_side(self) -> pd.DataFrame:
        """Point set of lower side of the profile.

        DataFrame keys are 'x' and 'z', given in meters.
        """
        return self._get_side_points(operator.sub)

    def get_sides(self) -> pd.DataFrame:
        """Point set of the whole profile

        Points are given from trailing edge to trailing edge, starting by upper side.
        """
        return pd.concat(
            [self.get_upper_side().sort_values(by=X, ascending=False), self.get_lower_side()[1:]]
        )

    def _get_side_points(self, operator_) -> pd.DataFrame:
        """
        Computes upper or lower side points.

        operator_ ==  operator.add() -> upper side
        operator_ ==  operator.sub() -> lower side
        """
        mean_line = self._rel_mean_line_and_thickness[[X, Z]]
        half_thickness = pd.DataFrame().reindex_like(mean_line)
        half_thickness[X] = 0.0
        half_thickness[Z] = (
            self._rel_mean_line_and_thickness[THICKNESS] / 2.0 * self.thickness_ratio
        )
        points = operator_(mean_line, half_thickness) * self.chord_length
        return points

    def _compute_mean_line_and_thickness(
        self, upper_side_points, lower_side_points
    ) -> Tuple[float, float]:
        """
        Computes mean line and thickness from upper_side_points and lower_side_points.

        Fills self._rel_mean_line_and_thickness with relative values.
        Returns actual chord length and maximum thickness (in meters)
        """
        x = (
            lower_side_points[X]
            .append(upper_side_points[X])
            .sort_values()
            .drop_duplicates()
            .reset_index(drop=True)
        )

        interp_lower = interp1d(lower_side_points[X], lower_side_points[Z], kind="quadratic")
        interp_upper = interp1d(upper_side_points[X], upper_side_points[Z], kind="quadratic")
        z_sides = pd.DataFrame({"z_lower": interp_lower(x), "z_upper": interp_upper(x)})
        z = z_sides.mean(axis=1)
        thickness = z_sides.diff(axis=1).iloc[:, -1]

        chord_length = np.max(x) - np.min(x)
        max_thickness = np.max(thickness)
        self._rel_mean_line_and_thickness = pd.DataFrame(
            {X: x / chord_length, Z: z / chord_length, THICKNESS: thickness / max_thickness}
        )
        return chord_length, max_thickness

    @staticmethod
    def _create_upper_lower_sides(x: Sequence, z: Sequence) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """returns upper side points and lower side points using provided x and z"""
        # FIXME: leading and trailing edges are located roughly.
        i_leading_edge = np.argmin(x)
        i_trailing_edge = np.argmax(x)

        i1 = min(i_leading_edge, i_trailing_edge)
        i2 = max(i_leading_edge, i_trailing_edge)
        side1 = pd.DataFrame({X: x[i1 : i2 + 1], Z: z[i1 : i2 + 1]})
        side2_1 = pd.DataFrame({X: x[i2:], Z: z[i2:]})
        side2_2 = pd.DataFrame({X: x[: i1 + 1], Z: z[: i1 + 1]})
        side2 = pd.concat((side2_1, side2_2)).reset_index(drop=True)

        side1.sort_values(by=X, inplace=True)
        side2.sort_values(by=X, inplace=True)

        # At this point, side2 and side1 have the same last point, but in in case of thick
        # trailing edge, it could lead to side2 having 2 points for the same X, which will be
        # harmful in next operations.
        # In that case, we simply have to remove last point of side2, as it actually belongs to
        # side1.
        if side2[X].iloc[-1] == side2[X].iloc[-2]:
            side2 = side2.iloc[:-1]

        if np.max(side1[Z]) > np.max(side2[Z]):
            upper_side_points = side1
            lower_side_points = side2
        else:
            upper_side_points = side2
            lower_side_points = side1

        upper_side_points.drop_duplicates(inplace=True)
        lower_side_points.drop_duplicates(inplace=True)
        upper_side_points.reset_index(drop=True, inplace=True)
        lower_side_points.reset_index(drop=True, inplace=True)

        return upper_side_points, lower_side_points
