.. _mission-definition:

############
Mission file
############

.. contents::
   :local:
   :depth: 2

*******************
General description
*******************
A mission file describes precisely one or several missions that could be computed by
the performance model :code:`fastoad.performances.mission` of FAST-OAD.

The file format of mission files is the `YAML <https://yaml.org>`_  format.
A quick tutorial for YAML (among many ones) is available
`here <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started/>`_.

The mission definition relies on 4 concepts that are, from lowest level to the highest one:
segments, phases, routes and missions. They are summarized in this table:

.. list-table:: Mission elements
    :widths: 3 10 30
    :width: 100%
    :header-rows: 1

    * - Type
      - Parts
      - Description
    * - :ref:`segment <flight-segments>`
      - N/A
      - | The basic bricks that are provided by FAST-OAD. They are
        | described in this :ref:`specific page <flight-segments>`.
    * - :ref:`phase <phase-section>`
      - | segment(s) and/or
        | phase(s)
      - A free assembly of one or more segments and/or other phases.
    * - :ref:`route <route-section>`
      - | zero or more phase(s)
        | **one cruise segment**
        | zero or more phase(s)
      - | A route is a climb/cruise/descent sequence with a fixed range.
        | The range is achieved by adjusting the distance covered during
        | the cruise part.
    * - :ref:`mission <mission-section>`
      - | routes and/or phases
        | and/or segments
      - | A mission is what is computed by :code:`fastoad.performances.mission`.
        | Generally, it begins when engine starts and ends when engine
        | stops.

.. important::

    Starting with version 1.4.0 of FAST-OAD, any mission has to use a variable for mass input. This
    variable can be defined using the :ref:`start segment <segment-start>`, if it provides the mass at
    mission start (typically a ramp-up weight), or using the :ref:`mass_input segment <segment-mass_input>`
    otherwise (typically a takeoff weight, achieved after the taxi-out).

    In the case no variable is defined for input mass, FAST-OAD will automatically add, at the
    beginning of the mission, a taxi-out and a very simple takeoff phase
    (:ref:`transition segment <segment-transition>`) with a
    :ref:`mass_input segment <segment-mass_input>`. In that case, the input
    mass is given by the :code:`data:mission:<mission_name>:TOW` variable, which represents the
    aircraft mass just **after** takeoff.

    This addition of taxi-out, takeoff and mass input allows to keep compatibility with
    mission definitions for FAST-OAD versions earlier than 1.4.

    (Please note that takeoff weight should be actually considered as
    the mass just **before** takeoff, but this way of doing is kept for maximum
    backward-compatibility)



*************
File sections
*************

The organization of a mission definition file is organized in sections according to
above-defined concepts.

.. contents::
   :local:
   :depth: 1


.. _phase-section:

Phase definition section
************************

This section, identified by the :code:`phases` keyword, defines flight phases. A flight phase is
defined as an assembly of one or more :ref:`flight segment(s) <flight-segments>`.

Basically, a phase has a name, and a :code:`parts` attribute that contains a list of segment definitions.

Nevertheless, it is also possible to set, at phase level, the parameters that are common to several
segments of the phase.

The phase section only defines flight phases, but not their usage, that is defined
in :ref:`route <route-section>` and :ref:`mission <mission-section>` sections. Therefore, the
definition order of flight phases has no importance.

.. note::

    Some parameters may be more conveniently set at an upper level than segment-level. See
    section :ref:`factorizing-parameters` to see how.


Example:

.. code-block:: yaml

    phases:
      initial_climb:                               # Phase name
        parts:                                         # Definition of segment list
          - segment: altitude_change                   # 1st segment (climb)
            polar: data:aerodynamics:aircraft:takeoff
            thrust_rate: 1.0
            target:
              altitude:
                value: 400.
                unit: ft
              equivalent_airspeed: constant
          - segment: speed_change                      # 2nd segment (acceleration)
            polar: data:aerodynamics:aircraft:takeoff
            thrust_rate: 1.0
            target:
              equivalent_airspeed:
                value: 250
                unit: kn
          - segment: altitude_change                   # 3rd segment (climb)
            polar: data:aerodynamics:aircraft:takeoff
            thrust_rate: 0.95
            target:
              altitude:
                value: 1500.
                unit: ft
              equivalent_airspeed: constant
        climb:                                    # Phase name
          ...                                          # Definition of the phase...


.. _route-section:

Route definition section
************************

This section, identified by the :code:`routes` keyword, defines flight routes. A flight route is
defined as climb/cruise/descent sequence with a fixed range. The range is achieved by
adjusting the distance covered during the cruise part. Climb and descent phases are
computed normally.

A route is identified by its name and has 4 attributes:

    - :code:`range`: the distance to be covered by the whole route
    - :code:`climb_parts`: a list of items like :code:`phase : <phase_name>`
    - :code:`cruise_part`: a :ref:`segment <flight-segments>` definition, except that it does not
      need any target distance.
    - :code:`descent_parts`: a list of items like :code:`phase : <phase_name>`

Example:

.. code-block:: yaml

  routes:
    main_route:
      range:
        value: 3000.
        unit: NM
      climb_parts:
        - phase: initial_climb
        - phase: climb
      cruise_part:
        segment: cruise
        engine_setting: cruise
        polar: data:aerodynamics:aircraft:cruise
        target:
          altitude: optimal_flight_level
        maximum_flight_level: 340
      descent_parts:
        - phase: descent
    diversion:
      range: distance
      climb_parts:
        - phase: diversion_climb
      cruise_part:
        segment: breguet
        engine_setting: cruise
        polar: data:aerodynamics:aircraft:cruise
      descent_parts:
        - phase: descent



.. _mission-section:

Mission definition section
**************************

This is the main section. It allows to define one or several missions, that will be computed
by the mission module.

A mission is identified by its name and has 3 attributes:

    - :code:`parts`: list of the :ref:`phase<phase-section>` and/or :ref:`route<route-section>`
      names that compose the mission, with optionally a last item that is the :code:`reserve`
      (see below).
    - :code:`use_all_block_fuel`: if True, the range of the main :ref:`route <route-section>`
      of the mission will be adjusted so that all block fuel (provided as input
      `data:mission:<mission_name>:block_fuel`) will be consumed for the mission, excepted the
      reserve, if defined. The provided range for first route is overridden but used as a first guess
      to initiate the iterative process.


The mission name is used when configuring the mission module in the FAST-OAD configuration file.
**If there is only one mission defined in the file, naming it in the configuration file is
optional.**

.. note::

    **About reserve**

    The :code:`reserve` keyword is typically designed to define fuel reserve as stated in
    EU-OPS 1.255.

    It defines the amount of fuel that is expected to be still in tanks once the mission is
    complete. It takes as reference one of the route that composes the mission
    (:code:`ref` attribute). The reserve is defined as the amount of fuel consumed during the
    referenced route, multiplied by the coefficient provided as the :code:`multiplier` attribute.

Example:

.. code-block:: yaml

    missions:
      sizing:
        parts:
          - phase: taxi_out
          - phase: takeoff
          - route: main_route
          - route: diversion
          - phase: holding
          - phase: landing
          - phase: taxi_in
          - reserve:
              ref: main_route
              multiplier: 0.03
      operational:
        parts:
          - phase: taxi_out
          - phase: takeoff
          - route: main_route
          - phase: landing
          - phase: taxi_in
      fuel_driven:
        parts:
          - phase: taxi_out
          - phase: takeoff
          - route: main_route
          - phase: landing
          - phase: taxi_in
        use_all_block_fuel: true



.. _factorizing-parameters:

**********************
Factorizing parameters
**********************

Some parameters may be common to several segments and have same value across all of them.
In such case, it is possible to define them at higher level (i.e. phase, route or mission)
to avoid repeating them.

For example, to specify a temperature increment at mission level, the mission section could be:

.. code-block:: yaml

    missions:
      operational:
        isa_offset: 15.0            # It will apply to the whole mission
        parts:
          - route: main_route
          - phase: landing
          - phase: taxi_in


A high-level parameter definition will be overloaded by a lower-level definition, as illustrated
in this example of phase definition:

.. code-block:: yaml

    phases:
      initial_climb:                               # Phase name
        engine_setting: takeoff                        # ---------------
        polar: data:aerodynamics:aircraft:takeoff      #   Common segment
        thrust_rate: 1.0                               #   parameters
        time_step: 0.2                                 # ---------------

        parts:                                         # Definition of segment list
          - segment: altitude_change                     # 1st segment (climb)
            target:
              altitude:
                value: 400.
                unit: ft
              equivalent_airspeed: constant
          - segment: speed_change                        # 2nd segment (acceleration)
            target:
              equivalent_airspeed:
                value: 250
                unit: kn
          - segment: altitude_change                     # 3rd segment (climb)
            thrust_rate: 0.95        # --> PHASE THRUST RATE VALUE IS OVERWRITTEN
            target:
              altitude:
                value: 1500.
                unit: ft
              equivalent_airspeed: constant

