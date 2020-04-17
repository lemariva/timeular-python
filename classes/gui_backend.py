import base64
import codecs
import tkinter as tk
import os
import queue
import json
import struct
import datetime

from .timeular import Timeular
from PIL import Image
from utils.wrapper import check_bluetooth

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.StreamHandler())
_log.setLevel(logging.INFO)

class GUIBackend():
    """This is a class which our GUI inherits from. 
    """
    def connect_to_timeular(self):
        try:
            self.actual_activity = None
            self.timeular = Timeular(self.apikey_value, self.apisecret_value)
            self.display_message('Connected to https://api.timeular.com/api/v2')
        except Exception as e:
            self.timeular = None
            self.display_message('Error: {0}'.format(e))

    def read_data(self):
        try:
            with open('data.json') as json_file:
                data = json.load(json_file)
                self.address_value = data['device_mac']
                self.apikey_value = data['apiKey']
                self.apisecret_value = data['apiSecret']
        except Exception as e:
            self.display_message('Error: {0}'.format(e))
            self.address_value = ""
            self.apikey_value = ""
            self.apisecret_value = ""
            pass

    def manage_received_notification(self, handle, data):
        """
        """
        if handle == 39:
            message_stop = None
            message_start = None
            # read the actual octahedron side
            octahedron_side = struct.unpack('B', data)[0]
            # read activity
            activity = self.timeular.activities.get_activitity_side(octahedron_side)

            # check last side and change it
            if activity:
                activity_name = activity["name"]
                activity_id = activity["id"]
                
                if self.activity_id is not None:   
                    message_stop = self.timeular.tracking.post_stop(self.activity_id)

                message_start = self.timeular.tracking.post_start(activity_id)

            else:
                activity_id = None
                if self.octahedron_side is not None:
                    activity_name = "Paused!"
                    message_stop = self.timeular.tracking.post_stop(self.activity_id)
                else:
                    message_stop = None
                    activity_name = "Not defined!"

            self.octahedron_side = octahedron_side
            self.activity_id = activity_id
        
            self.message_to_text(message_stop)
            self.message_to_text(message_start)
            
    def message_to_text(self, message):
        if message:
            if "currentTracking" in message:
                self.display_message('Tracking activity: [{0}]: {1}'
                                    .format(message["currentTracking"]["activity"]["id"],
                                    message["currentTracking"]["activity"]["name"]))
            if "status_code" in message:
                
                self.display_message('Error [{0}]: {1}'
                                    .format(message["status_code"],
                                    json.loads(message["message"])["message"]))

    def check_message_queue(self):
        """
        When called will check to determine if there is anything within our queue.
        If there is, we pull out the data and determine how to display it, unless
        the queue is empty, then it stops.
        """
        while self.message_queue.qsize():
            try:
                data = self.message_queue.get()
                self.manage_received_data(data)
            except queue.Empty:
                pass

