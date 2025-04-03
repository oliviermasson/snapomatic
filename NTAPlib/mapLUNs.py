import doREST
import time
import userio

class mapLUNs:

    def __init__(self,svm,lunpath,igroup,**kwargs):
        self.result=None
        self.reason=None
        self.svm=svm
        self.lunpath=lunpath
        self.igroup=igroup
        self.mapped=[]
        self.failed=[]
        self.stdout=[]
        self.stderr=[]
        self.lunpath=[]
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/protocols/san/lun-maps'
    
        if type(lunpath) is str:
            self.lunpath=[lunpath]
        elif type(lunpath) is list:
            self.lunpath=lunpath

        if 'cache' in kwargs.keys():
            cache=True
            store=kwargs['cache']
        else:
            cache=False

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

        self.result=0
        for item in self.lunpath:
            json4rest={'lun.name':item, 
                       'igroup.name': self.igroup,
                       'svm.name':self.svm }

            if self.debug & 1:
                userio.message("Mapping LUN " + self.svm + ":" + item + " to " + self.igroup,service=localapi + ":OP")
            rest=doREST.doREST(self.svm,'post',self.api,json=json4rest,debug=self.debug)

            if not rest.result == 201:
                self.result=1
                self.reason="Failed to map at least one LUN"
                self.stdout=self.stdout + rest.stdout
                self.stdout=self.stdout + rest.stderr
                self.failed.append((item,'REST call failed'))
                if rest.response is not None and 'error' in rest.response.keys():
                    self.reason=rest.response['error']['message']
                self.failed.append((item,rest.reason))
            else:
                self.mapped.append(item)

        if self.debug & 4:
            self.showDebug()
        if self.result == 0:
            return(True)
        else:
            return(False)

            #if cache:
            #    store.cacheVolumes(self.voluuid)

