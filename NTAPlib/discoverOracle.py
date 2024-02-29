import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import getOracleHome
import userio
import doSqlplus

class discoverOracle:

    def __init__(self,sid,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.sid=None
        self.home=None
        self.base=None
        self.user=None
        self.datafiles={}
        self.tempfiles={}
        self.arch={}
        self.redo={}
        self.pfile={}
        self.ctrl={}
        self.backup=None
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

    def go(self,**kwargs):

        if self.home == None or self.base == None:
            self.result=1
            return(False)

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        delim=userio.randomtoken(10)

        sqlcmds=[]
        sqlcmds.append("select name||'" + delim[0] + \
                       "'||file#||'" + delim[0] + \
                       "'||bytes " + \
                       "from v$datafile;")
        
        sqlcmds.append("select v$datafile.name||'" + delim[1] + \
                       "'||v$backup.status " \
                       "from v$datafile inner join v$backup on v$datafile.file#=v$backup.file# where v$datafile.con_id!='2';")

        sqlcmds.append("select dest_name||'" + delim[2] + \
                       "'||destination " + \
                       "from v$archive_dest where destination is not null;")
        
        sqlcmds.append("select group#||'" + delim[3] + \
                       "'||member " + \
                       "from v$logfile where type = 'ONLINE';")
        
        sqlcmds.append("select group#||'" + delim[4] + \
                       "'||thread#||'" + delim[4] + \
                       "'||bytes " + \
                       "from v$log;")
        
        sqlcmds.append("select name||'" + delim[5] + \
                       "'||file#||'" + delim[5] + \
                       "'||bytes " + \
                       "from v$tempfile;")
        
        sqlcmds.append("select name||'" + delim[6] + \
                       "'||value " + \
                       "from v$parameter where isdefault = 'FALSE' and value is not null order by name;")

        sqlcmds.append("select name||'" + delim[7] + \
                       "'||'' " + \
                       "from v$controlfile;")

        out=doSqlplus.doSqlplus(self.sid,sqlcmds,
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
        
        for item in out.stdout:
            if delim[0] in item:
                name,fileno,size=item.split(delim[0])
                self.datafiles[name]={'name':name,'fileno':fileno,'size':size,'backup':'Unknown'}
            if delim[2] in item:
                param,path=item.split(delim[2])
                self.arch[path]={'param':param}
            if delim[3] in item:
                group,path=item.split(delim[3])
                self.redo[path]={'group':group}
            if delim[5] in item:
                name,fileno,size=item.split(delim[5])
                self.tempfiles[name]={'name':name,'fileno':fileno,'size':size}
            if delim[6] in item:
                name,value=item.split(delim[6])
                self.pfile[name]=value
            if delim[7] in item:
                self.ctrl[item.split(delim[7])[0]]={}

        for item in out.stdout:
            if delim[1] in item:
                name,backup=item.split(delim[1])
                self.datafiles[name]['backup']=backup
                if backup == 'ACTIVE':
                    self.backup=True
            if delim[4] in item:
                group,thread,size=item.split(delim[4])
                for item in self.redo.keys():
                    if self.redo[item]['group'] == group:
                        self.redo[item]['thread']=thread
                        self.redo[item]['size']=size

        self.result=0
        return(True)


    def showDebug(self):
        userio.debug(self)

