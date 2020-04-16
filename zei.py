# -*- coding: utf-8 -*-
#

from bluepy import btle
import config
from timeular import Timeular
import struct

import logging
_log = logging.getLogger(__name__)
_log.addHandler(logging.StreamHandler())
_log.setLevel(logging.INFO)


timeular_zei = Timeular(api_key=config.credentials["apiKey"], 
            api_secret=config.credentials["apiSecret"])


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
        self.withDelegate(ZeiDelegate(self))

        # activate notifications about turn
        self.orientation = ZeiOrientationChar(self)
        self.orientation.enable()

class ZeiDelegate(btle.DefaultDelegate):

    def __init__(self, periph):
        btle.DefaultDelegate.__init__(self)
        self.parent = periph

    def handleNotification(self, cHandle, data):
        if cHandle == 39:
            side = struct.unpack('B', data)
            _log.info("Current side up is %s", side)

            #print(timeular_zei.activities.get_activitity_side(side[0]))
        
        else:
            _log.info("Notification from hndl: %s - %r", cHandle, data)

class ZeiDiscoveryDelegate(btle.DefaultDelegate):
    def __init__(self, scanner, periph):
        btle.DefaultDelegate.__init__(self)
        self.scanner = scanner
        self.periph = periph

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if not dev.addr == config.device_config["devMac"]:
            return
        _log.info("Device %s (%s), RSSI=%d dB", dev.addr, dev.addrType, dev.rssi)
        for (adtype, desc, value) in dev.getScanData():
            _log.info("  %s = %s", desc, value)
        # reconnect

        # bluepy can only do one thing at a time, so stop scanning while trying to connect
        # this is not supported by bluepy
        #self.scanner.stop()

        try:
            self.periph.connect(dev)
            self.scanner.stop_scanning = True
        except:
            # re
            self.scanner.start()
            pass

class ZeiDiscovery(btle.Scanner):

    def __init__(self, periph=None, **kwargs):
        self.zei = periph
        btle.Scanner.__init__(self, **kwargs)
        #self.withDelegate(ZeiDiscoveryDelegate(self, self.zei))
        #self.stop_scanning = False

    def reconnect(self):
        self.iface=self.zei.iface
        self.clear()
        self.start()
        while self.zei.addr not in self.scanned:
            self.process(timeout=2)
        self.stop()
        self.zei.connect(self.scanned[self.zei.addr])

def main():
    zei = Zei(config.device_config["devMac"], 'random', iface=0)
    scanner = ZeiDiscovery(zei)

    while True:
        try:
             zei.waitForNotifications(timeout=None)
        except Exception as e:
            _log.exception(e)
            scanner.reconnect()

    zei.disconnect()

if __name__ == "__main__":
    main()