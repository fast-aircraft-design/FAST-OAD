.. _mission-modules:

##############
Mission module
##############

The FAST-OAD mission module allows to simulate missions and to estimate their fuel burn,
which is an essential part of the sizing process.

The module aims at versatility, by:

    - providing a way to define missions from :ref:`custom files <mission-definition>`
    - linking mission inputs and outputs to the FAST-OAD data model
    - linking or not a mission to the sizing process


********************************
Inputs and outputs of the module
********************************

The performance module, as any FAST-OAD module, is linked to the MDA process by the connection
of its input and output variables. But unlike other modules, the list of inputs and outputs is not
fixed, and widely depends on the mission definition.

The input variables are defined in the mission file, as described
:ref:`here <setting-values-variable-name>`.

Most outputs variables are automatically decided by the structure of the mission. Distance, duration
and fuel burn are provided as outputs for each part of the mission.

Outputs for the whole mission:

 - :code:`data:mission:<mission_name>:distance`
 - :code:`data:mission:<mission_name>:duration`
 - :code:`data:mission:<mission_name>:fuel`

Outputs for each part of the mission (:ref:`flight route<route-section>` or :ref:`flight phase<phase-section>`):

 - :code:`data:mission:<mission_name>:<part_name>:distance`
 - :code:`data:mission:<mission_name>:<part_name>:duration`
 - :code:`data:mission:<mission_name>:<part_name>:fuel`

Outputs for each :ref:`flight phase<phase-section>` of a route:

 - :code:`data:mission:<mission_name>:<route_name>:<phase_name>:distance`
 - :code:`data:mission:<mission_name>:<route_name>:<phase_name>:duration`
 - :code:`data:mission:<mission_name>:<route_name>:<phase_name>:fuel`

Other mission-related variables are:

 - :code:`data:mission:<mission_name>:TOW`: TakeOff Weight. Input or output, depending on options below.
 - :code:`data:mission:<mission_name>:needed_block_fuel`: Burned fuel during mission. Output.
 - :code:`data:mission:<mission_name>:block_fuel`: Actual block fuel. Input or output, depending on options below.



************************************
Usage in FAST-OAD configuration file
************************************

The mission module can be used with the identifier :code`fastoad.performances.mission`.

The available parameters for this module are:

.. contents::
   :local:
   :depth: 1

.. centered:: Detailed description of parameters

:code:`propulsion_id`
=====================

    - **Mandatory**

    It is the identifier of a registered propulsion wrapper (see :ref:`add-propulsion-module`).

    FAST-OAD comes with a parametric propulsion model adapted to engine of the 1990s, with
    :code:`"fastoad.wrapper.propulsion.rubber_engine"` as identifier.



:code:`mission_file_path`
=========================

    - Optional (Default = :code:`"::sizing_mission"`)

    It is the path to the file that defines the mission. As any file path in the configuration file,
    it can be absolute or relative. If relative, the path of configuration file will be used as basis.

    FAST-OAD comes with two embedded missions, usable with special values:

     - :code:`"::sizing_mission"`: a time-step simulation of a classical commercial mission with
       diversion and holding phases
     - :code:`"::sizing_breguet"`: a very quick simulation based on Breguet formula, with rough
       assessment of fuel consumption during climb, descent, diversion and holding phases.


:code:`out_file`
================

    - Optional

    If provided, a CSV file will be written at provided path with all computed flight points.

    If relative, the path of configuration file will be used as basis.


:code:`mission_name`
====================

    - Mandatory if the used mission file defines several missions. Optional otherwise.

    Sets the mission to be computed.



:code:`use_initializer_iteration`
=================================

    Optional (Default = :code:`true` )

    During first solver loop, a complete mission computation can fail or consume useless CPU-time.
    When activated, this option ensures the first iteration is done using a simple, dummy, formula
    instead of the specified mission.

.. Warning::

    Set this option to :code:`false` if you do expect this model to be computed only once.
    Otherwise, the performance computation will be done only by the initializer.


:code:`adjust_fuel`
===================

    - Optional (Default = :code:`true` )

    If :code:`true`, block fuel will be adjusted to fuel consumption during mission. If :code:`false`,
    the input block fuel will be used.


:code:`compute_TOW`
===================

    - Optional (Default = :code:`false` )
    - Not used (actually forced to :code:`true`) if :code:`adjust_fuel` is :code:`true`.

    If :code:`true`, TakeOff Weight will be computed from mission block fuel and ZFW.

    If :code:`false`, block fuel will be computed from TOW and ZFW.


:code:`add_solver`
===================

    - Optional (Default = :code:`false` )
    - Not used (actually forced to :code:`false`) if :code:`compute_TOW` is :code:`false`.

    Setting this option to False will deactivate the local solver of the component. Useful if a
    global solver is used for the MDA problem.


:code:`is_sizing`
===================

    - Optional (Default = :code:`false` )

    If :code:`true`, TOW for the mission will be considered equal to MTOW and mission payload will
    be considered equal to design payload (variable :code:`data:weight:aircraft:payload`).
    Therefore, mission computation will be linked to the sizing process.
