'''
AMBConnection represents a connection to a CAN bus.
  It can be a local direct CAN connection or a bus provided by a SocketServer.
  Typically you will create only one AMBConection and share it amongst one or more AMBDevices.
  Implements bare CAN bus monitor, control, and node search.
'''

from abc import ABC, abstractmethod
from typing import Optional

class AmbConnectionItf(ABC):

    def __init__(self, channel:Optional[int] = 0):
        '''
        Constructor.  Open the connection
        :param channel: CAN channel or ABM port
        '''

    @abstractmethod
    def shutdown(self):
        '''
        Close the connection
        '''
        pass
    
    @abstractmethod
    def findNodes(self):
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of tuples (int nodeAddr, str seralNum)
        '''
        pass
        
    @abstractmethod
    def commandU8(self, nodeAddr:int, rca:int, data:bytes):
        '''
        Send a command with a one byte payload. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: a byte (any extra chars after the first are ignored)
        :return bool success
        '''
        pass

    @abstractmethod
    def commandU16(self, nodeAddr:int, rca:int, data:int):
        '''
        Send a command with a 16 bit unsigned integer payload. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: number must be in 0..65535
        :return bool success
        '''
        pass

    @abstractmethod
    def commandI16(self, nodeAddr:int, rca:int, data:int):
        '''
        Send a command with a 16 bit signed integer payload. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: number must be in -32768..32767
        :return bool success
        '''
        pass

    @abstractmethod
    def commandU32(self, nodeAddr:int, rca:int, data:int):
        '''
        Send a command with a 32 bit unsigned integer payload. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: number must be in 0..0xFFFFFFFF
        :return bool success
        '''
        pass

    @abstractmethod
    def commandFloat(self, nodeAddr:int, rca:int, data:float):
        '''
        Send a command with a float payload. No response is expected
        :param nodeAddr destination node for the command
        :param rca: relative CAN address
        :param data: number must fit in a 4-byte float
        :return bool success
        '''
        pass
        
    @abstractmethod
    def monitorU8(self, nodeAddr:int, RCA:int, timeout:Optional[float] = None):
        '''
        Send a monitor request and wait for the response
        :param nodeAddr: destination node for the request
        :param rca: relative CAN address
        :param timeout: if provided, override the default RCV_TIMEOUT
        :return (data:byte, statusCode:byte)
        ''' 
        pass
    
    int ADDCALL monitorU8(AmbRelativeAddr RCA, unsigned char *value);
int ADDCALL monitorU16(AmbRelativeAddr RCA, unsigned short *value);
int ADDCALL monitorI16(AmbRelativeAddr RCA, signed short *value);
int ADDCALL monitorU32(AmbRelativeAddr RCA, unsigned long *value);
int ADDCALL monitorFloat(AmbRelativeAddr RCA, float *value, int average = 1);
int ADDCALL monitorString(AmbRelativeAddr RCA, char *value);