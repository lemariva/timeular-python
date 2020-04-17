import tkinter as tk
import threading
import queue
import sys
from classes.bluetooth_gui import BluetoothChatGUI

class ThreadedClient():
    def __init__(self, root):
        """
        Threaded Client which does the socket receiving work. We call
        the main GUI through here aswell.

        Parameters
        ----------
        root : tkinter root object
            This is the passed along tk root thing
        """
        self.root = root
        self.message_queue = queue.Queue()

        self.thread_stop = threading.Event()
        self.running = True
        self.connection_running = False
        self.got_length = False

        self.gui = BluetoothChatGUI(root, 
                                self.message_queue, 
                                self.end_gui, 
                                self.start_message_awaiting,
                                self.end_bluetooth_connection)
        self.periodic_call()

    def start_message_awaiting(self):
        """
        Call the worker thread to begin the process of collecting incomming
        data. We set this as a daemon thread due to issues of it not joining
        back into our main thread because of the locking nature when we await
        data from our sockets.
        """
        self.thread_stop.clear()
        self.await_messages = threading.Thread(target=self.await_messages_thread,
            daemon=True)
        self.connection_running = True
        self.await_messages.start()

    def stop_threads(self):
        """
        Our hacky way of stopping threads via just a hard shutdown
        """
        try:
            sys.exit(1)
        except Exception as e:
            print(e)

    def periodic_call(self):
        """
        This is the function which as its name suggest, periodicly call
        the GUI thread to see if there are any new messages.
        """
        self.gui.check_message_queue()
        if not self.running:
            self.stop_threads()
        else:
            self.root.after(100, self.periodic_call)

    def get_complete_message(self):
        """
        While our bluetooth connection is ongoing, receive each message and
        if there is no '\n' delimiter, gradually peice the entire message together and
        return it.

        Returns
        -------
        message_buffer : byte string
            The full message data pieced together
        """
        try:
            more_data = True
            message_buffer = b''
            while more_data:
                data = self.gui.sock.recv(8192)
                if '\n'.encode('ascii') in data:
                    more_data = False
                    message_buffer += data.strip('\n'.encode('ascii'))
                else:
                    message_buffer += data
            return message_buffer
        except bt.btcommon.BluetoothError:
            self.connection_running = False

    def await_messages_thread(self):
        """
        While our bluetooth connection is ongoing, gather all complete messages received
        and place them into our message queue.
        """
        while self.connection_running:
            message = self.get_complete_message()
            if not self.connection_running:
                break
            try:
                self.message_queue.put(message)
            except AttributeError:
                pass

    def end_gui(self):
        """
        Set 'self.running' to False, starting the process of exiting out of 
        the application
        """
        self.running = False

    def end_bluetooth_connection(self):
        """
        Set 'self.connection_running' to false, starting the process of closing 
        our BlueTooth conneciton.
        """
        self.connection_running = False