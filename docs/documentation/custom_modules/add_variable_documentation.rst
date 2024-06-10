.. _add-variable-documentation:

##############################
How to document your variables
##############################

FAST-OAD can associate a description to each variable. Such description will be put as
comment in datafiles, or displayed along with other variable information, like in command line
(see :ref:`get-variable-list`).

The description of a variable can be defined in two ways:

.. contents::
   :local:
   :depth: 1

********************************************************
Defining variable description in your OpenMDAO component
********************************************************
OpenMDAO natively allows to define the description of a variable
when :doc:`declaring it <openmdao:features/core_features/working_with_components/continuous_variables>`.

FAST-OAD will retrieve this information (the description has to be defined once,
even if the variable is declared at several locations).

************************************************
Defining variable description in dedicated files
************************************************
If you want to add description to your variables in a more centralized way, FAST-OAD
will look for files named :code:`variable_descriptions.txt` that are dedicated to that.

The file content is expected to process one variable per line, containing the variable name
and its description, separated by :code:`||`, as in following example::

    my:variable||The description of my:variable, as long as needed, but on one line.
    # Comments are allowed
    my:other:variable || Another description (surrounding spaces are ignored)

FAST-OAD will search such files:

    - in the root package of plugin modules (see :ref:`add-plugin`)
    - in the root folder of module folders as declared in configuration file (see :ref:`add-modules-set-configuration-files`)
    - in the same package as any class which is declared as FAST-OAD module (see :ref:`add-modules-register-systems`)

In practice, here you can see what description files will be consider, depending on their location::

    my_modules/
    ├── __init__.py
    ├── subpackage1
    │   ├── __init__.py
    │   ├── model.py                      <- contains a class decorated with
    │   │                                    RegisterOpenMDAOSystem
    │   └── variable_descriptions.txt     <- this file will be loaded
    ├── subpackage2
    │   ├── __init__.py
    │   ├── propulsion_model.py           <- contains a class decorated with
    │   │                                    RegisterOpenPropulsion
    │   └── variable_descriptions.txt     <- this file will be loaded
    ├── util
    │   ├── __init__.py
    │   ├── utility_module.py             <- no registering done here
    │   └── variable_descriptions.txt     <- this file will NOT be loaded
    └── variable_descriptions.txt     <- this file will be loaded because it is in root folder/package

