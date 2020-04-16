#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
taken from https://github.com/Ankirama/python-timeular
"""

import requests
import json
from functools import wraps
from datetime import datetime

def check_token(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._access_token == None:
            return False
        return f(self, *args, **kwargs)

    return wrapper

def get_current_time():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

class API(object):
    _METHODS = ['get', 'post', 'patch', 'delete']
    _CLASS_STATUS_CODES = (200, 226) # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_Success

    _access_token = None
    _base_url = None

    def __init__(self, base_url, access_token=None):
        self._base_url = base_url
        self._access_token = access_token
    
    def _make_response(self, route='', method='get', json_data={}, need_auth=True, headers={}):
        if method not in self._METHODS:
            print('[%s] is not allowed' % method)
            return False
        url = self._base_url + route
        
        if need_auth:
            headers['Authorization'] = 'Bearer ' + self._access_token

        response = getattr(requests, method)(url, json=json_data, headers=headers)

        if response.status_code < self._CLASS_STATUS_CODES[0] or \
            response.status_code > self._CLASS_STATUS_CODES[1]:
            print('code error: %d' % response.status_code)
            print('[%s]: %s' % (url, response.text))
            return False
        return response.json()

class Timeular(API):
    activities = None
    devices = None
    tracking = None
    time_entries = None
    _api_key = None
    _api_secret = None

    def __init__(self, api_key='', api_secret='', base_url='https://api.timeular.com/api/v2'):
        super(Timeular, self).__init__(base_url)
        self._api_key = api_key
        self._api_secret = api_secret
        if not self.get_access_token():
            raise ValueError('Check base_url and the route to get your access token')
        self.activities = Activities(base_url, self._access_token)
        self.devices = Devices(base_url, self._access_token)
        self.tracking = Tracking(base_url, self._access_token)
        self.time_entries = TimeEntries(base_url, self._access_token)

    def set_api_key(self, api_key):
        self._api_key = api_key

    def set_api_secret(self, api_secret):
        self._api_secret = api_secret

    def get_access_token(self):
        result = self._make_response('/developer/sign-in', 
                                method="post", 
                                json_data={'apiKey': self._api_key, 
                                      'apiSecret': self._api_secret}, 
                                need_auth=False)
        if not result:
            return False
        self._access_token = result['token']
        return result

    @check_token
    def get_profile(self):
        return self._make_response('/user/profile')

    @check_token
    def get_integrations(self):
        return self._make_response('/integrations')

    @check_token
    def get_report(self, start_timestamp, stop_timestamp, timezone='Europe/Paris'):
        route = '/report/%s/%s?timezone=%s' % (str(start_timestamp), str(stop_timestamp), str(timezone))
        return self._make_response(route)

class Activities(API):
    _BASE_URL = '/activities'

    def __init__(self, base_url, access_token):
        super(Activities, self).__init__(base_url + self._BASE_URL, access_token)

    @check_token
    def get(self):
        return self._make_response()

    @check_token
    def get_activitity_side(self, side):
        activities = self._make_response()["activities"]
        for activity in activities:
            if activity["deviceSide"] == side:
                return activity

    @check_token
    def post(self, json):
        return self._make_response(method='post', json=json)

    @check_token
    def patch(self, activity_id, json={}):
        route = '/%s' % str(activity_id)
        return self._make_response(route, method='patch', json=json)

    @check_token
    def delete(self, activity_id):
        route = '/%s' % str(activity_id)
        return self._make_response(route, method='delete', json=json)

    @check_token
    def post_device_side(self, activity_id, device_side):
        route = '/%s/device-side/%s' % (str(activity_id), str(device_side))
        return self._make_response(route, method='post')

    @check_token
    def delete_device_side(self, activity_id, device_side):
        route = '/%s/device-side/%s' % (str(activity_id), str(device_side))
        return self._make_response(route, method='delete')

    @check_token
    def get_tags_and_mentions(self, activity_id):
        route = '/%s' % (str(activity_id))
        return self._make_response(route)

    @check_token
    def get_archived(self):
        return self._make_response('/archived-activities', method='delete')

class Devices(API):
    _BASE_URL = '/devices'

    def __init__(self, base_url, access_token):
        super(Devices, self).__init__(base_url + self._BASE_URL, access_token)

    @check_token
    def get(self):
        return self._make_response()

    @check_token
    def patch(self, device_serial, json={}):
        route = '/%s' % str(device_serial)
        return self._make_response(route, method='patch', json=json)

    @check_token
    def delete(self, device_serial):
        route = '/%s' % str(device_serial)
        return self._make_response(route, method='delete')

    @check_token
    def post_disabled(self, device_serial):
        route = '/%s/disabled' % str(device_serial)
        return self._make_response(route, method='post')

    @check_token
    def delete_disabled(self, device_serial):
        route = '/%s/disabled' % str(device_serial)
        return self._make_response(route, method='delete')

    @check_token
    def post_active(self, device_serial):
        route = '/%s/active' % str(device_serial)
        return self._make_response(route, method='post')

    @check_token
    def delete_active(self, device_serial):
        route = '/%s/active' % str(device_serial)
        return self._make_response(route, method='delete')

class Tracking(API):
    _BASE_URL = '/tracking'

    def __init__(self, base_url, access_token):
        super(Tracking, self).__init__(base_url + self._BASE_URL, access_token)

    @check_token
    def get(self):
        return self._make_response()

    @check_token
    def post_start(self, activity_id):
        route = '/%s/start' % str(activity_id)
        datetime = get_current_time()
        return self._make_response(route, method='post', json={'startedAt': datetime})

    @check_token
    def patch(self, activity_id, json={}):
        route = '/%s' % str(activity_id)
        return self._make_response(route, method='patch', json=json)

    @check_token
    def post_stop(self, activity_id):
        route = '/%s/stop' % str(activity_id)
        datetime = get_current_time()
        return self._make_response(route, method='post', json={'stoppedAt': datetime})

class TimeEntries(API):
    _BASE_URL = '/time-entries'

    def __init__(self, base_url, access_token):
        super(TimeEntries, self).__init__(base_url + self._BASE_URL, access_token)

    @check_token
    def get_in_range(self, stopped_after, started_before):
        route = '/%s/%s' % (str(stopped_after), str(started_before))
        return self._make_response(route)

    @check_token
    def get_by_id(self, time_entry_id):
        route = '/%s' % str(time_entry_id)
        return self._make_response(route)

    @check_token
    def post(self, json):
        return self._make_response(method='post', json=json)

    @check_token
    def patch(self, time_entry_id, json={}):
        route = '/%s' % str(time_entry_id)
        return self._make_response(route, method='patch', json=json)

    @check_token
    def delete(self, time_entry_id):
        route = '/%s' % str(time_entry_id)
        return self._make_response(route, method='delete')
