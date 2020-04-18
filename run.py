import tkinter as tk
import os
from classes.thread_client import ThreadedClient

if __name__ == '__main__':
    master = tk.Tk()
    master.wm_title("Timeular")
    master.iconphoto(True, tk.PhotoImage(file=os.path.join(os.sys.path[0], "icon.png")))
    client = ThreadedClient(master)
    master.mainloop()
