import time
import py_trees
from controllers.gesture_controller import GestureControl

class TakeOff(py_trees.behaviour.Behaviour):
    def __init__(self, name="Decolar"):
        super().__init__(name)
        self.drone = None

    def setup(self, **kwargs):
        try:
            self.drone = kwargs['drone']
            return True
        except KeyError as e:
            self.logger.error('setup() deve ser chamado com o argumento "drone"')
            return False

    def update(self):
        if self.drone is not None:
            self.drone.takeoff()
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE


class Land(py_trees.behaviour.Behaviour):
    def __init__(self, name="Pousar"):
        super().__init__(name)
        self.drone = None

    def setup(self, **kwargs):
        try:
            self.drone = kwargs['drone']
            return True
        except KeyError as e:
            self.logger.error('setup() deve ser chamado com o argumento "drone"')
            return False

    def update(self):
        if self.drone is not None:
            self.drone.land()
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE

class Stabilize(py_trees.behaviour.Behaviour):
    def __init__(self, name="Estabilizar", duration=5.0):
        super().__init__(name)
        self.duration = duration
        self.start_time = None

    def initialise(self):
        self.start_time = time.time()

    def update(self):
        if self.start_time is not None and time.time() - self.start_time > self.duration:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING

def create_root(gui):
    root = py_trees.composites.Sequence("Raiz", memory=True)
    
    takeoff_stabilize = py_trees.composites.Sequence("DecolarEEstabilizar", memory=True)
    takeoff = TakeOff()
    stabilize = Stabilize(duration=gui.stabilize_time.get())
    takeoff_stabilize.add_children([takeoff, stabilize])
    
    gesture_control = GestureControl(gui=gui)
    
    land = Land()
    
    root.add_children([takeoff_stabilize, gesture_control, land])
    return root

