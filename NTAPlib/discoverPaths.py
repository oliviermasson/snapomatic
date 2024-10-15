import os
import doProcess
import userio
import stat
import fileio
from discoverLUN import discoverLUN
from discoverLVM import discoverLVM
from discoverNFS import discoverNFS
from discoverASM import discoverASM

class discoverPaths:

    def __init__(self,discoverypaths,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.discoverypaths=discoverypaths
        self.paths={}
        self.lvmdevices={}
        self.asmdevices={}
        self.vgs={}
        self.luns={}
        self.allvolumes={}
        self.nfsvolumes={}
        self.blockvolumes={}
        self.asmvolumes={}
        self.unknown=[]
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

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

        if 'multipath' in kwargs.keys():
            self.multipath=kwargs['multipath']

        if 'cache' in kwargs.keys():
            self.cache=kwargs['cache']
        
    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):
        
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])
        
        if not os.path.isfile('/usr/bin/sg_raw'):
            self.result=1
            self.reason="Cannot find /usr/bin/sg_raw"
            if self.debug & 1:
                self.showDebug()
            return(False)

        blockpaths={}
        fspaths=[]
        asmdiscovery=False
        asminfo={}
        for path in self.discoverypaths:
            if path[0] == '+':
                if not asmdiscovery:
                    asminfo=discoverASM(cache=self.cache,debug=self.debug)
                    asminfo.go()
                    asmdiscovery=True
                diskgrouponly=path.split('/')[0]
                if diskgrouponly in asminfo.diskgroups.keys():
                    self.paths[path]={'device':diskgrouponly,'fstype':'asm','mountpoint':None}
                    if self.debug & 1:
                        userio.message('Path ' + path + ' resolves to ' + diskgrouponly,service=localapi + ":OP")
                else:
                    self.unknown.append(path)
            elif not os.path.exists(path):
                self.unknown.append(path)
                if self.debug & 1:
                    userio.message('Path ' + path + ' does not exist',service=localapi + ":OP")
                    self.unknown.append(path)
            else:
                if self.debug & 1:
                    userio.message('Resolving symlinks for ' + path,service=localapi + ":OP")
                realpath=os.path.realpath(path)
                if self.debug & 1:
                        if not realpath == path:
                            userio.message('Path ' + path + ' resolves to ' + realpath,service=localapi + ":OP")
                        userio.message('Checking for block device for ' + realpath,service=localapi + ":OP")
                mode=os.lstat(realpath).st_mode
                isblock=stat.S_ISBLK(mode)
                if isblock:
                    self.paths[path]={'device':realpath,'fstype':'block','mountpoint':None}
                    if self.debug & 1:
                        userio.message('Path ' + realpath + ' is block device',service=localapi + ":OP")
                else:
                    fspaths.append(realpath)
        
        if len(fspaths) > 0:
            knowndevices={}
            fsinfo=fileio.getFilesystems(fspaths)
            for path in fsinfo.keys():
                self.paths[path]=fsinfo[path]

        discoverypaths=list(self.paths.keys())
        nfspaths=[]
        for item in discoverypaths:
            device=self.paths[item]['device']
            if self.paths[item]['fstype'] == 'block':
                if device not in self.luns.keys():
                    nextlun=discoverLUN(device,multipath=self.multipath,cache=self.cache,debug=self.debug,apicaller=localapi)
                    if not nextlun.go():
                        del self.paths[item]
                        self.unknown.append(item)
                    else:
                        self.luns[device]=nextlun
            elif self.paths[item]['fstype'] == 'xfs':
                try:
                    vg,lv=device.split('/')[-1].split('-')
                    self.paths[item]['device']=tuple((vg,lv))
                except:
                    del self.paths[item]
                    self.unknown.append(item)
                    break
                if ((vg,lv)) not in self.lvmdevices.keys():
                    vgobject=discoverLVM(vg)
                    if not vgobject.go():
                        del self.paths[item]
                        self.unknown.append(item)
                    else:
                        for lvuuid in vgobject.vg['lvs'].keys():
                            if vgobject.vg['lvs'][lvuuid]['name'] == lv:
                                self.lvmdevices[(vg,lv)] = (vgobject.vg['uuid'],lvuuid)
                                if vgobject.vg['uuid'] not in self.vgs.keys():
                                    self.vgs[vg]=vgobject.vg
                                    for lunpath in vgobject.vg['luns'].keys():
                                        if lunpath not in self.luns.keys():
                                            self.luns[lunpath]=vgobject.vg['luns'][lunpath]
            elif self.paths[item]['fstype'] in ['nfs', 'nfs4']:
                nfspaths.append(item)
            elif self.paths[item]['fstype'] == 'asm':
                for asmdisk in asminfo.diskgroups[device]['disks']:
                    if asminfo.asmdisks[asmdisk]['device'] not in self.luns.keys():
                        nextlun=discoverLUN(asminfo.asmdisks[asmdisk]['device'],cache=self.cache,debug=self.debug,apicaller=localapi)
                        if not nextlun.go():
                            del self.paths[item]
                            self.unknown.append(item)
                        else:
                            self.luns[asminfo.asmdisks[asmdisk]['device']] = nextlun
            else:
                del self.paths[item]
                self.unknown.append(item)
        
        if len(nfspaths) > 0:
            nfspaths=list(set(nfspaths))
            pathinfo=discoverNFS(nfspaths,debug=self.debug,apicaller=localapi)
            if not pathinfo.go():
                for path in nfspaths:
                    del self.paths[path]
                    self.unknown.append(path)
            else:
                self.nfsvolumes=pathinfo.nfs

        for item in self.nfsvolumes.keys():
            for vol in self.nfsvolumes[item]['volumes'].keys():
                if self.nfsvolumes[item]['volumes'][vol]['svm']['name'] not in list(self.allvolumes.keys()):
                    self.allvolumes[self.nfsvolumes[item]['volumes'][vol]['svm']['name']] \
                         = [self.nfsvolumes[item]['volumes'][vol]['name']]
                else:
                    self.allvolumes[self.nfsvolumes[item]['volumes'][vol]['svm']['name']].append(self.nfsvolumes[item]['volumes'][vol]['name'])
        
        for item in self.luns.keys():
            if self.luns[item].svm['name'] not in list(self.allvolumes.keys()):
                self.allvolumes[self.luns[item].svm['name']] = [self.luns[item].volume]
            else:
                self.allvolumes[self.luns[item].svm['name']].append(self.luns[item].volume)

        for svm in self.allvolumes.keys():
            self.allvolumes[svm]=set(self.allvolumes[svm])

        self.result=0
        if self.debug & 1:
            self.showDebug()
        return(True)
    
