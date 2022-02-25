=========
Changelog
=========

Version 1.3.0.post0
===================
- Modified package organization. (#420)

Version 1.3.0
=============
- Changes:
    - Rework of plugin system. (#409 - #417)
        - Plugin group identifier is now `fastoad.plugins` (usage of `fastoad_model` is deprecated)
        - A plugin can now provide, besides models, notebooks and sample configuration files.
        - CLI and API have been updated to allow choosing the source when generating a configuration file, and to provide the needed information about installed plugin (`fastoad plugin_info`)
        - Models are loaded only when needed (speeds up some basic operations like `fastoad -h`)
    - CS25-related models are now in separate package [FAST-OAD-CS25](https://pypi.org/project/fast-oad-cs25/). This package is still installed along with FAST-OAD to preserve backward-compatibility. Also, package [FAST-OAD-core](https://pypi.org/project/fast-oad-core/) is now available, which does NOT install FAST-OAD-CS25 (thus contains only the mission model). (#414)
    - IndepVarComp variables in FAST-OAD models are now correctly handled and included in input data file. (#408)
    - Changes in mission module. Most noticeable change is that the number of engines is no more an input of the mission module, but should be handled by the propulsion model. No impact when using the base CS-25 process, since the variable name has not changed.(#411)

- Bug fixes:
    - FAST-OAD is now able to manage dynamically shaped problem inputs. (#416 - #418)


Version 1.2.1
=============
- Changes:
  - Updated dependency requirements. All used libraries are now compatible with Jupyter lab 3 without need for building extensions. (#392)
  - Now Atmosphere class is part of the [stdatm](https://pypi.org/project/stdatm/) package (#398)
  - For `list_variables` command, the output format can now be chosen, with the addition of the format of variables_description.txt (for custom modules now generate a variable descriptions. (#399)

- Bug fixes:
  - Minor fixes in Atmosphere class. (#386)


Version 1.1.2
=============
- Bug fixes:
    - Engine setting could be ignored for cruise segments. (#397)

Version 1.1.1
=============
- Bug fixes:
    - Fixed usage of list_modules with CLI. (#395)

Version 1.1.0
=============
- Changes:
    - Added new submodel feature to enable a more modular approach. (#379)
    - Implemented the submodel feature in the aerodynamic module. (#388)
    - Implemented the submodel feature in the geometry module. (#387)
    - Implemented the submodel feature in the weight module. (#385)
    - Added the possibility to list custom modules. (#369)
    - Updated high lift aerodynamics and rubber engine models. (#352)
    - Added custom modules tutorial notebook. (#317)
- Bug fixes:
    - Fixed incompatible versions of jupyter-client. (#390)
    - Fixed the naming and description of the virtual taper ratio used in the wing geometry. (#383)
    - Fixed some wrong file links and typos in CeRAS notebook. (#380)
    - Fixed issues with variable descriptions in xml file. (#364)

Version 1.0.5
=============
- Changes:
    - Now using the new WhatsOpt feature that allows to generate XDSM files without being registered on server. (#361)
    - Optimization viewer does no allow anymore to modify output values. (#372)
- Bug fixes:
    - Compatibility with OpenMDAO 3.10 (which becomes the minimal required version). (#375)
    - Variable descriptions can now be read from comment of XML data files, which fixes the missing descriptions in variable viewer. (#359)
    - Performance model: the computed taxi-in distance was irrelevant. (#368)

Version 1.0.4
=============
- Changes:
    - Enum classes in FAST-OAD models are now extensible by using `aenum` instead of `enum`. (#345)
- Bug fixes:
    - Incompatibility with `ruamel.yaml` 0.17.5 and above has been fixed. (#344)
    - Computation of partial derivatives for OpenMDAO was incorrectly declared in some components.
      MDA, or MDO with COBYLA solver, were not affected. (#347)
    - Errors in custom modules are no more hidden. (#348)

Version 1.0.3
=============
- Changes:
    - Configuration files can now contain unknown sections (at root level) to allow these files to be used by other tools. (#333)
- Bug fixes:
    - Importing, in a `__init__.py`, some classes that were registered as FAST-OAD modules could make that the register process fails. (#331)
    - When generating an input file using a data source, the whole data source was copied instead of just keeping the needed variables. (#332)
    - Instead of overwriting an existing input files, variables of previous file were kept. (#330)
    - A variable that was connected to an output could be incorrectly labelled as input when listing problem variables. (#341)
    - Fixed broken links in Sphinx documentation, including docstrings. (#315)

Version 1.0.2
=============
- FAST-OAD now requires a lower version of `ruamel.yaml`. It should prevent Anaconda to try and fail to update its
  "clone" of `ruamel.yaml`. (#308)

Version 1.0.1
=============
- Bug fixes:
    - In a jupyter notebook, each use of a filter in variable viewer caused the display of a new variable viewer. (#301)
    - Wrong warning message was displayed when an incorrect path was provided for `module_folders` in the configuration file. (#303)

Version 1.0.0
=============
- Core software:
    - Changes:
        - FAST-OAD configuration file is now in YAML format. (#277)
        - Module declaration are now done using Python decorators directly on registered classes. (#259)
        - FAST-OAD now supports custom modules as plugins. (#266)
        - Added "fastoad.loop.wing_position" module for computing wing position from target static margin in MDA. (#268)
        - NaN values in input data are now detected at computation start. (#273)
        - Now api.generate_inputs() returns the path of generated file. (#254)
        - `fastoad list_systems` is now `fastoad list_modules` and shows documentation for OpenMDAO options. (#287)
        - Connection of OpenMDAO variables can now be done in configuration file. (#263)
        - More generic code for mass breakdown plots to ease usage for custom weight models. (#250)
        - DataFile class has been added for convenient interaction with FAST-OAD data files. (#293)
        - Moved some part of code to private API. What is still public will be kept and maintained. (#295)
    - Bug fixes:
        - FAST-OAD was crashing when mpi4py was installed. (#272)
        - Output of `fastoad list_variables` can now be redirected in a file. (#284)
        - Activation of time-step mission computation in tutorial notebook is now functional. (#285)
        - Variable viewer toolbar now works correctly in JupyterLab. (#288)
        - N2 diagrams caused a 404 error in notebooks since OpenMDAO 3.7. (#289)
- Models:
    - Changes:
        - A notebook has been added that shows how to compute CeRAS-01 aircraft. (#275)
        - Unification of performance module. (#251)
            - Breguet computations are now defined using the mission input file.
            - A computed mission can now be integrated or not to the sizing process.
        - Better management of speed parameters in Atmosphere class. (#281)
        - More robust airfoil profile processing. (#256)
        - Added tuner parameter in computation of compressibility. (#258)

Version 0.5.4-beta
==================

- Bug fix: An infinite loop could occur if custom modules were declaring the same variable
  several times with different units or default values.


Version 0.5.3-beta
==================

- Added compatibility with OpenMDAO 3.4, which is now the minimum required
  version of OpenMDAO. (#231)
- Simplified call to VariableViewer. (#221)
- Bug fix: model for compressibility drag now takes into account sweep angle
  and thickness ratio. (#237)
- Bug fix: at installation, minimum version of Scipy is forced to 1.2. (#219)
- Bug fix: SpeedChangeSegment class now accepts Mach number as possible target. (#234)
- Bug fix: variable "data:weight:aircraft_empty:mass has now "kg" as unit. (#236)


Version 0.5.2-beta
==================

- Added compatibility with OpenMDAO 3.3. (#210)
- Added computation time in log info. (#211)
- Fixed bug in XFOIL input file. (#208)
- Fixed bug in copy_resource_folder(). (#212)

Version 0.5.1-beta
==================

- Now avoids apparition of numerous deprecation warnings from OpenMDAO.

Version 0.5.0-beta
==================

- Added compatibility with OpenMDAO 3.2.
- Added the mission performance module (currently computes a fixed standard mission).
- Propulsion models are now declared in a specific way so that another
  module can do a direct call to the needed propulsion model.

Version 0.4.2-beta
==================

- Prevents installation of OpenMDAO 3.2 and above for incompatibility reasons.
- In Breguet module, output values for climb and descent distances were 1000 times
  too large (computation was correct, though).

Version 0.4.0-beta
==================

Some changes in mass and performances components:
    - The Breguet performance model can now be adjusted through input variables
      in the "settings" section.
    - The mass-performance loop is now done through the "fastoad.loop.mtow"
      component.

Version 0.3.1-beta
==================

- Adapted the FAST-OAD code to handle OpenMDAO version 3.1.1.

Version 0.3.0-beta
==================

- In Jupyter notebooks, VariableViewer now has a column for input/output type.
- Changed base OAD process so that propulsion model can now be directly called
  by the performance module instead of being a separate OpenMDAO component (which
  is still possible, though). It prepares the import of FAST legacy
  mission-based performance model.

Version 0.2.2-beta
==================

- Changed dependency requirement to have OpenMDAO version at most 3.1.0
  (FAST-OAD is not yet compatible with 3.1.1)

Version 0.2.1-beta
==================

- Fixed compatibility with wop 1.9 for XDSM generation


Version 0.2.0b
==============

- First beta release


Version 0.1.0a
==============

- First alpha release
