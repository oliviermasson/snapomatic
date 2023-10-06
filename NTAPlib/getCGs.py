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
        self.cghierarchy={}
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

        self.restargs=self.restargs + "&svm.name=" + svm

        if 'cache' in kwargs.keys():
            self.cache=True
            store=kwargs['cache']
        else:
            self.cache=False

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
                if 'volumes' in record.keys():
                    self.cgs[cgname]={'uuid':cguuid,'volumes':{},'parent':None}
                    for volume in record['volumes']:
                        self.cgs[cgname]['volumes'][volume['name']]={'uuid':volume['uuid']}
                if 'parent_consistency_group' in record.keys():
                    self.cgs[cgname]['parent']={'name':record['parent_consistency_group']['name'],
                                                'uuid':record['parent_consistency_group']['uuid']}

                    if self.cgs[cgname]['parent']['name'] not in self.cghierarchy.keys():
                        self.cghierarchy[self.cgs[cgname]['parent']['name']]={'volumes':{},
                                                                              'uuid':record['parent_consistency_group']['uuid']}
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

                cgmatches=[]
                cgnames=self.cgs.keys()
                for item in cgnames:
                    cgmatch=False
                    for volitem in self.cgs[item]['volumes'].keys():
                        if re.match(rematch,volitem):
                            cgmatch=True
                            if self.debug & 1:
                                userio.message("CG " + item + " has constituent that matches " + pattern,service=localapi + ":OP")
                            cgmatches.append(item)
                            break

            nomatches=list(set(list(self.cgs.keys())) - set(cgmatches))
            for item in nomatches:
                if self.debug & 1:
                    userio.message("CG " + item + " has no constituent that matches " + pattern,service=localapi + ":OP")
                del self.cgs[item]
            
            singlecgs=list(self.cgs.keys())
            for cg in singlecgs:
                for volume in self.cgs[cg]['volumes'].keys():
                    if 'parent' in self.cgs[cg].keys():
                        self.cghierarchy[self.cgs[cg]['parent']['name']]['volumes'][volume]=self.cgs[cg]['volumes'][volume]

            mastervolumelist=[]
            for cg in self.cgs.keys():
                mastervolumelist = mastervolumelist + list(self.cgs[cg]['volumes'].keys())

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
            return(False)


        if self.result == 1:
            self.result=1
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            self.result=0
            if self.debug & 1:
                self.showDebug()
            return(True)

