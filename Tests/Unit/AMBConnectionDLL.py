import unittest
from AMB.AMBConnectionDLL import AMBConnectionDLL

class test_AMBConnectionDLL(unittest.TestCase):
    GET_FE_MODE             = 0x2000E
    SET_FE_MODE             = 0x2100E
    GET_AMBSI_PROTOCOL_REV  = 0x30000
    FEMC_NODE_ADDR          = 0x13
    conn = None
    
    @classmethod
    def setUpClass(cls):        
        cls.conn = AMBConnectionDLL(channel = 0)
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
        
    def test_setTimeout(self):
        #TODO how to test?
        pass
        
    def test_FindNodes(self):
        nodes = self.conn.findNodes()
        self.assertTrue(len(nodes) > 0)
        femcNode = next((node for node in nodes if node.address == self.FEMC_NODE_ADDR), None)
        self.assertTrue(femcNode, "FEMC node not found.  Expect other test cases to fail.")
        
    def test_command(self):
        # this assumes that the device is an FEMC module.   The AMBSI alone has no commands we can test.
        prevMode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
        self.conn.command(self.FEMC_NODE_ADDR, self.SET_FE_MODE, b'\x00')
        mode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
        self.assertTrue(mode == b'\x00', "SET_FE_MODE failed")
        self.conn.command(self.FEMC_NODE_ADDR, self.SET_FE_MODE, b'\x01')
        mode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
        self.assertTrue(mode == b'\x01', "SET_FE_MODE failed")
        # not testing x02 because that starts the FTP server in FEMC >= 3.5
        self.conn.command(self.FEMC_NODE_ADDR, self.SET_FE_MODE, b'\x03')
        mode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
        self.assertTrue(mode == b'\x03', "SET_FE_MODE failed")
        self.conn.command(self.FEMC_NODE_ADDR, self.SET_FE_MODE, prevMode)
        mode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
        self.assertTrue(mode == prevMode, "SET_FE_MODE failed")
        
    def test_monitor(self):
        data = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_AMBSI_PROTOCOL_REV)
        self.assertIsInstance(data, bytes, "Not bytes")
        self.assertTrue(len(data) > 0, "No data")
    
        
    