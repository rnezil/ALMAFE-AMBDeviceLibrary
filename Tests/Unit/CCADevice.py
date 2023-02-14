import unittest
from AMB.AMBConnectionNican import AMBConnectionNican
from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.FEMCDevice import FEMCDevice
from AMB.CCADevice import CCADevice
from time import sleep

class test_CCADevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.conn = AMBConnectionNican(channel = 0, resetOnError = True)
        cls.conn = AMBConnectionDLL(channel = 0, dllName = 'L:\ALMA-FEControl\FrontEndAMBDLL\deploy\FrontEndAMB.dll')
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
        
    def setUp(self):
        self.dev = CCADevice(self.conn, 0x13, FEMCDevice.PORT_BAND7)
        self.dev.initSession(FEMCDevice.MODE_SIMULATE)
        self.dev.setBandPower(FEMCDevice.PORT_BAND7, True)
        sleep(0.2)
        
    def tearDown(self):
        self.dev.setBandPower(FEMCDevice.PORT_BAND7, False)
        self.dev.shutdown()
        
    def test_setSIS(self):
        for pol in range(2):
            for sis in range(2): 
                with self.subTest(pol = pol, sis = sis + 1):
                    self.assertTrue(self.dev.setSIS(pol, sis + 1, Vj = 10, Imag = 25))
                    self.assertTrue(self.dev.setSIS(pol, sis + 1, Vj = 11))
                    self.assertTrue(self.dev.setSIS(pol, sis + 1, Imag = 15))
                    self.assertTrue(self.dev.setSIS(pol, sis + 1, Vj = 0, Imag = 0))

    def test_setSISHeater(self):
        self.dev.setSISHeater(0, False)
        sleep(0.01)
        currentOff = self.dev.getSISHeaterCurrent(0)
        self.dev.setSISHeater(0, True)
        sleep(0.01)
        currentOn = self.dev.getSISHeaterCurrent(0)
        print(f"SIS heater current off={currentOff} on={currentOn}")
        self.assertGreater(currentOn, currentOff)
        self.dev.setSISHeater(0, False)
        
    def test_setLNAEnable(self):
        self.dev.setLNAEnable(False)
        for pol in range(2):
            for lna in range(2): 
                with self.subTest(pol = pol, lna = lna + 1):
                    lnaData = self.dev.getLNA(pol, lna + 1)
                    self.assertFalse(lnaData['enable'])
                    self.dev.setLNAEnable(True, pol, lna + 1)
                    lnaData = self.dev.getLNA(pol, lna + 1)
                    self.assertTrue(lnaData['enable'])
        self.dev.setLNAEnable(False)

    def test_setLNA(self):
        for pol in range(2):
            for lna in range(2): 
                with self.subTest(pol = pol, lna = lna + 1):
                    self.dev.setLNAEnable(True, pol, lna + 1)
                    self.assertTrue(self.dev.setLNA(pol, lna + 1, VD1=0.5, VD2=0.4, VD3=0.3, ID1=2, ID2=2, ID3=2))
                    self.assertTrue(self.dev.setLNA(pol, lna + 1, VD1=0.5, VD2=0.4, VD3=0.3, ID1=2, ID2=2, ID3=2))
        self.dev.setLNAEnable(False)
    
    def test_getCartridgeTemps(self):
        temps = self.dev.getCartridgeTemps()
        self.__checkAll(temps)
        for val in temps.values():
            with self.subTest(val = val):
                self.assertTrue(val > 0 or val == -1)
        print("Temperatures: ", temps)
    
    def test_getSIS(self):
        for pol in range(2):
            for sis in range(2):
                with self.subTest(pol = pol, sis = sis + 1):
                    sisData = self.dev.getSIS(pol, sis + 1, averaging = 1)
                    self.__checkAll(sisData)
                    print(f"SIS pol{pol} sis{sis + 1}:", sisData)
                    sisData = self.dev.getSIS(pol, sis + 1, averaging = 8)
                    self.__checkAll(sisData)
                    print(f"SIS pol{pol} sis{sis + 1}:", sisData)
        
    def test_getSISOpenLoop(self):
        self.dev.setSISOpenLoop(False)
        self.assertFalse(self.dev.getSISOpenLoop())
        self.dev.setSISOpenLoop(True)
        self.assertTrue(self.dev.getSISOpenLoop())
        self.dev.setSISOpenLoop(False)
        self.assertFalse(self.dev.getSISOpenLoop())
    
    def test_getLNA(self):
        for pol in range(2):
            for lna in range(2):
                with self.subTest(pol = pol, lna = lna + 1):
                    lnaData = self.dev.getLNA(pol, lna)
                    self.__checkAll(lnaData)
                    print(f"LNA pol{pol} lna{lna + 1}:", lnaData)
    
    def test_getHeaterCurrent(self):
        current = self.dev.getSISHeaterCurrent(0)
        self.assertTrue(current != 0)
    
    def __checkAll(self, state:dict):
        '''
        Assert that all dictionary items do not have a value of None
        :param state:
        '''
        self.assertIsNotNone(state, "State dict is None")
        for val in state.values():
            with self.subTest(val = val):
                self.assertIsNotNone(val)