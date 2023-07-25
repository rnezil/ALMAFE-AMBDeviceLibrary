'''
AmbConnection implemented via the C++/Windows FrontEndAMB.dll
'''
from typing import Optional, List
from .AMBConnectionItf import AMBConnectionItf, AMBConnectionError, BusNode, AMBMessage
from .Utility import DLLClose
import ctypes
from copy import copy
from datetime import datetime
import logging

class AMBConnectionDLL(AMBConnectionItf):

    def __init__(self, channel:Optional[int] = 0, dllName = r'FrontEndAMB.dll'):
        '''
        Constructor opens a connection using the FrontEndAMB.DLL                
        :param channel: typically 0..5 corresponding to CAN0..CAN5 or can be the channel number on the ABM  
        :param dllName: path to the FrontEndAMB.dll.  
                        Can be just 'FrontEndAMB.dll' if it is on the system path or './FrontEndAMB.dll' if it is in the current dir
        '''
        self.channel = channel
        self.dll = ctypes.CDLL(dllName)
        self.logger = logging.getLogger("ALMAFE-AMBDeviceLibrary")
        ret = self.dll.initialize()
        if ret != 0:
            self.shutdown()
            raise AMBConnectionError(f"AMBConnectionDLL '{dllName}' initialize failed.")
        self.logger.debug(f"AMBConnectionDLL connected using {dllName} to channel {channel}")
              
    def __del__(self):
        self.shutdown()
          
    def shutdown(self):
        '''
        Close connection
        '''
        self.logger.debug("AMBConnectionDLL shutdown...")
        try:
            if self.dll:
                self.dll.shutdown()
                DLLClose.dlclose(self.dll._handle)
        except:
            pass
        self.channel = None
        self.dll = None
    
    def setTimeout(self, timeoutMs):
        '''
        Override the default monitor timeout
        :param timeoutMs: milliseconds
        '''
        self.dll.setTimeout(ctypes.c_ulong(timeoutMs))
        
    def findNodes(self) -> List[BusNode]:
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of BusNode
        
        int findNodes(unsigned short *numFound, unsigned char *nodeAddrs, unsigned char **serialNums, unsigned short maxLen);
        '''
        numFound = ctypes.c_ushort(0)                           # unsigned short *numFound
        nodeAddrs = ctypes.create_string_buffer(b'\x00' * 40)   # unsigned char *nodeAddrs
        serialNums = (ctypes.c_char_p * 40)()                   # unsigned char **serialNums
        serialNums[:] = [b'\x00' * 8 for _ in range(40)]        #  create the underlying buffers
        
        self.dll.findNodes.resstype = ctypes.c_ushort
        ret = self.dll.findNodes(ctypes.byref(numFound), nodeAddrs, serialNums, ctypes.c_ushort(40))
        if ret == 0:
            ret = []
            for i in range(numFound.value):
                ret.append(BusNode(address = nodeAddrs[i][0], serialNum = serialNums[i]))
            return ret
        else:
            return []
        
    def command(self, nodeAddr:int, RCA:int, data:bytes) -> bool:
        '''
        Send a command. No response is expected.
        :param nodeAddr destination node for the command
        :param RCA: relative CAN address
        :param data: 1-8 byte command payload
        :return bool success
        
        int command(unsigned char nodeAddr, unsigned long RCA, unsigned short dataLength, const unsigned char *data);
        '''
        r1 = ctypes.c_ubyte(nodeAddr)           # unsigned char nodeAddr
        r2 = ctypes.c_ulong(RCA)                # unsigned long RCA
        r3 = ctypes.c_ushort(len(data))         # unsigned short dataLength
        r4 = ctypes.c_char_p(data)              # const unsigned char *data
        
        self.dll.command.resstype = ctypes.c_ushort
        ret = self.dll.command(r1, r2, r3, r4)
        return ret == 0
        
    def monitor(self, nodeAddr:int, RCA:int) -> Optional[bytes]:
        '''
        Send a monitor request and wait for the response.
        :param nodeAddr: destination node for the request
        :param RCA: relative CAN address
        :return data:bytes: 1-8 byte response payload
        
        int monitor(unsigned char nodeAddr, unsigned long RCA, unsigned short *dataLength, unsigned char *data);
        ''' 
        r1 = ctypes.c_ubyte(nodeAddr)           # unsigned char nodeAddr
        r2 = ctypes.c_ulong(RCA)                # unsigned long RCA
        dataLen = ctypes.c_ushort(0)            # unsigned short *dataLength
        data = ctypes.POINTER(ctypes.c_char)((ctypes.c_char * 8)())
        # unsigned char *data
        
        self.dll.monitor.resstype = ctypes.c_ushort
        ret = self.dll.monitor(r1, r2, ctypes.byref(dataLen), data) 
        if ret == 0:
            response = bytes(data[:dataLen.value])
            return response
        else:
            self.logger.error(f"monitor nodeAddr={nodeAddr} RCA={RCA:X} returned {ret}")
            return None
            
    class MessageStruct(ctypes.Structure):
        """data structure for passing messages to and from the DLL
        """
        _fields_ = [
            ("RCA", ctypes.c_ulong),
            ("dataLength", ctypes.c_ushort),
            ("data", ctypes.POINTER(ctypes.c_char * 8)),
            ("timestamp", ctypes.c_ulonglong)
        ]
    
    def runSequence(self, nodeAddr:int, sequence:List[AMBMessage]) -> List[AMBMessage]:
        """Process a sequence of monitor and command messages.
        Monitor reesponse data shall be populated in-place in the 'sequence'

        :param int nodeAddr: for which device?
        :param List[AMBMessage] sequence: list of messages to process.
        :return List[AMBMessage] all the messages from 'sequence', with monitor data responses filled in.
        """
        contents = [
            self.MessageStruct(
                msg.RCA, 
                len(msg.data),
                ctypes.POINTER(ctypes.c_char * 8)((ctypes.c_char * 8)(*msg.data)),
                0) 
        for msg in sequence]

        seq = (self.MessageStruct * len(contents))(*contents)

        self.dll.runSequence.restype = ctypes.c_ushort
        ret = self.dll.runSequence(ctypes.c_ubyte(nodeAddr), ctypes.byref(seq), ctypes.c_ulong(len(seq)))
        if not ret == 0:
            raise AMBConnectionError(f"runSequence returned {ret}")
        else:
            return [AMBMessage(
                        RCA = r.RCA, 
                        data = ctypes.string_at(r.data, r.dataLength), 
                        timestamp = r.timestamp
                    ) for r in seq]

