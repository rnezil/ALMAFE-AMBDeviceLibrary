'''
AMBConnection represents a connection to a CAN bus.
  It can be a local direct CAN connection or a bus provided by a SocketServer.
  Typically you will create only one AMBConection and share it amongst one or more AMBDevices.
  AMBConnection protects access to the bus so that multiple devices aren't talking at once.
  Implements bare CAN bus monitor, control, and node search.
'''
from typing import Optional
from .AMBConnectionItf import AmbConnectionItf
import can
from can.interfaces.nican import NicanError

class AMBConnectionNican(AmbConnectionItf):
    
    ARBITRATION_ID = 0x20000000
    SEND_TIMEOUT = 0.002
    RCV_TIMEOUT = 0.002
    
    def __init__(self, channel:Optional[int] = 0, resetOnError = False):
        '''
        Constructor opens a connection using a local NI-CAN interface
                
        :param channel: typically 0..5 corresponding to CAN0..CAN5 or can be the channel number on the ABM  
        :param resetOnError: if true, and we get an 'already configured' error, try forcing a reset.
        '''
        self.channel = channel
        self.bus = None
        try:
            self.bus = can.ThreadSafeBus(interface = 'nican', channel = 'CAN{}'.format(channel), bitrate = 1000000)
        except (NicanError) as err:
            if err.error_code == 0xBFF62007 and resetOnError:
                self.bus.reset()
                self.bus = can.ThreadSafeBus(interface = 'nican', channel = 'CAN{}'.format(channel), bitrate = 1000000)
        
    def shutdown(self):
        '''
        Close connection
        '''
        if self.bus:
            self.bus.shutdown()
        self.channel = None
        self.bus = None
        
    def findNodes(self):
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of int node ids found
        '''
        msg = can.Message(arbitration_id=self.ARBITRATION_ID, is_extended_id=True, data=[])
        self.bus.send(msg, timeout=self.SEND_TIMEOUT)
        nodes = []
        while True:
            msg = self.bus.recv(timeout=self.RCV_TIMEOUT)
            if msg is not None:
                nodeAddr = (msg.arbitration_id - self.ARBITRATION_ID) / 0x40000 - 1
                print(f"{nodeAddr:X}: {msg.data}")
                nodes.apppend((nodeAddr, msg.data))
            else:
                break
        return nodes

    def command(self, nodeAddr:int, rca:int, data:bytearray):
        '''
        Send a command. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: bytearray of 1-8 bytes command payload
        :return bool success
        '''
        msg = can.Message(arbitration_id=self.rcaToArbId(nodeAddr, rca), is_extended_id=True, data=data)
        self.bus.send(msg, timeout=self.SEND_TIMEOUT)
        return True
        
    def monitor(self, nodeAddr:int, rca:int, timeout:Optional[float] = None):
        '''
        Send a monitor request and wait for the response
        :param nodeAddr: destination node for the request
        :param rca: relative CAN address
        :param timeout: if provided, override the default RCV_TIMEOUT
        :return bytearray of 1-8 bytes response payload or None if error
        ''' 
        # clear the read buffer of any stale replies
        while True:
            msg = self.bus.recv(timeout=self.RCV_TIMEOUT)
            if msg is None:
                break
        msg = can.Message(arbitration_id=self.rcaToArbId(nodeAddr, rca), is_extended_id=True, data=b'')
        self.bus.send(msg, timeout=self.SEND_TIMEOUT)
        msg = self.bus.recv(timeout=self.RCV_TIMEOUT)
        if msg is not None:
            return msg.data
        else:
            return None
        
    def rcaToArbId(self, nodeAddr, rca):
        return 0x40000 * (nodeAddr + 1) + self.ARBITRATION_ID + rca
    
    def arbIdToNodeRCA(self, arbId):
        nodeAddr = (arbId - self.ARBITRATION_ID) / 0x40000 - 1
        rca = arbId - self.ARBITRATION_ID - (0x4000 * (nodeAddr + 1))
        return nodeAddr, rca
