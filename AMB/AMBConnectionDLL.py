'''
AmbConnection implemented via the C++/Windows FrontEndAMB.dll
'''
from typing import Optional
from .AMBConnectionItf import AMBConnectionItf, BusNode
from .Utility import DLLClose
import ctypes
from datetime import datetime

class AMBConnectionDLL(AMBConnectionItf):
    
    def __init__(self, channel:Optional[int] = 0, dllName = r'L:\ALMA-FEControl\FrontEndControl2\FrontEndAMB.dll', logInfo = True):
        '''
        Constructor opens a connection using the FrontEndAMB.DLL                
        :param channel: typically 0..5 corresponding to CAN0..CAN5 or can be the channel number on the ABM  
        :param dllName: path to the FrontEndAMB.dll.  
                        Can be just 'FrontEndAMB.dll' if it is on the system path or './FrontEndAMB.dll' if it is in the current dir
        :param logInfo: if True, print diagnostic messages to the console
        '''
        self.channel = channel
        self.logInfo = logInfo
        self.dll = ctypes.CDLL(dllName)
        ret = self.dll.initialize()
        if ret != 0:
            self.__logMessage("dll.initialize failed.", True)
            self.shutdown()
                    
    def shutdown(self):
        '''
        Close connection
        '''
        if self.dll:
            self.dll.shutdown()
            DLLClose.dlclose(self.dll._handle)
            self.__logMessage("shutdown.")
        self.channel = None
        self.dll = None
    
    def setTimeout(self, timeoutMs):
        '''
        Override the default monitor timeout
        :param timeoutMs: milliseconds
        '''
        self.dll.setTimeout(ctypes.c_ulong(timeoutMs))
        
    def findNodes(self):
        '''
        Send a broadcast request to get all CAN nodes on the bus
        :return list of AMBConnectionItf.BusNode
        
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
        
    def command(self, nodeAddr:int, RCA:int, data:bytes):
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
        
    def monitor(self, nodeAddr:int, RCA:int):
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
            return None
    
    def __logMessage(self, msg, alwaysLog = False):
        if self.logInfo or alwaysLog:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " AMBConnectionDLL: " + msg)        
