import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import userio
import doProcess
import pwd
import grp

class doSqlplus:

    def __init__(self,sid, sqlcommands, **kwargs):
        self.sid=sid
        self.sql=None
        self.home=None
        self.base=None
        self.priv='sysdba'
        self.ssh=None
        self.result=None
        self.local=False
        self.errorflag=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        commandblock = ['set echo off;','set heading off;','set pagesize 0;','set linesize 500;']
        try:
            if kwargs['feedback']:
                commandblock.append('set feedback on;')
        except:
            commandblock.append('set feedback off;')
        
        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
        else:
            self.debug=0

        if 'ssh' in kwargs.keys() and kwargs['ssh'] is not None:
            self.ssh=kwargs['ssh']
    
        if 'priv' in kwargs.keys():
            self.priv=kwargs['priv']
    
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
            self.base=out.base
            if self.base is None:
                self.result=1
                self.reason="Unable to get ORACLE_BASE for " + self.sid
                return
            else:
                self.base=out.base

        if 'local' in kwargs.keys():
            self.local=kwargs['local']

        pids=os.listdir('/proc')
        if len(self.sid) > 3 and self.sid[:4] == '+ASM':
            procmatch="asm_pmon_"
        else:
            procmatch="ora_pmon_"
        for pid in pids:
            if pid.isdigit():
                try:
                    cmdline=open(os.path.join('/proc',pid,'cmdline'),'rb').read().decode('utf-8').rstrip('x\00')
                    try:
                        if cmdline[:9] == procmatch and cmdline[9:] == self.sid:
                            self.local=True
                    except Exception as e1:
                        pass
                except Exception as e2:
                    pass

        if not self.local:
            if os.getenv("SNAPOMATIC_CREDENTIAL_PATH") is not None:
                configFile=os.getenv("SNAPOMATIC_CREDENTIAL_PATH")
            elif os.name=='posix':
                configFile='/etc/snapomatic/config.json'
            elif os.name=='nt':
                configFile='c:\snapomatic\config.json'

            if 'username' in kwargs.keys():
                username=kwargs['username']
                try:
                    password=kwargs['password']
                except Exception as e:
                    self.result=1
                    self.reason="Failed to supply password with username"
                    self.stdout=None
                    self.stderr=None
                    return
            else:
                if 'config' in kwargs.keys():
                    configFile=kwargs['config']
                    if not os.path.isfile(self.configFile):
                        self.result=1
                        self.reason="Path to configfile does not exist"
                        self.stdout=None
                        self.stderr=None
                        return
        
            import getCredentials
            credential=getCredentials.getCredential('oracle',self.sid,debug=self.debug)
            if credential.result == 0:
                self.username=credential.username
                self.password=credential.password
            else:
                if self.debug & 16 and not self.debug & 8:
                    userio.message("Unable to find credential for " + self.sid + ", will attempt OS authentication",service='doSqlPlus.execute:EXEC')
                self.local=True

        if 'user' in kwargs.keys() and kwargs['user'] is not None:
            useraccount = kwargs['user']
            try:
                checkuid = pwd.getpwnam(kwargs['user']).pw_uid
                self.user=kwargs['user']
            except:
                self.result=1
                self.errorflag=1
                self.reason='Unknown user: ' + kwargs['user']
        else:
            import getOwner
            out = getOwner.getOwner(path=self.home)
            if out.user is None:
                self.result=1
                self.errorflag=1
                self.reason='Unable to get Oracle user for ' + self.home
            else:
                self.user=out.user
                checkuid = pwd.getpwnam(out.user).pw_uid
    
        if not checkuid == os.geteuid():
            if not os.geteuid() == 0:
                self.result=1
                self.errorflag=1
                self.reason='Only root can run sqlplus as alternate user'
                return
        
        if type(sqlcommands) is list:
            for line in sqlcommands:
                commandblock.append(line)
        elif type(sqlcommands) is str:
            commandblock.append(sqlcommands)
        
        for x in range(0,len(commandblock)):
            if not commandblock[x][-1] == "\n":
                commandblock[x]=commandblock[x] + "\n"
    
        if not (commandblock[-1][-6: -1]).lower() == 'exit;\n':
            commandblock.append("exit;\n")

        mypath = "/bin:/usr/bin:/usr/local/bin:" + self.home + "/bin"
        myldlibrarypath = self.home + "/lib"
        myenv = {"PATH":  mypath,
                 "LD_LIBRARY_PATH": myldlibrarypath,
                 "ORACLE_HOME": self.home,
                 "ORACLE_SID": self.sid,
                 "ORACLE_BASE": self.base}

        if self.debug & 16 and not self.debug & 8:
            userio.message('sqlplus -S / as ' + self.priv,service='doSqlPlus.execute:EXEC')
            userio.message(str(myenv),service='doSqlPlus.execute:ENV')
            userio.message(commandblock.splitlines(),service='doSqlPlus.execute:STDIN')

        if self.local:
            cmdline=['sqlplus', '-S', '/', 'as', self.priv]
            connectstring=0
        else:
            cmdline=['sqlplus', '-S', '/nolog']
            commandblock.insert(0,'connect ' + self.username + "/" + self.password + "@" + self.sid + " as " + self.priv + "\n")
            connectstring=1
        
        sqlpluscmd = doProcess.doProcess(cmdline, stdin=commandblock, displaystdin=connectstring,env=myenv, ssh=self.ssh, user=self.user, encoding='utf8',debug=self.debug)

        self.result=sqlpluscmd.result
        self.stdout=sqlpluscmd.stdout
        self.stderr=sqlpluscmd.stderr

        for line in self.stdout:
            if line[: 5] == 'ERROR' or line[:20] == 'ORACLE not available' or line[:9] == 'ORA-01034:':
                self.result=0
                self.errorflag=1
    
        if self.result or self.errorflag:
            self.reason = "Error detected during sqlplus operation for " + self.sid
    
        if self.debug & 16 and not self.debug & 8:
            userio.message(self.stdout,service='doSqlPlus.execute:STDOUT')
            userio.message(self.stderr,service='doSqlPlus.execute:STDERR')

        if self.errorflag is None:
            self.errorflag = False
