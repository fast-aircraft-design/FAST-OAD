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
import os.path as pth

import pytest

from fastoad.io.xml import XPathReader
from fastoad.modules.aerodynamics.openvsp.openvsp import OpenVSP
from tests.conftest import root_folder

OPENVSP_DIR = pth.join(root_folder, 'OpenVSP-3.5.1-win32')
OPENVSP_RESULTS = pth.join(pth.dirname(__file__), 'results')

TMP_DIR = pth.join(pth.dirname(__file__), 'tmp')


def get_OpenVSP():
    openvsp = OpenVSP()
    openvsp.options['ovsp_dir'] = OPENVSP_DIR
    openvsp.options['result_dir'] = OPENVSP_RESULTS
    openvsp.options['tmp_dir'] = TMP_DIR

    os.makedirs(OPENVSP_RESULTS, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    return openvsp


@pytest.fixture(scope="module")
def inputs():
    reader = XPathReader(pth.join(pth.dirname(__file__), 'data', 'A320base_units.xml'))

    inputs = {
        'geometry:wing_l2': reader.get_float('Aircraft/geometry/wing/l2_wing'),
        'geometry:wing_y2': reader.get_float('Aircraft/geometry/wing/y2_wing'),
        'geometry:wing_l3': reader.get_float('Aircraft/geometry/wing/l3_wing'),
        'geometry:wing_x3': reader.get_float('Aircraft/geometry/wing/x3_wing'),
        'geometry:wing_y3': reader.get_float('Aircraft/geometry/wing/y3_wing'),
        'geometry:wing_l4': reader.get_float('Aircraft/geometry/wing/l4_wing'),
        'geometry:wing_x4': reader.get_float('Aircraft/geometry/wing/x4_wing'),
        'geometry:wing_y4': reader.get_float('Aircraft/geometry/wing/y4_wing'),
        'geometry:wing_area': reader.get_float('Aircraft/geometry/wing/wing_area'),
        'geometry:wing_span': reader.get_float('Aircraft/geometry/wing/span'),
        'geometry:wing_l0': reader.get_float('Aircraft/geometry/wing/l0_wing'),
    }

    return inputs


def test_write_vspfile(inputs):
    openvsp = get_OpenVSP()
    openvsp.setup()
    filename = 'test.vspscript'

    geometry_vector = [
        inputs['geometry:wing_l2'],
        inputs['geometry:wing_y2'],
        inputs['geometry:wing_y3'],
        inputs['geometry:wing_x3'],
        inputs['geometry:wing_y3'],
        inputs['geometry:wing_l4'],
        inputs['geometry:wing_x4'],
        inputs['geometry:wing_y4']
    ]

    openvsp._write_vsp_file(geometry_vector, filename)
    assert pth.exists(pth.join(TMP_DIR, filename))
    os.remove(pth.join(TMP_DIR, filename))


def test_write_vspaero_file(inputs):
    openvsp = get_OpenVSP()
    openvsp.setup()
    filename = 'test.vspaero'

    wing_params = [
        inputs['geometry:wing_area'],
        inputs['geometry:wing_l0'],
        inputs['geometry:wing_span']
    ]

    openvsp._write_vspaero_file((0.75, 35000), wing_params, filename)
    assert pth.exists(pth.join(TMP_DIR, filename))

    # os.remove(pth.join(TMP_DIR, filename))


def test_run(inputs):
    openvsp = get_OpenVSP()
    openvsp.setup()

    inputs['AoA_min'] = 0.0
    inputs['AoA_max'] = 0.5
    inputs['AoA_step'] = 0.1
    inputs['openvsp:mach'] = 0.75
    inputs['openvsp:altitude'] = 32000

    outputs = {}

    openvsp.compute(inputs, outputs)

    assert pth.exists(pth.join(TMP_DIR, OpenVSP.vspscript_filename))
    # os.remove(pth.join(TMP_DIR, OpenVSP.vspscript_filename))

    assert pth.exists(pth.join(TMP_DIR, OpenVSP.result_filename))
    # os.remove(pth.join(TMP_DIR, OpenVSP.result_filename))

# def test_run_takeoff(inputs):
#
#     inputs['AoA_min'] = 0.0
#     inputs['AoA_max'] = 0.1
#     inputs['AoA_step'] = 0.1
#     inputs['openvsp:mach'] = 0.75
#     inputs['openvsp:altitude'] = 32000
#
#     self.openvsp.run(0.0, 0.1, 0.1, 0.75, 32000, takeoff=True)
#     self.assertTrue(
#         pth.exists(pth.join(TMP_DIR, OpenVSP.vspscript_filename)))
#     os.remove(pth.join(TMP_DIR, OpenVSP.vspscript_filename))
#     self.assertTrue(
#         pth.exists(pth.join(TMP_DIR, OpenVSP.takeoff_result_filename)))
#     os.remove(pth.join(TMP_DIR, OpenVSP.takeoff_result_filename))


# class TestOpenVSP(unittest.TestCase):
#     fpath = pth.join(pth.dirname(__file__), 'data', 'A320base_units.xml')
#
#     def setUp(self):
#         aircraft_xml = AircraftXml(self.fpath)
#         self.aircraft = aircraft_xml.get_aircraft()
#         if not pth.exists(TMP_DIR):
#             os.makedirs(TMP_DIR)
#         if not pth.exists(OPENVSP_RESULTS):
#             os.makedirs(OPENVSP_RESULTS)
#         self.openvsp = OpenVSP(
#             self.aircraft, resultdir=OPENVSP_RESULTS, tmpdir=TMP_DIR)
#
#     def tearDown(self):
#         try:
#             os.rmdir(TMP_DIR)
#             os.rmdir(OPENVSP_RESULTS)
#         except OSError:
#             pass
#
#     def test_write_vspfile(self):
#         filename = 'test.vspscript'
#         self.openvsp._write_vsp_file(filename)
#         self.assertTrue(pth.exists(pth.join(TMP_DIR, filename)))
#         os.remove(pth.join(TMP_DIR, filename))
#
#     def test_write_vspaero_file(self):
#         filename = 'test.vspaero'
#         self.openvsp._write_vspaero_file(0.75, 35000, filename)
#         self.assertTrue(pth.exists(pth.join(TMP_DIR, filename)))
#         os.remove(pth.join(TMP_DIR, filename))
#
#     def test_run(self):
#         self.openvsp.run(0.0, 0.1, 0.1, 0.75, 32000)
#         self.assertTrue(
#             pth.exists(pth.join(TMP_DIR, OpenVSP.vspscript_filename)))
#         os.remove(pth.join(TMP_DIR, OpenVSP.vspscript_filename))
#         self.assertTrue(
#             pth.exists(pth.join(TMP_DIR, OpenVSP.result_filename)))
#         os.remove(pth.join(TMP_DIR, OpenVSP.result_filename))
#
#     def test_run_takeoff(self):
#         self.openvsp.run(0.0, 0.1, 0.1, 0.75, 32000, takeoff=True)
#         self.assertTrue(
#             pth.exists(pth.join(TMP_DIR, OpenVSP.vspscript_filename)))
#         os.remove(pth.join(TMP_DIR, OpenVSP.vspscript_filename))
#         self.assertTrue(
#             pth.exists(pth.join(TMP_DIR, OpenVSP.takeoff_result_filename)))
#         os.remove(pth.join(TMP_DIR, OpenVSP.takeoff_result_filename))
