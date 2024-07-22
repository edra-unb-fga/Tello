import py_trees
import time
from djitellopy import Tello
import cv2
import mediapipe as mp
import numpy as np

class TakeOff(py_trees.behaviour.Behaviour):
    def __init__(self, name="TakeOff"):
        super().__init__(name)
        self.drone = None

    def setup(self, **kwargs):
        try:
            self.drone = kwargs['drone']
            return True
        except KeyError as e:
            self.logger.error('setup() must be called with "drone" keyword argument')
            return False

    def update(self):
        self.drone.takeoff()
        return py_trees.common.Status.SUCCESS

class Land(py_trees.behaviour.Behaviour):
    def __init__(self, name="Land"):
        super().__init__(name)
        self.drone = None

    def setup(self, **kwargs):
        try:
            self.drone = kwargs['drone']
            return True
        except KeyError as e:
            self.logger.error('setup() must be called with "drone" keyword argument')
            return False

    def update(self):
        self.drone.land()
        return py_trees.common.Status.SUCCESS

class Stabilize(py_trees.behaviour.Behaviour):
    def __init__(self, name="Stabilize", duration=5.0):
        super().__init__(name)
        self.duration = duration
        self.start_time = None

    def initialise(self):
        self.start_time = time.time()

    def update(self):
        if time.time() - self.start_time > self.duration:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING

class FlyDirection(py_trees.behaviour.Behaviour):
    def __init__(self, name, direction, distance):
        super().__init__(name)
        self.direction = direction
        self.distance = distance
        self.drone = None

    def setup(self, **kwargs):
        try:
            self.drone = kwargs['drone']
            return True
        except KeyError as e:
            self.logger.error('setup() must be called with "drone" keyword argument')
            return False

    def update(self):
        if self.direction == 'forward':
            self.drone.move_forward(self.distance)
        elif self.direction == 'right':
            self.drone.move_right(self.distance)
        elif self.direction == 'back':
            self.drone.move_back(self.distance)
        elif self.direction == 'left':
            self.drone.move_left(self.distance)
        return py_trees.common.Status.SUCCESS

def create_root(square_side_length = 50): #50cm
    root = py_trees.composites.Sequence("Root", memory=True)
    
    takeoff_stabilize = py_trees.composites.Sequence("TakeoffAndStabilize", memory=True)
    takeoff = TakeOff()
    stabilize = Stabilize(duration=3.0)
    takeoff_stabilize.add_children([takeoff, stabilize])
    
    fly_square = py_trees.composites.Sequence("FlySquare", memory=True)
    for direction in ['forward', 'right', 'back', 'left']:
        fly_square.add_child(FlyDirection(f"Fly{direction.capitalize()}", direction, square_side_length))
    
    land = Land()
    
    root.add_children([takeoff_stabilize, fly_square, land])
    return root

def safe_write(content, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully wrote to {filename}")
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")

def generate_tree_visualization(root, name='tello_mission_tree'):
    # ASCII Tree
    try:
        ascii_tree = py_trees.display.ascii_tree(root)
        safe_write(ascii_tree, f"{name}_ascii.txt")
    except Exception as e:
        print(f"Error generating ASCII tree: {e}")

    # DOT representation
    try:
        dot_tree = py_trees.display.dot_tree(root)
        safe_write(str(dot_tree), f"{name}.dot")
        print(f"DOT representation saved as '{name}.dot'")
    except Exception as e:
        print(f"Error generating DOT representation: {e}")

    # PNG visualization (if possible)
    try:
        py_trees.display.render_dot_tree(root, name=name, target_directory='.')
        print(f"Static tree visualization saved as '{name}.png'")
    except Exception as e:
        print(f"Error generating PNG visualization: {e}")
        print("You can manually convert the DOT file to PNG using Graphviz if it's installed:")
        print(f"dot -Tpng {name}.dot -o {name}.png")


class GestureControl(py_trees.behaviour.Behaviour):
    def __init__(self, name="GestureControl"):
        super().__init__(name)
        self.drone = None
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
        self.mp_drawing = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)

    def setup(self, **kwargs):
        try:
            self.drone = kwargs['drone']
            return True
        except KeyError as e:
            self.logger.error('setup() must be called with "drone" keyword argument')
            return False

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            return py_trees.common.Status.FAILURE

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Get the position of the index fingertip
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, _ = frame.shape
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)

                # Simple gesture recognition
                if cy < h // 3:  # Top third of the frame
                    self.drone.move_up(20)
                elif cy > 2 * h // 3:  # Bottom third of the frame
                    self.drone.move_down(20)
                elif cx < w // 3:  # Left third of the frame
                    self.drone.move_left(20)
                elif cx > 2 * w // 3:  # Right third of the frame
                    self.drone.move_right(20)
                else:  # Center of the frame
                    self.drone.send_rc_control(0, 0, 0, 0)  # Hover

        cv2.imshow('Gesture Control', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING

    def terminate(self, new_status):
        self.cap.release()
        cv2.destroyAllWindows()

def create_root(square_side_length=100):
    root = py_trees.composites.Sequence("Root", memory=True)
    
    takeoff_stabilize = py_trees.composites.Sequence("TakeoffAndStabilize", memory=True)
    takeoff = TakeOff()
    stabilize = Stabilize(duration=3.0)
    takeoff_stabilize.add_children([takeoff, stabilize])
    
    gesture_control = GestureControl()
    
    land = Land()
    
    root.add_children([takeoff_stabilize, gesture_control, land])
    return root

def main():
    drone = Tello()
    try:
        drone.connect()
        print("Successfully connected to Tello drone")
    except Exception as e:
        print(f"Error connecting to Tello drone: {e}")
        return

    root = create_root()
    tree = py_trees.trees.BehaviourTree(root)
    
    # Generate tree visualizations
    generate_tree_visualization(root)
    
    # Pass the drone object to all behaviours that need it
    try:
        tree.setup(timeout=15, drone=drone)
    except Exception as e:
        print(f"Error setting up behavior tree: {e}")
        return

    try:
        while True:
            tree.tick()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error during tree execution: {e}")
    finally:
        print("Attempting to land the drone...")
        try:
            drone.land()
            print("Drone landed successfully")
        except Exception as e:
            print(f"Error landing the drone: {e}")
        drone.end()

if __name__ == '__main__':
    main()