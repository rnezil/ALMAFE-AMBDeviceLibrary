'''
LODevice represents a standarf local oscillator connected via an FEMC module.
  It is a specialization of FEMCDevice: A LODevice object can be passed to any AMBDevice or FEMCDevice method.
  It has YTO endpoints and handles YTO tuning commands with frequency in GHz.
  Implements monitor and control of LO subsystems, lock search, and zero correction voltage.
'''
from AMB.FEMCDevice import FEMCDevice
from AMB.AMBConnectionItf import AMBConnectionItf
from datetime import datetime
from typing import Optional
from time import sleep

class LODevice(FEMCDevice):

    LOOPBW_DEFAULT      = -1    # use the band's default loop bandwidth
    LOOPBW_NORMAL       = 0     # override to use the "normal" loop BW:   7.5MHz/V (Band 2,4,8,9)
    LOOPBW_ALT          = 1     # override to use the "alternate" loop BW: 15MHz/V (Band 3,5,6,7,10, and NRAO band 2 prototype)
    
    LOCK_BELOW_REF      = 0     # lock below the reference signal
    LOCK_ABOVE_REF      = 1     # lock above the reference signal
    
    def __init__(self, 
                 conn:AMBConnectionItf, 
                 nodeAddr:int, 
                 band:int,                      # what band is the actual hardware
                 femcPort:Optional[int] = None, # optional override which port the band is connected to
                 logInfo = True):
        super(LODevice, self).__init__(conn, nodeAddr, femcPort if femcPort else band, logInfo)
        self.band = band
        self.ytoLowGHz = 0
        self.ytoHighGHz = 0
    
    def setYTOLimits(self, lowGHz:float, highGHz:float):
        self.ytoLowGHz = lowGHz
        self.ytoHighGHz = highGHz
        
    def setLOFrequency(self, freqGHz:float):
        # avoid divide by zero
        if freqGHz == 0:
            self.__logMessage(f"setLOFrequency ERROR freqLOGHz={freqGHz}", True)
            return 0, 0, 0
        # frequency at the WCA outputs: 
        wcaFreq = freqGHz / self.COLD_MULTIPLIERS[self.band]
        # YTO tuning frequency:
        ytoFreq = wcaFreq / self.WARM_MULTIPLIERS[self.band]
        ytoCourse = self.__ytoFreqToCourse(ytoFreq)
        if ytoCourse == 0:
            return 0, 0, 0
        self.setYTOCourseTune(ytoCourse)
        return wcaFreq, ytoFreq, ytoCourse
        
    def setYTOCourseTune(self, courseTune:int):
        if courseTune < 0:
            courseTune = 0
        elif courseTune > 4095:
            courseTune = 4095
        return self.command(self.CMD_OFFSET + self.YTO_COARSE_TUNE, self.packU16(courseTune))
    
    def __ytoFreqToCourse(self, ytoFreq:float):
        if not (self.ytoHighGHz > self.ytoLowGHz):
            # avoid divide by zero
            self.__logMessage("YTO limits are not valid.  Call setYTOLimits() first.", True)
            return 0
        if ytoFreq < self.ytoLowGHz:
            ytoFreq = self.ytoLowGHz
        elif ytoFreq > self.ytoHighGHz:
            ytoFreq = self.ytoHighGHz
        return int((ytoFreq - self.ytoLowGHz) / (self.ytoHighGHz - self.ytoLowGHz) * 4095)
    
    def lockPLL(self, freqLOGHz:float, freqFloogGHz:float = 0.0315):
        numPoints = 9
        interval = 5
        self.__logMessage(f"lockPLL ICT_19283_LOCK_CV_Points={numPoints} interval={interval}...")

        wcaFreq, ytoFreq, ytoCourse = self.setLOFrequency(freqLOGHz)
        if wcaFreq == 0:
            self.__logMessage(f"freqLOGHz:{freqLOGHz} is out of range.")
            return 0, 0, 0

        pll = self.getLockInfo()
        # If already locked, zero the CV:
        if pll['isLocked']:
            self.adjustPLL(0.0)
            pll = self.getLockInfo()
            if pll['isLocked']:
                self.__logMessage("PLL is locked")
                return wcaFreq, ytoFreq, ytoCourse
        else:
            # search for points where lock is achieved:
            pll = self.getPLLConfig()
            referenceFreq = wcaFreq + freqFloogGHz * (1 if pll['lockSB'] == 0 else -1)
            self.__logMessage(f"lockPLL:points-1 first guess: ytoCourse={ytoCourse} ytoFreq={ytoFreq} referenceFreq={referenceFreq}")
        
            pllVList = []
            for i in range(numPoints):
                # calculate points to try:
                offset = int(interval * (i - int(numPoints / 2)))
                thisTune = ytoCourse  + offset
            
                # Border control
                if thisTune > 4095:
                    thisTune = 4095
                elif thisTune < 0:
                    thisTune = 0
    
                self.__logMessage(f"lockPLL:points-2 i={i} offset={offset} thisTune={thisTune}")
    
                # Disable the PLL and reset the integrator
                self.setNullLoopIntegrator(True)
    
                # Set coarse tune
                self.setYTOCourseTune(thisTune)
    
                # Wait 10 ms to stabilize
                sleep(0.1)
    
                # Reactivate the PLL
                self.setNullLoopIntegrator(False)
    
                # Wait 10 ms to stabilize
                sleep(0.1)
    
                # Gather data
                pll = self.getPLL()
                yto = self.getYTO()
                self.__logMessage(f"lockPLL:points-3: isLocked={pll['isLocked']} corrV={pll['corrV']} courseTune={pll['courseTune']}")
    
                # Keep it if worth it
                if pll['isLocked']:
                    pll['courseTune'] = yto['courseTune']
                    pllVList.append(pll);

            # Fire: MAIN LOCK HERE
            # at this point the lists contain only those points where the locking voltage was high = the PLL is able to lock
            # we searched at -12,-6,0,6,12 etc. offset from the first guess
            # there must be at least two points, because the locking range is ~ 20 counts wide in B1
            
            # check for found only one point:
            if len(pllVList) == 1:
                pll = pllVList[0]
                # Lock at tune_zero
                self.setYTOCourseTune(pll['courseTune'])
                # Wait 10 ms to stabilize
                sleep(0.1);
                # Zero the CV from here:
                self.adjustPLL(0.0)
                # check if still locked:
                pll = self.getPLL()
                self.__logMessage(f"lockPLL:points: found only one good tuning: isLocked={pll['isLocked']} corrV={pll['corrV']} courseTune={pll['courseTune']}")
            
            # check for found no points:
            elif len(pllVList) == 0:
                self.__logMessage("lockPLL:points: FAILED TO FIND AT ANY POINTS")
                
            else:
                # we have found two or more locking points
                # Calculate slope:
                firstPllV = pllVList[0]
                lastPllV = pllVList[-1]
                y1 = lastPllV['corrV']
                y0 = firstPllV['corrV']
                x1 = lastPllV['courseTune']
                x0 = firstPllV['courseTune']
                slope = (y1 - y0) / (x1 - x0)

                # If we have a decreasing slope (good)
                if slope <= -0.001:
                    # Get tune zero following the slope until y=0
                    tuneZero = int(-y0/slope + x0)
                
                # Else, maybe in simulation
                else:
                    # Get the mean point
                    tuneZero = int((x0 + x1) / 2)
                    # Warn
                    self.__logMessage(f"lockPLL:points: seems to be in simulation, set YIG coarse tune to the mean: {tuneZero}")

                self.__logMessage(f"lockPLL:ponts-4: tuneZero={tuneZero} x0={x0} x1={x1} y0={y0} y1={y1} slope={slope}")

                # Lock at tune_zero
                self.setYTOCourseTune(tuneZero)
                # Wait 10 ms to stabilize
                sleep(0.1);

                # Clear unlock detect:
                self.clearUnlockDetect()

                # check if still locked:
                pll = self.getPLL()
                self.__logMessage(f"lockPLL:points: lock succeeded with: isLocked={pll['isLocked']} corrV={pll['corrV']} courseTune={pll['courseTune']}")

        pll = self.getLockInfo()            
        if pll['isLocked']:
            self.__logMessage("PLL is locked")
            return wcaFreq, ytoFreq, ytoCourse
        else:
            self.__logMessage("PLL NO LOCK")
            return 0, 0, 0

    def adjustPLL(self, targetCV:Optional[float] = 0):
        pll = self.getLockInfo()
        yto = self.getYTO()
        if not pll['isLocked']:
            self.__logMessage("adjustPLL ERROR: cant start search because PLL is not locked.")
            return None

        maxDistance = 50    # steps away we are willing to search
        window = 0.25       # acceptable volts error from targetCV
        retries = 50        # max iterations
        self.__logMessage(f"adjustPLL: targetCV={targetCV} +/- {window} V ")
        
        errorCV = pll['corrV'] - targetCV
        tryCourseTune = yto['courseTune']
        self.__logMessage(f"adjustPLL CV={pll['corrV']} vError={errorCV} coarseYIG={tryCourseTune}")

        hiThreshold = targetCV + window
        loThreshold = targetCV - window
        controlHistory = []    

        if 0 <= tryCourseTune <= 4095:
            self.setYTOCourseTune(tryCourseTune)
            controlHistory.append(tryCourseTune)
        else:
            self.__logMessage(f"adjustPLL ERROR: got tryCourseTune={tryCourseTune}", True)
            return None

        done = False
        error = False
        
        while not done and not error:
            pll = self.getLockInfo()
            yto = self.getYTO()
            if loThreshold <= pll['corrV'] <= hiThreshold:
                done = True
            # check for oscillations:
            elif len(controlHistory) == 5 and controlHistory[0] == controlHistory[2] and controlHistory[2] == controlHistory[4]:
                done = True
                self.__logMessage("adjustPLL: detected oscillation.")
            else:
                retries -= 1
                if retries <= 0:
                    done = True
                    self.__logMessage("adjustPLL: too many retries.")
                    
                else:
                    errorCV = pll['corrV'] - targetCV
                    tryCourseTune += (1 if errorCV > 0 else -1)
                    distance = abs(tryCourseTune - yto['courseTune'])
                    if distance > maxDistance:
                        error = True
                    elif 0 <= tryCourseTune <= 4095:
                        self.setYTOCourseTune(tryCourseTune)
                    # Save the history of control values, limited to 5 elements:
                    controlHistory.append(tryCourseTune)
                    if len(controlHistory) > 5:
                        controlHistory = controlHistory[-5:]
    
        pll = self.getLockInfo()
        if not pll['isLocked']:
            self.__logMessage(f"adjustPLL ERROR: band {self.band} lost the lock while adjusting the PLL.", True)
            error = True
        else:
            self.clearUnlockDetect()
        
        if done and not error:
            return pll['corrV']
        else:
            return None
    
    def setPhotmixerEnable(self, enable:bool):
        return self.command(self.CMD_OFFSET + self.PHOTOMIXER_ENABLE, self.packBool(enable))
    
    def clearUnlockDetect(self):
        return self.command(self.CMD_OFFSET + self.PLL_CLEAR_UNLOCK_DETECT_LATCH, self.packBool(True))
    
    def selectLoopBW(self, select:int = LOOPBW_DEFAULT):
        if select == self.LOOPBW_NORMAL:
            select = 0
        elif select == self.LOOPBW_ALT:
            select = 1
        else:
            if select != self.LOOPBW_DEFAULT:
                self.__logMessage(f"Unsupported value for selectLoopBw.  Using default for band {self.band}.", True)
            select = self.DEFAULT_LOOPBW[self.band]
        return self.command(self.CMD_OFFSET + self.PLL_LOOP_BANDWIDTH_SELECT, self.packU8(select))

    def selectLockSideband(self, select:int = LOCK_BELOW_REF):
        if select == self.LOCK_BELOW_REF:
            select = 0
        elif select == self.LOCK_ABOVE_REF:
            select = 1
        else:
            self.__logMessage("Unsupported value for selectLockSideband. No change.", True)
            return False
        return self.command(self.CMD_OFFSET + self.PLL_LOCK_SIDEBAND_SELECT, self.packU8(select))
    
    def setNullLoopIntegrator(self, enable:bool):
        return self.command(self.CMD_OFFSET + self.PLL_NULL_LOOP_INTEGRATOR, self.packBool(enable))

    def setPABias(self, pol:int, drainControl:float = None, gateVoltage:float = None):
        if pol < 0 or pol > 1:
            self.__logMessage("Unsupported pol for setPABias. No change.", True)
            return False
        ret = True
        if drainControl is not None:
            if drainControl < 0:
                drainControl = 0         
            elif drainControl > 2.5:
                drainControl = 2.5  # highest possible value based on equation in FEND-40.04.03.03-007-A08-DSN
            ret = self.command(self.CMD_OFFSET + self.PA_DRAIN_VOLTAGE + self.POL1_OFFSET if pol==1 else 0, self.packFloat(drainControl))
        if gateVoltage is not None:
            if gateVoltage < -0.84:
                gateVoltage = -0.84 # lowest possible value based on equation in FEND-40.04.03.03-007-A08-DSN
            elif gateVoltage > 0.15:
                gateVoltage = 0.15  # highest possible value
            if not self.command(self.CMD_OFFSET + self.PA_GATE_VOLTAGE + self.POL1_OFFSET if pol==1 else 0, self.packFloat(gateVoltage)):
                ret = False
        return ret 

    def setTeledynePAConfig(self, hasTeledyne:bool, collectorP0:int = 0, collectorP1:int = 0):
        if self.band != 7:
            self.__logMessage(f"Set Teledyne PA config is not supported for band {self.band}.", True)
            return False
        if collectorP0 < 0:
            collectorP0 = 0
        elif collectorP0 > 255:
            collectorP0 = 255
        if collectorP1 < 0:
            collectorP1 = 0
        elif collectorP1 > 255:
            collectorP1 = 255
        self.command(self.CMD_OFFSET + self.PA_HAS_TELEDYNE_CHIP, self.packBool(hasTeledyne))
        self.command(self.CMD_OFFSET + self.PA_TELEDYNE_COLLECTOR, self.packU8(collectorP0))
        self.command(self.CMD_OFFSET + self.PA_TELEDYNE_COLLECTOR + self.POL1_OFFSET, self.packU8(collectorP1))
        return True

    def getYTO(self):
        '''
        Read the YIG oscillator monitor data and configuration:
        :return { 'courseTune': int, 'lowGHz': float, 'highGHz': float }
        '''
        ret = {}
        ret['courseTune'] = self.unpackU16(self.monitor(self.YTO_COARSE_TUNE))
        ret['lowGHz'] = self.ytoLowGHz 
        ret['highGHz'] = self.ytoHighGHz 
        return ret

    def getPLL(self):
        '''
        Read all PLL monitor data:
        :return { 'courseTune': int, 'temperature': float, 'nullPLL': bool } 
                  plus everything from getLockInfo()
        '''
        ret = {}
        ret['courseTune'] = self.unpackU16(self.monitor(self.YTO_COARSE_TUNE))
        ret['temperature'] = round(self.unpackFloat(self.monitor(self.PLL_ASSEMBLY_TEMP)), 3)
        ret['nullPLL'] = self.unpackBool(self.monitor(self.PLL_NULL_LOOP_INTEGRATOR))
        return self.getLockInfo(ret)
    
    def getLockInfo(self, info = None):
        '''
        Read just the lock state info for the PLL:
        :return { 'lockDetect': bool,     -> True if the raw lock detect voltage >= 3.0
                  'unlockDetected': bool, -> latching unlock detect bit
                  'refTP': float,         -> reference total power detector voltage
                  'IFTP': float,          -> IF total power detector voltage
                  'corrV': float,         -> PLL correction voltage 
                  'isLocked': bool }      -> True if lockDetect and abs(refTP) >= 0.5 and abs(IFTP) >= 0.5
        '''
        if info is None:
            info = {}
        info['lockDetectBit'] = self.unpackFloat(self.monitor(self.PLL_LOCK_DETECT_VOLTAGE)) >= 3.0
        info['unlockDetected'] = self.unpackBool(self.monitor(self.PLL_UNLOCK_DETECT_LATCH))
        info['refTP'] = round(self.unpackFloat(self.monitor(self.PLL_REF_TOTAL_POWER)), 4)
        info['IFTP'] = round(self.unpackFloat(self.monitor(self.PLL_IF_TOTAL_POWER)), 4)
        info['corrV'] = round(self.unpackFloat(self.monitor(self.PLL_CORRECTION_VOLTAGE)), 4)
        info['isLocked'] = info['lockDetectBit'] and abs(info['refTP']) >= 0.5 and abs(info['IFTP']) >= 0.5
        return info
    
    def getPLLConfig(self):
        '''
        Read the PLL configuration info:
        :return { 'lockSB': int,         -> 0=LSB, 1=USB
                  'LoopBW': int,         -> 0=normal 7.5MHz/V (bands 2,4,8,9), 
                                            1=alternate 15MHz/V (Band 3,5,6,7,10 & NRAO band 2 prototype) 
                  'warmMult' : int,
                  'coldMult' : int }
        '''
        ret = {}
        ret['lockSB'] = self.unpackU8(self.monitor(self.PLL_LOCK_SIDEBAND_SELECT))
        ret['loopBW'] = self.unpackU8(self.monitor(self.PLL_LOOP_BANDWIDTH_SELECT))
        ret['warmMult'] = self.WARM_MULTIPLIERS[self.band]
        ret['coldMult'] = self.COLD_MULTIPLIERS[self.band]
        return ret
    
    def getPhotomixer(self):
        '''
        Read the photomixer monitor info:
        :return { 'enabled': bool, 'voltage': float, 'current': float mA }
        '''
        ret = {}
        ret['enabled'] = self.unpackBool(self.monitor(self.PHOTOMIXER_ENABLE))
        ret['voltage'] = round(self.unpackFloat(self.monitor(self.PHOTOMIXER_VOLTAGE)), 4)
        ret['current'] = round(self.unpackFloat(self.monitor(self.PHOTOMIXER_CURRENT)), 4)
        return ret
    
    def getAMC(self):
        '''
        Read the active multiplier chain monitor info:
        :return { 'VGA', 'VDA', 'IDA', 'VGB', 'VDB', 'IDB', 'VGE', 'VDE', 'IDE': all float V or mA,
                  'multDCounts': int, 'multDCurrent': float mA, 'supply5V': float } 
        '''
        ret = {}
        ret['VGA'] = round(self.unpackFloat(self.monitor(self.AMC_GATE_A_VOLTAGE)), 4)
        ret['VDA'] = round(self.unpackFloat(self.monitor(self.AMC_DRAIN_A_VOLTAGE)), 4)
        ret['IDA'] = round(self.unpackFloat(self.monitor(self.AMC_DRAIN_A_CURRENT)), 4)
        ret['VGB'] = round(self.unpackFloat(self.monitor(self.AMC_GATE_B_VOLTAGE)), 4)
        ret['VDB'] = round(self.unpackFloat(self.monitor(self.AMC_DRAIN_B_VOLTAGE)), 4)
        ret['IDB'] = round(self.unpackFloat(self.monitor(self.AMC_DRAIN_B_CURRENT)), 4)
        ret['multDCounts'] = self.unpackU8(self.monitor(self.AMC_MULTIPLIER_D_COUNTS))
        ret['multDCurrent'] = round(self.unpackFloat(self.monitor(self.AMC_MULTIPLIER_D_CURRENT)), 4)
        ret['VGE'] = round(self.unpackFloat(self.monitor(self.AMC_GATE_E_VOLTAGE)), 4)
        ret['VDE'] = round(self.unpackFloat(self.monitor(self.AMC_DRAIN_E_VOLTAGE)), 4)
        ret['IDE'] = round(self.unpackFloat(self.monitor(self.AMC_DRAIN_E_CURRENT)), 4)
        ret['supply5V'] = round(self.unpackFloat(self.monitor(self.AMC_SUPPLY_VOLTAGE_5V)), 4)
        return ret

    def getPA(self):
        '''
        Read the power amplifier monitor info:
        :return { 'VGp0': float,       -> gate voltage pol 0 (mapped, not the ambiguous pol A/B)
                  'VGp1': float,       -> gate voltage pol 1
                  'VDp0': float,       -> drain voltage pol 0
                  'VDp1': float,       -> drain voltage pol 1
                  'IDp0': float,       -> drain current mA pol 0
                  'IDp1': float,       -> drain current mA pol 1
                  'supply3V': float, 'supply5V': float }
        '''
        ret = {}
        ret['VGp0'] = round(self.unpackFloat(self.monitor(self.PA_GATE_VOLTAGE)), 4)
        ret['VGp1'] = round(self.unpackFloat(self.monitor(self.PA_GATE_VOLTAGE + self.POL1_OFFSET)), 4)
        ret['VDp0'] = round(self.unpackFloat(self.monitor(self.PA_DRAIN_VOLTAGE)), 4)
        ret['VDp1'] = round(self.unpackFloat(self.monitor(self.PA_DRAIN_VOLTAGE + self.POL1_OFFSET)), 4)
        ret['IDp0'] = round(self.unpackFloat(self.monitor(self.PA_DRAIN_CURRENT)), 4)
        ret['IDp1'] = round(self.unpackFloat(self.monitor(self.PA_DRAIN_CURRENT + self.POL1_OFFSET)), 4)
        ret['supply3V'] = round(self.unpackFloat(self.monitor(self.PA_SUPPLY_VOLTAGE_3V)), 4)
        ret['supply5V'] = round(self.unpackFloat(self.monitor(self.PA_SUPPLY_VOLTAGE_5V)), 4)
        return ret
    
    def getTeledynePA(self):
        '''
        Read the configuration related to band 7 Teledyne power amplifier chips:
        :return { 'hasTeledyne': bool,       -> True if Teledyne PA chips are configured
                  'collectorP0': int,        -> 0-255 digial pot setting for the pol 0 PA collector if hasTeledyne is True
                  'collectorP1': int }
        '''
        ret = {}
        ret['hasTeledyne'] = self.unpackBool(self.monitor(self.PA_HAS_TELEDYNE_CHIP))
        ret['collectorP0'] = self.unpackU8(self.monitor(self.PA_TELEDYNE_COLLECTOR)) 
        ret['collectorP1'] = self.unpackU8(self.monitor(self.PA_TELEDYNE_COLLECTOR + self.POL1_OFFSET)) 
        return ret
    
    def __logMessage(self, msg, alwaysLog = False):
        if self.logInfo or alwaysLog:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + f" LODevice band{self.band}: {msg}")
    
    # constants used internally:
    WARM_MULTIPLIERS = {
        1: 1,   # band 1
        2: 4,   # band 2: ESO first article
        3: 6,   # band 3
        4: 3,   # band 4
        5: 6,   # band 5
        6: 6,   # band 6
        7: 6,   # band 7
        8: 3,   # band 8
        9: 3,   # band 9
        10: 6   # band 10 
    }
        
    COLD_MULTIPLIERS = {
        1: 1,   # band 1
        2: 1,   # band 2: ESO first article
        3: 1,   # band 3
        4: 2,   # band 4
        5: 2,   # band 5
        6: 3,   # band 6
        7: 3,   # band 7
        8: 6,   # band 8
        9: 9,   # band 9
        10: 9   # band 10 
    }

    DEFAULT_LOOPBW = {
        1: 0,   # band 1: don't care. fixed 2.5 MHz/V
        2: 0,   # band 2: ESO first article
        3: 1,   # band 3: 1 -> 15MHz/V (Band 3,5,6,7,10 & NRAO band 2 prototype)
        4: 0,   # band 4: 0 -> 7.5MHz/V (Band 2,4,8,9)
        5: 1,   # band 5
        6: 1,   # band 6
        7: 1,   # band 7
        8: 0,   # band 8
        9: 0,   # band 9
        10: 1   # band 10 
    }
        
    # RCAs used internally:
    CMD_OFFSET                      = 0x10000
    POL1_OFFSET                     = 0x0004
    YTO_COARSE_TUNE                 = 0x0800
    PHOTOMIXER_ENABLE               = 0x0810
    PHOTOMIXER_VOLTAGE              = 0x0814
    PHOTOMIXER_CURRENT              = 0x0818
    PLL_LOCK_DETECT_VOLTAGE         = 0x0820
    PLL_CORRECTION_VOLTAGE          = 0x0821
    PLL_ASSEMBLY_TEMP               = 0x0822
    PLL_YTO_HEATER_CURRENT          = 0x0823
    PLL_REF_TOTAL_POWER             = 0x0824
    PLL_IF_TOTAL_POWER              = 0x0825
    PLL_UNLOCK_DETECT_LATCH         = 0x0827
    PLL_CLEAR_UNLOCK_DETECT_LATCH   = 0x0828
    PLL_LOOP_BANDWIDTH_SELECT       = 0x0829
    PLL_LOCK_SIDEBAND_SELECT        = 0x082A
    PLL_NULL_LOOP_INTEGRATOR        = 0x082B            
    AMC_GATE_A_VOLTAGE              = 0x0830
    AMC_DRAIN_A_VOLTAGE             = 0x0831
    AMC_DRAIN_A_CURRENT             = 0x0832
    AMC_GATE_B_VOLTAGE              = 0x0833
    AMC_DRAIN_B_VOLTAGE             = 0x0834
    AMC_DRAIN_B_CURRENT             = 0x0835
    AMC_MULTIPLIER_D_COUNTS         = 0x0836
    AMC_GATE_E_VOLTAGE              = 0x0837
    AMC_DRAIN_E_VOLTAGE             = 0x0838
    AMC_DRAIN_E_CURRENT             = 0x0839
    AMC_MULTIPLIER_D_CURRENT        = 0x083A
    AMC_SUPPLY_VOLTAGE_5V           = 0x083B
    PA_GATE_VOLTAGE                 = 0x0840
    PA_DRAIN_VOLTAGE                = 0x0841
    PA_DRAIN_CURRENT                = 0x0842
    PA_SUPPLY_VOLTAGE_3V            = 0x0848
    PA_SUPPLY_VOLTAGE_5V            = 0x084C
    PA_HAS_TELEDYNE_CHIP            = 0x0850
    PA_TELEDYNE_COLLECTOR           = 0x0851
