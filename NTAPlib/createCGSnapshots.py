import doREST
import datetime
import re
import sys
import userio
from getVolumes import getVolumes
from getCGs import getCGs

class createCGSnapshots:

    def __init__(self,svm,cgname,snapshot,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.label=None
        self.snapshot=snapshot
        self.debug=False
        self.cgname=cgname
        self.success=[]
        self.failed=[]

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

        knowncgs=getCGs(self.svm,name=self.cgname,debug=self.debug,apicaller=localapi)
        if not knowncgs.go():
            self.result=1
            self.reason=knowncgs.reason
            self.stdout=knowncgs.stdout
            self.stderr=knowncgs.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            cglist=list(knowncgs.cgs.keys())
            for cg in cglist:
                if cg in knowncgs.cgs.keys() and len(set(knowncgs.cgs[cg]['children']) - set(cglist)) == 0:
                    for child in knowncgs.cgs[cg]['children']:
                        del knowncgs.cgs[child]

        json4rest={'name' : self.snapshot}
        if self.label is not None:
            json4rest['snapmirror_label'] = self.label

        for cg in knowncgs.cgs.keys():
            rest=doREST.doREST(self.svm, \
                               'post', \
                               '/application/consistency-groups/' + knowncgs.cgs[cg]['uuid'] + '/snapshots/?return_timeout=60', \
                               json=json4rest, \
                               debug=self.debug)
            if rest.result == 0 and rest.reason=='Created':
                self.success.append(cg)
                if self.debug & 1:
                    userio.message("Created CG snapshot " + self.snapshot + " on " + self.svm + ":" + cg,service=localapi + ":OP")
            else:
                if self.debug & 1:
                    userio.message("Failed to create snapshot " + self.snapshot + " on " + self.svm + ":" + cg,service=localapi + ":OP")
                self.failed.append(self.cg)
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()

        if self.debug & 1:
            self.showDebug()
        if self.result == 0:
            return(True)
        elif self.result > 0:
            return(False)
