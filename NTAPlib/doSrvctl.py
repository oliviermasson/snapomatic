import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import userio
import doProcess
import pwd
import grp

class doSrvctl:

    def __init__(self,command,srvctlargs, **kwargs):
        self.sql=None
        self.home=None
        self.base=None
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.procargs=None

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        
        localapi='->'.join([self.apicaller,self.apibase])

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
        else:
            self.debug=False

        if 'home' in kwargs.keys() and kwargs['home'] is not None:
            self.home = kwargs['home']
        else:
            import getOracleHome
            out = getOracleHome.getOracleHome(grid=True,apicaller=localapi,debug=self.debug)
            if out.go():
                self.home=out.home
                self.base=out.base
            else:
                self.result=1
                self.reason="Unable to get ORACLE_HOME for Grid Infrastructure"
                return

        if 'base' in kwargs.keys() and kwargs['base'] is not None:
            self.base = kwargs['base']
        elif self.base is None:
            import getOracleBase
            out = getOracleBase.getOracleBase(home=self.home,apicaller=localapi,debug=self.debug)
            self.base=out.base
            if self.base is None:
                self.result=1
                self.reason="Unable to get ORACLE_BASE for Grid Infrastructure"
                return
            else:
                self.base=out.base

        if 'user' in kwargs.keys() and kwargs['user'] is not None:
            useraccount = kwargs['user']
            try:
                checkuid = pwd.getpwnam(kwargs['user']).pw_uid
                self.user=kwargs['user']
            except:
                self.result=1
                self.reason='Unknown user: ' + kwargs['user']
        else:
            import getOwner
            out = getOwner.getOwner(path=self.home)
            if out.user is None:
                self.result=1
                self.reason='Unable to get Oracle user for ' + self.home
            else:
                self.user=out.user
                checkuid = pwd.getpwnam(out.user).pw_uid
    
        if not checkuid == os.geteuid():
            if not os.geteuid() == 0:
                self.result=1
                self.reason='Only root can run srvctl as alternate user'
                return
    
        if type(command) is list:
            self.procargs=command
        elif type(command) is str:
            self.procargs=command.split()
        
        if type(srvctlargs) is list:
            for item in srvctlargs:
                self.procargs.append(item)
        elif type(srvctlargs) is dict:
            for item in srvctlargs.keys():
                if item[0] == '-':
                    self.procargs.append(item)
                else:
                    self.procargs.append('-' + item)
                if len(srvctlargs[item]) > 0:
                    self.procargs.append(srvctlargs[item])

        mypath = "/bin:/usr/bin:/usr/local/bin:" + self.home + "/bin"
        myldlibrarypath = self.home + "/lib"
        myenv = {"PATH":  mypath,
                 "LD_LIBRARY_PATH": myldlibrarypath,
                 "ORACLE_HOME": self.home,
                 "ORACLE_BASE": self.base}

        if self.debug & 16 and not self.debug & 8:
            userio.message('srvctl',service='doSrvctl.execute:EXEC')
            userio.message(str(myenv),service='doSrvctl.execute:ENV')
            userio.message(procargs.splitlines(),service='doSrvctl.execute:STDIN')

        srvctlcmd = doProcess.doProcess(['srvctl'] + self.procargs, env=myenv, user=self.user, encoding='utf8',debug=self.debug)
        
        if self.debug & 16 and not self.debug & 8:
            userio.message(self.stdout,service='doSrvctl.execute:STDOUT')
            userio.message(self.stderr,service='doSrvctl.execute:STDERR')

        if self.result:
            self.reason = "Error detected during srvctl operation"
            self.result=1
            self.stdout=srvctlcmd.stdout
            self.stderr=srvctlcmd.stderr
            return
        else:
            self.result=0
            self.stdout=srvctlcmd.stdout
