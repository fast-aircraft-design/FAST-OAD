.. _add-plugin:

##########################################################
How to add custom OpenMDAO modules to FAST-OAD as a plugin
##########################################################

Once you have :ref:`created your custom modules <add-modules>` for FAST-OAD,
you may want to share them with other users, which can be done in two ways:

    - Providing your code so they can copy it on their computer and have them set their
      :code:`custom_modules` field accordingly in their :ref:`configuration-file`.
    - Packaging your code as a FAST-OAD plugin and have them install it through :code:`pip`
      or equivalent. This is the subject of current chapter.

A FAST-OAD plugin can provide additional FAST-OAD modules, Jupyter notebooks, configuration files and source data files:

    - plugin-provided FAST-OAD modules are usable in :ref:`configuration files <configuration-file>`,
      and can be :ref:`listed<get-module-list>` and :ref:`used<configuration-file-problem-definition>`
      in the same way as native modules.
    - Command line can be used by users to retrieve :ref:`notebooks<python-usage>`,
      :ref:`configuration files<generate-conf-file>` and :ref:`source data files<generate-source-data_file>`.

Plugin structure
################
In your source folder, a typical plugin structure would be like this::

    my_package/
    ├── __init__.py
    ├── configurations/
    │   ├── __init__.py
    │   ├── configuration_1.yaml
    │   └── configuration_2.yaml
    ├── models/
    │   ├── __init__.py
    │   ├── my_model.py
    │   └── some_subpackage/
    │       ├── __init__.py
    │       └── some_more_code.py
    └── notebooks/
    │   ├── __init__.py
    │   ├── any_data/
    │   │   ├── __init__.py
    │   │   └── some_data.xml
    │   ├── awesome_notebook.ipynb
    │   └── good_notebook.ipynb
    └── source_data_files
        ├── __init__.py
        ├── source_data_file_1.xml
        ├── source_data_file_2.xml
        └── source_data_file_3.xml

As shown above, the expected structure is composed of Python **packages**, i.e. every folder should
contain a :code:`__init__.py` file, **even if it contains only non-Python files** (e.g. data for notebooks).

The root folder can be anywhere in your project structure, since plugin declaration will point to
its location.

Expected folders in a plugin package are:

    - :code:`models`: contains Python code where FAST-OAD modules are :ref:`registered<add-modules>`.
    - :code:`configurations`: contains only configuration files in YAML format. No sub-folder is
      allowed. These configuration files will be usable through :ref:`command line<generate-conf-file>`
      or API method :meth:`~fastoad.cmd.api.generate_configuration_file`.
    - :code:`notebooks`: contains any number of Jupyter notebooks and associated data, that will
      be made available to users through :ref:`command line<python-usage>`.
    - :code:`source_data_files`: contains only source data files in XML format. As for the :code:`configurations` package, no sub-folder is allowed. These source data files will be usable through :ref:`command line<generate-source-data_file>` or API method :meth:`~fastoad.cmd.api.generate_source_data_file`.

Any of these folders is optional. Any other folder will be ignored.


Plugin packaging
################

To make your custom modules usable as a FAST-OAD plugin, you have to package them
and declare your package as a plugin with :code:`fastoad.plugins` as plugin group name.

Here under is a brief tutorial about these operations using `Poetry <https://python-poetry.org>`_.

.. note::

    If you are not familiar with Python packaging, it is recommended to look at this
    `tutorial <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`_ first.
    It presents the important steps and notions of the packaging process, and the "classic" way
    using `setuptools <https://setuptools.pypa.io/en/latest/>`_.
    And if you want to stick to setuptools, check this
    `page <https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata>`_
    for details about plugin declaration.


.. contents::
   :local:
   :depth: 1

******************************
Plugin declaration
******************************

For the example, let's consider that your project contains the package :code:`star_trek.drives`, and
that your project structure contains::

    src/
    ├── star_trek/
    │   ├── __init__.py
    │   ├── drives/
    │   │   ├── __init__.py
    │   │   ├── configurations/
    │   │   ├── models/
    │   │   └── notebooks/
    │   └── ...
    └── ...

As previously stated, your folder :code:`src/star_trek/drives` does not have to contain all of the
folders :code:`models`, :code:`configurations`, :code:`notebooks` nor :code:`source_data_files`.

Assuming you project contains the package :code:`star_trek.drives` that contains
models you want to share, you can declare your plugin in your :code:`pyproject.toml`
file with:

.. code-block:: toml

    ...

    [tool.poetry]
    # Tells location of sources
    packages = [
        { include = "star_trek", from = "src" },
    ]

    ...

    # Plugin declaration
    [tool.poetry.plugins."fastoad.plugins"]
    "ST_plugin" = "star_trek.drives"

    ...

.. note::

    It is discouraged to declare several FAST-OAD plugins for a same project.

Once your :code:`pyproject.toml` is set, you can do :code:`poetry install`. Besides
installing your project dependencies, it will make your models **locally** available (i.e.
you could use their identifiers in your FAST-OAD configuration file without setting
the :code:`custom_modules` field)


******************************
Building
******************************
You can build your package with the command line :code:`poetry build`.
Let's assume your :code:`pyproject.toml` file is configured so that your project name is
:code:`ST_drive_models`, as below:

.. code-block:: toml

    ...

    [tool.poetry]
    name = "ST_drive_models"
    version = "1.0.0"

    # Tells location of sources
    packages = [
        { include = "star_trek", from = "src" },
    ]

    ...

    # Specify that Poetry is used for building the package
    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

    ...

    # Plugin declaration
    [tool.poetry.plugins."fastoad.plugins"]
    "ST_plugin" = "star_trek.drives"
    ...

The command :code:`poetry build` will create a :code:`dist` folder with two files:

:code:`ST_drive_models-1.0.0.tar.gz` and :code:`ST_drive_models-1.0.0-py3-none-any.whl`
(or something like this).

You may then have sent any of those two files to another user, who may then install your models
using :code:`pip` with:

.. code-block:: shell-session

    $ pip install ST_drive_models-1.0.0-py3-none-any.whl  # or ST_drive_models-1.0.0.tar.gz

******************************
Publishing
******************************
Once you have built your package, you may publish it on a a package repository.
:code:`poetry publish` will publish your package on `PyPI <https://pypi.org>`_,
provided that you have correctly set your account.

.. note::

    Publishing on PyPI requires a valid account, and also that the chosen package name (defined by
    `name` field in the `pyproject.toml` file) is unused, or already associated to your account.

Poetry can also publish to another destination.

Please see `here <https://python-poetry.org/docs/cli/#publish>`_ for detailed information.

