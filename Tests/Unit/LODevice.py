import unittest
from AMB.AMBConnectionNican import AMBConnectionNican
from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.FEMCDevice import FEMCDevice
from AMB.LODevice import LODevice
from time import sleep

class test_LODevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.conn = AMBConnectionNican(channel = 0, resetOnError = True)
        cls.conn = AMBConnectionDLL(channel = 0)
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
        
    def setUp(self):
        self.dev = LODevice(self.conn, 0x13, FEMCDevice.PORT_BAND7)
        self.dev.initSession(FEMCDevice.MODE_SIMULATE)
        self.dev.setBandPower(FEMCDevice.PORT_BAND7, True)
        sleep(0.2)
        
    def tearDown(self):
        self.dev.setBandPower(FEMCDevice.PORT_BAND7, False)
        self.dev.shutdown()
    
    def test_setLOFrequency(self):
        self.dev.setYTOLimits(14.0, 17.5)
        (outputFreq, ytoFreq, ytoCourse) = self.dev.setLOFrequency(300, 3)
        self.assertTrue(outputFreq == 100)
        self.assertTrue(14.0 <= ytoFreq <= 17.5)
        self.assertTrue(0 <= ytoCourse <= 4095)
        
    def test_setYTOCourseTune(self):
        self.dev.setYTOLimits(14.0, 17.5)
        self.assertTrue(self.dev.setYTOCourseTune(0))
        self.assertTrue(self.dev.setYTOCourseTune(2020))
        self.assertTrue(self.dev.setYTOCourseTune(4095))
        # illegal values should be coereced to in-range:
        self.assertTrue(self.dev.setYTOCourseTune(-10))
        yto = self.dev.getYTO()
        self.assertTrue(yto['courseTune'] == 0)
        self.assertTrue(self.dev.setYTOCourseTune(5000))
        yto = self.dev.getYTO()
        self.assertTrue(yto['courseTune'] == 4095)
        
    def test_lockPLL(self):
        self.dev.setYTOLimits(14.0, 17.5)
        self.dev.lockPLL(300, 3)
        #  what can we assert when simulating?

    def test_adjustPLL(self):
        # how to test?
        pass
        
    def test_setPhotomixerEnable(self):
        self.dev.setPhotmixerEnable(False)
        pll = self.dev.getPhotomixer()
        self.assertFalse(pll['enabled'], "Photomixer disabled.")
        self.dev.setPhotmixerEnable(True)
        pll = self.dev.getPhotomixer()
        self.assertTrue(pll['enabled'], "Photomixer enabled.")
        self.dev.setPhotmixerEnable(False)
        pll = self.dev.getPhotomixer()
        self.assertFalse(pll['enabled'], "Photomixer not enabled.")
    
    def test_clearUnlockDetect(self):
        # how to test?
        pass
    
    def test_selectLoopBW(self):
        self.dev.selectLoopBW(LODevice.LOOPBW_NORMAL)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOOPBW_NORMAL, "Normal loop BW")
        self.dev.selectLoopBW(LODevice.LOOPBW_ALT)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOOPBW_ALT, "Alternate Loop BW")
        self.dev.selectLoopBW(LODevice.LOOPBW_NORMAL)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOOPBW_NORMAL, "Normal loop BW")
        self.dev.selectLoopBW(LODevice.LOOPBW_DEFAULT)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOOPBW_NORMAL or pll['loopBW'] == LODevice.LOOPBW_ALT, "Default loop BW")
    
    def test_selectLockSideband(self):
        self.dev.selectLockSideband(LODevice.LOCK_BELOW_REF)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOCK_BELOW_REF, "Lock below ref")
        self.dev.selectLockSideband(LODevice.LOCK_ABOVE_REF)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOCK_ABOVE_REF, "Lock above ref")
        self.dev.selectLockSideband(LODevice.LOCK_BELOW_REF)
        pll = self.dev.getPLLConfig()
        self.assertTrue(pll['loopBW'] == LODevice.LOCK_BELOW_REF, "Lock below ref")
    
    def test_setNullLoopIntegrator(self):
        self.dev.setNullLoopIntegrator(False)
        pll = self.dev.getPLL()
        self.assertFalse(pll['nullPLL'], "Null integrator off")
        self.dev.setNullLoopIntegrator(True)
        pll = self.dev.getPLL()
        self.assertTrue(pll['nullPLL'], "Null integrator on")
        self.dev.setNullLoopIntegrator(False)
        pll = self.dev.getPLL()
        self.assertFalse(pll['nullPLL'], "Null integrator off")
    
    def test_setPABias(self):
        self.dev.setPABias(pol=0, drainControl=0, gateVoltage=0)
        self.dev.setPABias(pol=1, drainControl=0, gateVoltage=0)
        pa = self.dev.getPA()
        self.assertAlmostEqual(pa['VDp0'], 0, delta=0.1)
        self.assertAlmostEqual(pa['VDp1'], 0, delta=0.1)
        self.assertAlmostEqual(pa['VGp0'], 0, delta=0.1)
        self.assertAlmostEqual(pa['VGp1'], 0, delta=0.1)
        self.dev.setPABias(pol=0, gateVoltage=-0.2)
        self.dev.setPABias(pol=1, gateVoltage=-0.2)
        pa = self.dev.getPA()
        self.assertAlmostEqual(pa['VGp0'], -0.2, delta=0.1)
        self.assertAlmostEqual(pa['VGp1'], -0.2, delta=0.1)
        self.dev.setPABias(pol=0, drainControl=1)
        self.dev.setPABias(pol=1, drainControl=1)
        pa = self.dev.getPA()
        self.assertGreater(pa['VDp0'], 0.3)
        self.assertGreater(pa['VDp1'], 0.3)
        self.dev.setPABias(pol=0, drainControl=0, gateVoltage=0)
        self.dev.setPABias(pol=1, drainControl=0, gateVoltage=0)
        
    def test_setTeledynePAConfig(self):
        self.dev.setTeledynePAConfig(hasTeledyne = False, collectorP0 = 0, collectorP1 = 0)
        tdpa = self.dev.getTeledynePA()
        self.assertFalse(tdpa['hasTeledyne'])
        self.assertEqual(tdpa['collectorP0'], 0)
        self.assertEqual(tdpa['collectorP1'], 0)
        self.dev.setTeledynePAConfig(hasTeledyne = True, collectorP0 = 250, collectorP1 = 250)
        tdpa = self.dev.getTeledynePA()
        self.assertTrue(tdpa['hasTeledyne'])
        self.assertEqual(tdpa['collectorP0'], 250)
        self.assertEqual(tdpa['collectorP1'], 250)
        self.dev.setTeledynePAConfig(hasTeledyne = False)
        self.assertFalse(tdpa['hasTeledyne'])
        
    def test_getYTO(self):
        self.dev.setYTOLimits(12.0, 15.5)
        self.dev.setYTOCourseTune(987)
        yto = self.dev.getYTO()
        self.__checkAll(yto)
        self.assertTrue(yto['courseTune'] == 987)
        self.assertTrue(yto['lowGhz'] == 12.0)
        self.assertTrue(yto['highGhz'] == 15.5)
        self.assertTrue(yto['stepSize'] == 3.5 / 4095)
        print("YTO state: ", yto)
        
    def test_getPLL(self):
        self.dev.setYTOLimits(13.5, 16.5)
        self.dev.setYTOCourseTune(1234)
        pll = self.dev.getPLL()
        self.__checkAll(pll)
        self.assertTrue(pll['courseTune'] == 1234)
        print("PLL state: ", pll)

    def test_getPhotomixer(self):
        pmx = self.dev.getPhotomixer()
        self.__checkAll(pmx)
        print("Photomixer state: ", pmx)
        
    def test_getAMC(self):
        amc = self.dev.getAMC()
        self.__checkAll(amc)
        print("AMC state: ", amc)
        
    def test_getPA(self):
        pa = self.dev.getPA()
        self.__checkAll(pa)
        print("PA state: ", pa)

    def __checkAll(self, state):
        self.assertIsNotNone(state, "State dict is None")
        for val in state.values():
            with self.subTest(val = val):
                self.assertIsNotNone(val)
