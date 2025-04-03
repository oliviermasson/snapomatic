import os
from doSqlplus import doSqlplus
from getArchiveLogging import getArchiveLogging
from stopOracleInstance import stopOracleInstance
from startOracleInstance import startOracleInstance
from fileio import getpathinfo

def setArchiveLogging(**kwargs):
    oracleuser=None
    oraclehome=None
    oraclebase=None
    force=False

    if 'sid' in kwargs.keys():
        oraclesid=kwargs['sid']
    elif 'SID' in kwargs.keys():
        oraclesid=kwargs['SID']
    else:
        return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':'Nothing passed for sid='})

    if 'path' in kwargs.keys():
        path=kwargs['path']
    else:
        return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':'Nothing passed for path='})

    if 'home' in kwargs.keys() and kwargs['home'] is not None:
        oraclehome=kwargs['home']
    else:
        import getOracleHome
        out = getOracleHome.getOracleHome(sid=oraclesid)
        oraclehome=out['HOME']
        if oraclehome is None:
            return({'RESULT': 1,
                    'STDOUT': out['STDOUT'],
                    'STDERR': out['STDERR'],
                    'REASON': 'Unable to get ORACLE_HOME for ' + sid})

    if 'user' in kwargs.keys() and kwargs['user'] is not None:
        oracleuser=kwargs['user']
    else:
        import getOwner
        out = getOwner.getOwner(path=oraclehome)
        oracleuser=out['USER']
        if oracleuser is None:
            return({'RESULT': 1,
                    'STDOUT': out['STDOUT'],
                    'STDERR': out['STDERR'],
                    'REASON': ['Unable to get Oracle user for ' + oraclehome]})
    
    if 'base' in kwargs.keys():
        oraclebase=kwargs['base']

    if 'force' in kwargs.keys():
      force=kwargs['force']

    if force:
       if not os.path.isdir(path):
          try:
             os.makedirs(path)
          except:
             return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':"Unable to create path: " + path})
       oracleuid=pwd.getpwnam(oracleuser).pw_uid
       oraclegid=pwd.getpwnam(oracleuser).pw_gid
       try:
          os.chown(path,oracleuid,oraclegid)
       except:
          return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':"Unable to set ownership of " + path + " to " + oracleuser})

    checkaccess=getpathinfo(path)
    if not checkaccess['ISDIR']:
        return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':'Path ' + path + ' does not exist'})
    elif not checkaccess['USER'] == oracleuser:
        return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':'Oracle user does not own the archive log path'})

    current=getArchiveLogging(sid=oraclesid)
    if current['RESULT'] > 0:
       return({'RESULT':1,'STDOUT':current['STDOUT'],'STDERR':current['STDERR'],'REASON':current['REASON']})
    elif current['ENABLED'] == False or (len(current['PATHS']) > 0 and current['PATHS'][0] != path):
       out=doSqlplus(oraclesid,"alter system set log_archive_dest='" + path + "' scope=spfile;",user=oracleuser,home=oraclehome,base=oraclebase)
       if out['RESULT'] > 0 or out['ERRORFLAG'] > 1:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=stopOracleInstance(sid=oraclesid,home=oraclehome,user=oracleuser,base=oraclebase)
       if out['RESULT'] > 0:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=startOracleInstance(sid=oraclesid,home=oraclehome,user=oracleuser,base=oraclebase,method='mount')
       if out['RESULT'] > 0:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=doSqlplus(oraclesid,"alter database archivelog;",user=oracleuser,home=oraclehome,base=oraclebase)
       if out['RESULT'] > 0 or out['ERRORFLAG'] > 1:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=doSqlplus(oraclesid,"alter database open;",user=oracleuser,home=oraclehome,base=oraclebase)
       if out['RESULT'] > 0 or out['ERRORFLAG'] > 1:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       return({'RESULT':0,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
    else:
       return({'RESULT':0,'STDOUT':current['STDOUT'],'STDERR':current['STDERR'],'REASON':out['REASON']})
 
