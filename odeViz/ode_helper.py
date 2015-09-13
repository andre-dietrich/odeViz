# -*- coding: utf-8 -*-
#    Copyright (C) 2015 by
#    André Dietrich <dietrich@ivs.cs.uni-magdeburg.de>
#    Sebastian Zug <zug@ivs.cs.uni-magdeburg.de>
#    All rights reserved.
#    BSD license.

import ode

def loadObj(filename):
    faces = []
    vertices = []

    modelFile = open(filename, "r")
    for line in modelFile.readlines():
        line = line.strip()

        if len(line) == 0 or line.startswith("#"):
            continue

        line = " ".join(line.split())
        data = line.split(" ")
        if data[0] == "v":
            vertices.append((float(data[1].replace(",", ".")),
                             float(data[2].replace(",", ".")),
                             float(data[3].replace(",", "."))))

        if data[0] == "f":
            vertex1 = int(data[1].split("/")[0])-1
            vertex2 = int(data[2].split("/")[0])-1
            vertex3 = int(data[3].split("/")[0])-1
            faces.append((vertex1, vertex2, vertex3))

    triMesh = ode.TriMeshData()
    triMesh.build(vertices, faces)

    return triMesh
