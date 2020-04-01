.. _Add-modules:

How to add custom OpenMDAO modules to FAST-OAD
==============================================
With FAST-OAD, you can register any OpenMDAO system of your own so it can be
used though the configuration file.

To have your OpenMDAO system available in FAST-OAD, requirements are:

- You have to pay attention to the naming of your input and output variables.
  As FAST-OAD uses the `promotion system of OpenMDAO <http://openmdao.org/twodocs/versions/latest/basic_guide/promote_vs_connect.html?highlight=promote>`_,
  which means that variables you want to link to the rest of the process must have
  the name that is given in the global process. The names of variables are available
  using the command line (see :ref:`Get-variable-list`).
- Your system must be registered. Assuming your OpenMDAO class is named `MyOMClass`
  in `myclass.py`, you can create in the same folder the file `register.py` with following lines:

  .. code-block:: python

    from myclass import MyOMClass
    from fastoad.module_management import OpenMDAOSystemRegistry

    OpenMDAOSystemRegistry.register_system(MyOMClass, 'my.custom.name')

- The folder that contains these Python files must be listed in `module_folders`
  in the configuration file

  .. code-block:: TOML

    title = "OAD Process with custom component"

    # List of folder paths where user added custom registered OpenMDAO components
    module_folders = ["/path/to/my/custom/module/folder"]

  Once this is done, your custom system should appear in the list provided by the
  command:

  .. code:: bash

      $ fastoad list_systems my_custom_conf.toml

  (assuming your configuration file is named `my_custom_conf.toml` )

Then your component can be used like any other using the id you have given.

.. code-block:: TOML

    # Definition of OpenMDAO model
    [model]
        [ ... ]

        [model.my_custom_model]
            id = "my.custom.name"

        [ ... ]
