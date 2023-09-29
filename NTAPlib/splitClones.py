import doREST
import time
import userio
from getVolumes import getVolumes

class splitClones:

    def __init__(self,svm,volumes,**kwargs):
        self.servicename=self.__class__.__name__
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.volumes=[]
        self.cache=None
        self.success=[]
        self.failed=[]
        self.debug=False
        
        self.api='/storage/volumes/{uuid}'

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
    
        if type(volumes) is str:
            self.volumes=[volumes]
        elif type(volumes) is tuple:
            self.volumes = [volumes]
        elif type(volumes) is list:
            self.volumes=volumes

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

        matchingvolumes=getVolumes(self.svm,volumes=self.volumes,apicaller=self.apibase,debug=self.debug)
        if not matchingvolumes.go():
            self.result=1
            self.reason=matchingvolumes.reason
            self.stdout=matchingvolumes.stdout
            self.stderr=matchingvolumes.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)

        availvols=list(matchingvolumes.volumes.keys())
        splitlist=[]
        for item in self.volumes:
            if item in availvols:
                splitlist.append((item,matchingvolumes.volumes[item]['uuid']))
            else:
                self.result=1
                self.reason="Volume " + item + " does not exist"
                if self.debug & 1:
                    self.showDebug()
                return(False)

        self.servicename=self.__class__.__name__ + ".go"
        self.result=0
        for item,uuid in splitlist:
            json4rest={'clone.split_initiated':'true'}

            if self.debug & 1:
                message="Splitting clone " + self.svm + ":" + item
                userio.message(message,service=localapi + ":OP")
            rest=doREST.doREST(self.svm,'patch','/storage/volumes/' + uuid,json=json4rest,debug=self.debug)

            try:
                jobuuid=rest.response['job']['uuid']
            except:
                self.result=1
                self.reason="Unable to retrieve uuid for clone split operation"
                if self.debug:
                    self.showDebug()
                return(False)

            running=True
            while running:
                time.sleep(1)
                jobrest=doREST.doREST(self.svm,'get','/cluster/jobs/' + jobuuid,restargs='fields=state,message',debug=self.debug)
                if self.debug & 4:
                    self.showDebug()
                if not jobrest.result == 0 or not jobrest.response['state'] == 'running' or jobrest.response['message'] == 'Clone split initiated.':
                    running=False

            if jobrest.result > 0:
                self.result=1
                self.reason="Failed to split clone for at least one volume"
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

        if self.debug & 4:
            self.showDebug()

        if self.result == 0:
            return(True)
        else:
            return(False)
