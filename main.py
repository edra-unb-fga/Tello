import time
import py_trees
import threading
import tkinter as tk
from djitellopy import Tello
from controllers.tello_controller import create_root
from controllers.gui_controller import TelloControlGUI

def main():
    root = tk.Tk()
    gui = TelloControlGUI(root)
    print("==================GUI==================")

    def run_mission():
        drone = Tello()
        print("==================MISSION==================")
        try:
            drone.connect()
            print("Conectado com sucesso ao drone Tello")
            drone.streamoff()
            drone.streamon()
        except Exception as e:
            print(f"Erro ao conectar ao drone Tello: {e}")
            return

        behavior_tree = py_trees.trees.BehaviourTree(create_root(gui))
        
        try:
            behavior_tree.setup(timeout=15, drone=drone)
        except Exception as e:
            print(f"Erro ao configurar a árvore de comportamento: {e}")
            return

        try:
            while True:
                behavior_tree.tick()
                time.sleep(gui.tick_interval.get())
        except KeyboardInterrupt:
            print("\nPrograma interrompido pelo usuário")
        except Exception as e:
            print(f"Erro durante a execução da árvore: {e}")
        finally:
            print("Tentando pousar o drone...")
            try:
                drone.land()
                print("Drone pousou com sucesso")
            except Exception as e:
                print(f"Erro ao pousar o drone: {e}")
            drone.end()

    gui.start_button.config(command=lambda: threading.Thread(target=run_mission, daemon=True).start())
    
    root.mainloop()

if __name__ == '__main__':
    main()