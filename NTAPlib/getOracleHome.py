import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import getOracleBase
import getOwner
import xmltodict
import doProcess
import userio

class getOracleHome:

    def getVersion(self,**kwargs):
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".getVersion"])

        if self.debug & 1:
            userio.message("Discovering ORACLE_HOME versions",service=localapi + ":OP")

        if self.installed is None:
            self.go(apicaller=localapi)

        if not len(self.installed) > 0:
            self.result=1
            self.reason="No valid ORACLE_HOME found"
            if self.debug & 1:
                self.showDebug()
            return(False)
        installedhomes=list(self.installed.keys())
        for home in installedhomes:
            versionout=doProcess.doProcess(home + '/bin/sqlplus -v',env={'ORACLE_HOME':home},debug=self.debug)
            if versionout.result == 0:
                release=None
                version=None
                for line in versionout.stdout:
                    if 'SQL*Plus: Release ' in line:
                        release=line.split()[2]
                        self.installed[home]['release']=release
                    elif 'Version ' in line:
                        version=line.split()[1]
                        self.installed[home]['version']=version
                if self.debug & 1:
                    userio.message("ORACLE_HOME " + home + " is release " + str(release) + " version " + str(version),service=localapi + ":DATA")

            else:
                del self.installed[home]
        if len(self.installed) > 0:
            self.result=0
            return(True)
        else:
            self.result=1
            self.reason="Unable to obtain version information for any ORACLE_HOME"
            if self.debug & 1:
                self.showDebug()
            return(False)

    def __init__(self,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.sid=None
        self.path='/etc/oratab'
        self.installed=None
        self.home=None
        self.base=None
        self.user=None
        self.olsnodes=None
        self.olslocal=None
        self.grid=False
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
    
        if 'oratab' in kwargs.keys():
            self.path=kwargs['oratab']
    
        if 'sid' in kwargs.keys():
            self.sid=kwargs['sid']
        elif 'SID' in kwargs.keys():
            self.sid=kwargs['SID']

        if 'grid' in kwargs.keys():
            self.grid=True

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.debug & 1:
            userio.message("Opening /etc/oraInst.loc",service=localapi + ":OP")
        try:
            orainst=open('/etc/oraInst.loc', 'r').read().splitlines()
        except:
            self.result=False
            self.reason="Unable to open /etc/oraInst.loc"
        else:   
            invdir=None
            for line in orainst:
                try:
                    arg,val=line.split('=')
                    if arg == 'inventory_loc':
                        invdir=val
                except Exception as e:
                    pass
            if invdir is None:
                self.reason="Unable to parse /etc/oraInst.loc"
            else:
                invXMLtext=open(invdir + "/ContentsXML/inventory.xml",'r').read()
                invXML=xmltodict.parse(invXMLtext)
                homes=[]
                gridhomes=[]
                homeXML = invXML['INVENTORY']['HOME_LIST']['HOME']
                if type(homeXML) is dict:
                    homeXML = [invXML['INVENTORY']['HOME_LIST']['HOME']]
                for item in homeXML:
                    if os.path.exists(item['@LOC'] + "/bin/oracle"):
                        if '@CRS' in item.keys() and item['@CRS'] == 'true':
                            if self.grid:
                                homes.append(item['@LOC'])
                                self.home=(item['@LOC'])
                                self.user=getOwner.getOwner(self.home + "/bin/oracle").user
                                if self.debug & 1:
                                    userio.message("Found installed GI HOME at " + self.home,service=localapi + ":DATA")
                                break
                            gridhomes.append(item['@LOC'])
                        elif 'agent' not in item['@NAME']:
                            if self.debug & 1:
                                userio.message("Found installed ORACLE_HOME at " + item['@LOC'],service=localapi + ":DATA")
                            homes.append(item['@LOC'])
                if len(homes) > 0:
                    self.installed={}
                    for home in homes:
                        base=getOracleBase.getOracleBase(home,apicaller=localapi,debug=self.debug)
                        if base.go() and (self.grid or home not in gridhomes):
                            self.installed[home]={'base':base.base,'user':base.user,'release':None,'version':None}
                if self.grid:
                    try:
                        self.base=self.installed[self.home]['base']
                    except:
                        self.result=1
                        self.reason="Unable to find ORACLE_BASE for Grid user"
                        if self.debug & 1:
                            self.showDebug()
                        return(False)


        if self.debug & 1:
            userio.message("Retrieving RAC node list",service=localapi + ":DATA")

        if self.grid:
            out=doProcess.doProcess([os.path.join(self.home,'bin','olsnodes'),'-n'],debug=self.debug)
            if out.result > 0 or len(out.stdout) < 1:
                self.result=1
                self.reason='Failed to run doProcess' + os.path.join(self.home,'bin','olsnodes')
                self.stdout=out.stdout
                self.stderr=out.stderr
                if self.debug & 1:
                    self.showDebug()
                return(False)
            else:
                olsnodes={}
                for line in out.stdout:
                    import platform
                    localhost=platform.node().split('.', 1)[0]
                    hostname,nodeID=line.split()
                    olsnodes[hostname]=nodeID
                    if hostname==localhost:
                        self.olslocal=nodeID

            out=doProcess.doProcess(self.home + '/bin/srvctl status asm', \
                                    env={'ORACLE_HOME':self.home,
                                         'ORACLE_BASE':self.base},
                                    user=self.user,
                                    debug=self.debug)
            if out.result > 0:
                self.result=1
                self.stdout=out.stdout
                self.stderr=out.stderr
                if self.debug & 1:
                    self.showDebug()
                return(False)
            else:
                for line in out.stdout:
                    if 'ASM is running on' in line:
                        self.olsnodes={}
                        nodes=line.split()[-1].split(',')
                        for node in nodes:
                            if node in olsnodes.keys():
                                self.olsnodes[node]=olsnodes[node]
                                if self.debug & 1:
                                    userio.message("RAC node " + node + " is active",service=localapi + ":DATA")
                self.result=0
                return(True)

        elif self.sid is not None:
            try:
                oratablines=open(self.path, 'r').read().splitlines()
                if self.debug:
                    userio.message("Scanning oratab for " + self.sid,service=localapi + ":OP")
            except:
                self.result=1
                self.reason="Unable to open oratab file at " + self.path 
                return(False)
            else:   
                for line in oratablines:
                    if ':' in line:
                        oratabfields = line.split(':')
                        if oratabfields[0] == self.sid:
                            home=oratabfields[1]
                            if os.path.exists(home + "/bin/oracle"):
                                baseout=getOracleBase.getOracleBase(home,apicaller=localapi,debug=self.debug)
                                if not baseout.go():
                                    self.result=1
                                    self.reason=baseout.reason
                                    self.stdout=baseout.stdout
                                    self.stderr=baseout.stderr
                                    return(False)
                                else:
                                    self.result=0
                                    self.home=home
                                    self.base=baseout.base
                                    self.user=baseout.user
                                    self.installed={home:{'base':self.base,
                                                          'version':None,
                                                          'release':None,
                                                          'user':self.user}}
                                    return(True)
            pids=os.listdir('/proc')
            for pid in pids:
                if pid.isdigit():
                    try:
                        cmdline=open(os.path.join('/proc',pid,'cmdline'),'rb').read().decode('utf-8').rstrip('x\00')
                        try:
                            if cmdline[:9] == 'ora_pmon_' and (cmdline[9:] == self.sid or cmdline[9:-1] == self.sid + "_"):
                                if cmdline[-2:] == '_1' or cmdline[-2:] == '_2':
                                    self.sid=cmdline[9:]
                                home=os.readlink(os.path.join('/proc',pid,'exe'))[:-11] 
                                base=getOracleBase.getOracleBase(home,apicaller=localapi,debug=self.debug)
                                if not base.go():
                                    self.result=1
                                    self.reason=base.reason
                                    self.stdout=base.stdout
                                    self.stderr=base.stderr
                                    return(False)
                                else:
                                    self.result=0
                                    self.home=home
                                    self.base=base.base
                                    self.user=base.user
                                    self.installed={home:{'base':self.base,
                                                          'version':None,
                                                          'release':None,
                                                          'user':self.user}}
                                    return(True)



                        except Exception as e1:
                            pass
                    except Exception as e2:
                        pass
            
            from doSrvctl import doSrvctl
            out=doSrvctl('config database',{'database':self.sid},apicaller=localapi,debug=self.debug)
            if out.result:
                self.result=1
                self.reason=out.reason
                self.stdout=out.stdout
                self.stderr=out.stderr
                return(False)
            else:
                results={}
                for line in out.stdout:
                    try:
                        one,two=line.split(':')
                        results[one]=two.lstrip().rstrip()
                    except:
                        pass
                if 'Database unique name' in results.keys() and results['Database unique name'] == self.sid:
                    self.result=0
                    self.home=results['Oracle home']
                    self.user=results['Oracle user']
                    self.sid=results['Database instances'].split(',')[0]
                    baseout=getOracleBase.getOracleBase(self.home,user=self.user)
                    if baseout.go():
                        self.base=baseout.base
                        self.installed={home:{'base':self.base,
                                              'version':None,
                                              'release':None,
                                              'user':self.user}}
                        return(True)
                    else:
                        self.result=1
                        self.home=None
                        self.user=None
                        self.reason=baseout.reason
                        return(False)

            self.result=1
            self.reason="Unable to locate ORACLE_HOME for " + self.sid
            return(False)
                
    def showDebug(self):
        userio.debug(self)

