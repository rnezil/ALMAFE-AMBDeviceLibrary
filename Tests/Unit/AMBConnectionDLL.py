import unittest
from AMB.AMBConnectionDLL import AMBConnectionDLL
import configparser
import logging

class test_AMBConnectionDLL(unittest.TestCase):
    GET_FEMC_VERSION        = 0x20002
    GET_FE_MODE             = 0x2000E
    SET_FE_MODE             = 0x2100E
    GET_AMBSI_PROTOCOL_REV  = 0x30000
    FEMC_NODE_ADDR          = 0x13
    conn = None
    
    @classmethod
    def setUp(self):
        config = configparser.ConfigParser()
        config.read('FrontEndAMBDLL.ini')
        dllName = config['load']['dll']
        self.conn = AMBConnectionDLL(channel = 0, dllName = dllName)
        self.logger = logging.getLogger("ALMAFE-AMBDeviceLibrary")
        
    @classmethod
    def tearDown(self):
        self.conn.shutdown()
        
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

        # not testing FE_MODE=2 because that starts the FTP server in FEMC >= 3.5
                
        # check for firmware version which supports FE_MODE=3:
        version = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FEMC_VERSION)
        self.assertTrue(len(version) == 3)
        if version[0] >= 3 and version[1] >= 6 and version[2] >= 3:
            # test FE_MODE=3:
            self.conn.command(self.FEMC_NODE_ADDR, self.SET_FE_MODE, b'\x03')
            mode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
            self.assertTrue(mode == b'\x03', "SET_FE_MODE failed")

        #restore previous mode:
        self.conn.command(self.FEMC_NODE_ADDR, self.SET_FE_MODE, prevMode)
        mode = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_FE_MODE)
        self.assertTrue(mode == prevMode, "SET_FE_MODE failed")
        
    def test_monitor(self):
        data = self.conn.monitor(self.FEMC_NODE_ADDR, self.GET_AMBSI_PROTOCOL_REV)
        self.assertIsInstance(data, bytes, "Not bytes")
        self.assertTrue(len(data) > 0, "No data")
    
        
    