from AMB.AMBConnectionNican import AMBConnectionNican
from AMB.CCADevice import CCADevice, FEMCDevice
import time

# open a NI-CAN connection
conn = AMBConnectionNican(0, resetOnError = True)

# create a device using the connection
dev = CCADevice(conn, nodeAddr = 0x13, band = 3)
# band = 3 here specifies to operate it as a band 3 cartride in all ways (behavior, defaults, enabled subsystems).
# there is another option femcPort if you want to, say run a band 3 receiver on the band 1 port.

# initilize the FEMC module
dev.initSession(FEMCDevice.MODE_SIMULATE)
# MODE_SIMULATE only supported since FEMC firmware 3.6.3 otherwise you need a real bias module connected.

# since CCADevice is based on FEMCDevice, and ultimately AMBDevice, we can send requests to the FEMC module as well:
temp = dev.getAmbsiTemperature()
print(f"AMBSI temperature: {temp} C")

fw = dev.getFemcVersion()
print(f"FEMC firmware version: {fw}")

ESNs = dev.getEsnList()
print("All the ESNS:", ESNs)

# power up the CCA at FEMC port 3:
dev.setBandPower(3, True)
time.sleep(0.5)
# this is required by the FEMC module even if we don't have a cartridge power distribution module.

# read some cartridge monitor points:
temp = dev.getCartridgeTemps()
print("Cartridge temps:", temp)

sis = dev.getSIS(0, 1)
print("pol0 sis1:", sis)

# control something:
dev.setSIS(0, 1, 3.0)
sis = dev.getSIS(0, 1)
print("pol0 sis1:", sis)

# shutdown must be done explicitly:
dev.shutdown()
conn.shutdown()

