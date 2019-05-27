"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
from math import fabs
# pylint:disable=E302 # 
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
                    1] + (elem[0] - b[j][0]) / (b[j + 1][0] - b[j][0]) * (b[j + 1][1] - b[j][1])
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