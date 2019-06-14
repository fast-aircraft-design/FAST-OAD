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
import multiprocessing
import os

import win32event
import win32process
from fast.atmosphere import atmosphere
from openmdao.core.explicitcomponent import ExplicitComponent


class OpenVSP(ExplicitComponent):
    """Wrapper for OpenVSP tool: see http://www.openvsp.org/

    Class Attributes:
        vspscript_exe: OpenVSP script executable name
        vspaero_exe: OpenVSP vspareo executable name
        vspscript_filename: input file for OpenVSP script
        vspaero_filename: setup file for OpenVSP vspareo tool
        result_filename: openvsp result file
        takeoff_result_filename: openvsp result file when takeoff run option is enabled

    Attributes:
        aircraft: Aircraft object
        resultdir: absolute path to store results
        tmpdir: absolute path to store temporary files
        ovspdir (optional): installation directory of OpenVSP software
    """

    vspscript_exe = 'vspscript.exe'
    vspaero_exe = 'vspaero.exe'

    vspscript_filename = "wing_openvsp.vspscript"
    vspaero_filename = "wing_openvsp_DegenGeom.vspaero"
    result_filename = 'polar.txt'
    takeoff_result_filename = 'Result_of_vsp_takeoff.txt'

    def initialize(self):
        self.metadata.declare('ovsp_dir',
                              default=os.path.join(os.path.dirname(__file__), os.pardir,
                                                   'OpenVSP-3.5.1-win32'),
                              types=str)
        self.metadata.declare('result_dir',
                              default=os.path.join(os.path.dirname(__file__), os.pardir, 'result'),
                              types=str)
        self.metadata.declare('tmp_dir',
                              default=os.path.join(os.path.dirname(__file__), os.pardir, 'tmp'),
                              types=str)
        self.metadata.declare('openvsp_aero', default=False, types=bool)
        self.metadata.declare('takeoff_flag', default=False, types=bool)

    def setup(self):
        self.ovspdir = self.metadata['ovsp_dir']
        self.resultdir = self.metadata['result_dir']
        self.tmpdir = self.metadata['tmp_dir']
        self.openvsp_aero = self.metadata['openvsp_aero']
        self.takeoff_flag = self.metadata['takeoff_flag']

        if self.openvsp_aero:
            self.add_input('AoA_min_hs', val=0.)
            self.add_input('AoA_max_hs', val=0.)
            self.add_input('AoA_step_hs', val=0.)
            self.add_input('tlar:cruise_Mach', val=0.)
            self.add_input('sizing_mission:cruise_altitude', val=0.)
        else:
            self.add_input('AoA_min', val=0.)
            self.add_input('AoA_max', val=0.)
            self.add_input('AoA_step', val=0.)
            self.add_input('openvsp:mach', val=0.)
            self.add_input('openvsp:altitude', val=0.)

        self.add_input('geometry:wing_l2', val=0.)
        self.add_input('geometry:wing_y2', val=0.)
        self.add_input('geometry:wing_l3', val=0.)
        self.add_input('geometry:wing_x3', val=0.)
        self.add_input('geometry:wing_y3', val=0.)
        self.add_input('geometry:wing_l4', val=0.)
        self.add_input('geometry:wing_x4', val=0.)
        self.add_input('geometry:wing_y4', val=0.)
        self.add_input('geometry:wing_area', val=0.)
        self.add_input('geometry:wing_span', val=0.)
        self.add_input('geometry:wing_l0', val=0.)

    def compute(self, inputs, outputs):
        if self.openvsp_aero:
            AoA_min = inputs['AoA_min_hs'][0]
            AoA_max = inputs['AoA_max_hs'][0]
            step = inputs['AoA_step_hs'][0]
            mach = inputs['tlar:cruise_Mach'][0]
            altitude = inputs['sizing_mission:cruise_altitude'][0]
        else:
            AoA_min = inputs['AoA_min'][0]
            AoA_max = inputs['AoA_max'][0]
            step = inputs['AoA_step'][0]
            mach = inputs['openvsp:mach'][0]
            altitude = inputs['openvsp:altitude'][0]

        l2_wing = inputs['geometry:wing_l2'][0]
        y2_wing = inputs['geometry:wing_y2'][0]
        y3_wing = inputs['geometry:wing_y3'][0]
        y4_wing = inputs['geometry:wing_y4'][0]
        l4_wing = inputs['geometry:wing_l4'][0]
        l3_wing = inputs['geometry:wing_l3'][0]
        x3_wing = inputs['geometry:wing_x3'][0]
        x4_wing = inputs['geometry:wing_x4'][0]
        sref = inputs['geometry:wing_area'][0]
        cref = inputs['geometry:wing_l0'][0]
        bref = inputs['geometry:wing_span'][0]

        AoA_vector = [AoA_min, AoA_max, step]
        condition_vector = [mach, altitude]

        wing_geometry_vector = [l2_wing, y2_wing, l3_wing, x3_wing,
                                y3_wing, l4_wing, x4_wing, y4_wing]

        wing_parameter_vector = [sref, cref, bref]

        self.run(AoA_vector, condition_vector, wing_geometry_vector, wing_parameter_vector,
                 self.takeoff_flag)

    def run(self, AoA_vector, condition_vector, wing_geometry_vector,
            wing_parameter_vector, takeoff):

        self._write_vsp_file(wing_geometry_vector)
        self._write_vspaero_file(condition_vector, wing_parameter_vector)

        AoA_min = AoA_vector[0]
        AoA_max = AoA_vector[1]
        step = AoA_vector[2]

        alpha_vector = []
        result_cl = []
        result_cxi = []
        cx_wing = []

        vspaero_basename = os.path.splitext(OpenVSP.vspaero_filename)[0]

        self._make_inplace_change(
            os.path.join(self.tmpdir, OpenVSP.vspaero_filename),
            "\nAoA = " + str(0.0), "\nAoA = " + str(AoA_min))
        alpha = AoA_min
        while alpha < AoA_max:
            old_alpha = alpha
            alpha += step
            alpha_vector.append(alpha)
            self._make_inplace_change(
                os.path.join(self.tmpdir, OpenVSP.vspaero_filename),
                "\nAoA = " + str(old_alpha), "\nAoA = " + str(alpha))
            # Run the vspscript using vsp
            handle = win32process.CreateProcess(
                None,
                os.path.join(self.ovspdir, OpenVSP.vspscript_exe) + ' -script ' +
                os.path.join(self.tmpdir, OpenVSP.vspscript_filename),
                None,
                None,
                0,
                win32process.CREATE_NO_WINDOW,
                None,
                None,
                win32process.STARTUPINFO())
            # to wait for the exit of the process
            win32event.WaitForSingleObject(handle[0], -1)
            # Run DegenGeom using vspaero
            handle2 = win32process.CreateProcess(
                None,
                os.path.join(self.ovspdir, OpenVSP.vspaero_exe) + " " +
                os.path.join(self.tmpdir, vspaero_basename),
                None,
                None,
                0,
                win32process.CREATE_NO_WINDOW,
                None,
                None,
                win32process.STARTUPINFO())
            # to wait for the exit of the process
            win32event.WaitForSingleObject(handle2[0], -1)
            histfile = os.path.join(
                self.tmpdir,
                vspaero_basename + '.history')
            with open(histfile, 'r') as hf:
                l1 = hf.readlines()
                result = l1[5][40:50]
                result = result.replace(' ', '')
                result_cl.append(float(result))
                result2 = l1[5][60:70]
                result2 = result2.replace(' ', '')
                result_cxi.append(float(result2))
                result3 = l1[5][50:60]
                result3 = result3.replace(' ', '')
                cx_wing.append(float(result3))
        if takeoff:
            f_vsp = os.path.join(self.tmpdir, OpenVSP.takeoff_result_filename)
        else:
            f_vsp = os.path.join(self.tmpdir, OpenVSP.result_filename)
        fichier = open(f_vsp, "w")
        for iteration4 in range(len(result_cl)):
            fichier.write(str(result_cl[iteration4]) +
                          ',' +
                          str(result_cxi[iteration4]) +
                          ',' +
                          str(cx_wing[iteration4]) +
                          ',' +
                          str(alpha_vector[iteration4]) +
                          '\n')
        fichier.close()
        f_vsp_temp = os.path.join(self.tmpdir, vspaero_basename + '.lod')
        if os.path.isfile(f_vsp_temp):
            os.remove(os.path.join(self.tmpdir, vspaero_basename + '.lod'))
            os.remove(os.path.join(self.tmpdir, vspaero_basename + '.adb'))
            os.remove(
                os.path.join(
                    self.tmpdir,
                    vspaero_basename + '.history'))
            os.remove(os.path.join(self.tmpdir, vspaero_basename + '.csv'))
            os.remove(
                os.path.join(self.tmpdir, vspaero_basename + '.vspaero'))

    # use equations to calculate the oswald coefficient, in order not to use
    # vspaero

    def _write_vsp_file(
            self, wing_geom_v, filename=vspscript_filename,
            resourcesdir=os.path.join(os.path.dirname(__file__), 'resources')):
        l2_wing = wing_geom_v[0]
        y2_wing = wing_geom_v[1]
        l3_wing = wing_geom_v[2]
        x3_wing = wing_geom_v[3]
        y3_wing = wing_geom_v[4]
        l4_wing = wing_geom_v[5]
        x4_wing = wing_geom_v[6]
        y4_wing = wing_geom_v[7]

        area_1 = l2_wing * y2_wing
        span_2 = y3_wing - y2_wing
        span_3 = y4_wing - y3_wing
        const1 = x4_wing + l4_wing - l3_wing - x3_wing
        const2 = l3_wing + const1 - l4_wing
        area_3 = (const1 + l3_wing) * (y4_wing - y3_wing) - 0.5 * \
                 const1 * (y4_wing - y3_wing) - 0.5 * const2 * (y4_wing - y3_wing)

        # ----------------------------------------------------------------
        #                     WRITE VSPSCRIPT FOR THE WING FOR OPENVSP
        # ----------------------------------------------------------------

        vspaero_basename = os.path.splitext(OpenVSP.vspaero_filename)[0]
        resdir = os.path.abspath(resourcesdir)
        fichier = open(
            os.path.join(self.tmpdir, filename),
            "w")
        fichier.write(
            '\n//==== Create A Multi Section Wing and Change Some Parameters ====//\nvoid main()\n{\n    //==== Add Wing ====//\n    string wid = AddGeom( "WING", "");\n\n    //===== Insert A Couple More Sections =====//\n')
        insert_xsec = "    InsertXSec( wid, 1, XS_FOUR_SERIES );\n    InsertXSec( wid, 1, XS_FOUR_SERIES );\n    InsertXSec( wid, 1, XS_FOUR_SERIES );"
        fichier.write(insert_xsec)
        fichier.write(
            '\n\n    //===== Cut The Original Section =====//\n    CutXSec( wid, 1 );\n\n    //===== Change Driver =====//\n    SetDriverGroup( wid, 1, AREA_WSECT_DRIVER, ROOTC_WSECT_DRIVER, TIPC_WSECT_DRIVER );\n\n    SetParmVal( wid, "RotateAirfoilMatchDideralFlag", "WingGeom", 1.0 );\n\n    //===== Change Some Parameters 1st Section ====//\n')

        fichier.write('    SetParmVal( wid, "Root_Chord", "XSec_1", ')
        fichier.write(str(l2_wing))
        fichier.write(' );\n    SetParmVal( wid, "Tip_Chord", "XSec_1", ')
        fichier.write(str(l2_wing))
        fichier.write(' );\n    SetParmVal( wid, "Area", "XSec_1", ')
        fichier.write(str(area_1))
        fichier.write(' );\n    SetParmVal( wid, "Sweep", "XSec_1", 0.0 );')

        fichier.write(
            "\n\n    //==== Because Sections Are Connected Change One Section At A Time Then Update ====//\n    Update();\n\n    //===== Change Some Parameters 2nd Section ====//")

        fichier.write('\n    SetParmVal( wid, "Tip_Chord", "XSec_2", ')
        fichier.write(str(l3_wing))
        fichier.write(' );\n    SetParmVal( wid, "Span", "XSec_2", ')
        fichier.write(str(span_2))
        fichier.write(
            ' );\n    SetParmVal( wid, "Sweep", "XSec_2", 20.74 );\n    SetParmVal( wid, "Sweep_Location", "XSec_2", 0.17419 );\n    SetParmVal( wid, "Sec_Sweep_Location", "XSec_2", 0.9871 );\n    SetParmVal( wid, "Twist", "XSec_2", 0.5 );\n    SetParmVal( wid, "Twist_Location", "XSec_2", 0.25 );\n    SetParmVal( wid, "Dihedral", "XSec_2", 5.0 );\n    Update();')

        fichier.write(
            "\n\n    //===== Change Some Parameters 3rd Section ====//\n")

        fichier.write('    SetParmVal( wid, "Tip_Chord", "XSec_3", ')
        fichier.write(str(l4_wing))
        fichier.write(' );\n    SetParmVal( wid, "Span", "XSec_3", ')
        fichier.write(str(span_3))
        fichier.write(' );\n    SetParmVal( wid, "Area", "XSec_3", ')
        fichier.write(str(area_3))
        fichier.write(
            ' );\n    SetParmVal( wid, "Sweep", "XSec_3", 24.54 );\n    SetParmVal( wid, "Twist", "XSec_3", 0.3 );\n    SetParmVal( wid, "Twist_Location", "XSec_3", 0.25 );\n    SetParmVal( wid, "Dihedral", "XSec_3", 5.0 );\n    Update();')

        airfoil_0 = '\n\n    //==== Change Airfoil 0 ====//\n    string xsec_surf0 = GetXSecSurf( wid, 0 );\n    ChangeXSecShape( xsec_surf0, 0, XS_FILE_AIRFOIL );\n    string xsec0 = GetXSec( xsec_surf0, 0 );\n    ReadFileAirfoil( xsec0, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_15.dat") + '");\n\n    Update();\n\n'
        airfoil_0 = airfoil_0.replace('\\', '/')
        fichier.write(airfoil_0)
        airfoil_1 = '    //==== Change Airfoil 1====//\n    string xsec_surf = GetXSecSurf( wid, 1 );\n    ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL );\n    string xsec1 = GetXSec( xsec_surf, 1 );\n    ReadFileAirfoil( xsec1, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_15.dat") + '");\n\n    Update();\n\n'
        airfoil_1 = airfoil_1.replace('\\', '/')
        fichier.write(airfoil_1)
        airfoil_2 = '    //==== Change Airfoil 2====//\n    string xsec_surf2 = GetXSecSurf( wid, 2 );\n    ChangeXSecShape( xsec_surf2, 2, XS_FILE_AIRFOIL );\n    string xsec2 = GetXSec( xsec_surf2, 2 );\n    ReadFileAirfoil( xsec2, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_12.dat") + '");\n\n    Update();\n\n'
        airfoil_2 = airfoil_2.replace('\\', '/')
        fichier.write(airfoil_2)
        airfoil_3 = '    //==== Change Airfoil 3====//\n    string xsec_surf3 = GetXSecSurf( wid, 3 );\n    ChangeXSecShape( xsec_surf3, 3, XS_FILE_AIRFOIL );\n    string xsec3 = GetXSec( xsec_surf3, 3 );\n    ReadFileAirfoil( xsec3, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_11.dat") + '");\n\n    Update();\n\n'
        airfoil_3 = airfoil_3.replace('\\', '/')
        fichier.write(airfoil_3)

        fichier.write(
            "    //==== Check For API Errors ====//\n    while ( GetNumTotalErrors() > 0 )\n    {\n        ErrorObj err = PopLastError();\n        Print( err.GetErrorString() );\n    }\n\n")

        csvfile = '    //==== Set File Name ====//\n    SetComputationFileName( DEGEN_GEOM_CSV_TYPE, "' + \
                  os.path.join(
                      self.tmpdir,
                      vspaero_basename + '.csv') + '" );\n\n'
        csvfile = csvfile.replace('\\', '/')
        fichier.write(csvfile)
        fichier.write(
            '    //==== Run Degen Geom ====//\n    ComputeDegenGeom( SET_ALL, DEGEN_GEOM_CSV_TYPE );\n}')

        fichier.close()

    # ----------------------------------------------------------------
    #              MODIFY DEGENGEOM FUNCTION FOR THE WING FOR OPENVSP
    # ----------------------------------------------------------------

    @staticmethod
    def _make_inplace_change(filename, old_string, new_string):
        s = open(filename).read()
        if old_string in s:
            s = s.replace(old_string, new_string)
            f = open(filename, 'w')
            f.write(s)
            f.flush()
            f.close()
        else:
            print('No occurances of "{old_string}" found.'.format(**locals()))

    # ----------------------------------------------------------------
    #                     WRITE DEGENGEOM FOR THE WING FOR OPENVSP
    # ----------------------------------------------------------------
    def _write_vspaero_file(self, cond_v, wing_param_v,
                            filename=vspaero_filename):
        mach = cond_v[0]
        altitude = cond_v[1]
        Sref = wing_param_v[0]
        Cref = wing_param_v[1]
        Bref = wing_param_v[2]

        temperature, rho, pression, viscosity, sos = atmosphere(altitude)
        V_inf = sos * mach
        Re = V_inf * Cref / viscosity
        fichier = open(os.path.join(self.tmpdir, filename), "w")
        fichier.write("Sref = ")
        fichier.write(str(Sref))
        fichier.write("\nCref = ")
        fichier.write(str(Cref))
        fichier.write("\nBref = ")
        fichier.write(str(Bref))
        fichier.write(
            "\nX_cg = 0.000000\nY_cg = 0.000000\nZ_cg = 0.000000\nMach = ")
        fichier.write(str(mach))
        fichier.write("\nAoA = ")
        fichier.write(str(0.0))
        fichier.write("\nBeta = 0.000000")
        fichier.write("\nVinf = ")
        fichier.write(str(V_inf))
        fichier.write("\nRho = ")
        fichier.write(str(rho))
        fichier.write("\nReCref = ")
        fichier.write(str(Re))
        fichier.write("\nClMax = -1.000000\nMaxTurningAngle = -1.000000 \n\
        Symmetry = No \nFarDist = -1.000000\nNumWakeNodes = " + str(multiprocessing.cpu_count()) + " \nWakeIters = 5 \n\
        NumberOfRotors = 0")
        fichier.close()


def Convert_OpenVSP_2_AVL(user_data, user_drivers):
    # ==================================================================================================<
    #####--------Initializing progam--------#####
    print("\n### Initializing program...\n")
    # ---------Loading generic librairies--------#
    import os
    import time
    import shutil
    import winsound

    # --------- Creating generic methods --------#
    def ExitProgram():
        print('\n#####     END      #####\n')

    #    def err():
    #        winsound.Beep(200, 200 )
    #        winsound.Beep(150, 400 )
    #    def success():
    #        for i in range(1,2):
    #            winsound.Beep(300*i, 100 )
    #            winsound.Beep(400*i, 100 )
    #            winsound.Beep(100*i, 100 )

    # ---------- Requesting input files ---------#
    """Prompt code"""  # SOURCE: http://stackoverflow.com/questions/3579568/choosing-a-file-in-python-with-simple-dialog
    if user_drivers['Prompt_vsp3_file'] or user_drivers['Prompt_xml_file']:
        from Tkinter import Tk
        from tkFileDialog import askopenfilename  # file searcher
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing

        if user_drivers['Prompt_xml_file']:
            if user_drivers['Prompt_vsp3_file']:
                print("     No need to ask for vsp3 file.")
            f_type = 'XML';
            f_format = '.xml'
        else:
            if user_drivers['Prompt_vsp3_file']: f_type = 'OpenVSP';f_format = '.vsp3'

        print("\nSelect your " + f_type + " file *" + f_format)
        askedfile = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
        filedir = os.path.dirname(askedfile)
        if '.vsp3' in askedfile or '.xml' in askedfile:
            print("     Loading '" + os.path.basename(askedfile) + "' in:\n" + filedir)
            user_data['vehicle_name'] = str(os.path.basename(askedfile).split(f_format)[0])
            if 'VEGA' in filedir:
                if '\\OpenVSP' in filedir:
                    user_data['pathdir'] = filedir.split('\\OpenVSP')[0]
                elif '\\Input' in filedir:
                    user_data['pathdir'] = filedir.split('\\Input')[0]

            else:
                print("\n### This file is not in the correct 'VEGA' folder template!")
                print(
                    "\n-->  Please put the file in the right directory or fix the folder template then try again.")
                ExitProgram()
        else:
            user_data['vehicle_name'] = None
            print("\n### It is not a " + f_format + " file !")
            print("\n-->  Please import a", f_format, "file")
            ExitProgram()
    elif user_drivers['DoXMLtoAVL'] and not user_drivers['Prompt_xml_file'] and not user_data[
        'vehicle_name']:
        print("\n### Can't convert from XML to AVL without asking the file!")
        print("\n\n-->  Check 'Import .xml' then try again.")
        winsound.Beep(200, 200)
        winsound.Beep(150, 400)
        ExitProgram()

    # If 'user_data['pathdir']' doesn't exist the program stops
    try:
        user_data['pathdir']
    except NameError:
        print("\n### Default path is unknown...");
        ExitProgram()

    # -------------Setting work paths------------#
    VEGAdir = os.path.join(os.getcwd(), 'VEGA')
    #    VEGAdir = user_data['pathdir'] # work directory for an aircraft multi disciplinary analysis
    #    inputdir =  VEGAdir+'\\Input' # where the .csv file has been exported by OpenVSP/DegenGeom
    #    aerodir =   VEGAdir+'\\Aerodynamics'
    #    avldir =    aerodir+'\\AVL' # AVL input directory
    openvspdir = VEGAdir + '\\OpenVSP'
    #    codedir =   VEGAdir+'\\Code' # Python files folder
    inputdir = os.path.join(VEGAdir, 'Input')
    #    inputdir = VEGAdir
    aerodir = os.path.join(VEGAdir, 'Aerodynamics')
    avldir = os.path.join(aerodir, 'AVL')
    #    openvspdir = os.path.join(os.getcwd(),'OpenVSP-3.5.1-win32')
    codedir = os.path.join(VEGAdir, 'Code')
    print(avldir)
    VEGAready = True  # This variable allows the program to run, otherwise it will stop the process
    #    ERRORS = [] # List of all errors that could lead to critical mistakes

    # --------Checking work paths existence------#
    if os.path.exists(VEGAdir):  # We are checking for existing folders in the work directory
        os.chdir(VEGAdir)
        print("Work path set to:\n     ", VEGAdir)
        print("\nChecking the paths...")
        if not os.path.exists(inputdir):
            VEGAready = False
            print("### 'Input' folder is missing")
        if not os.path.exists(aerodir):
            VEGAready = False
            print("### 'Aerodynamics' folder is missing")
        if not os.path.exists(avldir):
            VEGAready = False
            print("### 'AVL' folder is missing")
        if not os.path.exists(openvspdir):
            VEGAready = False
            print("### 'OpenVSP' folder is missing")
        #    if not os.path.exists(weightsdir):
        #        VEGAready = False
        #        print("### 'Weights' folder is missing")
        #    if not os.path.exists(inertia):
        #        VEGAready = False
        #        print("### 'Inertia' folder is missing")
        #    if not os.path.exists(propuldir):
        #        VEGAready = False
        #        print("### 'Propulsion' folder is missing")
        #    if not os.path.exists(simdir):
        #        VEGAready = False
        #        print("### 'Simulator' folder is missing")
        if not os.path.exists(codedir):
            VEGAready = False
            print("### 'Code' folder is missing")

        if VEGAready: print("     VEGA's folders are ready.")
    else:
        VEGAready = False
    print("### Work path not found !")

    # ------------Getting input files------------#
    #    os.chdir(VEGAdir) # We are going to look for files in the work folder
    VEGAdir = os.path.join(os.getcwd(), '/VEGA')
    main_xml_file = user_data['vehicle_name'] + '.xml'  # Reference input file of the vehicle
    vsp3_file = user_data['vehicle_name'] + '.vsp3'  # Input file for OpenVSP
    degengeom_file = user_data['vehicle_name'] + '_DegenGeom.csv'  # File generated with OpenVSP

    if os.path.exists(inputdir + '\\' + main_xml_file):  # Checking if the reference xml file exists
        print("\n     Found file: " + main_xml_file)
    else:
        print("\n     Main XML file not found, continuing process...")
    if os.path.exists(openvspdir + '\\' + degengeom_file):  # Checking if the csv file exists
        print("     Found file: " + degengeom_file.split('.csv')[0])
    else:
        if user_drivers['DoOpenVSPtoAVLconversion']: print(
            "\n     CSV file not found, continuing...")
    if os.path.exists(openvspdir + '\\' + vsp3_file):  # Checking if the vsp3 file exists
        print("     Found file: " + vsp3_file.split(openvspdir + '.vsp3')[0])
    else:
        if user_drivers['DoOpenVSPtoAVLconversion']:
            if user_drivers['DoXMLtoAVL']:
                print("\n     VSP3 file not found, continuing...")
            else:
                VEGAready = False
                print("\n     Working with the input XML...")
                print("\n/!\# Needed VSP3 file not found #/!\ \n")
                print("-->  Put a .vsp3 file into the 'OpenVSP' folder here, then try again:")
                print("     " + inputdir)
        else:
            if user_drivers['DoRunAVL']:
                print("\n     Skipping OpenVSP-to-AVL conversion, running AVL")
            else:
                print("\n     Nothing to run...")

    # -----------Import custom libraries---------#
    os.chdir(codedir)
    #    import OpenVSP2AVL_vsp3reader as VSP3Reader # VSP3 reader functions
    #    import OpenVSP2AVL_avlwriter #as writeAVL # Code generating .avl file
    import OpenVSP2AVL_degengeom  # as DegenGeom # Extracts data from .csv file
    #    import OpenVSP2AVL_runavl #as RunAVL # We automatically run AVL after writing the .avl file.
    import XMLGeometryExtractor  # Geometry parser from the input XML

    if not VEGAready:
        print("\n\n-->  Check work directories and files then try again.")
        ExitProgram()

    #####--------Program initialized--------#####

    #####---------Launching program---------#####
    init_time = time.time()
    print("\nLaunching program on", time.ctime())

    # ==================================================================================================<
    # ----------- Getting XML Geometry-----------#
    if user_drivers['DoXMLtoAVL']:
        os.chdir(inputdir)
        xml_geometry = XMLGeometryExtractor.getXMLGeom(main_xml_file)

    # ------ Generate VSP3 Geometry from XML ----#
    os.chdir(openvspdir)
    if user_drivers['DoXMLtoAVL']:
        if os.path.exists(main_xml_file):
            os.remove(main_xml_file)

        os.chdir(inputdir)
        shutil.copy(main_xml_file, openvspdir)

        os.chdir(openvspdir)
        XMLGeometryExtractor.createVSP3Geom(main_xml_file, inputdir, xml_geometry)
        while not os.path.exists(vsp3_file):
            print('.')
        if os.path.exists(main_xml_file):
            os.remove(main_xml_file)

            # ------ Generate DegenGeom from OpenVSP ----#
    if user_drivers['DoOpenVSPtoAVLconversion']:
        print("\n## Initializing OpenVSP-2-AVL conversion ##")
        #    os.chdir(openvspdir)
        if os.path.exists(vsp3_file):  # and not os.path.exists(degengeom_file):
            OpenVSP2AVL_degengeom.writeCSVfile(vsp3_file)

    #    #-------Reading DegenGeom from OpenVSP------#
    #        while not os.path.exists(degengeom_file):
    #            print('.')
    #        VSP3Data = VSP3Reader.getVSP3data(vsp3_file)
    #        degengeom_components = OpenVSP2AVL_degengeom.getCSVcomponents(degengeom_file,VSP3Data)
    #        for dcomp in degengeom_components:
    #            if user_drivers['Dev']['components_data']:
    #                print("     "+dcomp.name),
    #                if dcomp.IsFin: print("(Vertical surface)"),
    #                if dcomp.span: print("\n        span =",dcomp.span),
    #                if dcomp.area: print(", area =",dcomp.area),
    #                if dcomp.mac: print(MAC =",dcomp.mac)
    #            if not dcomp.mac: print("     MAC hasn't been calculated for "+dcomp.name)
    #
    #        if user_drivers['MergeAllComponents']:
    #            for c in degengeom_components:
    #                c.component = 1 # Set component "1" to all surfaces and bodies
    #            print('\n/!\ "COMPONENT = 1" has been set for every surfaces and bodies!')
    #
    #    #-------- Postprocessing finished ----------#
    #    #==================================================================================================<
    #    #------------ Writing AVL file--------------#
    #        os.chdir(avldir)
    #        if degengeom_components:
    #            if user_drivers['DoXMLtoAVL']:
    #                updated_components = OpenVSP2AVL_degengeom.componentCompletion(degengeom_components,xml_geometry)
    #            else:
    #                updated_components = OpenVSP2AVL_degengeom.UpdateAllComponents(degengeom_components)
    #
    #            if user_drivers['Dev']['components_list']:
    #                print("\nDev - components_list:")
    #                for c in updated_components:
    #                    print(c.name)
    #
    #            if user_drivers['Dev']['sections_list']:
    #                print("\nDev - sections_list:")
    #                for c in updated_components:
    #                    print("\n",c.name,c.sections)
    #
    #            if user_drivers['Dev']['sections_coords']:
    #                print("\nDev - sections_coords:")
    #                for c in updated_components:
    #                    print("\n",c.name)
    #                    for s in c.sections:
    #                        if len(s.coordinates)>1:
    #                            print(s.name.split(c.name+"_")[1], s.coordinates[0], s.coordinates[-1])
    #
    #            if user_drivers['Dev']['controls_list']:
    #                print("\nDev - controls_list:")
    #                for c in updated_components:
    #                    print("\n",c.name)
    #                    for s in c.sections:
    #                        if not s.controls == []:
    #                            print(s.name,s.controls)
    #                        else:
    #                            print(s.name,"has no controls.")
    #
    #            avl_file = OpenVSP2AVL_avlwriter.writeAVLfile(user_data,updated_components)
    #
    #        else:
    #            print("No components have been found in the degenerated geometry !")
    #
    #        print('\n## Conversion finished ###\n')
    #
    #        if user_drivers['ViewDegenGeometry']:
    #            import GeometryViewer # this allows the user to show a cloud of coordinates into a graph
    #            GeometryViewer.showDegenGeom(degengeom_components)
    #
    #    #--- Running AVL then exporting results ----#
    #
    #    #==================================================================================================<
    #    os.chdir(avldir)
    #    if user_drivers['DoRunAVL']:
    #        if not user_drivers['DoOpenVSPtoAVLconversion']:
    #            avl_file = user_data['vehicle_name']+".avl"
    #        print
    #        OpenVSP2AVL_runavl.runAVL(avldir,avl_file,aerodir+'\\Results')

    print("\nElapsed process time:", round(time.time() - init_time, 2), "seconds")
    print("Finished on", time.ctime())

    # from tkMessageBox import showinfo
    # showinfo("FINISHED!", "Elapsed process time: "+str(round(time.time()-init_time,3))+" seconds\nFinished on "+str(time.ctime()))

    # print('\n## Errors list ###\n')
    # for err in ERRORS:
    #    print(err)

    ExitProgram()
