.. _polar-modifier:

####################
Using a polar modifier
####################

A **polar modifier** is a way to dynamically modify the aerodynamic polar during a mission computation.
It is useful for modelling effects that change the drag based on flight conditions, such as ground effect.

The base class for polar modifiers is
:class:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier`.
A polar modifier must implement the :meth:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier.modify_polar`
method, which takes the current polar and the current flight point, and returns a modified polar.

To make a polar modifier available in a mission definition file, the class must be registered
using the :class:`~fastoad.models.performances.mission.polar_modifier.RegisterPolarModifier` decorator.
See the :ref:`Polar module documentation <polar>` for the full Python API.


***************
Available modifiers
***************

The following polar modifiers are available out of the box:

    - **none** (``UnchangedPolar``): applies no modification. This is the default behaviour
      when no modifier is specified.
    - **ground_effect_raymer** (``GroundEffectRaymer``): evaluates the drag increase due to
      ground effect using Raymer's model (ref: *Aircraft Design: A Conceptual Approach*, D. Raymer, p. 304).
      Requires the fields ``span``, ``landing_gear_height``, ``induced_drag_coefficient``,
      ``k_winglet``, ``k_cd``, and optionally ``ground_altitude``.


************************************
Registering a custom polar modifier
************************************

To create and register a custom polar modifier, inherit from
:class:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier` and use the
:class:`~fastoad.models.performances.mission.polar_modifier.RegisterPolarModifier` decorator:

.. code-block:: python

    from dataclasses import dataclass
    import fastoad.api as oad
    from fastoad.models.performances.mission.polar_modifier import AbstractPolarModifier, RegisterPolarModifier
    from fastoad.models.performances.mission.polar import Polar
    from fastoad.model_base.flight_point import FlightPoint

    @RegisterPolarModifier("my_custom_modifier")
    @dataclass
    class MyCustomModifier(AbstractPolarModifier):
        """My custom polar modifier."""

        def modify_polar(self, polar: Polar, flight_point: FlightPoint) -> Polar:
            # ... compute modified polar ...
            return polar


*****************************
Using a polar modifier in the
        mission definition file
*****************************

Once registered, a polar modifier can be used in the mission definition file by specifying it
in the ``modifier`` sub-key of the ``polar`` parameter:

.. code-block:: yaml

    polar:
      CL: data:aerodynamics:aircraft:takeoff:CL
      CD: data:aerodynamics:aircraft:takeoff:CD
      modifier:
        name: my_custom_modifier
        # ... modifier-specific parameters ...

The same modifier can also be specified at the segment level using the ``polar_modifier`` parameter:

.. code-block:: yaml

    phases:
      some_phase:
        parts:
        - segment: some_segment
          polar:
            CL: data:aerodynamics:aircraft:takeoff:CL
            CD: data:aerodynamics:aircraft:takeoff:CD
          polar_modifier:
            name: ground_effect_raymer
            span: data:geometry:aircraft:wing:span
            landing_gear_height: data:geometry:landing_gear:main:extended_height
            induced_drag_coefficient: 1.0
            k_winglet: 1.0
            k_cd: 1.0


.. seealso::

    :ref:`The Polar module documentation <polar>` for the Python API,
    and :ref:`Adding segment types <adding-segments>` for the segment extensibility mechanism.
