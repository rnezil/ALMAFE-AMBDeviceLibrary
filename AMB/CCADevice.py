'''
CCADevice represents cold cartridge bias module connected via an FEMC module
  It is a specialization of FEMCDevice: A CCADevice object can be passed to any AMBDevice or FEMCDevice method.
  Implements monitor and control of cold cartridge subsystems.
'''

from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.FEMCDevice import FEMCDevice
from AMB.AMBConnectionItf import AMBConnectionItf, AMBMessage, AMBException
from datetime import datetime
from typing import Optional
from time import sleep

class CCADevice(FEMCDevice):
    
    def __init__(self, 
                 conn:AMBConnectionItf, 
                 nodeAddr:int, 
                 band:int,                      # what band is the actual hardware
                 femcPort:Optional[int] = None, # optional override which port the band is connected to
                 logInfo = True):
        super(CCADevice, self).__init__(conn, nodeAddr, femcPort if femcPort else band, logInfo)
        self.band = band
        
    def setSIS(self, pol:int, sis:int, Vj:float = None, Imag:float = None):
        '''
        Set SIS mixer and/or magnet bias
        :param pol:  int in 0,1
        :param sis:  int 1=SIS1, 2=SIS2.  Corresponds to sideband for some bands.
        :param Vj:   float junction voltage mV.  Do nothing if None
        :param Imag: float magnet current mA     Do nothing if None
        :return True if success
        '''
        pol, sis = self.__checkPolAndDevice(pol, sis)
        subsysOffset = self.__subsysOffset(pol, sis)
        
        ret = True
        if Vj is not None:
            ret &= self.command(self.CMD_OFFSET + self.SIS_VOLTAGE + subsysOffset, self.packFloat(Vj))
        if Imag is not None:
            ret &= self.command(self.CMD_OFFSET + self.SIS_MAGNET_CURRENT + subsysOffset, self.packFloat(Imag))
        return ret

    def setSISOpenLoop(self, openLoop:bool = False):
        '''
        Set or clear the SIS open loop control bit
        :param openLoop: True=open loop
        :return True if success
        '''
        return self.command(self.CMD_OFFSET + self.SIS_OPEN_LOOP, self.packBool(openLoop))
        
    def setSISHeater(self, pol: int, enable:bool):
        return self.command(self.CMD_OFFSET + self.SIS_HEATER_ENABLE + pol * self.POL1_OFFSET, self.packBool(enable))
    
    def setLNAEnable(self, enable:bool, pol:int = -1, lna:int = -1):
        '''
        Enable/disable one, two, or all LNA devices
        :param pol:    int in 0,1 or both pols if -1
        :param lna:    int in 1,2 or both LNAs if -1
        :param enable: bool
        :return True if success
        '''
        pol = int(pol)
        lna = int(lna)
        bothPols = (pol <= -1)
        bothLNAs = (lna <= -1) 
        pol, lna = self.__checkPolAndDevice(pol, lna)
        commandData = self.packBool(enable)
        if pol == 0 or bothPols:
            if lna == 1 or bothLNAs:
                subsysOffset = 0
                self.command(self.CMD_OFFSET + self.LNA_ENABLE + subsysOffset, commandData)
            if lna == 2 or bothLNAs:
                subsysOffset = self.DEVICE2_OFFSET
                self.command(self.CMD_OFFSET + self.LNA_ENABLE + subsysOffset, commandData)
        if pol == 1 or bothPols:
            if lna == 1 or bothLNAs:
                subsysOffset = self.POL1_OFFSET
                self.command(self.CMD_OFFSET + self.LNA_ENABLE + subsysOffset, commandData)
            if lna == 2 or bothLNAs:
                subsysOffset = self.POL1_OFFSET + self.DEVICE2_OFFSET
                self.command(self.CMD_OFFSET + self.LNA_ENABLE + subsysOffset, commandData)
        return True
    
    def setLNA(self, pol:int, lna:int, 
               VD1:float = None, VD2:float = None, VD3:float = None, VD4:float = None, VD5:float = None, VD6:float = None,
               ID1:float = None, ID2:float = None, ID3:float = None, ID4:float = None, ID5:float = None, ID6:float = None):
        '''
        Set one or more LNA biases
        :param pol: int in 0,1
        :param lna: int in 1,2.  Only LNA1 is supported for bands 1,2,9,10
        :param VD1...VD3: float drain voltage.  Do nothing if None
        :param VD4...VD6: only supported for bands 1 and 2
        :param ID1...ID3: float drain current mA.  Do nothing if None
        :param ID4...ID6: only supported for bands 1 and 2 
        :return True if successful
        '''
        pol, lna = self.__checkPolAndDevice(pol, lna)
        subsysOffset = self.__subsysOffset(pol, lna)
        if VD1 is not None:
            self.command(self.CMD_OFFSET + self.LNA_DRAIN_VOLTAGE + subsysOffset, self.packFloat(VD1))
        if VD2 is not None:
            self.command(self.CMD_OFFSET + self.LNA_DRAIN_VOLTAGE + subsysOffset, self.packFloat(VD2))
        if VD3 is not None:
            self.command(self.CMD_OFFSET + self.LNA_DRAIN_VOLTAGE + subsysOffset, self.packFloat(VD3))
        if ID1 is not None:
            self.command(self.CMD_OFFSET + self.LNA_DRAIN_CURRENT + subsysOffset, self.packFloat(ID1))
        if ID2 is not None:
            self.command(self.CMD_OFFSET + self.LNA_DRAIN_CURRENT + subsysOffset, self.packFloat(ID2))
        if ID3 is not None:
            self.command(self.CMD_OFFSET + self.LNA_DRAIN_CURRENT + subsysOffset, self.packFloat(ID3))
        if self.band in (1, 2):
            # map stage 4,5,6 to lna2 stage 1,2,3
            subsysOffset += self.DEVICE2_OFFSET
            if VD4 is not None:
                self.command(self.CMD_OFFSET + self.LNA_DRAIN_VOLTAGE + subsysOffset, self.packFloat(VD4))
            if VD5 is not None:
                self.command(self.CMD_OFFSET + self.LNA_DRAIN_VOLTAGE + subsysOffset, self.packFloat(VD5))
            if VD6 is not None:
                self.command(self.CMD_OFFSET + self.LNA_DRAIN_VOLTAGE + subsysOffset, self.packFloat(VD6))
            if ID4 is not None:
                self.command(self.CMD_OFFSET + self.LNA_DRAIN_CURRENT + subsysOffset, self.packFloat(ID4))
            if ID5 is not None:
                self.command(self.CMD_OFFSET + self.LNA_DRAIN_CURRENT + subsysOffset, self.packFloat(ID5))
            if ID6 is not None:
                self.command(self.CMD_OFFSET + self.LNA_DRAIN_CURRENT + subsysOffset, self.packFloat(ID6))
        return True
        
    def setLNALEDEnable(self, pol:int, enable:bool):
        pol, sis = self.__checkPolAndDevice(pol, 1)
        return self.command(self.CMD_OFFSET + self.LNA_LED_ENABLE + pol * self.POL1_OFFSET, self.packBool(enable))
        
    def getLNALEDEnable(self, pol:int):
        try:
            return self.unpackBool(self.monitor(self.LNA_LED_ENABLE + pol * self.POL1_OFFSET))
        except AMBException:
            return False

    def getCartridgeTemps(self):
        '''
        Read the cartridge temperature sensors:
        :return { 'temp0': float ... 'temp5': float } values in Celcius 
        '''
        ret = {}
        for i in range(6):
            try:
                ret[f"temp{i}"] = round(self.unpackFloat(self.monitor(self.CARTRIDGE_TEMP + (i * self.CARTRIDGE_TEMP_OFFSET))), 4)
            except AMBException:
                ret[f"temp{i}"] = 0.0
        return ret
    
    def getSIS(self, pol:int, sis:int, averaging:int = 1):
        '''
        Read the SIS monitor data for a specific pol and sb:
        :param pol: int in 0..1
        :param sis: int in 1=SIS1, 2=SIS2.  Corresponds to sideband in some bands.
        :averaging int number of samples of Vj and Ij to average
        :return { 'Vj': float mV, 'Ij': float mA, 'Vmag': float, 'Imag': float mA, 'averaging': int }
        '''
        if not self.hasSIS(self.band):
            return None
        pol, sis = self.__checkPolAndDevice(pol, sis)
        averaging = int(averaging)
        if averaging < 1:
            averaging = 1

        subsysOffset = self.__subsysOffset(pol, sis)
        
        sumVj = 0
        sumIj = 0
        try:
            for _ in range(averaging):
                sumVj += self.unpackFloat(self.monitor(self.SIS_VOLTAGE + subsysOffset))
                sumIj += self.unpackFloat(self.monitor(self.SIS_CURRENT + subsysOffset))
        except AMBException:
            pass
        ret = {}
        
        ret['Vj'] = round(sumVj / averaging, 4)  
        ret['Ij'] = round(sumIj / averaging, 4) 
        try:
            ret['Vmag'] = round(self.unpackFloat(self.monitor(self.SIS_MAGNET_VOLTAGE + subsysOffset)), 4)
            ret['Imag'] = round(self.unpackFloat(self.monitor(self.SIS_MAGNET_CURRENT + subsysOffset)), 4)
        except AMBException:
            ret['Vmag'] = 0
            ret['Imag'] = 0
        ret['averaging'] = averaging
        return ret

    def getSISSettings(self, pol: int, sis: int):
        """
        Get the set values for SIS voltage and magnet current
        :param pol: int in 0..1
        :param sis: int in 1=SIS1, 2=SIS2.  Corresponds to sideband in some bands.
        :return { 'Vj': float mV, 'Imag': float mA }
        """
        if not self.hasSIS(self.band):
            return None
        pol, sis = self.__checkPolAndDevice(pol, sis)
        subsysOffset = self.__subsysOffset(pol, sis)

        try:
            return {
                'Vj': self.unpackFloat(self.monitor(self.CMD_OFFSET + self.SIS_VOLTAGE + subsysOffset)),
                'Imag': self.unpackFloat(self.monitor(self.CMD_OFFSET + self.SIS_MAGNET_CURRENT + subsysOffset))
            }
        except AMBException:
            return {'Vj': 0, 'Imag': 0}

    def getSISOpenLoop(self):
        '''
        Get the SIS open loop configuration:
        :return True if open loop
        '''
        try:
            return self.unpackBool(self.monitor(self.SIS_OPEN_LOOP))
        except AMBException:
            return False

    def getLNA(self, pol:int, lna:int):
        '''
        Read the LNA monitor data for a specific pol and sb
        Handles mapping sb2 stages 1,2,3 to stages 4,5,6 for bands 1 and 2
        :param pol:   int in 0..1
        :param lna:   int in 1=LNA1, 2=LNA2.  Corresponds to sideband for some bands.
        :return { 'enable': bool, 
                  'VD1' ... 'VD6': float,        -> stages 4-6 only returned for bands 1 and 2.
                  'ID1' ... 'ID6': float,
                  'VG1' ... 'VG6': float } 
        '''
        pol, lna = self.__checkPolAndDevice(pol, lna)
        subsysOffset = self.__subsysOffset(pol, lna)

        ret = {}
        try:
            ret['enable'] = self.unpackBool(self.monitor(self.LNA_ENABLE + subsysOffset))
        except AMBException:
            ret['enable'] = False

        for stage in range(3):
            try:
                stageOffset = stage * self.LNA_STAGE_OFFSET
                ret[f"VD{stage + 1}"] = round(self.unpackFloat(self.monitor(self.LNA_DRAIN_VOLTAGE + subsysOffset + stageOffset)), 4)
                ret[f"ID{stage + 1}"] = round(self.unpackFloat(self.monitor(self.LNA_DRAIN_CURRENT + subsysOffset + stageOffset)), 4)
                ret[f"VG{stage + 1}"] = round(self.unpackFloat(self.monitor(self.LNA_GATE_VOLTAGE + subsysOffset + stageOffset)), 4)
            except AMBException:
                ret[f"VD{stage + 1}"] = 0
                ret[f"ID{stage + 1}"] = 0
                ret[f"VG{stage + 1}"] = 0

            if self.band in (1, 2):
                # for bands 1 and 2 we return VD4...VD6 etc. by mapping to stages 1-3 of sb2
                try:
                    ret[f"VD{stage + 4}"] = round(self.unpackFloat(self.monitor(self.LNA_DRAIN_VOLTAGE + subsysOffset + self.DEVICE2_OFFSET + stageOffset)), 4)
                    ret[f"ID{stage + 4}"] = round(self.unpackFloat(self.monitor(self.LNA_DRAIN_CURRENT + subsysOffset + self.DEVICE2_OFFSET + stageOffset)), 4)
                    ret[f"VG{stage + 4}"] = round(self.unpackFloat(self.monitor(self.LNA_GATE_VOLTAGE + subsysOffset + self.DEVICE2_OFFSET + stageOffset)), 4)
                except AMBException:
                    ret[f"VD{stage + 4}"] = 0
                    ret[f"ID{stage + 4}"] = 0
                    ret[f"VG{stage + 4}"] = 0
        return ret
            
    def getSISHeaterCurrent(self, pol: int):
        '''
        Get the SIS heater current 
        :return float
        '''
        try:
            return round(self.unpackFloat(self.monitor(self.SIS_HEATER_CURRENT + pol * self.POL1_OFFSET)), 4)
        except AMBException:
            return 0

    def IVCurve(self, pol: int, sis: int, VjLow: float = None, VjHigh: float = None, VjStep: float = None):
        pol, sis = self.__checkPolAndDevice(pol, sis)

        if not self.hasSIS(self.band):
            print(f"Band {self.dev.band} has no SIS.")
            return None

        if sis == 2 and not self.hasSIS2(self.band):
            print(f"Band {self.dev.band} has no SIS.")
            return None

        # get and conditionally assign band-specific defaults:
        dl, dh, ds = self.getIVCurveDefaults(self.band)
        VjLow = VjLow if VjLow is not None else dl
        VjHigh = VjHigh if VjHigh is not None else dh
        VjStep = VjStep if VjStep is not None else ds

        # sort the Vj inputs into min and max:
        if VjHigh < VjLow:
            VjLow, VjHigh = VjHigh, VjLow

        # make VjStep positive for now:
        VjStep = abs(VjStep)

        # prevent divide by zero:
        VjRange = VjHigh - VjLow
        if VjRange == 0:
            self.__logMessage(f"{VjLow} == {VjHigh} would divide by zero.")
            return None
        # check that VjRange is at least 1 step
        elif VjRange < VjStep:
            self.__logMessage(f"{VjLow}..{VjHigh} is smaller than one step.")
            return None

        # Sweep one or two ranges:
        Vj1Negative = VjLow < 0
        Vj2Positive = VjHigh > 0
        zeroCrossing = Vj1Negative and Vj2Positive

        # store the voltage setting in effect now:
        priorState = self.getSISSettings(pol, sis)
        subsysOffset = self.__subsysOffset(pol, sis) + self.femcPortOffset(self.femcPort)

        sequence1 = []
        sequence2 = []
        result1 = []
        result2 = []

        # check that we can monitor SIS at all and abort if not:
        try:
            self.monitor(self.SIS_VOLTAGE + subsysOffset)
        except AMBException:
            return None

        # Sweep first range from negative towards zero:
        if Vj1Negative:
            endpt = 0 if zeroCrossing else VjHigh
            self.__IVCurveInnerLoop(sequence1, subsysOffset, VjLow, endpt, VjStep)
            result1 = self.conn.runSequence(self.nodeAddr, sequence1)
            if not result1:
                return None

        # Sweep second range from positive towards zero:
        if Vj2Positive:
            endpt = 0 if zeroCrossing else VjLow
            self.__IVCurveInnerLoop(sequence2, subsysOffset, VjHigh, endpt, -VjStep)
            result2 = self.conn.runSequence(self.nodeAddr, sequence2)
            if not result2:
                return None
        
        VjSet = []
        VjRead = []
        IjRead = []
        for i in range(int(len(result1) / 3)):
            VjSet.append(self.unpackFloat(result1[i * 3].data))
            VjRead.append(self.unpackFloat(result1[i * 3 + 1].data))
            IjRead.append(self.unpackFloat(result1[i * 3 + 2].data))

        # reverse the results from sequence2 so that VjSet increases monotonically:
        for i in range(int(len(result2) / 3) - 1, -1, -1):
            VjSet.append(self.unpackFloat(result2[i * 3].data))
            VjRead.append(self.unpackFloat(result2[i * 3 + 1].data))
            IjRead.append(self.unpackFloat(result2[i * 3 + 2].data))
            
        return (VjSet, VjRead, IjRead)

    def __IVCurveInnerLoop(self, sequence, subsysOffset, Vj1, Vj2, VjStep):

        # sweep to the first point:
        VjSet = Vj1
        self.command(self.CMD_OFFSET + self.SIS_VOLTAGE + subsysOffset, self.packFloat(VjSet))
        sleep(.01)

        done = False
        while not done:
            # set and read messages:
            sequence.append(AMBMessage(
                self.CMD_OFFSET + self.SIS_VOLTAGE + subsysOffset,
                self.packFloat(VjSet)
            ))
            sequence.append(AMBMessage(
                self.SIS_VOLTAGE + subsysOffset,
                bytes(0)
            ))
            sequence.append(AMBMessage(
                self.SIS_CURRENT + subsysOffset,
                bytes(0)
            ))
            
            # increment and loop end condition:
            VjSet += VjStep

            if VjStep < 0.0:
                if VjSet <= Vj2:
                    done = True
            else:
                if VjSet >= Vj2:
                    done = True

    @staticmethod
    def getIVCurveDefaults(band):
        numPoints = 401
        VjMax = 3.0
        
        if band == 4:
            VjMax = 6.5
        elif band in (3, 6):
            VjMax = 12.0
        elif band in (5, 7, 8, 9, 10):
            VjMax = 3.0
        else:
            return None
        return (-VjMax, VjMax, (2 * VjMax) / (numPoints - 1))

    def __subsysOffset(self, pol, device):
        return (pol * self.POL1_OFFSET) + ((device - 1) * self.DEVICE2_OFFSET)

    def __checkPolAndDevice(self, pol:int, device:int):
        '''
        Coerce pol and device into legal ranges, depending on cartridge band
        :return (pol, device) coerced
        '''
        pol = int(pol)
        device = int(device)

        if pol < 0:
            pol = 0
        elif pol > 1:
            pol = 1
        if device < 1:
            device = 1
        elif device > 2:
            device = 2
        # only device 1 supported for bands 1, 2, 9, 10:
        if not self.hasSIS2(self.band):
            device = 1
        return (pol, device)
    
    def __logMessage(self, msg, alwaysLog = False):
        if self.logInfo or alwaysLog:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + f" CCADevice band{self.band}: {msg}")

    @staticmethod
    def hasSIS(band : int):
        return band >= 3

    @staticmethod
    def hasSIS2(band: int):
        return band in (3, 4, 5, 6, 7, 8)

    # RCAs used internally:
    CMD_OFFSET              = 0x10000
    POL1_OFFSET             = 0x0400
    DEVICE2_OFFSET          = 0x0080
    CARTRIDGE_TEMP_OFFSET   = 0x0010
    LNA_STAGE_OFFSET        = 0x0004
    CARTRIDGE_TEMP          = 0x0880
    SIS_VOLTAGE             = 0x0008
    SIS_CURRENT             = 0x0010
    SIS_OPEN_LOOP           = 0x0018
    SIS_MAGNET_VOLTAGE      = 0x0020
    SIS_MAGNET_CURRENT      = 0x0030
    LNA_ENABLE              = 0x0058
    LNA_DRAIN_VOLTAGE       = 0x0040
    LNA_DRAIN_CURRENT       = 0x0041
    LNA_GATE_VOLTAGE        = 0x0042
    LNA_LED_ENABLE          = 0x0100
    SIS_HEATER_ENABLE       = 0x0180    # command only
    SIS_HEATER_CURRENT      = 0x01C0
