#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import numpy as np


def convert_8digit_nastran(value):
    if isinstance(value, (np.ndarray, list)) and len(value) == 1:
        value = value[0]
    elif not isinstance(value, (int, float, np.int32, np.float32)):
        msg = "Value MUST be int, float or array-like of size 1 while it is : %s" % type(value)
        raise TypeError(msg)
    if isinstance(value, (float, np.float32)):
        if value > 0.0:
            if value < 0.000001:
                strval = format(value, "8.2e")
            elif value < 1:
                strval = format(value, "8.6f")
            elif value < 10:
                strval = format(value, "8.5f")
            elif value < 100:
                strval = format(value, "8.4f")
            elif value < 1000:
                strval = format(value, "8.3f")
            elif value < 10000:
                strval = format(value, "8.2f")
            elif value >= 10000:
                strval = format(value, "8.2e")
        elif value < 0.0:
            if value > -0.00001:
                strval = format(value, "8.2e")
            elif value > -1:
                strval = format(value, "8.6f")
            elif value > -10:
                strval = format(value, "8.5f")
            elif value > -100:
                strval = format(value, "8.4f")
            elif value > -1000:
                strval = format(value, "8.3f")
            elif value <= -1000:
                strval = format(value, "8.2e")
        else:
            strval = format(value, "8.6f")
    elif isinstance(value, (int, np.int32)):
        strval = format(value, "8d")
        if len(strval) > 8:
            msg = "Integer field too long"
            raise RuntimeError(msg)
    value_8dgt = str(strval)
    return value_8dgt


def get_nodes_cards(comp_name, nodes, id_basis):
    strg = ["$ Component:   " + comp_name + "\n \n" + "$$ Grids: \n"]
    for i in range(np.size(nodes, axis=0)):
        id0 = convert_8digit_nastran(id_basis + i)
        c_1 = convert_8digit_nastran(nodes[i, 0])
        c_2 = convert_8digit_nastran(nodes[i, 1])
        c_3 = convert_8digit_nastran(nodes[i, 2])
        strg.append("GRID," + id0 + ",," + c_1 + "," + c_2 + "," + c_3 + "\n \n")
    return strg


def get_props_cards(comp_name, props, id_basis):
    strg = ["$$ Beams definition and properties:  \n"]
    for i in range(np.size(props, axis=0)):
        b_ids = convert_8digit_nastran(id_basis + i + 1000)
        p_ids = convert_8digit_nastran(id_basis + i + 11000)
        p_mat = convert_8digit_nastran(id_basis + 111000)
        if comp_name == "wing" or comp_name == "horizontal_tail" or comp_name == "strut":
            if i < np.size(props, axis=0) / 2:
                id1 = convert_8digit_nastran(id_basis + i)
                id2 = convert_8digit_nastran(id_basis + i + 1)
            else:
                id1 = convert_8digit_nastran(id_basis + i + 1)
                id2 = convert_8digit_nastran(id_basis + i + 2)
        else:
            id1 = convert_8digit_nastran(id_basis + i)
            id2 = convert_8digit_nastran(id_basis + i + 1)
        if comp_name != "vertical_tail":
            v_1 = convert_8digit_nastran(0.0)
            v_2 = convert_8digit_nastran(0.0)
            v_3 = convert_8digit_nastran(1.0)
        else:
            v_1 = convert_8digit_nastran(0.0)
            v_2 = convert_8digit_nastran(1.0)
            v_3 = convert_8digit_nastran(0.0)
        area = convert_8digit_nastran(props[i, 0])
        i_1 = convert_8digit_nastran(props[i, 1])
        i_2 = convert_8digit_nastran(props[i, 2])
        j = convert_8digit_nastran(props[i, 3])
        strg.append(
            "CBAR,"
            + b_ids
            + ","
            + p_ids
            + ","
            + id1
            + ","
            + id2
            + ","
            + v_1
            + ","
            + v_2
            + ","
            + v_3
            + "\n"
        )
        strg.append(
            "PBAR," + p_ids + "," + p_mat + "," + area + "," + i_1 + "," + i_2 + "," + j + "\n"
        )
    return strg


def get_mat_cards(mat_props, id_basis):
    strg = ["\n$$ Material card: \n"]
    p_mat = convert_8digit_nastran(id_basis + 111000)  # Only one Mat per comp until now
    young_modulus = convert_8digit_nastran(mat_props[0])
    mu = convert_8digit_nastran(mat_props[1])
    rho = convert_8digit_nastran(mat_props[2])
    strg.append("MAT1," + p_mat + "," + young_modulus + ",," + mu + "," + rho + "\n \n \n")
    return strg


def get_rbe_junction_cards(comp_name, nodes, id_basis):
    strg = ["$ Junction of " + comp_name + " symmetrical parts \n"]
    if comp_name == "wing" or comp_name == "horizontal_tail" or comp_name == "strut":
        id1 = id_basis
        id2 = convert_8digit_nastran(id_basis + int(np.size(nodes, axis=0) / 2))
        strg.append("RBE2," + str(90000000 + id_basis) + "," + str(id1) + ", 123456," + id2 + "\n")
    else:
        strg.append("$ Non-symmetrical component i.e. no need for junction \n")
    return strg


def get_forces_cards(component_name, forces, id_basis):
    strg = ["$ Component:   " + component_name + "\n \n" + "$$ Grids: \n", "$ Forces card : \n"]
    for i in range(0, np.size(forces, axis=0)):
        fid = convert_8digit_nastran(id_basis + i)
        f_x = convert_8digit_nastran(forces[i, 0])
        f_y = convert_8digit_nastran(forces[i, 1])
        f_z = convert_8digit_nastran(forces[i, 2])
        m_x = convert_8digit_nastran(forces[i, 3])
        m_y = convert_8digit_nastran(forces[i, 4])
        m_z = convert_8digit_nastran(forces[i, 5])
        strg.append("FORCE,11," + fid + ",," + f_x + ",1.,0.,0. \n")
        strg.append("FORCE,11," + fid + ",," + f_y + ",0.,1.,0. \n")
        strg.append("FORCE,11," + fid + ",," + f_z + ",0.,0.,1. \n")
        strg.append("MOMENT,11," + fid + ",," + m_x + ",1.,0.,0. \n")
        strg.append("MOMENT,11," + fid + ",," + m_y + ",0.,1.,0. \n")
        strg.append("MOMENT,11," + fid + ",," + m_z + ",0.,0.,1. \n")
    strg.append("\n" * 2)
    strg.append("\n" * 2)
    return strg


def get_spc_cards(spc_id, dof, id_basis):
    strg = ["$ Clamping \n", "SPC1, " + str(spc_id) + ", " + str(dof) + ", " + str(id_basis) + "\n"]
    return strg


def get_rbe_cards(component_name, master_name, master_nodes, slave_nodes, loc_cg):
    strg = []
    if master_name == "fuselage":
        ids = np.arange(0, np.size(master_nodes, axis=0)) + 2000000
        if component_name != "fuselage":
            dist = slave_nodes[0, 0] - master_nodes[:, 0]
        else:
            dist = master_nodes[:, 0] - loc_cg
    if master_name == "wing" and component_name == "strut":
        ids = np.arange(0, np.size(master_nodes, axis=0), dtype=int) + 1000000
        dist = slave_nodes[-1, 1] - master_nodes[:, 1]
    ind_sup = np.where(dist >= 0)
    ind_inf = np.where(dist <= 0)
    ind_min = np.where(dist[ind_sup] == np.min(dist[ind_sup]))
    ind_max = np.where(dist[ind_inf] == np.max(dist[ind_inf]))
    sew_id1 = convert_8digit_nastran(ids[ind_sup][ind_min][0])
    sew_id2 = convert_8digit_nastran(ids[ind_inf][ind_max][0])
    d_1 = dist[ind_sup][ind_min][0]
    d_2 = abs(dist[ind_inf][ind_max][0])
    if d_1 < d_2:
        sew_id = sew_id1
    else:
        sew_id = sew_id2

    if component_name == "wing" and master_name != "wing":
        strg.append("\n$$ sewing fuselage / wings \n")
        strg.append("RBE2,91000001," + sew_id + ",123456,1000000 \n")

    if component_name == "horizontal_tail":
        strg.append("RBE2,93000001," + sew_id + ",123456,3000000 \n")
        strg.append("\n$$ sewing fuselage / htails \n")

    if component_name == "vertical_tail":
        strg.append("\n$$ sewing fuselage / vtails \n")
        strg.append("RBE2,94000001," + sew_id + ",123456,4000000 \n")

    if component_name == "strut" and master_name == "fuselage":
        strg.append("\n$$ sewing fuselage / strut \n")
        strg.append("RBE2,95000001," + sew_id + ",123456,5000000 \n")
    if component_name == "strut" and master_name == "wing":
        id_slave1 = int(5000000 + np.size(slave_nodes, axis=0) / 2)
        id_slave2 = int(5000000 + np.size(slave_nodes, axis=0))
        sew_id1 = int(sew_id - np.size(master_nodes, axis=0) / 2)
        strg.append("\n$$ sewing fuselage / strut \n")
        strg.append("RBE2,95000002," + sew_id1 + ",123456," + id_slave1 + " \n")
        strg.append("RBE2,95000003," + sew_id + ",123456," + id_slave2 + " \n")

    return strg


def get_nastran_bdf(file_name, strg, sol="static", nz=0.0):
    with open(file_name, "w") as dat_file:
        if sol == "static":
            start_lines = [
                "ID A/C BEAM MODEL \n",
                "SOL 1 \n",
                "CEND \n",
                "TITLE = STATIC WING SIZING \n",
                "DISP = ALL \n",
                "STRESS = ALL \n",
                "SPCFORCE = ALL \n",
                "LOAD = 1 \n",
                "SPC = 1 \n",
                "\n",
                "BEGIN BULK \n \n",
            ]
            dat_file.writelines(start_lines)
            dat_file.writelines(strg)
            dat_file.writelines(
                [
                    "\n$ Gravity and Loads cards: \n" "GRAV,10,,9.81,0.,0.,-1. \n \n",
                    "\nLOAD,1,1.," + convert_8digit_nastran(nz * 1.0) + ",10,1.,11 \n ",
                    "\nPARAM,GRIDSEQ,GRID\n\n",
                ]
            )
            dat_file.writelines(["\nENDDATA"])

        if sol == "dynamic":
            msg = "Not yet implemented"
            raise ValueError(msg)
