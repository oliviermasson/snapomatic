class updateOratab:

    def __init__(self,action,sid,*args):
        self.result=None
        self.reason=None
        self.stdout=None
        self.stderr=None
        self.home=None
        self.sid=sid
        self.action=action

        if self.action == 'remove':
            if not len(args) == 0:
                self.result=1
                self.reason="Removing a SID requires only 'remove' and the SID"
                return
        elif self.action == 'add':
            if not len(args) == 1:
                self.result=1
                self.reason="Adding a SID requires only 'add', the SID, and the ORACLE_HOME"
                return
            else:
                self.home=args[0]
        else:
            self.result=1
            self.reason="Invalid oratab operation: " + action
            return

        neworatab=[]
        sidlist=[]
    
        try:
            lines=open('/etc/oratab','r').readlines()
        except:
            self.result=1
            self.reason="Unable to open /etc/oratab"
            return

        for line in lines:
            if line[0] == '#':
                neworatab.append(line.rstrip())
            elif len(line) < 2:
                neworatab.append(line.rstrip())
            else:
                try:
                    oraclesid,home,startup=line.rstrip().split(':')
                    sidlist.append(oraclesid)
                    if action == 'add' and oraclesid == self.sid:
                        self.result=1
                        self.reason="SID " + self.sid + " already exists in oratab"
                        return
                    elif action == 'remove' and oraclesid == self.sid:
                        pass
                    else:
                        neworatab.append(line.rstrip())
                except Exception as e:
                    self.result=1
                    self.reason='Unable to parse /etc/oratab'
                    return

        if action == 'remove' and self.sid not in sidlist:
            self.result=1
            self.reason="SID " + self.sid + " does not exist in oratab"
            return

        if action == 'add':
            neworatab.append(':'.join([self.sid,self.home,'N']))

        try:
            newfile=open('/etc/oratab','w')
            for line in neworatab:
                newfile.write(line + "\n")
            newfile.close()
            self.result=0
        except:
            self.result=1
            self.reason='Unable to open /etc/oratab for writing'
