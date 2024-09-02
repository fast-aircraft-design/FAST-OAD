.. _flight-point:

#####################
The FlightPoint class
#####################

The :class:`~fastoad.model_base.flight_point.FlightPoint` class is designed to store
flight parameters for one flight point of any computed mission.

FlightPoint class is meant for:

    - **storing all needed parameters** that are needed for performance modelling,
      including propulsion parameters.
    - easily exchanging data with **pandas DataFrame**.
    - **being extensible** for new parameters.

.. note::

    All parameters in FlightPoint instances are expected to be in SI units.

***************************
Available flight parameters
***************************
The documentation of :class:`~fastoad.model_base.flight_point.FlightPoint` provides
the list of available flight parameters, available as attributes.
This list is available through Python using::

    >>> import fastoad.api as oad

    >>> oad.FlightPoint.get_field_names()

*******************************
Exchanges with pandas DataFrame
*******************************
A pandas DataFrame can be generated from a list of FlightPoint instances::

    >>> import pandas as pd
    >>> import fastoad.api as oad

    >>> fp1 = oad.FlightPoint(mass=70000., altitude=0.)
    >>> fp2 = oad.FlightPoint(mass=60000., altitude=10000.)
    >>> df = pd.DataFrame([fp1, fp2])

And FlightPoint instances can be created from DataFrame rows::

    # Get one FlightPoint instance from a DataFrame row
    >>> fp1bis = oad.FlightPoint.create(df.iloc[0])

    # Get a list of FlightPoint instances from the whole DataFrame
    >>> flight_points = oad.FlightPoint.create_list(df)


.. _flight_point_extensibility:

***************************
Extensibility
***************************
FlightPoint class is bundled with several fields that are commonly used in trajectory
assessment, but one might need additional fields.

Python allows to add attributes to any instance at runtime, but for FlightPoint to run
smoothly, especially when exchanging data with pandas, you have to work at class level.
This can be done using :meth:`~fastoad.model_base.flight_point.FlightPoint.add_field`, preferably
outside any class or function::

    # Adding a float field with None as default value
    >>> FlightPoint.add_field(
    ...    "ion_drive_power",
    ...    unit="YW",
    ...    is_cumulative=False, # Tells if quantity sums up during mission
    ...    is_output=True, # Tells if quantity is expected as mission output
    ...    )

    # Adding a field and defining its type and default value
    >>> FlightPoint.add_field("warp", annotation_type=int, default_value=9)

    # Now these fields can be used at instantiation
    >>> fp = FlightPoint(ion_drive_power=110.0, warp=12)

    # Removing a field, even an original one
    >>> FlightPoint.remove_field("sfc")

