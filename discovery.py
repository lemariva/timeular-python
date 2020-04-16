# -*- coding: utf-8 -*-
#
#

from bluepy import btle

class ScanDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if not dev.addr == 'f1:05:a5:9c:2e:9b':
            return
        if isNewDev:
            print ("Discovered device", dev.addr)
            print ("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
            print (dev.getScanData())
            for (adtype, desc, value) in dev.getScanData():
                print ("  %s = %s" % (desc, value))
        elif isNewData:
            print ("Received new data from", dev.addr)
            print ("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
            for (adtype, desc, value) in dev.getScanData():
                print ("  %s = %s" % (desc, value))
#        else:
#            print "Discovered device", dev.addr


scanner = btle.Scanner(0).withDelegate(ScanDelegate())
scanner.start()

while True:
    scanner.process(30)

scanner.stop()

# for dev in devices:
#     print "Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi)
#     for (adtype, desc, value) in dev.getScanData():
#         print "  %s = %s" % (desc, value)