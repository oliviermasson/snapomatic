import os
import doProcess
import userio
import re
import getOracleHome

class discoverASM:

    def __init__(self,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.paths=[]
        self.diskgroups={}
        self.asmdisks={}
        self.asmpaths={}
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

        if 'cache' in kwargs.keys():
            self.cache=kwargs['cache']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

        if 'path' in kwargs.keys():
            self.paths=userio.mklist(kwargs['path'])
        
    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        gridhome=getOracleHome.getOracleHome(grid=True,debug=self.debug)
        if not gridhome.go():
            self.result=1
            self.reason="Unable to discover Grid home for host"
            self.stdout=gridhome.stdout
            self.stderr=gridhome.stderr
            if debug & 1:
                showDebug()

        if len(self.paths) == 0:
            multipaths=os.listdir('/dev/')
            r=re.compile('dm-*')
            dmdevices=list(filter(r.match,multipaths))
        else:
            dmdevices=self.paths

        for item in dmdevices:
            if not item[:4] == '/dev/':
                item='/dev/' + item
            if self.cache and item in self.cache.asmpaths.keys():
                if self.debug & 1:
                    userio.message('Using cached LUN data for ' + item,service=localapi + ":CACHE")
                self.asmpaths[item]=self.cache.asmpaths[item]
                diskgroup=self.asmpaths[item]['diskgroup']
                diskname=self.asmpaths[item]['name']
                if not diskgroup in self.diskgroups.keys():
                    self.diskgroups[diskgroup]={'disks':[diskname]}
                else:
                    self.diskgroups[diskgroup]['disks'].append(diskname)
                self.asmdisks[diskname]={'name':diskname,'diskgroup':diskgroup,'device':item}
            else:
                header=doProcess.doProcess(gridhome.home + '/bin/kfed read ' + item, \
                                 env={'ORACLE_HOME':gridhome.home}, \
                                 debug=self.debug)
                if header.stdout is not None:
                    getgrp=False
                    getdskname=False
                    try:
                        getgrp=[line for line in header.stdout if 'kfdhdb.grpname' in line][0]
                    except:
                        pass
                    try:
                        getdskname=[line for line in header.stdout if 'kfdhdb.dskname' in line][0]
                    except:
                        pass
                    if getgrp and getdskname:
                        diskgroup='+' + getgrp.split()[1]
                        diskname=getdskname.split()[1]
                        if not diskgroup in self.diskgroups.keys():
                            self.diskgroups[diskgroup]={'disks':[diskname]}
                        else:
                            self.diskgroups[diskgroup]['disks'].append(diskname)
                        self.asmdisks[diskname]={'name':diskname,'diskgroup':diskgroup,'device':item}
                        self.asmpaths[item]={'name':diskname,'diskgroup':diskgroup,'device':item}
                        if self.cache:
                            self.cache.asmpaths[item]=self.asmpaths[item]
                            if self.debug & 1:
                                userio.message('Caching ASM path data for ' + item,service=localapi + ":CACHE")

        if self.debug & 1:
            self.showDebug()
        return(True)
    
