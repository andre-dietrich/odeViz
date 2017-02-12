# -*- coding: utf-8 -*-
#    Copyright (C) 2015 by
#    André Dietrich <dietrich@ivs.cs.uni-magdeburg.de>
#    Sebastian Zug <zug@ivs.cs.uni-magdeburg.de>
#    All rights reserved.
#    BSD license.

from vtk import vtkPolyDataMapper, vtkActor, vtkTransform, vtkCubeSource,\
    vtkLineSource, vtkPolyData, vtkPoints, vtkCellArray, vtkSphereSource,\
    vtkCylinderSource, vtkAppendPolyData, vtkContourFilter, vtkCylinder,\
    vtkPlane, vtkSphere, vtkImplicitBoolean, vtkSampleFunction, vtkDiskSource,\
    vtkMatrix4x4

import numpy
#import ode


class ODE_Object():
    """ Standard class for visualizations of ODE-Geometries  """
    def __init__(self, geom, ident=None, mapper=0):
        self.ident = ident

        self.geom = geom

        self.mapper = vtkPolyDataMapper()
        self.act = vtkActor()
        self.trans = vtkTransform()

        if mapper == 0:
            self.mapper.SetInputConnection(self.src.GetOutputPort())
        else:
            self.mapper.SetInputData(eval("self.src" + mapper))

        self.mapper.ScalarVisibilityOff()

        self.act.SetMapper(self.mapper)
        self.act.SetUserTransform(self.trans)

        # for speed increase
        self.RotateX = self.trans.RotateX
        self.SetMatrix = self.trans.SetMatrix
        self.isEnabled = self.geom.isEnabled
        self.geomgetRotation = self.geom.getRotation
        self.geomgetPosition = self.geom.getPosition

    def getRotation(self):
        return self.geomgetRotation()

    def getPosition(self):
        return self.geomgetPosition()

    def update(self):
        if self.isEnabled():
            (x, y, z) = self.getPosition()
            R = self.getRotation()

            self.SetMatrix([R[0], R[1], R[2], x,
                            R[3], R[4], R[5], y,
                            R[6], R[7], R[8], z,
                            0,    0,    0,    1])


class ODE_Box(ODE_Object):
    """ VTK visualization of class ode.GeomBox  """
    def __init__(self, geom, ident=None):

        self.src = vtkCubeSource()
        ODE_Object.__init__(self, geom, ident)

        (xsize, ysize, zsize) = self.geom.getLengths()

        self.src.SetXLength(xsize)
        self.src.SetYLength(ysize)
        self.src.SetZLength(zsize)


class ODE_Ray(ODE_Object):
    """ VTK visualization of class ode.GeomRay  """
    def __init__(self, geom, ident=None):

        self.src = vtkLineSource()
        ODE_Object.__init__(self, geom, ident, ".GetOutput()")

        length = self.geom.getLength()

        (px, py, pz), (rx, ry, rz) = self.geom.get()
        (rx, ry, rz) = self.norm(rx, ry, rz, length)

        self.src.SetPoint1(px, py, pz)
        self.src.SetPoint2(px+rx, py+ry, pz+rz)

    def norm(self, vx, vy, vz, length=1):
        norm = (vx**2 + vy**2 + vz**2)**0.5

        vx = (vx/norm) * length
        vy = (vy/norm) * length
        vz = (vz/norm) * length

        return (vx, vy, vz)

    def update(self):
        if self.isEnabled():
            length = self.geom.getLength()

            (px, py, pz), (rx, ry, rz) = self.geom.get()
            (rx, ry, rz) = self.norm(rx, ry, rz, length)

            self.src.SetPoint1(px, py, pz)
            self.src.SetPoint2(px+rx, py+ry, pz+rz)


class ODE_TriMesh(ODE_Object):
    """ VTK visualization of class ode.GeomTriMesh  """
    def __init__(self, geom, ident=None):

        self.src = vtkPolyData()
        ODE_Object.__init__(self, geom, ident, "")

        points = vtkPoints()
        vertices = vtkCellArray()

        for i in range(geom.getTriangleCount()):
            (p0, p1, p2) = geom.getTriangle(i)

            id0 = points.InsertNextPoint(p0)
            id1 = points.InsertNextPoint(p1)
            id2 = points.InsertNextPoint(p2)

            vertices.InsertNextCell(3)
            vertices.InsertCellPoint(id0)
            vertices.InsertCellPoint(id1)
            vertices.InsertCellPoint(id2)

        self.src.SetPoints(points)
        self.src.SetPolys(vertices)


#    def update(self):
#        if self.isEnabled():
#            (x,y,z) = self.getPosition()
#            R = self.getRotation()
#
#            self.SetMatrix([R[0], R[1], R[2], x,
#                            R[3], R[4], R[5], y,
#                            R[6], R[7], R[8], z,
#                            0,    0,    0,    1])


class ODE_Sphere(ODE_Object):
    """ VTK visualization of class ode.GeomSphere  """
    def __init__(self, geom, ident=None):
        self.src = vtkSphereSource()
        ODE_Object.__init__(self, geom, ident)

        radius = self.geom.getRadius()

        self.src.SetRadius(radius)
        self.src.SetThetaResolution(20)
        self.src.SetPhiResolution(11)


class ODE_Cylinder(ODE_Object):
    """ VTK visualization of class ode.GeomCylinder  """
    def __init__(self, geom, ident=None):
        self.src = vtkCylinderSource()

        ODE_Object.__init__(self, geom, ident)

        (radius, height) = self.geom.getParams()

        self.src.SetRadius(radius)
        self.src.SetHeight(height)

        self.src.SetResolution(20)

    def update(self):
        if self.isEnabled():
            ODE_Object.update(self)
            self.RotateX(90)


class ODE_Capsule_imp(ODE_Object):
    """ VTK visualization of class ode.GeomCapsule  """
    def __init__(self, geom, ident=None):

        self.src = vtkAppendPolyData()

        ODE_Object.__init__(self, geom, ident)

        (radius, height) = geom.getParams()

        cylinder = vtkCylinderSource()
        cylinder.SetResolution(20)
        cylinder.SetRadius(radius)
        cylinder.SetHeight(height)

        sphere_1 = vtkSphereSource()
        sphere_1.SetThetaResolution(20)
        sphere_1.SetPhiResolution(11)
        sphere_1.SetRadius(radius)
        sphere_1.SetCenter(0, 0.5*height, 0)

        sphere_2 = vtkSphereSource()
        sphere_2.SetThetaResolution(20)
        sphere_2.SetPhiResolution(11)
        sphere_2.SetRadius(radius)
        sphere_2.SetCenter(0, -0.5*height, 0)

        self.src.AddInput(cylinder.GetOutput())
        self.src.AddInput(sphere_1.GetOutput())
        self.src.AddInput(sphere_2.GetOutput())

    def update(self):
        if self.isEnabled():
            ODE_Object.update(self)
            self.RotateX(90)


class ODE_Capsule(ODE_Object):
    """ VTK visualization of class ode.GeomCapsule  """
    def __init__(self, geom, ident=None):

        self.src = vtkContourFilter()

        ODE_Object.__init__(self, geom, ident)

        (radius, height) = geom.getParams()

        cylinder = vtkCylinder()
        cylinder.SetRadius(radius)

        vertPlane = vtkPlane()
        vertPlane.SetOrigin(0, height/2, 0)
        vertPlane.SetNormal(0, 1, 0)

        basePlane = vtkPlane()
        basePlane.SetOrigin(0, -height/2, 0)
        basePlane.SetNormal(0, -1, 0)

        sphere_1 = vtkSphere()
        sphere_1.SetCenter(0, -height/2, 0)
        sphere_1.SetRadius(radius)

        sphere_2 = vtkSphere()
        sphere_2.SetCenter(0, height/2, 0)
        sphere_2.SetRadius(radius)

        # Combine primitives, Clip the cone with planes.
        cylinder_fct = vtkImplicitBoolean()
        cylinder_fct.SetOperationTypeToIntersection()
        cylinder_fct.AddFunction(cylinder)
        cylinder_fct.AddFunction(vertPlane)
        cylinder_fct.AddFunction(basePlane)

        # Take a bite out of the ice cream.
        capsule = vtkImplicitBoolean()
        capsule.SetOperationTypeToUnion()
        capsule.AddFunction(cylinder_fct)
        capsule.AddFunction(sphere_1)
        capsule.AddFunction(sphere_2)

        capsule_fct = vtkSampleFunction()
        capsule_fct.SetImplicitFunction(capsule)
        capsule_fct.ComputeNormalsOff()
        capsule_fct.SetModelBounds(-height-radius, height+radius,
                                   -height-radius, height+radius,
                                   -height-radius, height+radius)

        self.src.SetInputConnection(capsule_fct.GetOutputPort())
        self.src.SetValue(0, 0.0)

    def update(self):
        if self.isEnabled():
            ODE_Object.update(self)
            self.RotateX(90)


class ODE_Plane(ODE_Object):
    """ VTK visualization of class ode.GeomPlane  """
    def __init__(self, geom, ident=None):
        self.src = vtkDiskSource()
        ODE_Object.__init__(self, geom, ident)
        self.size = 2000

        self.src.SetOuterRadius(self.size)
        self.src.SetInnerRadius(0)
        self.src.SetCircumferentialResolution(30)

    def getRotation(self):
        (a, b, c), d = self.geom.getParams()

        p1 = [.5, .5, .0]
        p2 = [.1, .7, .2]

        if a != 0:
            p1[0] = (b*p1[1] + c*p1[2] - d) / -a
            p2[0] = (b*p2[1] + c*p2[2] - d) / -a
        elif b != 0:
            p1[1] = (a*p1[0] + c*p1[2] - d) / -b
            p2[1] = (a*p2[0] + c*p2[2] - d) / -b
        elif c != 0:
            p1[2] = (a*p1[0] + b*p1[1] - d) / -c
            p2[2] = (a*p2[0] + b*p2[1] - d) / -c

        w = [p2[0]-p1[0],
             p2[1]-p1[1],
             p2[2]-p1[2]]

        v = [w[1]*c - w[2]*b,
             w[2]*a - w[0]*c,
             w[0]*b - w[1]*a]

        w_norm = (w[0]**2 + w[1]**2 + w[2]**2)**0.5
        w = [w[0]/w_norm,
             w[1]/w_norm,
             w[2]/w_norm]

        v_norm = (v[0]**2 + v[1]**2 + v[2]**2)**0.5
        v = [v[0]/v_norm,
             v[1]/v_norm,
             v[2]/v_norm]

        return [v[0], w[0], a,
                v[1], w[1], b,
                v[2], w[2], c]

    def getPosition(self):
        (a, b, c), d = self.geom.getParams()
        h = d/(a**2 + b**2 + c**2)
        return [a*h, b*h, c*h]
