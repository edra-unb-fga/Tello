import time
import py_trees
import tkinter as tk
from tkinter import ttk
from djitellopy import Tello
from controllers.gesture_controller import GestureControl

class TelloControlGUI:
    def __init__(self, master):
        self.master = master
        master.title("Controle do Drone Tello")

        self.performance_frame = ttk.LabelFrame(master, text="Configurações de Desempenho")
        self.performance_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.mission_frame = ttk.LabelFrame(master, text="Variáveis de Missão")
        self.mission_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.create_performance_widgets()
        self.create_mission_widgets()

        self.start_button = ttk.Button(master, text="Iniciar Missão", command=self.start_mission)
        self.start_button.grid(row=1, column=0, columnspan=2, pady=10)

    def create_performance_widgets(self):
        self.frame_rate = tk.IntVar(value=30)
        self.resolution = tk.IntVar(value=720)
        self.detection_confidence = tk.DoubleVar(value=0.7)
        self.skip_frames = tk.IntVar(value=0)
        self.draw_landmarks = tk.BooleanVar(value=True)

        ttk.Label(self.performance_frame, text="Taxa de Quadros:").grid(row=0, column=0, sticky="w")
        ttk.Scale(self.performance_frame, from_=5, to=30, variable=self.frame_rate, orient="horizontal").grid(row=0, column=1)
        ttk.Label(self.performance_frame, textvariable=self.frame_rate).grid(row=0, column=2)

        ttk.Label(self.performance_frame, text="Resolução:").grid(row=1, column=0, sticky="w")
        ttk.Combobox(self.performance_frame, textvariable=self.resolution, values=[360, 480, 720]).grid(row=1, column=1, columnspan=2)

        ttk.Label(self.performance_frame, text="Confiança de Detecção:").grid(row=2, column=0, sticky="w")
        ttk.Scale(self.performance_frame, from_=0.1, to=1.0, variable=self.detection_confidence, orient="horizontal").grid(row=2, column=1)
        ttk.Label(self.performance_frame, textvariable=self.detection_confidence).grid(row=2, column=2)

        ttk.Label(self.performance_frame, text="Pular Quadros:").grid(row=3, column=0, sticky="w")
        ttk.Scale(self.performance_frame, from_=0, to=5, variable=self.skip_frames, orient="horizontal").grid(row=3, column=1)
        ttk.Label(self.performance_frame, textvariable=self.skip_frames).grid(row=3, column=2)

        ttk.Checkbutton(self.performance_frame, text="Desenhar Landmarks", variable=self.draw_landmarks).grid(row=4, column=0, columnspan=3)

    def create_mission_widgets(self):
        self.move_distance = tk.IntVar(value=20)
        self.stabilize_time = tk.DoubleVar(value=3.0)
        self.tick_interval = tk.DoubleVar(value=0.1)

        ttk.Label(self.mission_frame, text="Distância de Movimento (cm):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.mission_frame, textvariable=self.move_distance).grid(row=0, column=1)

        ttk.Label(self.mission_frame, text="Tempo de Estabilização (s):").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.mission_frame, textvariable=self.stabilize_time).grid(row=1, column=1)

        ttk.Label(self.mission_frame, text="Intervalo de Tick (s):").grid(row=2, column=0, sticky="w")
        ttk.Entry(self.mission_frame, textvariable=self.tick_interval).grid(row=2, column=1)

    def start_mission(self):
        print("Iniciando missão com as configurações atuais...")
        self.run_mission()

    def run_mission(self):
        self.drone = Tello()
        try:
            self.drone.connect()
            print("Conectado com sucesso ao drone Tello")
            self.drone.streamoff()
            self.drone.streamon()
        except Exception as e:
            print(f"Erro ao conectar ao drone Tello: {e}")
            return

        self.behavior_tree = py_trees.trees.BehaviourTree(create_root(self))
        
        try:
            self.behavior_tree.setup(timeout=15, drone=self.drone)
        except Exception as e:
            print(f"Erro ao configurar a árvore de comportamento: {e}")
            return

        self.tick()

    def tick(self):
        try:
            self.behavior_tree.tick()
            self.master.after(int(self.tick_interval.get() * 1000), self.tick)
        except Exception as e:
            print(f"Erro durante a execução da árvore: {e}")
            self.terminate()

    def terminate(self):
        print("Tentando pousar o drone...")
        try:
            self.drone.land()
            print("Drone pousou com sucesso")
        except Exception as e:
            print(f"Erro ao pousar o drone: {e}")
        self.drone.end()
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
        self.drone.takeoff()
        return py_trees.common.Status.SUCCESS

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
        self.drone.land()
        return py_trees.common.Status.SUCCESS

class Stabilize(py_trees.behaviour.Behaviour):
    def __init__(self, name="Estabilizar", duration=5.0):
        super().__init__(name)
        self.duration = duration
        self.start_time = None

    def initialise(self):
        self.start_time = time.time()

    def update(self):
        if time.time() - self.start_time > self.duration:
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