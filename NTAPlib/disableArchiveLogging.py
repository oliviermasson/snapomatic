from doSqlplus import doSqlplus
from getArchiveLogging import getArchiveLogging
from stopOracleInstance import stopOracleInstance
from startOracleInstance import startOracleInstance

def disableArchiveLogging(**kwargs):
    oracleuser=None
    oraclehome=None
    oraclebase=None

    if 'sid' in kwargs.keys():
        oraclesid=kwargs['sid']
    elif 'SID' in kwargs.keys():
        oraclesid=kwargs['SID']
    else:
        return({'RESULT':1,'STDOUT':None,'STDERR':None,'REASON':'Nothing passed for sid='})

    if 'home' in kwargs.keys():
        oraclehome=kwargs['home']

    if 'user' in kwargs.keys():
        oracleuser=kwargs['user']

    if 'base' in kwargs.keys():
        oraclebase=kwargs['base']

    current=getArchiveLogging(sid=oraclesid)
    if current['RESULT'] > 0:
       return({'RESULT':1,'STDOUT':current['STDOUT'],'STDERR':current['STDERR'],'REASON':current['REASON']})
    elif current['ENABLED'] == True:
       out=stopOracleInstance(sid=oraclesid,home=oraclehome,user=oracleuser,base=oraclebase)
       if out['RESULT'] > 0:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=startOracleInstance(sid=oraclesid,home=oraclehome,user=oracleuser,base=oraclebase,method='mount')
       if out['RESULT'] > 0:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=doSqlplus(oraclesid,'alter database noarchivelog;',user=oracleuser,home=oraclehome)
       if out['RESULT'] > 0 or out['ERRORFLAG'] > 1:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       out=doSqlplus(oraclesid,'alter database open;',user=oracleuser,home=oraclehome)
       if out['RESULT'] > 0 or out['ERRORFLAG'] > 1:
          return({'RESULT':1,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
       return({'RESULT':0,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'REASON':out['REASON']})
    else:
       return({'RESULT':0,'STDOUT':current['STDOUT'],'STDERR':current['STDERR'],'REASON':current['REASON']})
