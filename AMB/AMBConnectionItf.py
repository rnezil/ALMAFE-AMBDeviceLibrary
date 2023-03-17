'''
AMBConnectionItf represents a connection to a CAN bus.
This interface class declares what the various concrete AmbConnnection* classes must do.
It can be a local direct CAN connection or a bus provided by a SocketServer.
Typically you will create only one AMBConection and share it among one or more AMBDevices.
Implements bare CAN bus monitor, control, and node search.
'''

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class BusNode(BaseModel):
    """A CAN bus node on a given AMBConnection, identified by it's node address.    
    """
    address:int             # node address in 0..0xFF
    serialNum:bytes         # node serial number 8 bytes

class AMBMessage(BaseModel):
    """A CAN message
    """
    RCA: int
    data: bytes
    timestamp: int = 0

class AMBConnectionError(Exception):
    """Our own exception type for connection and communication errors."""
    def __init__(self, *args):
        super(AMBConnectionError, self).__init__(*args)

class AMBConnectionItf(ABC):
    """Abstract interface for AMBConnection*
    Derived classes will implement these methods in terms of CAN, DLL, socket, etc.
    """
    @abstractmethod
    def setTimeout(self, timeoutMs):
        '''
        Override the default monitor timeout
        :param timeoutMs: milliseconds
        '''
        pass
    
    @abstractmethod
    def shutdown(self):
        '''
        Close the connection
        '''
        pass
    
    @abstractmethod
    def findNodes(self) -> List[BusNode]:
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of BusNode
        '''
        pass
        
    @abstractmethod
    def command(self, nodeAddr:int, RCA:int, data:bytes) -> bool:
        '''
        Send a command. No response is expected.
        :param nodeAddr destination node for the command
        :param RCA: relative CAN address
        :param data: 1-8 byte command payload
        :return bool success
        '''
        pass

    @abstractmethod
    def monitor(self, nodeAddr:int, RCA:int) -> Optional[bytes]:
        '''
        Send a monitor request and wait for the response.
        :param nodeAddr: destination node for the request
        :param RCA: relative CAN address
        :return data:bytes: 1-8 byte response payload or None
        ''' 
        pass
    
    @abstractmethod
    def runSequence(self, nodeAddr:int, sequence:List[AMBMessage]) -> List[AMBMessage]:
        """Process a sequence of monitor and command messages.
        Monitor reesponse data shall be populated in-place in the 'sequence'

        :param int nodeAddr: for which device?
        :param List[AMBMessage] sequence: list of messages to process.
        """
        pass
