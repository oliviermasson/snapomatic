import os
import subprocess
import pwd
import grp
import signal
import sys
import userio

def signal2exit(signum, frame):
    sys.exit(0)


def execute(self,**kwargs):
    passkwargs = {'stdin': subprocess.PIPE,
                  'stdout': subprocess.PIPE,
                  'stderr': subprocess.PIPE,
                  'shell': False}
    retryable = False
    showchange = False
    tryagain = True
    trapsignals = False
    returndict = {}

    if self.user is not None:
        passkwargs['preexec_fn'] = changeUser(self.user, showchange=False)
        if self.debug & 8:
            userinfo = pwd.getpwnam(self.user)
            newuid = userinfo.pw_uid
            newgid = userinfo.pw_gid
            grouplist = [newgid]
            allgroups = grp.getgrall()
            for item in allgroups:
                if self.user in item[3]:
                    grouplist.append(item[2])
            userio.message("---> Changing GID to " + str(newgid),service='doProcess.execute:USER')
            userio.message("---> Changing group memberships to " + str(grouplist),service='doProcess.execute:USER')
            userio.message("---> Changing user to " + self.user,service='doProcess.execute:USER')

    if 'retry' in kwargs.keys():
        retryable = kwargs['retry']

    if self.cwd is not None:
        passkwargs['cwd'] = self.cwd

    if self.env is not None:
        passkwargs['env'] = self.env

    if 'trapsignals' in kwargs.keys():
        signal.signal(signal.SIGINT, signal2exit)

    while tryagain:
        tryagain = False
        self.stdout = []
        self.stderr = []
        self.result = None

        if self.debug & 8:
            userio.message(str(self.cmd),service='doProcess.execute:EXEC')
            userio.message(str(passkwargs['env']),service='doProcess.execute:ENV')
            if len(self.stdin) > 0:
                userio.message(self.stdin[self.startblock:],service='doProcess.execute:STDIN')

        try:
            cmd = subprocess.Popen(self.cmd, **passkwargs, encoding=self.encoding)
        except Exception:
            self.result = 1

        if self.result is None:
            if self.stdin is not None:
                cmds=''
                for line in self.stdin:
                    cmds=cmds + line
                cmdout, cmderr = cmd.communicate(input=cmds)
            else:
                cmdout, cmderr = cmd.communicate()

            if self.binary:
                self.stdout = cmdout
                self.stderr = cmderr
            else:
                lines = cmdout.splitlines()
                self.stdout=[]
                self.stderr=[]
                for line in lines:
                    if len(line) > 0:
                        self.stdout.append(line)
                lines = cmderr.splitlines()
                for line in lines:
                    if len(line) > 0:
                        self.stderr.append(line)
            self.result = cmd.returncode
    if self.debug & 8 and not self.binary:
        if len(self.stdout) > 0:
            for line in self.stdout:
                userio.message(str(line).rstrip(),service='doProcess.execute:STDOUT')
        if len(self.stdout) > 0:
            for line in self.stderr:
                userio.message(str(line).rstrip(),service='doProcess.execute:STDERR')

def changeUser(user, **kwargs):
    if 'showchange' in kwargs.keys():
        showchange = kwargs['showchange']
    else:
        showchange = False
    userinfo = pwd.getpwnam(user)
    newuid = userinfo.pw_uid
    newgid = userinfo.pw_gid
    grouplist = [newgid]
    allgroups = grp.getgrall()
    for item in allgroups:
        if user in item[3]:
            grouplist.append(item[2])

    def set_ids():
        if showchange:
            userio.message("---> Changing GID to " + str(newgid))
        os.setgid(newgid)
        if showchange:
            userio.message("---> Changing group memberships to " + str(grouplist))
        os.setgroups(grouplist)
        if showchange:
            userio.message("---> Changing user to " + user)
        os.setuid(newuid)
    return set_ids

class doProcess():

    def showDebug(self):
        userio.debug(self)

    def __init__(self,command,**kwargs):
        mypath = "/bin:/usr/bin:/usr/local/bin"
        myldlibrarypath = "/lib"

        self.cmd=[]
        self.env=None
        self.result=None
        self.stdout=[]
        self.stderr=[]
        self.stdin=[]
        self.ssh=None
        self.user=None
        self.encoding='utf8'
        self.cwd=None
        self.binary=False
        self.env = {"PATH": mypath, "LD_LIBRARY_PATH": myldlibrarypath}
        self.startblock=0
         
        self.apibase=self.__class__.__name__


        if 'debug' in kwargs.keys():
            self.debug = kwargs['debug']
        else:
            self.debug=False

        if 'ssh' in kwargs.keys() and kwargs['ssh'] is not None:
            self.ssh=kwargs['ssh']

        if 'encoding' in kwargs.keys():
            self.encoding = kwargs['encoding']

        if 'stdin' in kwargs.keys():
            if type(kwargs['stdin']) is str:
                self.stdin=[kwargs['stdin']]
            else:
                self.stdin=kwargs['stdin']

        if self.ssh:
            self.cmd=["ssh",self.ssh,'']
        
        if 'env' in kwargs.keys():
            for key in kwargs['env'].keys():
                if key in self.env.keys():
                    self.env[key] = self.env[key]+":"+kwargs['env'][key]
                else:
                    self.env[key] = kwargs['env'][key]
                if self.ssh:
                    self.cmd[-1]=self.cmd[-1] + "export " + key + "=" + kwargs['env'][key] + ";"
        
        if type(command) is str:
            if self.ssh:
                self.cmd[-1]=self.cmd[-1] + command
            else:
                mylist = command.split(' ')
                for item in mylist:
                    self.cmd.append(item)
        elif type(command) is list:
            if  self.ssh:
                self.cmd[-1]=self.cmd[-1] + ' '.join(command)
            else:
                for item in command:
                    self.cmd.append(item)

        if 'cwd' in kwargs.keys():
            self.cwd=kwargs['cwd']

        if 'user' in kwargs.keys():
            self.user=kwargs['user']
            
        if 'binary' in kwargs.keys():
            self.binary=True
    
        if 'displaystdin' in kwargs.keys():
            self.startblock=kwargs['displaystdin']

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''

        
        execute(self)
