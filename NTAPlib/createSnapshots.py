import doREST
import datetime
import re
import sys
import userio
from getVolumes import getVolumes
from getCGs import getCGs

class createSnapshots:

    def __init__(self,svm,volumes,snapshot,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.volumematch=[]
        self.volumes=[]
        self.label=None
        self.snapshot=snapshot
        self.debug=False
        self.cg=False
        self.cgname=None
        self.cguuid=None
        self.success=[]
        self.failed=[]

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        if type(volumes) is str:
            self.volumematch=[volumes]
        else:
            try:
                newlist=list(volumes)
            except:
                print("Error: 'volumes' passed to createSnapshots with illegal type")
                sys.exit(1)
            for item in newlist:
                self.volumematch.append(item)

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if 'cg' in kwargs.keys():
            self.cg=kwargs['cg']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

        if 'label' in kwargs.keys() and kwargs['label'] is not None:
            self.label=kwargs['label']
            if self.debug & 1:
                userio.message('snapmirror-label = ' + self.label,service=localapi + ":OP")


    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        self.result=0
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        
        if self.cg:
            knowncgs=getCGs(self.svm,volumes=self.volumematch,debug=self.debug,apicaller=localapi)
            if not knowncgs.go():
                self.result=1
                self.reason=knowncgs.reason
                self.stdout=knowncgs.stdout
                self.stderr=knowncgs.stderr
                if self.debug & 1:
                    self.showDebug()
                return(False)
            else:
                self.cgname=None
                self.cguuid=None
                for cg in knowncgs.cgs.keys():
                    if len(set(list(knowncgs.volumes.keys())) - set(list(knowncgs.cgs[cg]['volumes']))) == 0:
                        self.cgname=cg
                        cguuid=knowncgs.cgs[cg]['uuid']
                        if self.debug & 1:
                            userio.message("CG " + cg + " contains all required volumes for snapshot operation")
                        break
                if self.cgname is None:
                        for cg in knowncgs.cghierarchy.keys():
                            if len(set(list(knowncgs.volumes.keys())) - set(list(knowncgs.cghierarchy[cg]['volumes']))) == 0:
                                self.cgname=cg
                                self.cguuid=knowncgs.cghierarchy[cg]['uuid']
                                if self.debug & 1:
                                    userio.message("CG " + cg + " contains all required volumes for snapshot operation")
                                break
                if self.cgname is None:
                    self.result=1
                    self.reason=knowncgs.reason
                    self.stdout=knowncgs.stdout
                    self.stderr=knowncgs.stderr
                    if self.debug & 1:
                        self.showDebug()
                    return(False)
                else:
                    print(self.cgname)
                    print(self.cguuid)
                    self.volumes=list(knowncgs.volumes.keys())

        else:
            if self.debug & 1:
                userio.message("Retriving volumes on " + self.svm,service=localapi + ":OP")
                userio.message("Volume search list: " + ','.join(self.volumematch),service=localapi + ":OP")
            matchingvolumes=getVolumes(self.svm,volumes=self.volumematch,apicaller=localapi,debug=self.debug)
            if not matchingvolumes.go():
                self.result=1
                self.reason=matchingvolumes.reason
                self.stdout=matchingvolumes.stdout
                self.stderr=matchingvolumes.stderr
                if self.debug & 1:
                    self.showDebug()
                return(False)
            else:
                self.volumes=list(matchingvolumes.volumes.keys())

        if len(self.volumes) == 0:
            self.result=1
            self.reason="No matching volumes"
            return(False)

        if cg:
            json4rest={'name' : self.snapshot}
            if self.label is not None:
                json4rest['snapmirror_label'] = self.label
            rest=doREST.doREST(self.svm, \
                               'post', \
                               '/application/consistency-groups/' + self.cguuid + '/snapshots/?return_timeout=60', \
                               json=json4rest, \
                               debug=self.debug)
            if rest.result == 0 and rest.reason=='Created':
                self.success.append(self.cgname)
                if self.debug & 1:
                    userio.message("Created CG snapshot " + self.snapshot + " on " + self.svm + ":" + self.cgname,service=localapi + ":OP")
            else:
                if self.debug & 1:
                    userio.message("Failed to create snapshot " + self.snapshot + " on " + self.svm + ":" + self.cgname,service=localapi + ":OP")
                self.failed.append(self.cgname)
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()

        else:
            for volmatch in self.volumes:
                json4rest={'name' : self.snapshot}
                if self.label is not None:
                    json4rest['snapmirror_label'] = self.label
                rest=doREST.doREST(self.svm, \
                                   'post', \
                                   '/storage/volumes/' +  matchingvolumes.volumes[volmatch]['uuid'] + '/snapshots?return_timeout=60', \
                                   json=json4rest, \
                                   debug=self.debug)
                if rest.result == 0 and rest.reason=='Created':
                    self.success.append(volmatch)
                    if self.debug & 1:
                        userio.message("Created snapshot " + self.snapshot + " on " + self.svm + ":" + volmatch,service=localapi + ":OP")
                else:
                    if self.debug & 1:
                        userio.message("Failed to create snapshot " + self.snapshot + " on " + self.svm + ":" + volmatch,service=localapi + ":OP")
                    self.failed.append(volmatch)
                    self.result=1
                    self.reason=rest.reason
                    self.stdout=rest.stdout
                    self.stderr=rest.stderr
                    if self.debug & 4:
                        self.showDebug()

        if self.debug & 4:
            self.showDebug()
        if self.result == 0:
            return(True)
        elif self.result > 0:
            return(False)
