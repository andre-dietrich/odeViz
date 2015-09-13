import ode
import xode.parser
import odeViz.ode_visualization as ode_viz
#from vtk import vtkFFMPEGWriter, vtkWindowToImageFilter


import sys

sys.path = ["../odeViz/"] + sys.path


class my_sim(ode_viz.ODE_Visualization):
    def __init__(self, world, space, dt):
        ode_viz.ODE_Visualization.__init__(self, world, space, dt)

        self.contactgroup = ode.JointGroup()

        self.GetActiveCamera().SetPosition(0.725472557934,
                                           0.888052344093,
                                           5.504911860770)

        self.GetActiveCamera().SetFocalPoint(-0.0201045961788,
                                             0.840176342681,
                                             -0.00458023275766)

        self.GetActiveCamera().SetViewUp(0.0287954448360,
                                         0.999506133230,
                                         -0.0125822093364)

        #screenshot = vtkWindowToImageFilter()
        #screenshot.SetInput(self.win)
        #self.video = vtkFFMPEGWriter()
        #self.video.SetInputConnection(screenshot.getGetOutput())
        #self.video.Start()

    def execute(self, caller, event):
        self.space[0].collide((self.world, self.contactgroup),
                              self.near_callback)
        self.step(self.dt)
        self.contactgroup.empty()
        self.update()

    def near_callback(self, args, geom1, geom2):
        # Check if the objects do collide
        contacts = ode.collide(geom1, geom2)

        # Create contact joints
        self.world, self.contactgroup = args
        for c in contacts:
            c.setBounce(0.2)
            c.setMu(5000)
            j = ode.ContactJoint(self.world, self.contactgroup, c)
            j.attach(geom1.getBody(), geom2.getBody())

xml = open("test.xml", 'r')


p = xode.parser.Parser()
root = p.parseFile(xml)

world = root.namedChild('world').getODEObject()
space = root.namedChild('space').getODEObject()


world.setGravity((0, -9.81, 0.01))
world.setERP(0.8)
world.setCFM(1E-5)

viz = my_sim(world, [space], 0.01)


viz.start()
