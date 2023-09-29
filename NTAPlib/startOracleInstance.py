import doSqlplus

class startOracleInstance:

    def __init__(self,sid,**kwargs):
        self.sid=sid
        self.result=None
        self.reason=None
        self.stdout=None
        self.stderr=None
        self.startuptype=None
        self.user=None
        self.home=None
        self.base=None
    
        if 'home' in kwargs.keys():
            self.home=kwargs['home']
        
        if 'user' in kwargs.keys():
            self.user=kwargs['user']
        
        if 'base' in kwargs.keys():
            self.base=kwargs['base']
    
        if 'method' in kwargs.keys():
            self.startuptype=kwargs['method']

    
        if self.startuptype is None:
            cmd='startup;'
        else:
            cmd='startup ' + self.startuptype+ ';'

        out=doSqlplus.doSqlplus(self.sid,cmd,user=self.user,home=self.home,base=self.base)
        if out.result > 0:
            self.result=1
            self.reason="SQLPLUS call failed"
            self.stdout=out.stdout
            self.stderr=out.stderr
            return
        else:
            for line in out.stdout:
                if line == 'Database opened.' and self.startuptype=="":
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return
                elif line == 'Database mounted.' and self.startuptype=="mount":
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return
                elif line[-24:] == 'ORACLE instance started.' and self.startuptype=="mount":
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return

            self.result=1
            self.reason="Unable to confirm instance startup"
            self.stdout=out.stdout
            self.stderr=out.stderr
            return
