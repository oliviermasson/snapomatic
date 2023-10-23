import doREST
import sys
import userio
import re
from getVolumes import getVolumes

class getCGs:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.volumematch=[]
        self.volumes={}
        self.cgs={}
        self.name=[]
        self.debug=False
        
        self.api='/application/consistency-groups'
        self.restargs='fields=uuid,' + \
                      'svm.name,' + \
                      'parent_consistency_group,' + \
                      'volumes.name,' + \
                      'volumes.uuid'
        
        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller'] 
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'volumes' in kwargs.keys():
            if type(kwargs['volumes']) is str:
                self.volumematch=kwargs['volumes'].split(',')
            else:
                try:
                    newlist=list(kwargs['volumes'])
                except:
                    print("Error: 'volumes' passed to getCGs with illegal type")
                    sys.exit(1)
                for item in newlist:
                    self.volumematch.append(item)
        else:
            self.volumematch='*'
        
        if 'name' in kwargs.keys():
            if type(kwargs['name']) is str:
                self.volumematch=kwargs['name'].split(',')
            else:
                try:
                    newlist=list(kwargs['name'])
                except:
                    print("Error: 'name' passed to getCGs with illegal type")
                    sys.exit(1)
                for item in newlist:
                    self.name.append(item)
        else:
            self.name=['*']

        self.restargs=self.restargs + "&svm.name=" + svm

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        rest=doREST.doREST(self.svm,'get',self.api,restargs=self.restargs,debug=self.debug)
        if rest.result == 0:
            for record in rest.response['records']:
                svmname=record['svm']['name']
                cgname=record['name']
                cguuid=record['uuid']
                if not svmname == self.svm:
                    sys.stderr.write("svm name mismatch in getCGs")
                    sys.exit(1)
                if self.debug & 1:
                    userio.message("Found CG " + cgname + " with uuid " + cguuid,service=localapi + ":OP")
                self.cgs[cgname]={'uuid':cguuid,'volumes':[],'parent':None,'children':[]}
                if 'volumes' in record.keys():
                    for volume in record['volumes']:
                        self.cgs[cgname]['volumes'].append(volume['name'])
                if 'parent_consistency_group' in record.keys():
                    if self.debug & 1:
                        userio.message("CG " + cgname + " has parent CG of " + record['parent_consistency_group']['name'],service=localapi + ":OP")
                    self.cgs[cgname]['parent']=record['parent_consistency_group']['name']

            for cg in self.cgs.keys():
                if self.cgs[cg]['parent'] is not None:
                    self.cgs[self.cgs[cg]['parent']]['volumes']=self.cgs[self.cgs[cg]['parent']]['volumes'] + self.cgs[cg]['volumes']
                    if self.cgs[cg]['parent'] in self.cgs.keys() and cg not in self.cgs[self.cgs[cg]['parent']]['children']:
                        self.cgs[self.cgs[cg]['parent']]['children'].append(cg)
            
            cgmatches=[]
            for pattern in self.name:
                if pattern == '*':
                    rematch=re.compile('^.*.$')
                elif re.findall(r'[?*.^$]',pattern):
                    try:
                        rematch=re.compile(pattern)
                    except:
                        self.result=1
                        self.reason="Illegal volume pattern match"
                        return(False)
                else:
                    rematch=re.compile('^' + pattern + '$')

                cgnames=self.cgs.keys()
                for cgitem in cgnames:
                    cgmatch=False
                    for cgitem in self.cgs.keys():
                        if re.match(rematch,cgitem):
                            cgmatch=True
                            if self.debug & 1:
                                userio.message("CG " + cgitem + " matches " + pattern,service=localapi + ":OP")
                            cgmatches.append(cgitem)
            
            nomatches=list(set(list(self.cgs.keys())) - set(cgmatches))
            for item in nomatches:
                if self.debug & 1:
                    userio.message("CG " + item + " does not match any cg pattern ",service=localapi + ":OP")
                del self.cgs[item]

            cgmatches=[]
            for pattern in self.volumematch:
                if pattern == '*':
                    rematch=re.compile('^.*.$')
                elif re.findall(r'[?*.^$]',pattern):
                    try:
                        rematch=re.compile(pattern)
                    except:
                        self.result=1
                        self.reason="Illegal volume pattern match"
                        return(False)
                else:
                    rematch=re.compile('^' + pattern + '$')

                cgnames=self.cgs.keys()
                for item in cgnames:
                    cgmatch=False
                    for volitem in self.cgs[item]['volumes']:
                        if re.match(rematch,volitem):
                            cgmatch=True
                            if self.debug & 1:
                                userio.message("CG " + item + " has constituent that matches " + pattern,service=localapi + ":OP")
                            cgmatches.append(item)
                            break

            nomatches=list(set(list(self.cgs.keys())) - set(cgmatches))
            for item in nomatches:
                if self.debug & 1:
                    userio.message("CG " + item + " does not match any volume pattern",service=localapi + ":OP")
                del self.cgs[item]
            
            mastervolumelist=[]
            for cg in self.cgs.keys():
                mastervolumelist = mastervolumelist + self.cgs[cg]['volumes']

            if len(self.cgs) > 0:
                volumes=getVolumes(self.svm,volumes=mastervolumelist,debug=self.debug,apicaller=localapi)
                if not volumes.go():
                    self.result=1
                    self.reason=volumes.reason
                    if self.debug & 1:
                        self.showDebug()
                    return(False)
                else:
                    self.volumes=volumes.volumes

            self.result=0
            return(True)

        else:
            self.result=1
            self.reason=rest.reason
            if self.debug & 1:
                self.showDebug()
            return(False)

