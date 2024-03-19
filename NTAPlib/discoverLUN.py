import os
import doProcess
import userio

class discoverLUN:

    def __init__(self,device,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.igroup=None
        self.svm={}
        self.device=device
        self.path=None
        self.type=None
        self.volume=None
        self.size=None
        self.blocksize=None
        self.protocol=None
        self.wwid=None
        self.mdalias=None
        self.multipath=False
        self.cache=None
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if 'multipath' in kwargs.keys():
            self.multipath=kwargs['multipath']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")
        
        if 'cache' in kwargs.keys():
            self.cache=kwargs['cache']

        if not os.path.isfile('/usr/bin/sg_raw'):
            self.result=1
            self.reason="Cannot find /usr/bin/sg_raw"
            return

    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.cache and self.device in self.cache.luns.keys():
            if self.debug & 1:
                userio.message('Using cached LUN data for ' + self.device,service=localapi + ":CACHE")
            self.igroup=self.cache.luns[self.device].igroup
            self.svm=self.cache.luns[self.device].svm
            self.path=self.cache.luns[self.device].path
            self.type=self.cache.luns[self.device].type
            self.volume=self.cache.luns[self.device].volume
            self.size=self.cache.luns[self.device].size
            self.blocksize=self.cache.luns[self.device].blocksize
            self.protocol=self.cache.luns[self.device].protocol
            self.wwid=self.cache.luns[self.device].wwid
            self.mdalias=self.cache.luns[self.device].mdalias

            self.result=0
            return(True)

        if not os.path.isfile('/usr/bin/sg_raw'):
            self.result=1
            self.reason="Cannot find /usr/bin/sg_raw"
            if self.debug & 1:
                self.showDebug()
            return(False)
        
        if self.debug & 1:
            userio.message('Running sg_raw against ' + self.device,service=localapi + ":OP")
        
        sgcmd=doProcess.doProcess("/usr/bin/sg_raw -r 4k -b " + self.device + " 12 00 00 00 ff 00",debug=self.debug,encoding=None, binary=True)
    
        if sgcmd.result > 0:
            self.result=1
            self.reason="Cannot execute /usr/bin/sg_raw"
            self.stderr=sgcmd.stderr
            return(False)
        
        self.luntype=sgcmd.stdout[8:14]
    
        try:
            self.luntype=sgcmd.stdout[8:14].decode('utf8')
        except:
            self.reason="Cannot find LUN owner for " + self.device
            self.error=1
            self.stderr=sgcmd.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
    
        if self.luntype is None:
            self.reason="Unknown owner for " + self.device
            self.error=1
            self.stderr=sgcmd.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
    
        if self.luntype=='NETAPP':
            if self.debug & 1:
                userio.message(self.device + " is ONTAP device",service=localapi + ":OP")
            sgcmd=doProcess.doProcess("/usr/bin/sg_raw -r 4k -b " + self.device + " c0 00 02 0a 98 0a FF 10 00 00", debug=self.debug,encoding=None, binary=True)
            if sgcmd.result > 0:
                self.reason="Cannot execute /usr/bin/sg_raw"
                self.error=1
                self.stderr=sgcmd.stderr
                return(False)
    
            outstring=sgcmd.stdout
            startofblock=8
            while startofblock<len(outstring):
                pagecode=hex(outstring[startofblock])
                length=int.from_bytes(outstring[startofblock+2:startofblock+4],"big")
                if pagecode=='0x0':
                    self.svm={'name':outstring[startofblock+4:startofblock+length].decode('utf-8').rstrip('\x00')}
                elif pagecode == '0x10':
                    self.path=outstring[startofblock+4:startofblock+length].decode('utf-8').rstrip('\x00')
                    self.volume=self.path.split('/')[2]
                elif pagecode == '0x11':
                    self.volname=outstring[startofblock+20:startofblock+length].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x16':
                    self.igroup=outstring[startofblock+8:startofblock+length].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x22':
                    self.ontapversion=outstring[startofblock+4:startofblock+22].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x40':
                    self.protocol='ISCSI'
                startofblock=startofblock+(length)
            sgcmd=doProcess.doProcess("/usr/bin/sg_raw -r 4k -b " + self.device + " 9e 10 00 00 00 00 00 00 00 00 00 00 00 FF 00 00",debug=self.debug,encoding=None, binary=True)
            if sgcmd.result > 0:
                self.reason="Cannot execute /usr/bin/sg_raw"
                self.error=1
                self.stderr=sgcmd.stderr
                return(False)
    
            outstring=sgcmd.stdout
            totalblocks=int.from_bytes(outstring[0:8],"big")
            blocksize=int.from_bytes(outstring[9:12],"big")
            lunsize=totalblocks * blocksize
            self.size=int(lunsize)
            self.blocksize=blocksize

            if self.multipath:
                multipathcmd=doProcess.doProcess("/usr/sbin/multipath -ll " + self.device,debug=self.debug)
                if multipathcmd.result > 0:
                    self.reason="Cannot execute /usr/bin/multipath"
                    self.error=1
                    self.stderr=multipathcmd.stderr
                    return(False)
                
                try:
                    wwid,alias = multipathcmd.stdout[0].split()[:2]
                    self.wwid=wwid
                    self.mdalias=alias
                except:
                    self.reason="Error executing /usr/bin/multipath -ll " + self.device
                    self.error=1
                    self.stderr=multipathcmd.stderr
                    return(False)

        else:
            result=1
            self.reason="LUN is not a NetApp LUN"
            return(False)

        self.result=0
        if self.cache:
            if self.debug & 1:
                userio.message("Caching LUN data for device " + self.device,service=localapi + ":CACHE")
            self.cache.luns[self.device]=self
        if self.debug & 1:
            self.showDebug()
        return(True)
    
