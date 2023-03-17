'''
AMBConnection represents a connection to a CAN bus.
  It can be a local direct CAN connection or a bus provided by a SocketServer.
  Typically you will create only one AMBConection and share it amongst one or more AMBDevices.
  AMBConnection protects access to the bus so that multiple devices aren't talking at once.
  Implements bare CAN bus monitor, control, and node search.
'''
from typing import Optional, List
from .AMBConnectionItf import AMBConnectionItf, AMBConnectionError, BusNode, AMBMessage
import can
from datetime import datetime
from can.interfaces.nican import NicanError
from .Utility.logger import getLogger

class AMBConnectionNican(AMBConnectionItf):
    
    ARBITRATION_ID = 0x20000000
    SEND_TIMEOUT = 0.2
    RCV_TIMEOUT = 0.2
    
    def __init__(self, channel:Optional[int] = 0, resetOnError = False):
        '''
        Constructor opens a connection using a local NI-CAN interface
        :param channel: typically 0..5 corresponding to CAN0..CAN5  
        :param resetOnError: if True, and we get an 'already configured' error, try forcing a reset.
        '''
        self.channel = channel
        self.logger = getLogger()
        self.bus = None
        self.receiveTimeout = self.RCV_TIMEOUT
        try:
            self.bus = can.ThreadSafeBus(interface = 'nican', channel = 'CAN{}'.format(channel), bitrate = 1000000)
        except (NicanError) as err:
            self.logger.error(repr(err))
            if err.error_code == 0xBFF62007 and resetOnError:
                self.logger.info("resetting bus and trying again...")
                try:
                    self.bus.reset()
                    self.bus = can.ThreadSafeBus(interface = 'nican', channel = f"CAN{channel}", bitrate = 1000000)
                except:
                    self.bus = None
            else:
                self.bus = None
        if not self.bus:
            self.logger.error("NO CONNECTION.")
        else:
            self.logger.info("Connected.")
        if not self.bus:
            raise AMBConnectionError("AMBConnectionNican initialize failed.")
        
    def shutdown(self):
        '''
        Close connection
        '''
        try:
            if self.bus:
                self.logger.info("shutdown...")
                self.bus.shutdown()
        except:
            pass
        self.channel = None
        self.bus = None

    def setTimeout(self, timeoutMs):
        '''
        Override the default monitor timeout
        :param timeoutMs: milliseconds
        '''
        self.receiveTimeout = timeoutMs / 1000.0
                
    def findNodes(self) -> List[BusNode]:
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of BusNode
        '''
        if not self.bus:
            return []
        msg = can.Message(arbitration_id=self.ARBITRATION_ID, is_extended_id=True, data=[])
        self.bus.send(msg, timeout=self.SEND_TIMEOUT)
        self.logger.debug("findNodes...")
        nodes = []
        while True:
            msg = self.bus.recv(timeout=self.receiveTimeout)
            if msg is not None:
                address = (msg.arbitration_id >> 18) - 1
                nodes.append(BusNode(address = address, serialNum = bytes(msg.data)))
                self.logger.debug(f"{address:X}: {msg.data.hex().upper()}")
            else:
                break
        return nodes

    def command(self, nodeAddr:int, RCA:int, data:bytes) -> bool:
        '''
        Send a command. No response is expected.
        :param nodeAddr destination node for the command
        :param RCA: relative CAN address
        :param data: 1-8 byte command payload
        :return bool success
        '''
        if not self.bus:
            return False
        msg = can.Message(arbitration_id=self.rcaToArbId(nodeAddr, RCA), is_extended_id=True, data=data)
        self.bus.send(msg, timeout=self.SEND_TIMEOUT)
        return True
        
    def monitor(self, nodeAddr:int, RCA:int) -> Optional[bytes]:
        '''
        Send a monitor request and wait for the response.
        :param nodeAddr: destination node for the request
        :param RCA: relative CAN address
        :return data:bytes: 1-8 byte response payload or none
        ''' 
        if not self.bus:
            return None
        # clear the read buffer of any stale replies
        while True:
            msg = self.bus.recv(timeout=self.receiveTimeout)
            if msg is None:
                break
        msg = can.Message(arbitration_id=self.rcaToArbId(nodeAddr, RCA), is_extended_id=True, data=b'')
        self.bus.send(msg, timeout = self.SEND_TIMEOUT)
        msg = self.bus.recv(timeout = self.receiveTimeout)
        if msg is not None:
            return bytes(msg.data)
        else:
            self.logger.error(f"monitor nodeAddr={nodeAddr:X} RCA={RCA:X} returned None")
            return None

    def runSequence(self, nodeAddr:int, sequence:List[AMBMessage]) -> List[AMBMessage]:
        for msg in sequence:
            if msg.data:
                self.command(nodeAddr, msg.RCA, msg.data)
            else:
                msg.data = self.monitor(nodeAddr, msg.RCA)
        return sequence                

    def rcaToArbId(self, nodeAddr, RCA):
        return ((nodeAddr + 1) << 18) + RCA

