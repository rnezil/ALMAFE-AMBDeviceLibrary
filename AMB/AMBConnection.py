'''
AMBConnection represents a connection to a CAN bus.
  It can be a local direct CAN connection or a bus provided by a SocketServer.
  Typically you will create only one AMBConection and share it amongst one or more AMBDevices.
  AMBConnection protects access to the bus so that multiple devices aren't talking at once.
  Implements bare CAN bus monitor, control, and node search.
'''
from typing import Optional
import can
from can.interfaces.nican import NicanError
import socket

class AMBConnection():
    
    ARBITRATION_ID = 0x20000000
    SEND_TIMEOUT = 0.002
    RCV_TIMEOUT = 0.002
    
    def __init__(self, 
                 channel:int = 0, 
                 host:Optional[str] = 'acc2.atf.nrao.edu', 
                 port:Optional[int] = 2000, 
                 abmIndex:Optional[int] = 0,
                 forceLocal = True, 
                 resetOnError = False):
        '''
        Constructor opens a connection either to local CAN or a port on a remote ABM
                
        :param channel: typically 0..5 corresponding to CAN0..CAN5 or can be the channel number on the ABM  
        :param host: host name or IP address of the socket server. 
        :param port: TCP/IP port of the socket server.
        :param abmIndex: which ABM as known to the socket server
        :param forceLocal: if True, ignore socket server settings and only make local CAN connection
        :param resetOnError: if true, and we get an 'already configured' error, try forcing a reset.
        '''
        self.shutdown()
        self.channel = channel
        self.host = host
        self.port = port
        self.abmIndex = abmIndex
        if forceLocal:
            self.__openLocal(channel, resetOnError)
        else:
            self.__openSocket(host, port)
        
    def shutdown(self):
        try:
            self.bus.shutdown()
        except:
            pass
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except:
            pass
        self.bus = None
        self.sock = None
        self.channel = None
        self.host = None
        self.port = None
        self.abmIndex = None
        
    def findNodes(self):
        if self.bus:
            return self.__findNodesLocal()
        elif self.sock:
            return self.__findNodesSocket()
        
    def command(self, nodeAddr, rca, data):
        if self.bus:
            return self.__commandLocal(nodeAddr, rca, data)
        elif self.sock:
            return self.__commandSocket(nodeAddr, rca, data)
        
    def monitor(self, nodeAddr, rca):
        if self.bus:
            return self.__monitorLocal(nodeAddr, rca)
        elif self.sock:
            return self.__monitorSocket(nodeAddr, rca)
        
    def __openLocal(self, channel, resetOnError):
        try:
            self.bus = can.ThreadSafeBus(interface = 'nican', channel = 'CAN{}'.format(channel), bitrate = 1000000)
        except (NicanError) as err:
            if err.error_code == 0xBFF62007 and resetOnError:
                self.bus.reset()
                self.bus = can.ThreadSafeBus(interface = 'nican', channel = 'CAN{}'.format(channel), bitrate = 1000000)
    
    def __openSocket(self, host, port):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
        except:
            raise
    
    def __findNodesLocal(self):
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

    def __commandLocal(self, nodeAddr, rca, data):
        msg = can.Message(arbitration_id=self.rcaToArbId(nodeAddr, rca), is_extended_id=True, data=data)
        self.bus.send(msg, timeout=self.SEND_TIMEOUT)
        
    def __monitorLocal(self, nodeAddr, rca):
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
        
    def __findNodesSocket(self):
        raise NotImplementedError
    
    def __commandSocket(self, nodeAddr, rca, data):
        raise NotImplementedError
    
    def __monitorSocket(self, nodeAddr, rca):
        raise NotImplementedError
