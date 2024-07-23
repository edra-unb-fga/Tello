import tkinter as tk
from tkinter import ttk

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
        # Aqui você chamaria sua função principal de controle do drone
