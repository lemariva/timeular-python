import base64
import codecs
import tkinter as tk
import os
import queue
import json
import struct
import datetime
import dateutil.parser

from .timeular import Timeular
from PIL import Image
from utils.wrapper import check_bluetooth

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.StreamHandler())
_log.setLevel(logging.NOTSET)

class GUIBackend():
    """This is a class which our GUI inherits from. 
    """
    def connect_to_timeular(self):
        try:
            self.actual_activity = None
            self.timeular = Timeular(self.apikey_value, self.apisecret_value)
            self.display_message('Connected to https://api.timeular.com/api/v2')
            self.check_current_tracking()
            self.tags = self.timeular.tags_and_mentions.get()
        except Exception as e:
            self.timeular = None
            self.display_message('Error: {0}'.format(e))

    def check_current_tracking(self):
        tracking = self.timeular.tracking.get()["currentTracking"]
        if tracking is not None:
            self.manage_activity_change(tracking=tracking)
            
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
        if handle == 39 or handle == 38:
            # read the actual octahedron side
            octahedron_side = struct.unpack('B', data)[0]
            self.manage_activity_change(octahedron_side=octahedron_side)
    
    def manage_activity_change(self, octahedron_side = None, tracking = None):
        message_stop = None
        message_start = None
        self.start_time = datetime.datetime.utcnow().isoformat()
        
        if octahedron_side is not None:
            activity = self.timeular.activities.get_activitity_side(octahedron_side)
        
        if tracking is not None:
            activity = self.timeular.activities.get_activity_id(tracking["activity"]["id"])
            self.start_time = tracking["startedAt"]

        if activity:
            activity_name = activity["name"]
            activity_id = activity["id"]
            
            if self.activity_id is not None:  
                message_stop = self.timeular.tracking.post_stop(self.activity_id)

            message_start = self.timeular.tracking.post_start(activity_id)
                
        else:
            activity_id = None
            message_stop = self.timeular.tracking.post_stop(self.activity_id)
            if self.octahedron_side is not None:
                activity_name = "Paused!"      
            else:
                activity_name = "Not defined!"

        self.octahedron_side = octahedron_side
        self.activity_id = activity_id

        # gui update
        self.activity_name.set(activity_name)
        self.message_to_text(message_stop)
        self.message_to_text(message_start)

    def check_activity_time(self):
        if self.start_time is not None:
            activity_time = datetime.datetime.utcnow().replace(microsecond=0) - \
                            dateutil.parser.parse(self.start_time).replace(microsecond=0)
            self.activity_time.set(activity_time)

    def check_tracker_notifications(self):
        if self.wait_for_notification():
            self.zei_connector.set("Tracker connected")
        else:
            self.zei_connector.set("Tracker not connected")

    def check_timeular_status(self):
        if self.timeular:
            if not self.timeular.get_access_token():
                self.timeular_status.set("Timeular not connected")
            else:
                self.timeular_status.set("Timeular connected")
        else:
            self.timeular_status.set("Timeular not connected")

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

    def save_note_on_task(self):
        if self.timeular:
            tracking = self.timeular.tracking.get()["currentTracking"]
            if tracking is not None:
                note = self.text_activity.get("1.0","end").replace("\n","").replace("\t","")
                if len(note) != 0:
                    tags = self.extract_tags(note)
                    _log.info(tags)
                    activity_id = tracking["activity"]["id"]
                    activity_name = tracking["activity"]["name"]
                    tracking["note"]["text"] = note.replace("#","")
                    tracking["note"]["tags"] = tags
                    _log.info(tracking)
                    message = self.timeular.tracking.patch(activity_id, tracking)
                    self.display_message('[{0}] {1}: {2}'.format(activity_name, note, message))

    def extract_tags(self, text):
        tag_temp = []
        indices = [-1, -1]
        tag_start = False
        tag_stop = False
        tag_nr = 0
        text_clean = text.replace("#", "")
        for idx, letter in enumerate(text):
            if letter == "#":
                tag_start = True
            if tag_start:
                if indices[0] == -1:
                    indices[0] = idx
                if idx == len(text)-1:
                    indices[1] = idx
                    tag_start = False
                    tag_stop = True
                if letter == " ":
                    indices[1] = idx-1
                    tag_start = False
                    tag_stop = True
            if tag_stop:
                tag_temp.append({'indices': [indices[0]-tag_nr, indices[1]-tag_nr],
                                    'key': self.get_keys(text[indices[0]+1:indices[1]+1])})
                tag_stop = False
                tag_nr += 1
                indices = [-1, -1]
        return tag_temp

    def get_keys(self, tag_value):
        for tag in self.tags["tags"]:
            if tag_value == tag["label"]:
                return tag["key"]

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

