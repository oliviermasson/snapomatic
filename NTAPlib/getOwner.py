import os
import pwd
import grp

class getOwner:

    def __init__(self,path,**kwargs):
        self.user=None
        self.group=None
        self.path=path
        self.result=None
        self.reason=None
        self.uid=None
        self.gid=None
    
        try:
            self.uid=os.stat(self.path).st_uid
            self.gid=os.stat(self.path).st_gid
            self.user=pwd.getpwuid(self.uid).pw_name
            self.group=grp.getgrgid(self.gid).gr_name
            self.result=0
        except Exception:
            self.result=1
            self.reason="Unable to get ownership for path " + str(self.path)
