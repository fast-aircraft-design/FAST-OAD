.. _mission-definition:

############
Mission file
############

A mission file describes precisely one or several missions that could be computed by
the performance model :code:`fastoad.performances.mission` of FAST-OAD.

The file format of mission files is the `YAML <https://yaml.org>`_  format.
A quick tutorial for YAML (among many ones) is available `here <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started/>`_


.. contents::
   :local:
   :depth: 1


***************************
mission description
***************************


.. list-table:: Mission elements
    :widths: 3 10 30
    :width: 100%
    :header-rows: 1

    * - Type
      - Parts
      - Description
    * - :ref:`segment <flight-segments>`
      - N/A
      - The basic bricks that are provided by FAST-OAD.
    * - :ref:`phase <phase-section>`
      - segment(s)
      - A free assembly of one or more segments.
    * - :ref:`route <route-section>`
      - | zero or more phase(s)
        | **one cruise segment**
        | zero or more phase(s)
      - | A route is a climb/cruise/descent sequence with a fixed range. The
        | range is achieved by adjusting the distance covered during the
        | cruise part.
    * - :ref:`mission <mission-section>`
      - routes and/or phases
      - | A mission is what is computed by :code:`fastoad.performances.mission`.
        | Generally, it begins when engine starts and ends when engine
        | stops.


.. _phase-section:

***************
Phase section
***************

This section, identified by the :code:`phases` keyword, defines flight phases. A flight phase is
defined as an assembly of one or more :ref:`flight segment(s) <flight-segments>`.

Basically, a phase has a name, and a :code:`parts` attribute that contains a list of segment definitions.

Nevertheless, it is also possible to set, at phase level, the parameters that are common to several
segments of the phase.

The phase section only defines flight phases, but not their usage, that is defined
in :ref:`route <route-section>` and :ref:`mission <mission-section>` sections. Therefore, the
definition order of flight phases has no importance.

Example:

.. code-block:: yaml

    phases:
      initial_climb:                                # Phase name
        engine_setting: takeoff                         # ---------------
        polar: data:aerodynamics:aircraft:takeoff       #   Common segment
        thrust_rate: 1.0                                #   parameters
        time_step: 0.2                                  # ---------------
        parts:                                          # Definition of segment list
          - segment: altitude_change                    # 1st segment (climb)
            target:
              altitude:
                value: 400.
                unit: ft
              equivalent_airspeed: constant
          - segment: speed_change                       # 2nd segment (acceleration)
            target:
              equivalent_airspeed:
                value: 250
                unit: kn
          - segment: altitude_change                    # 3rd segment (climb)
            thrust_rate: 0.95                           # phase thrust rate value is overwritten
            target:
              altitude:
                value: 1500.
                unit: ft
              equivalent_airspeed: constant
        climb:                                    # Phase name
          ...                                       # Definition of the phase...


.. _route-section:

*************
Route section
*************

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

.. code-block::         yaml

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

***************
Mission section
***************

This is the main section. It allows to define one or several missions, that will be computed
by the mission module.

A mission is identified by its name and has only the :code:`parts` attribute that lists the
:ref:`phase<phase-section>` and/or :ref:`route<route-section>` names that compose the mission, with
optionally a last item that is the :code:`reserve` (see below).


The mission name is used when configuring the mission module in the FAST-OAD configuration file.
**If there is only one mission defined in the file, naming it in the configuration file is
optional.**

About reserve:
    The :code:`reserve` is the amount of fuel that is expected to be still in tanks once the mission is
    complete. It takes as reference one of the route that composes the mission (:code:`ref` attribute).
    The reserve is defined as the amount of fuel consumed during the referenced route, multiplied
    by the coefficient provided as the :code:`multiplier` attribute.


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


