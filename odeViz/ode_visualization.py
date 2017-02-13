# -*- coding: utf-8 -*-
#    Copyright (C) 2015 by
#    André Dietrich <dietrich@ivs.cs.uni-magdeburg.de>
#    Sebastian Zug <zug@ivs.cs.uni-magdeburg.de>
#    All rights reserved.
#    BSD license.

from vtk import vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor, \
    vtkInteractorStyleTrackballCamera, vtkAxesActor, vtkTextActor, \
    vtkOrientationMarkerWidget, vtkWindowToImageFilter, vtkPNGWriter

from ode import Body, GeomBox, GeomSphere, GeomCapsule, GeomCCylinder, \
    GeomPlane, GeomTriMesh, GeomRay, GeomCylinder, CloseODE

from ode_objects import ODE_Box, ODE_Sphere, ODE_Plane, ODE_Ray, ODE_TriMesh, \
    ODE_Cylinder, ODE_Capsule

#import threading
from operator import eq
from time import time, sleep
from threading  import Thread
from thread import start_new_thread


class VTK_Visualization(Thread):
    """ Visualization-Window """
    def __init__(self):

        Thread.__init__(self)

        self.ren = vtkRenderer()

        self.win = vtkRenderWindow()
        self.win.AddRenderer(self.ren)

        self.iren = vtkRenderWindowInteractor()
        self.iren.SetRenderWindow(self.win)

        style = vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(style)

        self._ctrl = False

        self.iren.AddObserver("KeyPressEvent", self._KeypressCtrl)
        self.iren.AddObserver("KeyReleaseEvent", self._KeyreleaseCtrl)
        self.iren.AddObserver("ExitEvent", self._stop)

        axesActor = vtkAxesActor()
        self.axes = vtkOrientationMarkerWidget()
        self.axes.SetOrientationMarker(axesActor)
        self.axes.SetInteractor(self.iren)
        self.axes.EnabledOn()
        self.axes.InteractiveOn()
        self.axes.SetViewport(0, 0.8, 0.15, 1)
        self.ren.ResetCamera()

        # information
        self.info = vtkTextActor()
        self.info.SetDisplayPosition(10, 10)
        self.ren.AddActor(self.info)

        # window-definitions
        self.SetSize(800, 600)
        self.SetWindowName("odeViz")
        self.SetBackground(0.6, 0.6, 0.8)

    def SetSize(self, width, height):
        """ set the size of the window (width, height)  """
        self.win.SetSize(width, height)

    def SetWindowName(self, title):
        """ set the name of the window """
        self.win.SetWindowName(title)

    def SetBackground(self, red, green, blue):
        """ set background color (red, green, blue) """
        self.ren.SetBackground(red, green, blue)

    def GetActiveCamera(self):
        """ return the current camera """
        return self.ren.GetActiveCamera()

    def _KeypressCtrl(self, obj, event):
        key = obj.GetKeySym()

        if key == "Control_L" or key == "Control_R":
            self._ctrl = True

    def _KeyreleaseCtrl(self, obj, event):
        key = obj.GetKeySym()

        if key == "Control_L" or key == "Control_R":
            self._ctrl = False

    def _stop(self, obj, event):
        self.stop()

    def setInfo(self, info):
        self.info.SetInput(info)

    def screenshot(self, folder="", filename='screenshot', number=-1):
        if number < 0:
            number = ""
        else:
            number = str(number)

        # screenshot code:
        w2if = vtkWindowToImageFilter()
        w2if.SetInput(self.win)
        w2if.Update()

        writer = vtkPNGWriter()
        writer.SetFileName(folder+filename+"_"+number+".png")
        writer.SetInput(w2if.GetOutput())
        writer.Write()


class ODE_Visualization(VTK_Visualization):
    """ Visualization of the ODE-Space  """

    # status
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2
    statusString = ["stopped", "running", "paused"]

    def __init__(self, world, space, dt=0.01, updateStep=1):
        """Create an object of this class with an instance of the world and
           space. All geometric information is automatically extracted from the
           space and gets converted to adequat vtk-representations.
        """
        VTK_Visualization.__init__(self)
        self.world = world
        self.space = space
        self.dt = dt
        self.obj = set()

        self.simulationStatus = ODE_Visualization.RUNNING
        self.simulationTime = 0
        self.simulationStep = 0
        self.timeStart = 0
        self.updateStep = updateStep
        self.simulationViz = True
        self.recording = False

        self.iren.AddObserver("KeyPressEvent", self._Keypress)

        self.create()
        self._printInfo()

    def _printInfo(self):
        print ("odeViz")
        print ("======")
        print ("VisualizationToolKit (vtk) for the OpenDynamicsEngine")
        print ("")
        print ("Key-Press-Events")
        print ("----------------")
        print ("Ctrl + c|C -> print Camera-settings")
        print ("Ctrl + h|H -> take a screensHot")
        print ("Ctrl + p|P -> Pause and run simulation")
        print ("Ctrl + q|Q -> Quit simualtion")
        print ("Ctrl + s|S -> enable/disable StereoScopic view")
        print ("Ctrl + v|V -> enable/disable Visualization")

    def execute(self):
        """ execute one simulation step and update the view;
            overwrite this method to change the simulation
        """
        self.step(self.dt)
        self.update()

    def __execute(self, caller, event):
        sleep(0.01)

    def step(self, dt):
        if self.simulationStatus == ODE_Visualization.RUNNING:
            self.world.step(dt)

    def GetProperty(self, geom):
        """ return the VTK-Property for a given ode body or geometry """
        return self.GetActor(geom).GetProperty()

    def GetActor(self, geom):
        """ return the VTK-Actor for a given ode body or geometry """
        if type(geom) == Body:
            _find = lambda o: eq(o.geom.getBody(), geom)
        elif type(geom) == str:
            _find = lambda o: eq(o.geom.ident, geom)
        else:
            _find = lambda o: eq(o.geom, geom)
        for obj in self.obj:
            if _find(obj):
                return obj.act

    def create(self):
        """ this method searches the space for objects to visualize """
        for space in self.space:
            for i in range(space.getNumGeoms()):
                geom = space.getGeom(i)
                self.addGeom(geom)

    def start(self, iren_start=True):

        self.iren.Initialize()
        self.iren.AddObserver('TimerEvent', self.__execute)
        self.timerid = self.iren.CreateRepeatingTimer(10)
        self.timeStart = time()

        self.running = 1
        super(ODE_Visualization, self).start()

        if iren_start:
            self.iren.Start()

    def run(self):
        """ running the simulation, can be overwritten """
        while self.running:
            if self.simulationStatus == ODE_Visualization.RUNNING:
                self.execute(None, None)
                sleep(0.00001)

    def stop(self):
        """ stops the simulation """
        self.running = 0
        CloseODE()
        self.iren.DestroyTimer(self.timerid)
        self.iren.GetRenderWindow().Finalize()
        self.iren.TerminateApp()

    def pause(self, p=True):
        if p:
            self.simulationStatus = ODE_Visualization.PAUSED
        else:
            self.simulationStatus = ODE_Visualization.RUNNING

    def _Keypress(self, obj, event):
        key = obj.GetKeySym()

        # toggle shadows
        # Ctrl + s
#        if (key == "s" or key == "S") and self._ctrl:
#            print "shadow"

        # print current viewpoint coordinates
        # Crtl + c
        if (key == "c" or key == "C") and self._ctrl:
            (val1, val2, val3) = self.ren.GetActiveCamera().GetPosition()
            print ("Position:  ", val1, val2, val3)
            (val1, val2, val3) = self.ren.GetActiveCamera().GetFocalPoint()
            print ("FocalPoint:", val1, val2, val3)
            (val1, val2, val3) = self.ren.GetActiveCamera().GetViewUp()
            print ("ViewUp:    ", val1, val2, val3)

        # Ctrl + q -> stops the simulation
        if (key == "q" or key == "Q") and self._ctrl:
            self.stop()

        # Ctrl + q -> stops the simulation
        if (key == "h" or key == "H") and self._ctrl:
            self.screenshot(number=self.simulationTime)

        # pause or unpause
        # Ctrl + p
        if (key == "p" or key == "P") and self._ctrl:
            if self.simulationStatus == ODE_Visualization.PAUSED:
                self.simulationStatus = ODE_Visualization.RUNNING
            elif self.simulationStatus == ODE_Visualization.RUNNING:
                self.simulationStatus = ODE_Visualization.PAUSED

        if (key == "s" or key == "S") and self._ctrl:
            if self.win.GetStereoRender() == 0:
                self.win.SetStereoRender(1)
            else:
                self.win.SetStereoRender(0)

        if (key == "v" or key == "V") and self._ctrl:
            self.simulationViz = not self.simulationViz

        self.Keypress(key)

    def Keypress(self, key):
        """ overwrite this method to define own Keypress-Actions """
        pass

    def updateStatus(self):
        """ prints the current simulation-status and time """
        if self.simulationStatus == ODE_Visualization.RUNNING:
            self.simulationTime += self.dt
            self.simulationStep += 1

        info = "simulation\nstatus:  %s\nstep:    %i\nsim-time:  %f" % (
            ODE_Visualization.statusString[self.simulationStatus],
            self.simulationStep,
            self.simulationTime)

        #info = "simulation\nstatus:  %s\nstep:    %i\nsim-time:
        #%f\nreal-time: %f" % #(ODE_Visualization.statusString[
        #self.simulationStatus], self.simulationStep, self.simulationTime,
        #time()-self.timeStart)

        self.setInfo(info)

    def update(self):
        self.updateStatus()

        if self.simulationStep % self.updateStep == 0:
            if self.simulationViz:
                _update = lambda o: o.update()
                for obj in self.obj:
                    _update(obj)
            self.win.Render()

            if self.recording:
                self.screenshot(number=self.simulationStep)

    def startRecording(self):
        self.recording = True

    def stopRecording(self):
        self.recording = False

    def addGeom(self, geom, ident=None):
        obj = False
        # Box
        if type(geom) == GeomBox:
            obj = ODE_Box(geom, ident)
        # Sphere
        elif type(geom) == GeomSphere:
            obj = ODE_Sphere(geom, ident)
        # Plane
        elif type(geom) == GeomPlane:
            obj = ODE_Plane(geom, ident)
        # Ray
        elif type(geom) == GeomRay:
            obj = ODE_Ray(geom, ident)
        # TriMesh
        elif type(geom) == GeomTriMesh:
            obj = ODE_TriMesh(geom, ident)
        # Cylinder
        elif type(geom) == GeomCylinder:
            obj = ODE_Cylinder(geom, ident)
        # Capsule
        elif type(geom) == GeomCapsule:
            obj = ODE_Capsule(geom, ident)
        # CappedCylinder
        elif type(geom) == GeomCCylinder:
            obj = ODE_Capsule(geom, ident)

        if obj:
            self.obj.add(obj)
            self.addActor(obj.act)

    def removeGeom(self, geom):
        if type(geom) == Body:
            _find = lambda o: eq(o.geom.getBody(), geom)
        if type(geom) == str:
            _find = lambda o: eq(o.geom.ident, geom)
        else:
            _find = lambda o: eq(o.geom, geom)
        for obj in self.obj:
            if _find(obj):
                self.removeActor(obj.act)
                self.obj.remove(obj)
                del(obj)
                return True

        return False

    def addActor(self, actor):
        self.ren.AddActor(actor)

    def removeActor(self, actor):
        self.ren.RemoveActor(actor)
        #self.ren.RemoveVolume(actor)
        self.ren.Clear()
