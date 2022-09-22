import unittest
from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.CCADevice import CCADevice
from time import time, sleep
import plotly.graph_objects as go

class test_IVCurve(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.conn = AMBConnectionNican(channel = 0, resetOnError = True)
        cls.conn = AMBConnectionDLL(channel = 0)
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
        
    def setUp(self):
        self.dev = CCADevice(self.conn, 0x13, CCADevice.PORT_BAND7)
        self.dev.initSession(CCADevice.MODE_SIMULATE)
        self.dev.setBandPower(CCADevice.PORT_BAND7, True)
        sleep(0.2)
        
    def tearDown(self):
        self.dev.setBandPower(CCADevice.PORT_BAND7, False)
        self.dev.shutdown()
        
    def test_setIVCurve(self):
        start = time()
        VjSet, VjRead, IjRead = self.dev.IVCurve(0, 1)
        end = time()
        print(end - start)
        
        fig = go.Figure()
        lines = dict(color='blue', width=1)
        fig.add_trace(go.Scatter(x = VjSet[:-1], y = IjRead[:-1], mode = 'lines', line = lines, name="Ij"))
        # lines['color'] = 'red'
        # fig.add_trace(go.Scatter(x = VjSet, y = VjRead, mode = 'lines', line = lines, name="Vj"))
        fig.show()
        
