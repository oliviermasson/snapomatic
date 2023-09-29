import os
import doProcess
import userio

class getOracleBase:

    def __init__(self,home,**kwargs):
        self.result=None
        self.reason=None
        self.home=home
        self.base=None
        self.user=None
        self.stdout=[]
        self.stderr=[]

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
        else:
            self.debug=False


        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")
    
        if 'user' in kwargs.keys():
            self.user=kwargs['user']
        else:
            import getOwner
            out=getOwner.getOwner(path=self.home + "/bin/oracle")
            if out.user is None:
                self.result=1
                self.reason="Unable to find Oracle user for " + self.home
                if self.debug & 1:
                    showDebug()
                return
            else:
                self.user=out.user
                if self.debug & 1:
                    userio.message("ORACLE_HOME " + home + " is owned by " + self.user,service=localapi + ":DATA")
    
    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.user is None:
            if self.debug & 1:
                showDebug()
            return(False)

        out=doProcess.doProcess(self.home + "/bin/orabase",user=self.user,env={'ORACLE_HOME':self.home,'LIB':self.home + '/lib'})
        if out.result == 0:
            if os.path.exists(out.stdout[-1]):
                self.result=0
                self.base=out.stdout[-1]
                if self.debug & 1:
                    self.showDebug()
                return(True)
            else:
                self.result=1
                self.reason="Unable to find ORACLE_BASE for " + self.home
                if self.debug & 1:
                    showDebug()
                return(False)
        else:
            self.result=1
            self.reason="Unable to run " + self.home + "/bin/orabase"
            if self.debug & 1:
                showDebug()

