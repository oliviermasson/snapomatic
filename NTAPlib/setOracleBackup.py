import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import getOracleHome
import getOwner
import userio
import doSqlplus

class setOracleBackup:

    def __init__(self,sid,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.sid=None
        self.home=None
        self.base=None
        self.user=None
        self.backup=None
        self.indeterminate=None
        self.force=False

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

        if 'force' in kwargs.keys():
            self.force=kwargs['force']

        self.sid=sid
        
        home=getOracleHome.getOracleHome(sid=self.sid,apicaller=localapi,debug=self.debug)
        if not home.go():
            self.result=home.result
            self.reason=home.reason
            return
        else:
            self.home=home.home
            self.base=home.base
            self.user=home.user

    def go(self,requestedbackupmode,**kwargs):

        if self.home == None or self.base == None:
            self.result=1
            return(False)

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        delim=userio.randomtoken()
        out=doSqlplus.doSqlplus(self.sid,"select v$datafile.name||'" + delim + \
                                         "'||v$backup.status " \
                                         "from v$datafile inner join v$backup on v$datafile.file#=v$backup.file# where v$datafile.con_id!='2';",
                                user=self.user,
                                priv='sysdba',
                                home=self.home,
                                base=self.base,
                                debug=self.debug)
        if out.result > 0 or out.errorflag:
            self.result=1
            self.reason=out.reason
            self.stdout=out.stdout
            self.stderr=out.stderr
            return(False)
        else:
            self.backup=False
            for line in out.stdout:
                fields=line.split(delim)
                try:
                    if fields[1] == 'ACTIVE':
                        self.backup=True
                    if not fields[1] == 'NOT ACTIVE' and not fields[1] == 'ACTIVE':
                        self.indeterminate=True
                    if fields[1] == 'NOT ACTIVE' and self.backup:
                        self.indeterminate=True
                except:
                    pass

        if self.debug & 1:
            if self.backup:
                userio.message("Database " + self.sid + " has datafiles in backup mode",service=localapi)
            if self.indeterminate:
                userio.message("Backup state of " + self.sid + " is indeterminate",service=localapi)
            if not self.backup and not self.indeterminate:
                userio.message("Unable to confirm " + self.sid + " is currently in backup mode",service=localapi)

        if self.indeterminate and not self.force:
            self.result=1
            self.reason="Unable to determine backup state of database " + self.sid
            return(False)

        if requestedbackupmode:
            if self.backup:
                self.result=1
                self.reason=('Database ' + self.sid + ' is already in backup mode')
                return(False)
            else:
                out=doSqlplus.doSqlplus(self.sid,"alter database begin backup;",
                                        user=self.user,
                                        priv='sysdba',
                                        home=self.home,
                                        base=self.base,
                                        debug=self.debug)
                if out.result > 0 or out.errorflag > 0:
                    self.result=1
                    self.reason=out.reason
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return(False)
                else:
                    self.result=0
                    return(True)
        else:
            if not self.backup:
                self.result=1
                self.reason=('Unable to confirm database ' + self.sid + ' is currently in backup mode')
                return(False)
            else:
                out=doSqlplus.doSqlplus(self.sid,"alter database end backup;",
                                        user=self.user,
                                        priv='sysdba',
                                        home=self.home,
                                        base=self.base,
                                        debug=self.debug)
                if out.result > 0:
                    self.result=1
                    self.reason=out.reason
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return(False)
                else:
                    self.result=0
                    return(True)

    def showDebug(self):
        userio.debug(self)

