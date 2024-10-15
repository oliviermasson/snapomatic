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
        self.failedreason={}
        self.debug=False
        self.synchronous=False
        
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

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
        
        if 'synchronous' in kwargs.keys():
            self.synchronous=kwargs['synchronous']

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
            return(False)

        availvols=list(matchingvolumes.volumesmatch.keys())
        splitlist=[]
        for item in self.volumes:
            if item in availvols:
                splitlist.append((item,matchingvolumes.volumesmatch[item]['uuid']))
            else:
                self.result=1
                self.failed.append(item)
                self.failedreason[item]="Volume " + item + " does not exist"

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
                self.failed.append(item)
                self.failedreason[item]=jobrest.response['message']
                break

            running=True
            while running:
                time.sleep(2)
                jobrest=doREST.doREST(self.svm,'get','/cluster/jobs/' + jobuuid,restargs='fields=state,message',debug=self.debug)
                if self.synchronous and not jobrest.response['state'] == 'running' and not jobrest.response['message'] == 'Clone split initiated.':
                    running=False
                elif not self.synchronous and (jobrest.response['state'] == 'running' or jobrest.response['message'] == 'Clone split initiated.'):
                    running=False

            if jobrest.result > 0:
                self.result=1
                self.reason="Failed to split clone for at least one volume"
                self.stdout=self.stdout + jobrest.stdout
                self.stdout=self.stdout + jobrest.stderr
                self.failed.append(item)
                self.failedreason[item]=jobrest.response['message']
            elif self.synchronous and not jobrest.response['state'] == 'success':
                self.result=1
                self.reason=jobrest.response['message']
                self.stdout=self.stdout + jobrest.stdout
                self.stdout=self.stdout + jobrest.stderr
                self.failed.append(item)
                self.failedreason[item]=jobrest.response['message']
            elif not self.synchronous and not jobrest.response['state'] == 'success' and not jobrest.response['state'] == 'running':
                self.result=1
                self.reason=jobrest.response['message']
                self.stdout=self.stdout + jobrest.stdout
                self.stdout=self.stdout + jobrest.stderr
                self.failed.append(item)
                self.failedreason[item]=jobrest.response['message']
            else:
                self.success.append(item)

        if self.result == 0:
            return(True)
        else:
            return(False)
