# pyODE example 3: Collision detection

# Originally by Matthias Baas.
# Updated by Pierre Gay to work without pygame or cgkit.

import random
import time
import ode
from math import sqrt, pi, cos, sin
import odeViz.ode_visualization as ode_viz


# geometric utility functions
def scalp(vec, scal):
    vec[0] *= scal
    vec[1] *= scal
    vec[2] *= scal


def length(vec):
    return sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)


# create_box
def create_box(world, space, density, lx, ly, lz):
    """Create a box body and its corresponding geom."""

    # Create body
    body = ode.Body(world)
    M = ode.Mass()
    M.setBox(density, lx, ly, lz)
    body.setMass(M)

    # Set parameters for drawing the body
    body.shape = "box"
    body.boxsize = (lx, ly, lz)

    # Create a box geom for collision detection
    geom = ode.GeomBox(space, lengths=body.boxsize)
    geom.setBody(body)

    return body, geom


# drop_object
def drop_object():
    """Drop an object into the scene."""

    global bodies, geom, counter, objcount, viz

    body, geom = create_box(world, space, 1000, 1.0, 0.2, 0.2)
    body.setPosition((random.gauss(0, 0.1), 2, random.gauss(0, 0.1)))
    theta = random.uniform(0, 2*pi)
    ct = cos(theta)
    st = sin(theta)
    body.setRotation([ct, 0., -st, 0., 1., 0., st, 0., ct])
    bodies.append(body)
    geoms.append(geom)
    counter = 0
    objcount += 1

    viz.addGeom(geom)

    viz.GetProperty(geom).SetColor(random.uniform(0, 1),
                                   random.uniform(0, 1),
                                   random.uniform(0, 1))


# explosion
def explosion():
    """Simulate an explosion.

    Every object is pushed away from the origin.
    The force is dependent on the objects distance from the origin.
    """
    global bodies

    for b in bodies:
        l = b.getPosition()
        d = length(l)
        a = max(0, 40000 * (1.0 - 0.2 * d * d))
        l = [l[0] / 4, l[1], l[2] / 4]
        scalp(l, a / length(l))
        b.addForce(l)


# pull
def pull():
    """Pull the objects back to the origin.

    Every object will be pulled back to the origin.
    Every couple of frames there'll be a thrust upwards so that
    the objects won't stick to the ground all the time.
    """
    global bodies, counter

    for b in bodies:
        l = list(b.getPosition())
        scalp(l, -1000 / length(l))
        b.addForce(l)
        if counter % 60 == 0:
            b.addForce((0, 10000, 0))


# Collision callback
def near_callback(args, geom1, geom2):
    """Callback function for the collide() method.

    This function checks if the given geoms do collide and
    creates contact joints if they do.
    """

    # Check if the objects do collide
    contacts = ode.collide(geom1, geom2)

    # Create contact joints
    world, contactgroup = args
    for c in contacts:
        c.setBounce(0.2)
        c.setMu(5000)
        j = ode.ContactJoint(world, contactgroup, c)
        j.attach(geom1.getBody(), geom2.getBody())


######################################################################

# Create a world object
world = ode.World()
world.setGravity((0, -9.81, 0))
world.setERP(0.8)
world.setCFM(1E-5)

# Create a space object
space = ode.Space()

# Create a plane geom which prevent the objects from falling forever
floor = ode.GeomPlane(space, (0, 1, 0), 0)

# A list with ODE bodies
bodies = []

# The geoms for each of the bodies
geoms = []

# A joint group for the contact joints that are generated whenever
# two bodies collide
contactgroup = ode.JointGroup()

# Some variables used inside the simulation loop
dt = 0.01
running = True
state = 0
counter = 0
objcount = 0
lasttime = time.time()


# idle callback
def _idlefunc():
    global counter, state, lasttime

    t = dt - (time.time() - lasttime)
    if (t > 0):
        time.sleep(t)

    counter += 1

    if state == 0:
        if counter == 20:
            drop_object()
        if objcount == 30:
            state = 1
            counter = 0
    # State 1: Explosion and pulling back the objects
    elif state == 1:
        if counter == 100:
            explosion()
        if counter > 300:
            pull()
        if counter == 500:
            counter = 20

    # Simulate
    n = 2

    for _ in range(n):
        # Detect collisions and create contact joints
        space.collide((world, contactgroup), near_callback)

        # Simulation step
        world.step(dt/n)

        # Remove all contact joints
        contactgroup.empty()

    lasttime = time.time()


class my_sim(ode_viz.ODE_Visualization):
    def __init__(self, world, space, dt):
        ode_viz.ODE_Visualization.__init__(self, world, space, dt)

        self.GetActiveCamera().SetPosition(0.0287138864171,
                                           11.878271021700,
                                           18.654766874600)

        self.GetActiveCamera().SetFocalPoint(-0.110497968225,
                                             2.844859412940,
                                             -0.428463020196)

        self.GetActiveCamera().SetViewUp(0.00265609624752,
                                         0.90383731040800,
                                         -0.427868042119)

    def execute(self, caller, event):
        # test if the simulation is in pause mode
        if self.simulationStatus == self.RUNNING:
            _idlefunc()
        self.update()

viz = my_sim(world, [space], dt)
drop_object()
viz.start()
