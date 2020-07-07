=========
Changelog
=========

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
