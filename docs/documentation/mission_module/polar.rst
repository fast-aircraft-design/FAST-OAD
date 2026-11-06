.. _polar:

################
Polar
################

The :class:`~fastoad.models.performances.mission.polar.Polar` class manages aerodynamic polar data,
providing an linear interpolation relation between lift coefficient (CL) and drag coefficient (CD),
or lift coefficient (CL) and angle of attack (alpha).

It is used in segments that rely on aerodynamic polar data (e.g. :class:`~fastoad.models.performances.mission.segments.time_step_base.AbstractTimeStepFlightSegment`)
and is referenced in the mission definition file through the ``polar`` parameter.


************
Polar class
************

.. autoclass:: fastoad.models.performances.mission.polar.Polar
   :members:
   :inherited-members:
   :undoc-members:
   :show-inheritance:

