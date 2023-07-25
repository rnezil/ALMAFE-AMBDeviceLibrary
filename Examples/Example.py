from AMB.AMBConnectionNican import AMBConnectionNican
from AMB.CCADevice import CCADevice, FEMCDevice
import time

# open a NI-CAN connection
start = time.time()
conn = AMBConnectionNican(0, resetOnError = True)
self.logger.info(f"Connected in {time.time() - start} sec")
conn.receiveTimeout = 0.005

# create a device using the connection
start = time.time()
dev = CCADevice(conn, nodeAddr = 0x13, band = 3)
self.logger.info(f"CCADevice in {time.time() - start} sec")
# band = 3 here specifies to operate it as a band 3 cartride in all ways (behavior, defaults, enabled subsystems).
# there is another option femcPort if you want to, say run a band 3 receiver on the band 1 port.

# initilize the FEMC module
start = time.time()
dev.initSession(FEMCDevice.MODE_SIMULATE)
self.logger.info(f"initSession in {time.time() - start} sec")
# MODE_SIMULATE only supported since FEMC firmware 3.6.3 otherwise you need a real bias module connected.

# since CCADevice is based on FEMCDevice, and ultimately AMBDevice, we can send requests to the FEMC module as well:
start = time.time()
temp = dev.getAmbsiTemperature()
self.logger.info(f"AMBSI temperature: {temp} C in {time.time() - start} sec")

start = time.time()
fw = dev.getFemcVersion()
self.logger.info(f"FEMC firmware version: {fw} C in {time.time() - start} sec")

start = time.time()
ESNs = dev.getEsnList()
self.logger.info(f"All the ESNS: {ESNs} in {time.time() - start} sec")

# power up the CCA at FEMC port 3:
start = time.time()
dev.setBandPower(3, True)
self.logger.info(f"setBandPower in {time.time() - start} sec")
time.sleep(0.5)
# this is required by the FEMC module even if we don't have a cartridge power distribution module.

# read some cartridge monitor points:
start = time.time()
temp = dev.getCartridgeTemps()
self.logger.info(f"Cartridge temps: {temp} in {time.time() - start} sec")

start = time.time()
sis = dev.getSIS(0, 1)
self.logger.info(f"pol0 sis1: {sis} in {time.time() - start} sec")

# control something:
start = time.time()
dev.setSIS(0, 1, 3.0)
self.logger.info(f"setSIS in {time.time() - start} sec")

start = time.time()
sis = dev.getSIS(0, 1)
self.logger.info(f"pol0 sis1: {sis} in {time.time() - start} sec")

# shutdown must be done explicitly:
start = time.time()
dev.shutdown()
self.logger.info(f"dev.shutdown in {time.time() - start} sec")

start = time.time()
conn.shutdown()
self.logger.info(f"conn.shutdown in {time.time() - start} sec")
