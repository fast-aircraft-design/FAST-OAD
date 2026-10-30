.. _polar-modifier:

###############################
Polar and polar modifications
###############################

The aerodynamic polar links the lift coefficient (:math:`C_L`) of the aircraft to
its drag coefficient (:math:`C_D`). In the FAST-OAD mission module, each
:ref:`flight segment<flight-segments>` receives its polar through the
:code:`polar` parameter of the :ref:`mission definition file<mission-definition>`,
and uses it at every time step to compute lift and drag.

The polar may change during the computation, for instance when the aircraft flies
close to the ground: this is the purpose of a **polar modifier**. This page shows
how to use the :class:`~fastoad.models.performances.mission.polar.Polar` class, how
to apply a provided polar modifier in a mission file, and how to write your own.

.. contents::
   :local:
   :depth: 2


.. _polar-class:

Using the Polar class
#####################

A :class:`~fastoad.models.performances.mission.polar.Polar` instance is built from
three arrays of the same length:

.. list-table::
   :header-rows: 1

   * - Array
     - Content
     - Unit
   * - :code:`cl`
     - lift coefficients (:math:`C_L`) used to define the polar
     - unitless
   * - :code:`cd`
     - drag coefficients (:math:`C_D`) matching :code:`cl`
     - unitless
   * - :code:`alpha`
     - angles of attack matching :code:`cl`. Optional.
     - rad

The instance then provides:

- :meth:`~fastoad.models.performances.mission.polar.Polar.cd`: drag coefficient
  from a lift coefficient, by quadratic interpolation of the definition data,
- :meth:`~fastoad.models.performances.mission.polar.Polar.cl`: lift coefficient
  from an angle of attack, by linear interpolation (only if :code:`alpha` was
  provided, otherwise a :class:`ValueError` is raised),
- :attr:`~fastoad.models.performances.mission.polar.Polar.optimal_cl`: the lift
  coefficient giving the best lift-to-drag ratio,
- :attr:`~fastoad.models.performances.mission.polar.Polar.definition_cl`,
  :attr:`~fastoad.models.performances.mission.polar.Polar.definition_cd` and
  :attr:`~fastoad.models.performances.mission.polar.Polar.definition_alpha`: the
  arrays used for defining the polar.

.. code:: python

    import numpy as np

    import fastoad.api as oad

    polar = oad.Polar(
        cl=np.array([0.5, 1.0, 1.5]),
        cd=np.array([0.01, 0.035, 0.07]),
        alpha=np.array([0.0, 0.1, 0.2]),
    )

    cd_at_cl_1 = polar.cd(1.0)     # drag coefficient for CL = 1.0
    cl_at_alpha = polar.cl(0.15)   # lift coefficient for alpha = 0.15 rad
    best_ld_cl = polar.optimal_cl  # CL giving the best CL/CD

.. note::

    The interpolations extrapolate outside the definition range instead of raising
    an error, and the :math:`C_D` interpolation is quadratic, so at least three
    points are needed to define a polar.

In a mission definition file, the polar is described with variable names instead of
Python objects: see :ref:`the polar parameter<segment-parameter-polar>`.


Where to declare the polar
**************************

A polar is declared in the mission definition file, either at the level of a
**phase** (it then applies to all its parts) or at the level of a
**part/segment**, where it overrides the value given by the phase::

    phases:
      climb:
        engine_setting: max_climb
        polar: data:aerodynamics:aircraft:high_speed   # applies to all parts
        parts:
          - segment: altitude_change
            target:
              altitude: 10000.
          - segment: cruise
            polar:                                     # overrides the phase value
              CL: data:aerodynamics:aircraft:cruise:CL
              CD: data:aerodynamics:aircraft:cruise:CD

The values may be given in three ways:

.. list-table::
   :header-rows: 1

   * - Way
     - Example
     - When to use it
   * - numbers
     - :code:`CL: [0.0, 0.5, 1.0]` and :code:`CD: [0.01, 0.03, 0.12]`
     - quick test, or a single fixed polar
   * - variable names
     - :code:`CL: data:aerodynamics:aircraft:high_speed:CL`
     - usual way: the polar is computed by another discipline or read in the data file
   * - common prefix
     - :code:`polar: data:aerodynamics:aircraft:high_speed`
     - shortcut when the variables end with :code:`:CL` and :code:`:CD`

The :code:`alpha` sub-key is optional. It is needed only by the segments that
compute the lift coefficient from the angle of attack, such as the takeoff
segments.

For a segment built from Python, no file is involved: the polar is simply given as
a :class:`~fastoad.models.performances.mission.polar.Polar` instance through the
:code:`polar` field of the segment.


.. _polar-modifier-usage:

Applying a polar modifier
#########################

A polar modifier receives the polar of the segment and the current flight point,
and returns the polar to be used for this time step:

.. code:: python

    modified_polar = polar_modifier.modify_polar(polar, flight_point)

Modifiers derive from
:class:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier`
and implement
:meth:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier.modify_polar`.
They are called at **every time step**, so the modification must stay cheap, and
they must return a **new** :class:`~fastoad.models.performances.mission.polar.Polar`
instance instead of changing the given one.

Every time-step segment has a :code:`polar_modifier` attribute, which is an
:class:`~fastoad.models.performances.mission.polar_modifier.UnchangedPolar` instance
by default. Using a modifier from Python therefore amounts to assigning this
attribute before running the segment.

FAST-OAD provides two modifiers:

.. list-table::
   :header-rows: 1

   * - Keyword
     - Class
     - Effect
   * - :code:`none`
     - :class:`~fastoad.models.performances.mission.polar_modifier.UnchangedPolar`
     - returns the polar unchanged. This is the default.
   * - :code:`ground_effect_raymer`
     - :class:`~fastoad.models.performances.mission.polar_modifier.GroundEffectRaymer`
     - reduces the induced drag when the aircraft is close to the ground.

A modifier is selected in the mission definition file with the :code:`modifier`
sub-key of the :code:`polar` parameter (see
:ref:`the polar modifier sub-key<the-polar-modifier-sub-key>`). The other keys of
the :code:`modifier` block are the fields of the modifier class::

    phases:
      takeoff:
        parts:
          - segment: takeoff
            polar:
              CL: data:aerodynamics:aircraft:takeoff:CL
              CD: data:aerodynamics:aircraft:takeoff:CD
              alpha: data:aerodynamics:aircraft:takeoff:AoA
              modifier:
                name: ground_effect_raymer
                span:
                  value: data:geometry:wing:span
                  unit: m
                landing_gear_height:
                  value: data:geometry:landing_gear:height
                  unit: m
                induced_drag_coefficient:
                  value: data:aerodynamics:aircraft:low_speed:CD:induced:coefficient
                k_winglet:
                  value: tuning:aerodynamics:aircraft:high_speed:CD:winglet_effect:k
                k_cd:
                  value: tuning:aerodynamics:aircraft:high_speed:CD:k

.. note::

    The parameters of a modifier are passed as plain numbers to the fields of its
    class. Lengths must therefore be provided in metres, the unit used for
    altitudes in the mission computation.

This mission can be found in the test data of FAST-OAD
(:code:`test_mission_takeoff.yml`), next to a second mission that uses the same
polar without any modifier, so that the two can be compared.


Ground effect model
*******************

The :code:`ground_effect_raymer` modifier is based on Raymer's model
:cite:`Raymer1992`. It computes a ground proximity factor from the height of the
wing above ground, normalised by the wing span, and applies it to the induced drag:

.. math::

    h_b = \frac{\left|0.1\,b + h_{gear} + z - z_{ground}\right|}{b}

    k_{ground} = \frac{33\,h_b^{1.5}}{1 + 33\,h_b^{1.5}}

    C_D = C_{D,0} + k_{cd}\,k_{winglet}\,C_L^{2}\,(k_{ground} - 1)

with:

- :math:`b` the wing span (m), field :code:`span`,
- :math:`h_{gear}` the height of the main landing gear (m), field
  :code:`landing_gear_height`,
- :math:`z` the altitude of the flight point (m), read from the
  :class:`~fastoad.model_base.FlightPoint` at each time step,
- :math:`z_{ground}` the altitude of the ground (m), field :code:`ground_altitude`
  (default :code:`0.0`),
- :math:`C_{D,0}` the drag coefficient of the unmodified polar, and :math:`C_L` the
  lift coefficient (both unitless),
- :math:`k_{cd}` and :math:`k_{winglet}` the tuning coefficients (unitless), fields
  :code:`k_cd` and :code:`k_winglet`,
- the coefficient of :math:`C_L^{2}` being the field
  :code:`induced_drag_coefficient` (unitless).

Since :math:`k_{ground}` is lower than 1 near the ground, the correction term
:math:`(k_{ground} - 1)` is negative and the drag coefficient is **reduced**. The
factor tends to 1 when the aircraft goes away from the ground, so the effect
vanishes at high altitude.

Assumptions and limits:

- the model corrects the induced drag only, through the term proportional to
  :math:`C_L^{2}`,
- the height of the wing is approximated by :math:`0.1\,b + h_{gear}`, that is, a
  fraction of the span plus the landing gear height,
- the absolute value of the height above ground is used, so the model stays defined
  when the flight point is below the ground altitude,
- a zero span is not allowed, as :math:`h_b` is divided by the span,
- for :class:`~fastoad.models.performances.mission.segments.time_step_base.AbstractTakeOffSegment`,
  the ground altitude is automatically set to the altitude at the beginning of the
  segment, so :code:`ground_altitude` does not need to be provided in this case.


.. _polar-modifier-new:

Writing a new polar modifier
############################

A new modifier is a dataclass that derives from
:class:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier`
and is declared with the
:class:`~fastoad.models.performances.mission.polar_modifier.RegisterPolarModifier`
decorator. The keyword given to the decorator is the :code:`name` to use in the
mission file, and the fields of the dataclass are the parameters of the
:code:`modifier` block::

    from dataclasses import dataclass

    import fastoad.api as oad


    @oad.RegisterPolarModifier("drag_increase_with_altitude")
    @dataclass
    class DragIncreaseWithAltitude(oad.AbstractPolarModifier):
        """Adds a drag increment that grows with the altitude."""

        #: Drag increment per metre of altitude (unitless)
        increment_per_meter: float

        def modify_polar(self, polar: oad.Polar, flight_point: oad.FlightPoint) -> oad.Polar:
            """Return a polar with an altitude-dependent drag increase.

            :param polar: the polar of the segment
            :param flight_point: the current flight point (altitude in m)
            :return: a new polar with modified drag coefficients
            """
            extra_cd = self.increment_per_meter * abs(flight_point.altitude)
            return oad.Polar(
                polar.definition_cl,
                polar.definition_cd + extra_cd,
                polar.definition_alpha,
            )

Once this code is imported, the keyword :code:`drag_increase_with_altitude` can be
used as :code:`name` in a mission file, and the class can be retrieved from Python:

.. code:: python

    import fastoad.api as oad

    modifier_class = oad.RegisterPolarModifier.get_class("drag_increase_with_altitude")
    all_modifiers = oad.RegisterPolarModifier.get_classes()  # dict: keyword -> class

.. warning::

    A class that does not derive from
    :class:`~fastoad.models.performances.mission.polar_modifier.AbstractPolarModifier`
    is not registered. Asking for an unknown keyword raises a
    :class:`fastoad.models.performances.mission.exceptions.FastUnknownMissionElementError`.


Where to put the code
*********************

The modifier must be in a Python module that is imported **before** the mission file
is read, because the keyword exists only once the class has been registered:

- **in a FAST-OAD plugin** (recommended as soon as the modifier is shared with other
  users): put the module in the :code:`models` package of the plugin, described in
  :ref:`How to add custom OpenMDAO modules to FAST-OAD as a plugin<add-plugin>`.
  Every module of this package is imported when the plugin is loaded, so the
  keyword is available as soon as the plugin is installed,
- **in a script or a notebook**: import the module yourself before building or
  running the mission.

The modifiers that are available are the ones listed by
:meth:`~fastoad.models.performances.mission.polar_modifier.RegisterPolarModifier.get_classes`,
and their keywords are the only values accepted as :code:`name` in a
:code:`modifier` block.

.. seealso::

    :ref:`Adding segment types <adding-segments>` for the same registration
    mechanism applied to flight segments, and
    :ref:`the mission definition file<mission-definition>` for the other parameters
    of a segment.


References
##########

.. bibliography::
