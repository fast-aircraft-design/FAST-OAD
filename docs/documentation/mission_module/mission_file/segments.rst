.. _flight-segments:



###############
Flight segments
###############

Flight segments are the Python-implemented, base building blocks for the mission definition.

They can be used as parts in :ref:`phase <phase-section>` definition.

A segment simulation starts at the flight parameters (altitude, speed, mass...) reached at
the end of the previous simulated segment.
The segment simulation ends when its **target** is reached (or if it cannot be reached).

Sections:

.. contents::
   :local:
   :depth: 1



*************
Segment types
*************

In the following, the description of each segment type links to the documentation of the
Python implementation.
All parameters of the Python constructor can be set in the mission file (except for
:code:`propulsion` and :code:`reference_area` that are set within the mission module).
Most of these parameters are scalars and can be set as described :ref:`here<setting-values>`.
The segment target is a special parameter, detailed in :ref:`further section<segment-parameter-target>`.
Other special parameters are detailed in :ref:`last section<segment-special-parameters>`.



Available segments are:

.. contents::
   :local:
   :depth: 1


.. _segment-start:

:code:`start` segment
=====================

.. versionadded:: 1.4.0

.. list-attributes-for:: start

:code:`start` is a special segment to be used at the beginning of the mission definition to
specify the starting point of the mission, preferably by defining variables so it can be
controlled from FAST-OAD input file.

With no :code:`start` specified, the mission is assumed to start at altitude 0.0, speed 0.0.


.. note::

    The :code:`start` segment allows to define the aircraft mass at the beginning of the mission.
    Yet it is possible to define aircraft mass at some intermediate phase (e.g. takeoff) using
    the `mass_input segment`_.

.. important::

    **In any case, a variable for input mass has to be defined once and
    only once in the whole mission.**


**Example:**

.. code-block:: yaml

    phases:
      start_phase:
        - segment: start
          target:
            true_airspeed: 0.0                # hard-coded value
            altitude:
              value: my:altitude:variable     # variable definition WITH associated default value
              unit: ft
              default: 100.0
            mass:
              value: my:mass:variable         # variable definition WITHOUT associated default value
              unit: kg                        # (will have to be set by another module or by FAST-OAD
                                            #  input file)

    ...

    missions:
      main_mission:
        parts:
          - phase: start_phase
          - ...


.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.start.Start`


.. _segment-mass-input:

:code:`mass_input` segment
==========================

.. versionadded:: 1.4.0

.. list-attributes-for:: mass_input

The `start segment`_ allows to define aircraft mass at the beginning of the mission, but it
is sometimes needed to define the aircraft mass at some point in the mission. The typical
example would be the need to specify a takeoff weight that is expected to be achieved after the
taxi-out phase.

The :code:`mass_input` segment is designed to address this need. It will ensure this mass is
achieved at the specify instant in the mission by setting the start mass input accordingly.



**Example:**

.. code:: yaml

    # For setting mass at the end of taxi-out:
    phases:
      taxi-out:
        parts:
          - segment: taxi
            ...
          - segment: mass_input
            target:
              mass:
                value: my:MTOW:variable
                unit: kg

.. warning::

    Currently, FAST-OAD assumes the fuel consumption before the :code:`mass_input` segment is
    independent of aircraft mass, which is considered true in a phase such as taxi. Assuming
    otherwise would require to solve an additional inner loop. Since it does not correspond to
    any use case we currently know of, it has been decided to stick to the simple case.

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.mass_input.MassTargetSegment`


.. _segment-speed-change:

:code:`speed_change` segment
============================

.. list-attributes-for:: speed_change

A :code:`speed_change` segment simulates an acceleration or deceleration flight part, at constant
altitude and thrust rate. It ends when the target speed (mach, true_airspeed or
equivalent_airspeed) is reached.

**Example:**

.. code-block:: yaml

    segment: speed_change
    polar: data:aerodynamics:aircraft:takeoff   # High-lift devices are ON
    engine_setting: takeoff
    thrust_rate: 1.0                            # Full throttle
    target:
      # altitude: constant                      # Assumed by default
      equivalent_airspeed:                      # Acceleration up to EAS = 250 knots
        value: 250
        unit: kn

.. seealso::

    Python documentation: :mod:`~fastoad.models.performances.mission.segments.registered.speed_change.SpeedChangeSegment`


.. _segment-altitude-change:

:code:`altitude_change` segment
===============================

.. list-attributes-for:: altitude_change

An :code:`altitude_change` segment simulates a climb or descent flight part at constant thrust rate.
Typically, it ends when the target altitude is reached.

But also, a target speed, or CL, can be set, while keeping another speed constant (e.g. climbing up to
Mach 0.8 while keeping equivalent_airspeed constant).

If :code:`maximum_CL` is provided, the segment will ensure no point exceeds this limit. If the
starting point already exceeds :code:`maximum_CL`, the segment is skipped and a warning is issued.
If the limit is exceeded during the segment, the target is adjusted to reach the maximum CL rather
than the original altitude target (the climb stops when the maximum CL is reached).

**Examples:**

.. code-block:: yaml

    segment: altitude_change
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: idle
    thrust_rate: 0.15                           # Idle throttle
    target:                                     # Descent down to 10000. feet at constant EAS
      altitude:
        value: 10000.
        unit: ft
      equivalent_airspeed: constant

.. code-block:: yaml

    segment: altitude_change
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: climb
    thrust_rate: 0.93                           # Climb throttle
    target:                                     # Climb up to Mach 0.78 at constant EAS
      equivalent_airspeed: constant
      mach: 0.78

.. code-block:: yaml

    segment: altitude_change
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: climb
    thrust_rate: 0.93                           # Climb throttle
    target:                                     # Climb at constant Mach up to the flight
      mach: constant                            #  level that provides maximum lift/drag
      altitude:                                 #  at current mass.
        value: optimal_flight_level
    maximum_CL: 0.6                             # Limitation on lift coefficient.
                                                # The altitude will be limited to the closest
                                                # flight level within the CL limitation.

.. code-block:: yaml

    segment: altitude_change
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: climb
    thrust_rate: 0.93                           # Climb throttle
    target:
      mach: constant                            # Climb at constant Mach until target CL
      CL: 0.55                                  # is reached.


.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.altitude_change.AltitudeChangeSegment`


.. _segment-cruise:

:code:`cruise` segment
======================

.. list-attributes-for:: cruise

A :code:`cruise` segment simulates a flight part at constant speed and altitude, and regulated
thrust rate (drag is compensated).

Optionally, target altitude can be set to :code:`optimal_flight_level`. In such case, cruise will
be preceded by a climb segment that will put the aircraft at the altitude that will minimize the
fuel consumption for the whole segment (including the prepending climb).
This option is available because the :ref:`segment-altitude-change` segment can reach an altitude
that will optimize the lift/drag ratio at current mass, but the obtained altitude will not
guaranty an optimal fuel consumption for the whole cruise.

.. note::

  When using mission files, the :code:`climb_segment` attribute is automatically populated when using a route segment with a climb phase, and the climb segment is automatically prepended to the
  :code:`RangedRoute` with the last climb phase before cruise. Explicit definition is only needed
  when using :code:`ClimbAndCruiseSegment` directly in Python code or when there is need to modify the climb segment before the cruise.

It ends when the target ground distance is covered (including the distance covered during
prepending climb, if any).

If :code:`maximum_CL` is set, the segment will avoid selecting a higher flight level when it would
exceed the maximum lift coefficient. The same limit is passed to the prepended climb segment.

**Examples:**

.. code-block:: yaml

    segment: cruise
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: cruise
    target:
      # altitude: constant                      # Not needed, because assumed by default
      ground_distance:                          # Cruise for 2000 nautical miles
        value: 2000
        unit: NM

.. code-block:: yaml

    segment: cruise
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: cruise
    target:
      altitude: optimal_flight_level            # Commands a prepending climb, id needed
      ground_distance:                          # Cruise for 2000 nautical miles
        value: 2000
        unit: NM

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.cruise.ClimbAndCruiseSegment`


.. _segment-optimal-cruise:

:code:`optimal_cruise` segment
==============================

.. list-attributes-for:: optimal_cruise

An :code:`optimal_cruise` segment simulates a cruise climb, i.e. a cruise where the aircraft
climbs gradually to keep being at altitude of maximum lift/drag ratio.

The :code:`optimal_cruise` segment can be realised at a constant lift coefficient using the parameter :code:`maximum_CL`.

Two optional altitude caps can be set for this segment:

* :code:`maximum_altitude` (in meters) caps the optimal cruise altitude.
* :code:`maximum_flight_level` (in flight levels, i.e. multiples of 100 ft) caps the altitude to
  :code:`maximum_flight_level * 100 ft`.

If both are provided, the most restrictive (lowest) cap is applied. When a cap is active, the
segment will stay at the capped altitude and reduce :code:`CL` accordingly.

It assumed the segment actually starts at altitude of maximum lift/drag ratio or the altitude given by :code:`maximum_CL`, which can be
achieved with an :ref:`segment-altitude-change` segment with :code:`optimal_altitude` as target
altitude and :code:`maximum_CL` as parameter.

.. warning::

  The :code:`optimal_cruise` segment computes the optimal altitude at its start and applies it
  immediately. If the previous segment ends at a different altitude, this creates an
  instantaneous altitude change. To avoid this discontinuity, add a climb segment with
  :code:`optimal_altitude` as target immediately before the :code:`optimal_cruise` segment.

*The common way to optimize the fuel consumption for commercial aircraft is a step climb cruise.
Such segment will be implemented in the future.*

**Example:**

.. code-block:: yaml

    segment: optimal_cruise
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    engine_setting: cruise
    maximum_CL: 0.6
    maximum_altitude: 8000.0                    # meters (optional cap)
    maximum_flight_level: 350.0                 # FL350 (optional cap)
    target:
      ground_distance:                          # Cruise for 2000 nautical miles
        value: 2000
        unit: NM

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.cruise.OptimalCruiseSegment`


.. _segment-holding:

:code:`holding` segment
=======================

.. list-attributes-for:: holding

A :code:`holding` segment simulates a flight part at constant speed and altitude, and regulated
thrust rate (drag is compensated). It ends when the target time is covered.

**Example:**

.. code-block:: yaml

    segment: holding
    polar: data:aerodynamics:aircraft:cruise    # High speed aerodynamic polar
    target:
      # altitude: constant                      # Not needed, because assumed by default
      time:
        value: 20                               # 20 minutes holding
        unit: min

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.hold.HoldSegment`


.. _segment-taxi:

:code:`taxi` segment
====================

.. list-attributes-for:: taxi

A :code:`taxi` segment simulates the mission parts between gate and takeoff or landing, at constant
thrust rate. It ends when the target time is covered.

**Example:**

.. code-block:: yaml

    segment: taxi
    thrust_rate: 0.3
    target:
      time:
        value: 300              # taxi for 300 seconds (5 minutes)

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.taxi.TaxiSegment`


.. _segment-transition:

:code:`transition` segment
==========================

.. list-attributes-for:: taxi

A :code:`transition` segment is intended to "fill the gaps" when some flight part is not available
for computation or is needed to be assessed without spending CPU time.

It can be used in various ways:

.. contents::
   :local:
   :depth: 1

Target definition
-----------------
The most simple way is specifying a target with absolute and/or relative parameters. The second and
last point of the flight segment will simply uses these values.

**Example:**

.. code-block:: yaml

    segment: transition # Rough simulation of a takeoff
    target:
      delta_time: 60            # 60 seconds after start point
      delta_altitude:           # 35 ft above start point
        value: 35
        unit: ft
      delta_mass: -80.0         # 80kg lost from start point (implicitly 80kg consumed fuel)
      true_airspeed: 85         # 85m/s at end of segment.

Usage of a mass ratio
---------------------

As seen above, it is possible to force a mass evolution of a certain amount by specifying
:code:`delta_mass`.

It is also possible to specify a mass ratio. This can be done outside the target, as a segment
parameter.

**Example:**

.. code-block:: yaml

    segment: transition # Rough climb simulation
    mass_ratio: 0.97            # Aircraft end mass will be 97% of total start mass
    target:
      altitude: 10000.
      mach: 0.78
      delta_ground_distance:    # 250 km after start point.
        value: 250
        unit: km

Reserve mass ratio
------------------

Another segment parameter is :code:`reserve_mass_ratio`. When using this parameter, another flight
point is added to computed segment, where the aircraft mass is decreased by a fraction of the mass
that remains at the end of the segment (including this reserve consumption).

Typically, it will be used as last segment to compute a reserve based on the Zero-Fuel-Weight mass.

**Example:**

.. code-block:: yaml

    segment: transition # Rough reserve simulation
    reserve_mass_ratio: 0.06
    target:
      altitude: 0.
      mach: 0.

Mass change without fuel consumption
----------------------------------

.. versionadded:: 1.8.2

Using :code:`delta_mass` allows to simulate a fuel consumption equivalent to the mass loss.

For cases where mass variation should be simulated without fuel consumption, it is possible to set
to :code:`False` the parameter :code:`fuel_is_consumed`.

**Example:**

.. code-block:: yaml

    segment: transition
    target:
      delta_mass: -100.
      fuel_is_consumed: False

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.transition.DummyTransitionSegment`


.. _segment-ground-speed-change:

:code:`ground_speed_change` segment
===================================

.. versionadded:: 1.5.0

This segment is used specifically during accelerating or decelerating parts while still on the ground.
The friction force with the ground is accounted in the equation of movements.
Whilst on the ground, the key :code:`wheels_friction` is used to define the friction coefficient.
The segment ends when the target velocity is reached.

**Example:**

.. code-block:: yaml

    segment: ground_speed_change
    wheels_friction: 0.03
    target:
      equivalent_airspeed:
        value: data:mission:operational:takeoff:Vr

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.ground_speed_change.GroundSpeedChangeSegment`


.. _segment-rotation:

:code:`rotation` segment
========================

.. versionadded:: 1.5.0

This segment is used to represent a rotation while still on the ground. This segment is specifically used for takeoff.
The specific keys are (in addition to wheel friction coefficient):

:code:`rotation_rate` in (rad/s) is the rotation speed used to realise the manoeuvre (by default 3deg/s, compliant with CS-25 )

:code:`alpha_limit` (in rad) is the maximum angle of attack possible before tail strike (by default 13.5deg).

The segment ends when lift equals weight. Therefore, no target needs to be set.

**Example:**

.. code-block:: yaml

    segment: rotation
    wheels_friction: 0.03
    rotation_rate:
      value: 0.0523
    alpha_limit:
      value: 0.3489

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.takeoff.rotation.RotationSegment`


.. _segment-end-of-takeoff:

:code:`end_of_takeoff` segment
==============================

.. versionadded:: 1.5.0

This segment is used at the end of the takeoff phase, between lift off and before reaching the safety altitude. The target sets the safety altitude.
Because this phase is quite dynamic, it is a good practice to lower the time step at least to 0.05s for a
good accuracy on takeoff distance.

**Example:**

.. code-block:: yaml

    segment: end_of_takeoff
    time_step: 0.05
    target:
      delta_altitude:
        value: 35
        unit: ft

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.takeoff.end_of_takeoff.EndOfTakeoffSegment`


.. _segment-takeoff:

:code:`takeoff` segment
=======================

.. versionadded:: 1.5.0

This segment is the sequence of `ground_speed_change segment`_, `rotation segment`_ and `end_of_takeoff segment`_.

The parameters for this segment are the same as for its 3 components, except that:

  - :code:`time_step` is used only for `ground_speed_change segment`_ and `rotation segment`_.
  - time step for `end_of_takeoff segment`_ is driven by the additional parameter :code:`end_time_step`
  - target speed at end of `ground_speed_change segment`_ is driven by the additional parameter :code:`rotation_equivalent_airspeed`
  - the target of :code:`takeoff` segment is the target of `end_of_takeoff segment`_, meaning it sets the safety altitude.

**Example:**

.. code-block:: yaml

    segment: takeoff
    wheels_friction: 0.03
    rotation_equivalent_airspeed:
      value: data:mission:operational:takeoff:Vr
    rotation_rate:
      value: 0.0523
      units: rad/s
    rotation_alpha_limit:
      value: 0.3489
      units: rad
    end_time_step: 0.05
    target:
      delta_altitude:
        value: 35
        unit: ft

.. seealso::

    Python documentation: :class:`~fastoad.models.performances.mission.segments.registered.takeoff.takeoff.TakeOffSequence`


.. _segment-special-parameters:

**************************
Special segment parameters
**************************

Most of segment parameters must be set with a unique value, which can be done in several ways,
as described :ref:`here<setting-values>`.

There are some special parameters that are detailed below.

.. contents::
   :local:
   :depth: 1


.. _segment-parameter-target:

:code:`target` parameter
=======================

.. list-segments-for:: target

The target of a flight segment is a set of parameters that drives the end of the segment simulation.

Possible target parameters are the available fields of
:class:`~fastoad.model_base.flight_point.FlightPoint`. The actually useful parameters depend on the
segment.

Each parameter can be set the :ref:`usual way<setting-values>`, generally with a numeric value or
a variable name, but it can also be a string. The most common string value is :code:`constant`
that tells the parameter value should be kept constant and equal to the start value.
In any case, please refer to the documentation of the flight segment.

Absolute and relative values
----------------------------

Amost all target parameters are considered as absolute values, i.e. the target is considered
reached if the named parameter gets equal to the provided value.

They can also be specified as relative values, meaning that the target is considered reached if the
named parameter gets equal to the provided value **added** to start value. To do so, the parameter
name will be preceded by :code:`delta_`.

**Examples:**

.. code-block:: yaml

    target:
      altitude: # Target will be reached at 35000 ft.
        value: 35000
        unit: ft

.. code-block:: yaml

    target:
      delta_altitude: # Target will be 5000 ft above the start altitude of the segment.
        value: 5000
        unit: ft

.. important::
    There are 2 exceptions : :code:`ground_distance` and :code:`time` are always considered as
    relative values. Therefore, :code:`delta_ground_distance` and :code:`delta_time` will have the
    same effect.



.. _segment-parameter-engine-setting:

:code:`engine_setting` parameter
================================

.. list-segments-for:: engine_setting

Expected value for :code:`engine_setting` are :code:`takeoff`, :code:`climb`
, :code:`cruise` or :code:`idle`

This setting can be used by a model like the "rubber engine" propulsion model
(see class `RubberEngine <https://fast-oad-cs25.readthedocs.io/en/latest/api/fastoad_cs25.models.propulsion.fuel_propulsion.rubber_engine.rubber_engine.html#fastoad_cs25.models.propulsion.fuel_propulsion.rubber_engine.rubber_engine.RubberEngine>`_).
It roughly links the "turbine inlet temperature" (a.k.a. T4) to the flight conditions.

If another propulsion model is used, this parameter may become irrelevant, and then can be omitted.


.. _segment-parameter-polar:

:code:`polar` parameter(s)
==========================

.. list-segments-for:: polar

The aerodynamic polar defines the relation between lift and drag coefficients
(respectively CL and CD).
This parameter is composed of two vectors of same size, one for CL, and one for CD.

The :code:`polar` parameter has 2 sub-keys that are :code:`CL` and :code:`CD`.

A basic example would be:

.. code-block:: yaml

    segment: cruise
    polar:
      CL: [0.0, 0.5, 1.0]
      CD: [0.01, 0.03, 0.12]

But generally, polar values will be obtained through variable names, because they
will be computed during the process, or provided in the input file. This should give:

.. code-block:: yaml

    segment: cruise
    polar:
      CL: data:aerodynamics:aircraft:cruise:CL
      CD: data:aerodynamics:aircraft:cruise:CD

Additionally, a convenience feature is proposes, which assumes CL and CD are provided
by variables with same names, except one ends with :code:`:CL` and the other one by :code:`:CD`.
In such case, providing only the common prefix is enough.

Therefore, the next example is equivalent to the previous one:

.. code-block:: yaml

    segment: cruise
    polar: data:aerodynamics:aircraft:cruise

