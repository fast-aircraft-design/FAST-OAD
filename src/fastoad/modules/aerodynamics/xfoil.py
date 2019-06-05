"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
import subprocess

from math import cos, pi, fabs
from openmdao.core.explicitcomponent import ExplicitComponent


# TODO: convert to ExternalCodeComp
class Xfoil(ExplicitComponent):
    xfoil_exe = 'xfoil.exe'
    xfoil_cmd = 'run_xfoil.bat'
    xfoil_script_filename = 'xfoil_script.txt'
    xfoil_result_filename = 'xfoil_result.txt'
    xfoil_log = 'xfoil.log'

    # we use airfoil of Boeing aircraft,data from
    # "http://m-selig.ae.illinois.edu/ads/coord_database.html"
    xfoil_bacj_template = 'BACJ.txt'
    xfoil_bacj_new = 'BACJ-new.txt'

    def initialize(self):
        self.options.declare('xfoil_dir',
                             default=os.path.join(os.path.dirname(__file__), os.pardir, 'XFOIL'),
                             types=str)
        self.options.declare('tmp_dir',
                             default=os.path.join(os.path.dirname(__file__), 'tmp'),
                             types=str)
        self.options.declare('resources_dir',
                             default=os.path.join(os.path.dirname(__file__), 'resources'),
                             types=str)
        self.options.declare('xfoil_result',
                             default=os.path.join(os.path.dirname(__file__),
                                                  'tmp', Xfoil.xfoil_result_filename),
                             types=str)

    def setup(self):
        self.xfoildir = self.options['xfoil_dir']
        self.tmpdir = self.options['tmp_dir']
        self.resourcesdir = self.options['resources_dir']
        self.xfoil_result = self.options['xfoil_result']

        self.add_input('geometry:wing_toc_aero', val=0.128)
        self.add_input('xfoil:reynolds', val=1e7)
        self.add_input('xfoil:mach', val=0.2)
        self.add_input('geometry:wing_sweep_25', val=25.)

        self.add_output('aerodynamics:Cl_max_clean')

    def compute(self, inputs, outputs):
        el_aero = inputs['geometry:wing_toc_aero']
        reynolds = inputs['xfoil:reynolds']
        mach = inputs['xfoil:mach']

        self._prepare_run(el_aero, reynolds, mach, self.resourcesdir)
        subprocess.call(os.path.join(self.tmpdir, Xfoil.xfoil_cmd))

        cl_max_2d = self.get_max_cl()
        #        cl_max_2d = 2.0

        outputs['aerodynamics:Cl_max_clean'] = \
            cl_max_2d * 0.9 * cos(inputs['geometry:wing_sweep_25'] / 180. * pi)

    def _prepare_run(self, el_aero, reynolds, mach, resourcesdir, logfile=False):
        f_path_ori = os.path.join(self.resourcesdir, Xfoil.xfoil_bacj_template)
        f_path_new = os.path.join(self.tmpdir, Xfoil.xfoil_bacj_new)

        # TODO : this is a geometry operation and should be done outside this module
        airfoil_reshape(el_aero, f_path_ori, f_path_new)

        f_path = os.path.join(self.tmpdir, Xfoil.xfoil_script_filename)

        script_file = open(f_path, "w")
        script_file.write('load' + "\n")

        script_file.write(os.path.join(self.tmpdir, 'BACJ-new.txt') + "\n")
        script_file.write('plop' + "\n")
        script_file.write('g' + "\n")
        script_file.write('' + "\n")
        script_file.write('oper' + "\n")
        script_file.write('re' + "\n")
        script_file.write(str(reynolds) + "\n")
        script_file.write('m' + "\n")
        script_file.write(str(mach) + "\n")
        script_file.write('visc' + "\n")
        script_file.write('iter' + "\n")
        script_file.write('500' + "\n")
        script_file.write('pacc' + "\n")
        script_file.write(self.xfoil_result + "\n")
        script_file.write('' + "\n")
        script_file.write('aseq' + "\n")
        script_file.write('0' + "\n")
        script_file.write('30' + "\n")
        script_file.write('0.5' + "\n")
        script_file.write('pacc' + "\n")
        script_file.write('' + "\n")
        script_file.write('quit' + "\n")
        script_file.close()
        if os.path.isfile(self.xfoil_result):
            os.remove(self.xfoil_result)

        f_path = os.path.join(self.tmpdir, Xfoil.xfoil_cmd)
        cmd_file = open(f_path, "w")
        cmd_file.write('@echo off' + "\n")

        xfoildir = os.path.abspath(self.xfoildir)
        cmd = os.path.join(xfoildir, Xfoil.xfoil_exe) + ' <' + \
              os.path.join(self.tmpdir, Xfoil.xfoil_script_filename)
        if logfile:
            if os.path.isfile(os.path.join(self.tmpdir, Xfoil.xfoil_log)):
                os.remove(os.path.join(self.tmpdir, Xfoil.xfoil_log))
            cmd += ' > ' + \
                   os.path.join(self.tmpdir, Xfoil.xfoil_log) + ' 2>&1' + "\n"

        cmd_file.write(cmd)
        cmd_file.close()

    def _run_once(self):
        subprocess.call(
            os.path.join(self.tmpdir, Xfoil.xfoil_cmd))

    def get_max_cl(self):
        """
        Returns: 
            maximum lift coefficient Cl value if successful, None otherwise.
        """
        if os.path.isfile(self.xfoil_result):
            resfile = open(self.xfoil_result, "r")
            lines = resfile.readlines()
            resfile.close()
            CL = []
            AOA = []
            for i, line in enumerate(lines):
                if i >= 12:
                    a = line
                    b = a.split('  ')
                    AOA.append(float(b[1]))
                    CL.append(float(b[2]))

            if max(AOA) >= 5.0:
                max_CL = max(CL)
            else:
                max_CL = 1.9
                print('Cl max not found!')
        else:
            max_CL = 1.9
            print('Xfoil results file not found')

        return max_CL


# FIXME: to be removed after reshape operation is put outside this module
def airfoil_reshape(toc_mean, f_path_ori, f_path_new):
    fichier = open(f_path_ori, "r")
    l1 = fichier.readlines()
    fichier.close()
    b = []
    for i, elem in enumerate(l1):
        if i >= 1:
            a = elem
            b.append(list(map(float, a.split("\t"))))
        else:
            pass
    t = []
    for i, elem in enumerate(b):
        for j in range(i + 1, len(b) - 1):
            if (b[j][0] <= elem[0] and b[j + 1][0] >= elem[0]
            ) or (b[j][0] >= elem[0] and b[j + 1][0] <= elem[0]):
                t_down = b[j][
                             1] + (elem[0] - b[j][0]) / (b[j + 1][0] - b[j][0]) * (
                                 b[j + 1][1] - b[j][1])
                t_up = elem[1]
                t.append(fabs(t_down) + fabs(t_up))
    toc = max(t)
    factor = toc_mean / toc

    fichier = open(f_path_new, "w")
    fichier.write("Wing\n")
    for i, elem in enumerate(l1):
        if i >= 1:
            a = elem
            b = a.split("\t")
            fichier.write(
                str(float(b[0])) + ' \t' + str((float(b[1])) * factor) + "\n")
        else:
            pass
    fichier.close()
