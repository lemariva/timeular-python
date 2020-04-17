import tkinter as tk
from classes.thread_client import ThreadedClient

if __name__ == '__main__':
    master = tk.Tk()
    master.wm_title("Timeular")
    client = ThreadedClient(master)
    master.mainloop()
