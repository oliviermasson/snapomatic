import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import getOracleHome
import getOwner
import userio
import doProcess
import pwd

class stopOracleRAC:

    def __init__(self,sid,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.sid=sid
        self.home=None
        self.base=None
        self.user=None
        self.abort=None
        self.dbtype='RAC'
        self.debug=0

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
        
        if 'abort' in kwargs.keys() and kwargs['abort']:
            self.abort=True

        if 'onenode' in kwargs.keys() and kwargs['onenode']:
            self.dbtype='RACONENODE'

        if 'home' in kwargs.keys() and kwargs['home'] is not None:
            self.home = kwargs['home']
        else:
            import getOracleHome
            out = getOracleHome.getOracleHome(sid=self.sid,apicaller=localapi,debug=self.debug)
            if not out.go():
                self.result=1
                self.reason="Unable to get ORACLE_HOME for " + self.sid
            else:
                self.home=out.home

        if 'base' in kwargs.keys() and kwargs['base'] is not None:
            self.base = kwargs['base']
        else:
            import getOracleBase
            out = getOracleBase.getOracleBase(home=self.home,apicaller=localapi,debug=self.debug)
            if not out.go():
                self.result=1
                self.reason="Unable to get ORACLE_BASE for " + self.sid
                return
            else:
                self.base=out.base
        
        if 'user' in kwargs.keys():
            self.user=kwargs['user']
        else:
            out = getOwner.getOwner(path=self.home)
            if out.user is None:
                self.result=1
                self.errorflag=1
                self.reason='Unable to get Oracle user for ' + self.home
            else:
                self.user=out.user

    def go(self,**kwargs):

        if self.home == None or self.base == None:
            self.result=1
            return(False)

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        delim=userio.randomtoken()


        if self.abort:
            stopoption='abort'
        else:
            stopoption='immediate'

        out=doProcess.doProcess(self.home + '/bin/srvctl stop database -db ' + self.sid \
                                    + ' -stopoption ' + stopoption, \
                       env={'ORACLE_HOME':self.home,
                            'ORACLE_BASE':self.base},
                       user=self.user,
                       debug=self.debug)
        if out.result > 0:
            self.result=1
            self.reason="srvctl command failed"
            for line in out.stdout:
                if 'PRCC-1016' in line:
                    self.reason="Database was already stopped"
                    break
            self.stdout=out.stdout
            self.stderr=out.stderr
            return(False)
        else:
            self.result=0
            self.stdout=out.stdout
            self.stderr=out.stderr
            return(True)

    def showDebug(self):
        userio.debug(self)

