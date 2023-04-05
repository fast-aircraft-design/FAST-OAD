"""Base for macro-segments."""
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
from abc import ABCMeta
from dataclasses import dataclass, field, fields, make_dataclass

from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.models.performances.mission.base import FlightSequence


@dataclass
class MacroSegmentBase(FlightSequence):
    """
    Base class for macro-segments.

    A macro-segment is a sequence of flight segments. Parameters of the macro-segment drive the
    parameters of aggregated segments.

    A field value will be applied to all segments that have the concerned field. The exception is
    the `target` field, that is applied only on last segment.

    This class is expected to be used through :class:`MacroSegmentMeta`. It sets the basic
    mechanism for aggregating flight segments.

    Derived classes are expected to have dataclass fields that match dataclass fields
    of aggregated segment classes.
    """

    #: Target flight point for end of takeoff
    target: FlightPoint = MANDATORY_FIELD

    #: List of segment classes that will compose this macro-segment.
    cls_sequence = []

    # Flag that is set to True after instantiation is finished.
    _initialized: bool = field(default=False, init=False)

    # Flag that is set to True during sequence building.
    _building: bool = field(default=False, init=False)

    def __post_init__(self):
        self.build_sequence()
        self._building = False
        self._initialized = True

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        # Here we build the sequence after each field modification, to ensure any
        # field values will be taken into account, whenever it is set.
        if key != "_building" and self._initialized and not self._building:
            self._building = True

            # Rebuild the sequence after this update of value.
            self.build_sequence()
            self._building = False

    def build_sequence(self):
        """
        Instantiates all segments, using dataclass field values of this macro-segment.

        Since only target of the last segment is set (using target of this macro-segment),
        derived classes should overload this method to manage at least targets of intermediate
        segments.

        Note: this method is called each time a dataclass field value is modified.
        """
        self.clear()

        for segment_class in self.cls_sequence:
            segment_field_names = {
                f.name for f in fields(segment_class) if not f.name.startswith("_")
            }
            segment_kwargs = {
                name: value
                for name, value in dict(
                    (cls_field.name, getattr(self, cls_field.name)) for cls_field in fields(self)
                ).items()
                if name in segment_field_names
            }
            segment_kwargs["target"] = FlightPoint()
            self.append(segment_class(**segment_kwargs))

        self[-1].target = self.target


class MacroSegmentMeta(ABCMeta):
    """
    Metaclass for macro-segments.

    It should be used with ::

        >>> class TakeOffSequence( metaclass=MacroSegmentMeta,
        >>>                        cls_sequence=[...],
        >>>                      ):

    It will make so that the created class will have dataclass fields that match
    dataclass fields of all classes in 'cls_sequence'.
    """

    def __new__(mcs, cls_name, bases, attrs, *, cls_sequence=None):
        name = cls_name + "___Base"
        cls_fields = []
        field_names = set()
        for segment_class in cls_sequence:
            for segment_field in fields(segment_class):
                if not segment_field.name.startswith("_") and segment_field.name not in field_names:
                    field_names.add(segment_field.name)
                    cls_fields.append((segment_field.name, segment_field.type, segment_field))
        base_cls = make_dataclass(name, cls_fields)

        cls = super().__new__(mcs, cls_name, (MacroSegmentBase, base_cls, *bases), attrs)
        cls.cls_sequence = cls_sequence

        return cls
