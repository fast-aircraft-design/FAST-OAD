=========
Changelog
=========

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
