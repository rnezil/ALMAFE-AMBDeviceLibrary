import unittest
from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.CCADevice import CCADevice
from time import time, sleep
import plotly.graph_objects as go
import configparser
import logging

class test_IVCurve(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config = configparser.ConfigParser()
        config.read('FrontEndAMBDLL.ini')
        dllName = config['load']['dll']
        cls.conn = AMBConnectionDLL(channel = 0, dllName = dllName)

    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
        
    def setUp(self):
        self.logger = logging.getLogger("ALMAFE-AMBDeviceLibrary")        
        self.dev = CCADevice(self.conn, 0x13, CCADevice.PORT_BAND6)
        self.dev.initSession()
        self.dev.setBandPower(CCADevice.PORT_BAND6, True)
        sleep(0.2)
        
    def tearDown(self):
        self.dev.setBandPower(CCADevice.PORT_BAND6, False)
        self.dev.shutdown()
        
    def test_setIVCurve(self):
        start = time()
        VjSet, VjRead, IjRead = self.dev.IVCurve(0, 1)
        end = time()
        self.logger.info(f"I-V Curve took {end - start} seconds")
        
        fig = go.Figure()
        lines = dict(color='blue', width=1)
        fig.add_trace(go.Scatter(x = VjSet, y = IjRead, mode = 'lines', line = lines, name="Ij"))
        fig.show()
        
