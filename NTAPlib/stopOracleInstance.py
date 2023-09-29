from doSqlplus import doSqlplus

class stopOracleInstance:

    def __init__(self,sid,**kwargs):
        self.result=None
        self.sid=sid
        self.reason=None
        self.stdout=None
        self.stderr=None
        self.shutdowntype='immediate'
        self.user=None
        self.home=None
        self.base=None
    
        if 'method' in kwargs.keys():
            self.shutdowntype=kwargs['method']
        
        cmd='shutdown ' + self.shutdowntype + ';'
    
        if 'home' in kwargs.keys():
            self.home=kwargs['home']
    
        if 'user' in kwargs.keys():
            self.user=kwargs['user']
        
        if 'base' in kwargs.keys():
            self.base=kwargs['base']

        out=doSqlplus(self.sid,cmd,user=self.user,home=self.home,base=self.base)
        if out.result > 0:
            self.result=1
            self.reason="SQLPLUS call failed"
            self.stdout=out.stdout
            self.stderr=out.stderr
            return
        else:
            for line in out.stdout:
                if line == 'ORACLE instance shut down.':
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return
            self.reason=1
            self.reason="Unable to confirm instance shutdown"
            self.stdout=out.stdout
            self.stderr=out.stderr
            return
