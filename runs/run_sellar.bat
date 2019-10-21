REM To have fast.exe ready, do "python setup.py install_scripts"
REM and set your path accordingly (not needed in PyCharm terminal)


REM generate inputs.xml
fast.exe conf_sellar.toml --gen_inputs

REM run the sellar problem
fast.exe conf_sellar.toml --run