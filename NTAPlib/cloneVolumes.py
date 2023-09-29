#
# self.clonesets = (current volume name),(clone volume name)
#                  list of (current volume name),(clone volume name) pairs
#
# self.split     = clone split requested
#
# self.success   = clone successfully created
#
# self.failed    = clone operation failed
#
# self.unsplit   = clone splt operation failed

import doREST
import time
import userio
from splitClones import splitClones

class cloneVolumes:

    def __init__(self,svm,clonesets,**kwargs):
        self.servicename=self.__class__.__name__
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.clonesets=[]
        self.cache=None
        self.split=False
        self.success=[]
        self.failed=[]
        self.unsplit=[]
        self.warning=[]
        self.debug=False
        
        self.api='/storage/volumes'

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'uuid' in kwargs.keys():
            self.uuid=kwargs['uuid']
        else:
            self.uuid=False
    
        if type(clonesets) is str:
            self.clonesets=[(clonesets.split(','))]
        elif type(clonesets) is tuple:
            self.clonesets = [clonesets]
        elif type(clonesets) is list:
            for item in clonesets:
                if type(item) is str:
                    self.clonesets.append((item.split(',')))
                elif type(item) is tuple:
                    self.clonesets.append(item)

        if 'cache' in kwargs.keys():
            self.cache=True
            store=kwargs['cache']
        else:
            self.cache=False

        if 'split' in kwargs.keys():
            self.split=kwargs['split']

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

        self.servicename=self.__class__.__name__ + ".go"
        self.result=0
        for item in self.clonesets:
            json4rest={'clone.is_flexclone':True, 
                       'clone.parent_svm.name': self.svm,
                       'clone.parent_volume.name': item[0],
                       'name' : item[1],
                       'svm.name':self.svm }

            if len(item) > 2:
                if self.uuid:
                    json4rest['clone.parent_snapshot.uuid']=item[2]
                else:
                    json4rest['clone.parent_snapshot.name']=item[2]

            if self.debug & 1:
                message="Cloning volume " + self.svm + ":" + item[0] + " as " + item[1]
                if len(item) > 2:
                    message = message + " using snapshot " + item[2]
                if self.split:
                    message=message + " split requested"
                userio.message(message,service=localapi + ":OP")
            rest=doREST.doREST(self.svm,'post',self.api,json=json4rest,debug=self.debug)

            try:
                jobuuid=rest.response['job']['uuid']
            except:
                self.result=1
                self.reason="Unable to retrieve uuid for cloning operation"
                if self.debug:
                    self.showDebug()
                return(False)

            running=True
            while running:
                time.sleep(1)
                jobrest=doREST.doREST(self.svm,'get','/cluster/jobs/' + jobuuid,restargs='fields=state,message',debug=self.debug)
                if not jobrest.result == 0 or not jobrest.response['state'] == 'running':
                    running=False

            if jobrest.result > 0:
                self.result=1
                self.reason="Failed to clone at least one volume"
                self.stdout=self.stdout + jobrest.stdout
                self.stdout=self.stdout + jobrest.stderr
                self.failed.append((item,'REST call failed'))
            elif not jobrest.response['state'] == 'success':
                self.result=1
                self.reason=jobrest.response['message']
                self.stdout=self.stdout + jobrest.stdout
                self.stdout=self.stdout + jobrest.stderr
                self.failed.append((item,jobrest.response['message']))
            else:
                self.success.append(item)
                if self.split:
                    split=splitClones(self.svm,item[1],apicaller=self.apibase,debug=self.debug)
                    if not split.go():
                        self.unsplit.append(item[1])

        if self.debug & 4:
            self.showDebug()

        if self.result == 0:
            return(True)
        else:
            return(False)
