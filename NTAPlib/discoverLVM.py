import os
import doProcess
import userio
from discoverLUN import discoverLUN

class discoverLVM:

    def __init__(self,vgname,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.lvs={}
        self.pvs={}
        self.luns={}
        self.vg={'pvs':self.pvs,'lvs':self.lvs,'luns':self.luns}
        self.vgname=vgname
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")
        
        if 'cache' in kwargs.keys():
            store=kwargs['cache']
            cache=True
        else:
            cache=False

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
        
        cmd=doProcess.doProcess("/usr/sbin/vgs --noheadings --nosuffix --separator : --options vg_name,vg_uuid,lv_name,lv_uuid " + self.vgname,debug=self.debug)
    
        if cmd.result > 0:
            self.result=1
            self.reason="Cannot execute /usr/bin/vgs"
            self.stderr=cmd.stderr
            return(False)

        self.vg['uuid']=cmd.stdout[0].split(':')[1]

        foundit=False
        for line in cmd.stdout:
            vgname,vguuid,lvname,lvuuid = line.lstrip().rstrip().split(':')
            if vgname == self.vgname:
                self.lvs[lvname]={'name':lvname,'uuid':lvuuid}
                foundit=True
                break

        if not foundit:
            self.result=1
            self.reason="Unable to find VG/LV pair"
            self.stdout=cmd.stdout
            self.stderr=cmd.stderr
            return(False)

        cmd=doProcess.doProcess("/usr/sbin/vgs --noheadings --nosuffix --separator : --options pv_uuid,pv_name " + self.vgname,debug=self.debug)
    
        if cmd.result > 0:
            self.result=1
            self.reason="Cannot execute /usr/bin/vgs"
            self.stderr=cmd.stderr
            return(False)

        for line in cmd.stdout:
            pvuuid,pvname = line.lstrip().rstrip().split(':')
            self.pvs[pvname]={'name':pvname,'uuid':pvuuid}

        for name in self.vg['pvs'].keys():
            luninfo=discoverLUN(name,debug=self.debug,apicaller=localapi)
            if not luninfo.go():
                self.result=1
                self.reason=luninfo.reason
                self.stdout=luninfo.stdout
                self.stderr=luninfo.stderr
                return(False)
            else:
                self.vg['luns'][name]=luninfo

        self.result=0
        if self.debug & 1:
            self.showDebug()
        return(True)
    
