class getOratab:

    def __init__(self):
        self.result=None
        self.reason=None
        self.comments=[]
        self.sids={}

        try:
            lines=open('/etc/oratab','r').readlines()
        except:
            self.result=1
            self.reason='Unable to open /etc/oratab'
            return()

        for line in lines:
            if line[0] == '#':
                self.comments.append(line.rstrip())
            elif len(line) > 1:
                result=0
                try:
                    oraclesid,home,startup=line.rstrip().split(':')
                    self.sids[oraclesid]={'HOME':home,'STARTUP':startup}
                except:
                    self.result=1
                    self.reason='Unable to open /etc/oratab'
                    self.sids={}
                    self.comments=[]
