import tkinter as tk
from controllers.tello_controller import *

def main():
    root = tk.Tk()
    gui = TelloControlGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
