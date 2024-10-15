import doSqlplus

class getArchiveLogging:

    def __init__(self,sid,**kwargs):
        self.result=None
        self.reason=None
        self.home=None
        self.user=None
        self.base=None
        self.sid=sid
        self.stdout=[]
        self.stderr=[]
        self.enabled=None
        self.paths=[]
    
        if 'home' in kwargs.keys():
            self.home=kwargs['home']
    
        if 'user' in kwargs.keys():
            self.user=kwargs['user']
    
        if 'base' in kwargs.keys():
            self.base=kwargs['base']
    
        out=doSqlplus.doSqlplus(self.sid,"archive log list;",user=self.user,home=self.home,base=self.base)
        if not out.result == 0 or out.errorflag:
            self.result=1
            self.reason=out.reason
            self.stdout=out.stdout
            self.stderr=out.stderr
            return
        else:
            for line in out.stdout:
                if line[:17] == 'Database log mode':
                    if line.split()[3].rstrip() + line.split()[4].rstrip() == "ArchiveMode":
                        self.enabled=True
                    elif line.split()[3].rstrip() + line.split()[4].rstrip() == "NoArchive":
                        self.enabled=False
                elif line[:19] == 'Archive destination':
                    self.paths.append(line.split()[2].rstrip())
                result=0

