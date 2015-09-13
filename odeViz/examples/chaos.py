import ode
import odeViz.ode_visualization as ode_viz
#import xode.parser
from random import uniform as rand, randint as randInt, seed as randSeed


class Simulation(ode_viz.ODE_Visualization):

    def __init__(self, dt=0.01, dx=10):

        #p = xode.parser.Parser()
        #root = p.parseFile(open("cage.xml", 'r'))
        #world = root.namedChild('world').getODEObject()
        #space = [root.namedChild('space').getODEObject()]

        world = ode.World()
        space = ode.Space()

        top = ode.GeomBox(space, lengths=(10., .1, 10.))
        top.setPosition((0, 5, 0))

        bottom = ode.GeomBox(space, lengths=(10., .1, 10.))
        bottom.setPosition((0, -5, 0))

        left = ode.GeomBox(space, lengths=(.1, 10., 10.))
        left.setPosition((-5, 0, 0))

        right = ode.GeomBox(space, lengths=(.1, 10., 10.))
        right.setPosition((5, 0, 0))

        front = ode.GeomBox(space, lengths=(10., 10., .1))
        front.setPosition((0, 0, -5))

        back = ode.GeomBox(space, lengths=(10., 10., .1))
        back.setPosition((0, 0, 5))

        ode_viz.ODE_Visualization.__init__(self, world, [space], dt, dx)

        self.SetWindowName('odeViz: Chaos Example')

        self.setParam(seed=1,
                      gravity=(0, 0, 0),
                      bounce=0.3,
                      Mu=500,
                      probExplode=0.01,
                      probInsert=0.5,
                      maxInsertTrials=33,
                      minSize=0.1,
                      maxSize=0.5,
                      minDensity=100,
                      maxDensity=1000,
                      minmaxForce=500)

        self.contactgroup = ode.JointGroup()

        for i in range(self.space[0].getNumGeoms()):
            element = self.space[0].getGeom(i)
            element.setCollideBits(0)
            self.GetProperty(element).SetColor(0, 0, 1)
            self.GetProperty(element).SetOpacity(.05)
            self.GetProperty(element).SetAmbient(1)

        self.GetActiveCamera().SetPosition(13.0398894156,
                                           10.6892707758,
                                           25.1683655272)

        self.GetActiveCamera().SetFocalPoint(-2.49559087329,
                                             -1.1945521966,
                                             1.23069362877)

        self.GetActiveCamera().SetViewUp(-0.209379146836,
                                         0.923152871777,
                                         -0.322411457924)

        self.objExplode = []

    def randomPos(self, x=0, y=0, z=0, border=4):
        return (x+rand(-border, border),
                y+rand(-border, border),
                z+rand(-border, border))

    def execute(self, caller, event):

        #if self.simulationStep >= 82400: # 62004 :
        #    return#    self.iren.DestroyTimer()

        #objs = iter(self.obj)

        self.space[0].collide((self.world, self.contactgroup),
                              self.near_callback)
        self.world.step(self.dt)
        self.contactgroup.empty()

        if (self.simulationTime % 1) <= self.dt:
            self.insertGeom(self.probInsert)
        self.explode(4)
        #print self.simulationTime

        self.update()  # do not forget ...

    def explode(self, maxObjects=3):
        for geom in self.objExplode:
            x, y, z = geom.getPosition()

            if geom.getBody():
                self.space[0].remove(geom)
            self.removeGeom(geom)

            try:
                for _ in range(randInt(0, maxObjects)):
                    g = self.create_geom(maxSize=0.3)

                    for _ in range(self.maxInsertTrials):
                        g.setPosition(self.randomPos(x, y, z, 0.3))
                        if not self.insertCollision(g):
                            self.addGeom(g)
                            self.GetProperty(g).SetOpacity(0.25)
                            break
            except ValueError:
                print "not my fault"

        self.objExplode = []

    def insertGeom(self, probability=0.01):
        if rand(0, 1) < probability:

            geom = self.create_geom(self.minSize, self.maxSize,
                                    self.minDensity, self.maxDensity,
                                    self.minmaxForce)

            for _ in range(self.maxInsertTrials):
                geom.setPosition(self.randomPos())

                if not self.insertCollision(geom):
                        self.addGeom(geom)
                        self.GetProperty(geom).SetColor(rand(0, 1),
                                                        rand(0, 1),
                                                        rand(0, 1))

                        self.GetProperty(geom).SetShading(1)
                        break

    def insertCollision(self, geom):
        #objs = iter(self.obj)
        _collide = lambda o: ode.collide(geom, o.geom)
        for obj in self.obj:
            if _collide(obj):
                return True
        return False

    def create_geom(self, minSize=0.1, maxSize=0.5,
                    minDensity=100, maxDensity=100, minmaxForce=100):
        """Create a box body and its corresponding geom."""
        element = randInt(1, 3)

        if element == 1:
            body, geom = self.create_sphere(rand(minDensity, maxDensity),
                                            rand(minSize, maxSize))
        elif element == 2:
            body, geom = self.create_capsule(rand(minDensity, maxDensity),
                                             rand(minSize, maxSize),
                                             rand(minSize, maxSize))
        elif element == 3:
            body, geom = self.create_box(rand(minDensity, maxDensity),
                                         rand(minSize, maxSize),
                                         rand(minSize, maxSize),
                                         rand(minSize, maxSize))

        body.addForce((rand(-minmaxForce, minmaxForce),
                       rand(-minmaxForce, minmaxForce),
                       rand(-minmaxForce, minmaxForce)))

        return geom

    def create_sphere(self, density, radius):
        body = ode.Body(self.world)
        M = ode.Mass()
        M.setSphere(density, radius)
        body.setMass(M)

        geom = ode.GeomSphere(self.space[0], radius=radius)
        geom.setBody(body)

        return body, geom

    def create_box(self, density, lx, ly, lz):
        body = ode.Body(self.world)
        M = ode.Mass()
        M.setBox(density, lx, ly, lz)
        body.setMass(M)

        geom = ode.GeomBox(self.space[0], lengths=(lx, ly, lz))
        geom.setBody(body)

        return body, geom

    def create_capsule(self, density, r, h):
        body = ode.Body(self.world)
        M = ode.Mass()
        M.setCapsule(density, 1, r, h)
        body.setMass(M)

        geom = ode.GeomCapsule(self.space[0], radius=r, length=h)
        geom.setBody(body)

        return body, geom

    def near_callback(self, args, geom1, geom2):
        if geom1.getCollideBits() == geom2.getCollideBits() == 0:
            return

        # Check if the objects do collide
        contacts = ode.collide(geom1, geom2)

        if len(contacts) >= 1 and \
           geom1.getCollideBits() != 0 and \
           geom2.getCollideBits() != 0:

            if rand(0, 1) < self.probExplode:
                if rand(0, 1) < 0.5:
                    self.objExplode.append(geom1)
                else:
                    self.objExplode.append(geom2)

        # Create contact joints
        self.world, self.contactgroup = args
        for c in iter(contacts):
            c.setBounce(self.bounce)
            c.setMu(self.Mu)
            j = ode.ContactJoint(self.world, self.contactgroup, c)
            j.attach(geom1.getBody(), geom2.getBody())

    def setParam(self, seed=None, gravity=None, bounce=None, Mu=None,
                 probExplode=None, probInsert=None, maxInsertTrials=None,
                 minSize=None, maxSize=None, minDensity=None, maxDensity=None,
                 minmaxForce=None):

        if seed is not None:
            self.seed = seed
            randSeed(seed)

        if gravity is not None:
            self.gravity = gravity
            self.world.setGravity(self.gravity)

        if bounce is not None:
            self.bounce = bounce

        if Mu is not None:
            self.Mu = Mu

        if probExplode is not None:
            self.probExplode = probExplode

        if probInsert is not None:
            self.probInsert = probInsert

        if maxInsertTrials is not None:
            self.maxInsertTrials = maxInsertTrials

        if minSize is not None:
            self.minSize = minSize

        if maxSize is not None:
            self.maxSize = maxSize

        if minDensity is not None:
            self.minDensity = minDensity

        if maxDensity is not None:
            self.maxDensity = maxDensity

        if minmaxForce is not None:
            self.minmaxForce = minmaxForce


if __name__ == "__main__":
    sim = Simulation(0.03)

    # start the simulation
    sim.start()
