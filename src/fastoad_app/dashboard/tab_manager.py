#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
#
# import panel as pn
# import param
# from panel.viewable import Viewable
# from ruamel.yaml import YAML
#
#
# from fastoad.mdao.problem import FASTOADProblem
#
# pn.extension("codeeditor")
#
#
# class TabViewer(pn.viewable.Viewer):
#     tabs = pn.param.Tabs()
#
#     def __panel__(self) -> Viewable:
#         return self.tabs
#
#
# class BaseTab(TabViewer):
#     data_tab = pn.param.Column(name="Data")
#     visu_tab = pn.param.Column(name="Visualisation")
#     problem = param.ClassSelector(class_=FASTOADProblem, instantiate=False)
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.tabs.extend([self.data_tab, self.visu_tab])
#
#
# class MainTab(pn.viewable.Viewer):
#     conf_tab = pn.param.Column(name="Data")
#     tabs = pn.param.Tabs()
#
#     def __panel__(self) -> Viewable:
#         return self.tabs
#
#     def load_configuration_file(self, file_path):
#         yaml = YAML(typ="safe")
#         with open(file_path) as yaml_file:
#             self.conf_editor.value = yaml.load(yaml_file)
#
#
# class AppTabs(BaseTab):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.tabs.clear()
#         self.main_tab = MainTab()
#         self.tabs.append(self.main_tab)
#
#     def load_configuration_file(self, file_path):
#         pass
