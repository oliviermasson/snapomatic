import doREST
import getVolumes
import time
import userio

class destroyVolumes:

    def __init__(self,svm,volume,**kwargs):
        self.result=None
        self.reason=None
        self.svm=svm
        self.volume=volume
        self.stdout=[]
        self.stderr=[]
        self.debug=False
        self.failed=[]

        ignoreunknown=False 

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        self.api='/storage/volumes'

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

        if self.debug & 1:
            userio.message("Validating volume to be destroyed",service=localapi + ":OP")
        allvols=getVolumes.getVolumes(self.svm,volumes=self.volume,apicaller=localapi,debug=self.debug)
        allvols.go()

        if self.volume not in allvols.volumes.keys():
            self.result=1
            self.reason="Volume " + self.volume + " does not exist on SVM " + self.svm
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            uuid=allvols.volumes[self.volume]['uuid']

        if self.debug & 1:
            userio.message("Destroying volume " + self.svm + ":" + self.volume,service=localapi + ":OP")
        rest=doREST.doREST(self.svm,'delete','/storage/volumes/' + uuid,debug=self.debug)
        jobuuid=rest.response['job']['uuid']
        if self.debug & 4:
            useriomessage("Polling job UUID " + jobuuid,service=localapi + ":OP")

        running=True
        while running:
            time.sleep(1)
            jobrest=doREST.doREST(self.svm,'get','/cluster/jobs/' + jobuuid,restargs='fields=state,message',debug=self.debug)
        
            if not jobrest.result == 202 and not jobrest.response['state'] == 'running':
                running=False


        if not jobrest.result == 200 or not jobrest.response['state'] == 'success':
            self.result=1
            self.reason="Failed to destroy " + self.volume
            self.stdout=self.stdout + jobrest.stdout
            self.stdout=self.stdout + jobrest.stderr
            self.failed.append((self.volume,'REST call failed'))
            if self.debug & 1:
                self.showDebug()
            return(False)
        elif not jobrest.response['state'] == 'success':
            self.result=1
            self.reason=jobrest.response['message']
            self.stdout=self.stdout + jobrest.stdout
            self.stdout=self.stdout + jobrest.stderr
            self.failed.append((self.volume,jobrest.response['message']))
            if self.debug & 1:
                self.showDebug()
            return(True)
        else:
            self.result=0
            if self.debug & 1:
                self.showDebug()
            return(True)
