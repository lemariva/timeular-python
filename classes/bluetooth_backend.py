from bluepy import btle
import struct
from utils.wrapper import check_bluetooth

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.StreamHandler())
_log.setLevel(logging.NOTSET)

def _ZEI_UUID(short_uuid):
    return 'c7e7%04X-c847-11e6-8175-8c89a55d403c' % (short_uuid)

def _ZEI_UUID(short_uuid):
    return 'c7e7%04X-c847-11e6-8175-8c89a55d403c' % (short_uuid)

class ZeiCharBase:

    def __init__(self, periph):
        self.periph = periph
        self.hndl = None

    def enable(self):
        _svc = self.periph.getServiceByUUID(self.svcUUID)
        _chr = _svc.getCharacteristics(self.charUUID)[0]
        self.hndl = _chr.getHandle()

        # this is uint16_t - see:
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.descriptor.gatt.client_characteristic_configuration.xml
        _cccd = _chr.getDescriptors(btle.AssignedNumbers.client_characteristic_configuration)[0]
        _cccd.write(struct.pack("<H", 2), withResponse=True)

class ZeiOrientationChar(ZeiCharBase):
    svcUUID = _ZEI_UUID(0x0010)
    charUUID = _ZEI_UUID(0x0012)

    def __init__(self, periph):
        ZeiCharBase.__init__(self, periph)

class BatteryLevelChar(ZeiCharBase):
    svcUUID = btle.AssignedNumbers.battery_service
    charUUID = btle.AssignedNumbers.battery_level

    def __init__(self, periph):
        ZeiCharBase.__init__(self, periph)

class Zei(btle.Peripheral):

    def __init__(self, *args, **kwargs):
        btle.Peripheral.__init__(self, *args, **kwargs)
        
        # activate notifications about turn
        self.orientation = ZeiOrientationChar(self)
        self.orientation.enable()

    def set_handler(self, handler):
        self._handler = handler
        self.withDelegate(ZeiDelegate(self, self._handler))


class ZeiDelegate(btle.DefaultDelegate):

    def __init__(self, periph, handler):
        btle.DefaultDelegate.__init__(self)
        self.parent = periph
        self.ble_handler = handler

    def handleNotification(self, cHandle, data):
        self.ble_handler(cHandle, data)

        if cHandle == 39:
            side = struct.unpack('B', data)
            _log.info("Current side up is %s", side)
        else:
            _log.info("Notification from hndl: %s - %r", cHandle, data)

class ZeiDiscovery(btle.Scanner):

    def __init__(self, periph=None, **kwargs):
        self.zei = periph
        btle.Scanner.__init__(self, **kwargs)

    def reconnect(self):
        self.iface=self.zei.iface
        self.clear()
        self.start()
        while self.zei.addr not in self.scanned:
            self.process(timeout=2)
        self.stop()
        self.zei.connect(self.scanned[self.zei.addr])

class BluetoothBackend():
    """
    This is a class which our GUI inherits from. It's main purpose is to deal
    with really anything that involves the Bluetooth network. Things like creating, 
    closing sockets, discovering devices, and sending data over sockets.

    Functions which deal with manipulation of data prior to socket interaction will
    not be housed within this class.

    Note however that there are multiple instances of calling methods which
    adjust or modify the GUI. Still not sure if those sections are appropirate
    or whether they should be seperated entirely.
    """
    zei = None
    scanner = None
    delimiter = '\n'.encode('ascii')

    def discover_nearby_devices(self):
        """
        Scan for any nearby devices and display their address. If nothing was found,
        display an error message stating as such.
        """
        self.display_message('Searching for nearby devices...')
        devices = btle.Scanner().scan(10.0)
        if devices:
            self.display_message('Found the following devices: ')
            for device in devices:
                self.display_message('{0}', device.addr)
        else:
            self.display_message_box('showerror', 'Error', 'Unable to find any devices')

    def connect_to_zei(self, adress, handler):
        self.mac_address = adress
        self.gui_handler = handler
        self.zei = Zei(adress, 'random', iface=0)
        self.zei.set_handler(self.gui_handler)
        self.scanner = ZeiDiscovery(self.zei)

    def wait_for_notification(self, timeout=1):
        if self.zei:
            try:
                self.zei.waitForNotifications(timeout=timeout)
                return True
            except btle.BTLEDisconnectError:
                self.connect_to_zei(self.mac_address, self.gui_handler)
                return True
        else:
            return False 

    def the_connection_was_lost(self):
        self.display_message_box('showerror','Error','The connection was lost')
        self.close_connection()

    def remove_zei(self):
        self.zei = None

    @check_bluetooth
    def close_connection(self):
        try:
            self.zei.disconnect()
        finally:
            self.remove_zei()
            self.display_message('Closed connection')
