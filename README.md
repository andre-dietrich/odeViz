# odeViz: [or simply ode - Visualization]

## Preface

Playing around with the OpenDynamicsEngine (ODE) I found it a bit confusing and
difficult to cope with both, the physical simulation as well as with the
visualization. All relevant data is already included in the physical part, so
why using with both?

I wrote a simple wrapper for python, that uses pyvtk to visualize a simulation,
just pass the “world” and the “space” to ODE_Visualization and let it handle the
rest …


## Install


### Requirements

###### Open Dynamics Engine: http://www.ode.org

Download the latest tar from : https://bitbucket.org/odedevs/ode/downloads/

and decompress it to your desired destination ...

``` bash
cd ode-0.16
./configure --enable-shared   # has to be compiled as a shared lib for python
make
sudo make install
```

To build it for Python, you will probably have to install Cython

``` base
sudo apt install cython3
cd bindings
cd python
sudo python3 setup.py build
sudo python3 setup.py install
```

###### PyODE: http://pyode.sourceforge.net

This is not mandatory, it is only used in some of the examples. This is the
ode-interface for Python, it also contains the xode-project, which enables
the definition of ode-simulations with XML. See the ReadMe for further
installation information.

###### Visualization Toolkit (VTK) version 8 : http://www.vtk.org

Install the current version of vtk ... in my case this was 8...

```
sudo pip3 install vtk
```

###### Additional

If you are using Linux as I do (Ubuntu), nearly all of these tools and libraries
can be installed from precompiled versions. But for xode you will have to download
PyODE from http://pyode.sourceforge.net.

### Installation

Using the python setup tools:

``` bash
git clone https://github.com/andre-dietrich/odeViz
cd odeViz
sudo python3 setup.py build
sudo python3 setup.py install
```

### Try out the examples

``` bash
cd odeViz/odeViz/examples
python3 chaos.py

python3 tutorial3.py
```

## Basic architecture

You can skip this part, if you just want a quick visualization, but if you want
to extend your visualization with further VTK-functionalities ... have a look on
it.

The used classes can be devided into two parts, a visualization-part and a object-
part, as depicted in the uml diagram below (created with umbrello).

![odeViz-UML](http://www.aizac.info/wp-content/uploads/ODE-VIZ-UML.png)

VTK_Visualization and the inherited methods are used to handle and define window
specifics, like size, title, background-color, etc. ODE-Visualization takes in as
parameters, the world, the space, and is responsible to run the simulation. During
initialization, the space is scanned for primitive objects, such as boxes, spheres,
etc. ODE-Visualization creates a VTK object (encapsulated within a ODE_Object) for
every primitive entity. These objects can be seen as glue-objects, each one is bound
to a single object/geometry within the space, knowing its position, rotation, and
size within the virtual space. By calling update(), the vtk-objects are simply set
onto the same position/orientation in the visualization, as the ode-object in the
simulation. ODE-Visualization only responsible to maintain a list of ODE_Object and
to update the vtk-simulation in a appropriate manner.

VTK_Visualization is furthermore an ancestor of threading.Thread, and thus
responsible to start and run the thread for the simulation. You simply have to
overwrite method execute with all required stuff, as explained in more detail
within the examples...


## Examples

### From XML to VTK

This example is included into the project, which can be simply executed by calling:
```
$ python test.py
```

Within this example, our world an all included objects are defined within a single
XML file. Simple capsules on different heights and a plane on the ground. By using
xode, it is possible to read in this xml-file and to retrieve all required data for
the simulation.

``` python
import ode
import xode.parser
import libxml2
import odeViz.ode_visualization as ode_viz

class my_sim(ode_viz.ODE_Visualization):
    def __init__(self, world, space, dt):
        ode_viz.ODE_Visualization.__init__(self, world, space, dt)

        self.contactgroup = ode.JointGroup()

    def execute(self, caller, event):
        self.space[0].collide((self.world,self.contactgroup), self.near_callback)
        self.world.step(self.dt)
        self.contactgroup.empty()
        self.update() # do not forget ...

    def near_callback(self, args, geom1, geom2):
        # Check if the objects do collide
        contacts = ode.collide(geom1, geom2)

        # Create contact joints
        self.world,self.contactgroup = args
        for c in contacts:
            c.setBounce(0.2)
            c.setMu(5000)
            j = ode.ContactJoint(self.world, self.contactgroup, c)
            j.attach(geom1.getBody(), geom2.getBody())

# parsing the xml file
xml = libxml2.parseFile("test.xml")
xml.xincludeProcess()
p = xode.parser.Parser()
root = p.parseString(str(xml))
world = root.namedChild('world').getODEObject()
space = root.namedChild('space').getODEObject()

# setting some parameters
world.setGravity( (-0.001,-9.81,-0.001) )
world.setERP(0.8)
world.setCFM(1E-10)

# pass all requred parameters world, space, and time step dt
viz = my_sim(world, [space], 0.005)

# start the simulation
viz.start()
```

Pass the space and the world, as presented in line second last command to the
visualization. Within the constructor it is possible to change the camera
parameters, window properties, etc. Have a now a look to the execute method,
this is the method which is called from within the working thread. It is
everything that is required for the simulation... It check if there occurred
some collisions, and calculates the the next step of the simulation, with
delta time dt, which was also defined during the initialization.

[![example/tutorial3.py](http://img.youtube.com/vi/1VQMAje62FE/0.jpg)](http://www.youtube.com/watch?v=1VQMAje62FE "watch on YouTube")

### Changing Tutorial 3

But if you want to add or remove new objects during runtime or change their colors,
etc., this has to be done manually. To explain this, I chose the third step of the
pyode tutorial from the project site:

http://pyode.sourceforge.net/tutorials/tutorial3.html

See therefor example/tutorial3.py

The video below shows the my version of this tutorial, where I simply re removed
all the OpenGL stuff and added a new visualization class, in the same way as it was
used in the previous example. The original update function is here called from within
the execute method. And if you take a look into function drop(), which is responsible
for the creation of objects. Every new object is here directly added to the
visualization, and their color-properties are changed in the vtk manner (to random
colors).

[![example/tutorial3.py](http://img.youtube.com/vi/T7C_IB3Cri8/0.jpg)](http://www.youtube.com/watch?v=T7C_IB3Cri8 "watch on YouTube")
