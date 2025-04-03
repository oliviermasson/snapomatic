import doSqlplus

class getOracleParameters:

    def __init__(self,**kwargs):
        params={}
        oraclehome=None
        oracleuser=None
        oraclebase=None
    
        if 'sid' in kwargs.keys():
            oraclesid=kwargs['sid']
        elif 'SID' in kwargs.keys():
            oraclesid=kwargs['SID']
        else:
            return({'RESULT':False,'REASON':'Oracle SID not passed','HOME':home,'STDOUT':None,'STDERR':None})
    
        if 'home' in kwargs.keys():
           oraclehome=kwargs['home']
    
        if 'user' in kwargs.keys():
           oracleuser=kwargs['user']
    
        if 'base' in kwargs.keys():
           oraclebase=kwargs['base']
    
        out=doSqlplus.doSqlplus(oraclesid,"select name||' '||value from v$parameter;",user=oracleuser,home=oraclehome,base=oraclebase)
        print(out.stdout)
        if not out.result == 0 or out.errorflag:
            self.result=1
            self.stdout=out.stdout
            self.stderr=out.stderr
            self.reason=out.reason
            return
        else:
           for line in out['STDOUT']:
               fields=line.split(' ',1)
               key=fields[0]
               if len(fields) == 1:
                   values=None
               else:
                   values=fields[1].split(', ')
               params[key]={'VALUE':values}
           return({'RESULT':0,'STDOUT':out['STDOUT'],'STDERR':out['STDERR'],'PARAMS':params,'REASON':out['REASON']})
