# ALMAFE-AMBDeviceLibrary
## A Python package for monitor and control of ALMA Antenna Master Bus devices, particularly the Front End
Morgan McLeod <mmcleod@nrao.edu>, February 2023

### Background
At the North America Front End Integration Center (FEIC), Christian Holmstedt wrote a pair of LabVIEW applications:
* Master3.vi
* TestCartridgeM&C.vi

Master3 is mainly for low-level probing of the CAN bus to see which devices are there, and to send and recieve individual messages.   TestCartridgeM&C supports operating one Cold Cartridge and one LO simultaneously.  Several features were added to TestCartridgeM&C over the years (2003 - 2011 approximately) such as for sweeping I-V curves and for some low-level hardware diagnostics of the M&C hardware in the front end.  It remains quite suitable today for bench testing CCAs and WCAs.

I have maintained TestCartridgeM&C since 2012.

When I was improving the band 6 mixer test system (MTS) software in 2018, I found that the central kernel of TestCartridgeM&C which talks to the hardware, had also been reused in this system.  I rewrote it in LabVIEW using a much more object-oriented approach.  I called the resulting library AMBDeviceLibrary, same as this package.  It was used in the MTS and subsequently in several tests sets in the NRAO front end local oscillator lab.

This package is a port from that LabVIEW library to Python.  They both are structured and work in about the same way.

### Connection Classes
**AMBConnectionItf** defines the abstract interface to a bus connection as well as some helper classes.

**AMBConnectionNican** implements AMBConnectionItf in terms of the [python-can](https://pypi.org/project/python-can/) package.  It presumes you have National Instruments CAN hardware and the NI-CAN driver installed on your system.

**AMBConnectionDLL** also implements AMBConnectionItf and depends on NI-CAN hardware and driver.  I noticed while sweeping an I-V curve that the performance of python-can was quite poor compared to LabVIEW.  This class uses a C++ Windows DLL, [FrontEndAMBDLL](https://github.com/morganmcleod/ALMA-FEControl/tree/master/FrontEndAMBDLL) which I wrote.  The DLL is an extremely simple pass-through for most CAN messages but it adds a *runSequence()* method so that a list of CAN requests can be serviced rapid-fire with the results passed back to the Python method which called it.

Future: **AMBConnectionNixnet** will implement the interface for National Instruments XNET hardware.  NI stopped updating the NI-CAN driver in 2018 and stopped selling NI-CAN hardware in early 2020.  Now the only hardware available from NI is not backwards compatible with the NI-CAN drivers.  The only upside to this forced upgrade is that it will now support 64-bit applications.  NI-CAN only ever supported 32-bit.

### Device Classes
**AMBDevice** implements the [ALMA Monitor and Control Bus Standard Interface](https://aedm.alma.cl/document/4e664760-998e-4a81-9298-fd181a3ce36e/info).  It can be used to send messages to any CAN device, anywhere in an antenna or elsewhere.

**FEMCDevice** inherits from AMBDevice and adds all the messages for the FEMC module.  It can be used to send messages to any subsystem of the front end.

**CCADevice** inherits from FEMCDevice and adds all the messages for the cold cartridge bias module.

**LODevice** inherits from FEMCDevice and adds all the messages for the local oscillator monitor and control module.

Future:  Other classes could be added for other front end subsystems: Cryostat, LPR, etc.

### Usage
See (/Examples)





