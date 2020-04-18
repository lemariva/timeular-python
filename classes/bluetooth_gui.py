import tkinter as tk
import json
import webbrowser
import struct
from tkinter import filedialog
from classes.bluetooth_backend import BluetoothBackend
from classes.gui_backend import GUIBackend
import tkinter.scrolledtext as tkScrollText
from tkinter import messagebox
from .modals.settings_modal import SettingsWindow

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.StreamHandler())
_log.setLevel(logging.INFO)

class BluetoothChatGUI(BluetoothBackend,GUIBackend):
    def __init__(self, root, message_queue, end_gui, start_message_awaiting,
        end_bluetooth_connection):
        """
        This is the GUI class which provides the main interface between the client and
        the backend. It's functions consist of things which directly modify the GUI Without
        dealing with Bluetooth or checking data transmited to and from the connections.

        Parameters
        ----------
        root : tk root object
            This is the passed along tk root thing
        message_queue : a queue.queue
            Passed in queue which we check periodically for data
        end_gui : a function
            When called, will notify the working thread to exit out of the thread
        start_message_awaiting : a function
            When called, will notify the working thread that its ok to start
            the process of accepting any incoming data
        end_bluetooth_connection : a function
            When called, notifies the working thread that the Bluetooth Connection
            will be shut down, and that there is to be no more checking for messages.
        """
        self.root = root
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.message_queue = message_queue
        self.end_gui = end_gui
        self.start_message_awaiting = start_message_awaiting
        self.end_bluetooth_connection = end_bluetooth_connection

        # Menu Bar
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)

        # File Tab
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label='Exit',command=self.end_gui)
        self.file_menu.add_command(label='Settings',command=self.create_setting_gui)
        self.file_menu.add_command(label='Help',command=self.get_help)

        # Bluetooth Tab
        self.bt_menu = tk.Menu(self.menubar, tearoff=0)
        self.bt_menu.add_command(label='Scan',
            command=self.discover_nearby_devices)

        # Timeular Tab
        self.timeular = tk.Menu(self.menubar, tearoff=0)
        self.timeular.add_command(label='Connect',
            command=self.create_connect_to_window)
        self.timeular.add_command(label='Disconnect',
            command=self.close_connection)

        # Add Tabs to Menu
        self.menubar.add_cascade(label='File',menu=self.file_menu)
        self.menubar.add_cascade(label='Bluetooth',menu=self.bt_menu)
        self.menubar.add_cascade(label='Timeular',menu=self.timeular)

        # Logging display
        self.log_display = tkScrollText.ScrolledText(root, width=60, height=4)
        self.log_display.configure(state='disabled',font='helvetica 10')
        self.log_display.grid(row=7, 
            column=0, 
            rowspan=4,
            columnspan=60,
            sticky="nswe")
        self.log_display.bind("<1>", lambda event: self.log_display.focus_set())

        #  Activity   
        tk.Label(root, text="Actual Activity").grid(row=0, column=0, columnspan=35)
        self.activity_name = tk.StringVar()
        tk.Label(root, textvariable=self.activity_name).grid(row=1, column=0, columnspan=35)
        self.activity_time = tk.StringVar()
        tk.Label(root, textvariable=self.activity_time).grid(row=3, column=0, columnspan=35)

        tk.Label(root, text="Note").grid(row=0, column=35, columnspan=30)
        self.text_activity = tk.Text(root, width=30, height=2)
        self.text_activity.grid(row=1,
            rowspan=3,
            column=35,
            columnspan=30,
            sticky="nswe")
        self.text_activity.focus_set()

        button = tk.Button(root, text="Save", 
                        command=self.save_note_on_task).grid(row=4, column=35, columnspan=30)

        # Connection
        self.zei_connector = tk.StringVar()
        tk.Label(root, textvariable=self.zei_connector).grid(row=20, column=0, columnspan=30)
        self.zei_connector.set("Tracker not connected")
        
        self.timeular_status = tk.StringVar()
        tk.Label(root, textvariable=self.timeular_status).grid(row=20, column=31, columnspan=30)
        self.timeular_status.set("Timeular not connected")

        # Load settings
        self.octahedron_side = None
        self.activity_id = None
        self.start_time = None
        self.read_data()

        # Timeular API connector
        self.timeular = None
        
        # Time start loop
        self.root.after(5000, self.update_gui)

    def display_message_box(self, the_type, title, text):
        """
        Create and display a tkinter messagebox via 'messagebox',
        a builtin tkinter module.

        'messagebox.thetype(title, text)'

        Parameters
        ----------
        the_type : string
            The type of messagebox we want to have display
        title : string
            The title we want the message box to have
        text : string
            The text we want the message box to dispay
        """
        getattr(messagebox, the_type)(title, text)

    def display_message(self, message, data=None):
        """
        Display a message within our chat display widget.
check_ble_notification
        message : string
            The message to be displayed
        data : string, optional
            If there is any additonal information we want to display within
            our message which we couldn't do otherwise.
        """
        self.enable_log_display_state()
        if data:
            self.log_display.insert('end', message.format(data) + '\n')
        else:
            self.log_display.insert('end', message + '\n')
        self.log_display.see('end')
        self.update_log_display()
        self.disable_log_display_state()
        
    def disable_log_display_state(self):
        """
        Prevents the chat display widget from being modified.
        """
        self.log_display.configure(state='disabled')

    def enable_log_display_state(self):
        """
        Enables the chat display widget to be modified.
        """
        self.log_display.configure(state='normal')

    def update_log_display(self):
        """
        When called will force our chat display widget to refresh any changes
        which may be waiting to be shown. If we don't call this, then certain
        things may not be shown in the order or at the time we want them to be
        shown.
        """
        self.log_display.update_idletasks()  

    def update_gui(self):
        #_log.info("updating gui")
        # ble notification update
        
        self.root.after(2000, self.update_gui)
        self.check_tracker_notifications()
        self.check_timeular_status()
        self.check_activity_time()

    def create_setting_gui(self):
        settings = SettingsWindow(self.root, title='Settings')

    def create_connect_to_window(self):
        """
        Connect to the ZEI device
        """
        if self.zei:
            self.display_message_box('showerror','Already Connected','Disconnect your zei before attempting to connect to another zei.')
        else:
            self.read_data()
            if self.address_value:
                try:
                    self.connect_to_zei(self.address_value, self.manage_received_notification)
                    self.display_message('Connected Succesfully to {0}'.format(self.address_value))
                except Exception as e:
                    self.display_message('Error: {0}'.format(e))
                    self.display_message_box('showerror', 'Error', 'Connection Failed')
            if self.apikey_value and self.apisecret_value:
                self.connect_to_timeular()
    
    def get_help(self):
        webbrowser.open('https://lemariva.com/linker/timeular')
