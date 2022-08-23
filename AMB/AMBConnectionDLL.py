'''
AmbConnection implemented via the C++/Windows FrontEndAMB.dll
'''
from typing import Optional
from .AMBConnectionItf import AmbConnectionItf
import ctypes, _ctypes, time

class AMBConnectionDLL(AmbConnectionItf):
    
    def __init__(self, channel:int = 0):
        '''
        Constructor opens a connection using the FrontEndAMB.DLL                
        :param channel: typically 0..5 corresponding to CAN0..CAN5 or can be the channel number on the ABM  
        '''
        self.channel = channel
        dllName = r'L:\ALMA-FEControl\FrontEndControl2\FrontEndAMB'
        self.dll = ctypes.CDLL(dllName)
        ret = self.dll.initialize()
        if ret != 0:
            print(time.strftime("%Y-%m-%d %H:%M:%S"), "Error connecting to FrontEndAMB.dll.")
            self.shutdown()
        
    def shutdown(self):
        '''
        Close connection
        '''
        if self.dll:
            self.dll.shutdown()
        self.channel = None
        self.dll = None
        
    def findNodes(self):
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of int node ids found
        '''
        return []
        
    def command(self, nodeAddr:int, rca:int, data:bytearray):
        '''
        Send a command. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: bytearray of 1-8 bytes command payload
        :return bool success
        '''
        
    def monitor(self, nodeAddr:int, rca:int, timeout:Optional[float] = None):
        '''
        Send a monitor request and wait for the response
        :param nodeAddr: destination node for the request
        :param rca: relative CAN address
        :param timeout: if provided, override the default RCV_TIMEOUT
        :return bytearray of 1-8 bytes response payload or None if error
        ''' 
        
