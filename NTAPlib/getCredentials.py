import json

class getCredential():

    def __init__(self,resourcetype,resourcename,**kwargs):
        self.resourcetype=resourcetype
        self.resourcename=resourcename
        self.mgmtaddr=None
        self.username=None
        self.password=None
        self.dataLIF=None
        self.uuid=None
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        debug=False
        self.log=None
    
        if 'debug' in kwargs.keys():
            debug=kwargs['debug']
            self.log=[]
    
        if 'config' in kwargs.keys():
            configFile=kwargs['config']
        else:
            import os
            if os.getenv("SNAPOMATIC_CREDENTIAL_PATH") is not None:
                configFile=os.getenv("SNAPOMATIC_CREDENTIAL_PATH")
            elif os.name=='posix':
                configFile='/etc/snapomatic/config.json'
            elif os.name=='nt':
                configFile='c:\snapomatic\config.json'
    
        try:
            lines=open(configFile).readlines()
            configjson=json.loads('\n'.join(lines))
            if self.resourcetype == 'ontap' and 'ontap' not in configjson.keys():
                self.result=1
                self.reason="No 'ontap' section detected in " + configFile
                return
            elif self.resourcetype == 'ontap' and 'svm' not in configjson['ontap'].keys():
                self.result=1
                self.reason="No 'ontap/svm' section detected in " + configFile
                return
            elif self.resourcetype == 'oracle' and 'oracle' not in configjson.keys():
                self.result=1
                self.reason="No 'oracle' section detected in " + configFile
                return
            elif self.resourcetype == 'oracle' and 'sid' not in configjson['oracle'].keys():
                self.result=1
                self.reason="No 'ontap/sid' section detected in " + configFile
                return
            else:
                if self.resourcetype=='ontap':
                    allsvms=[]
                    allmgmtaddrs=[]
                    for item in configjson['ontap']['svm']:
                        try:
                            nextsvm=item['name']
                            nextmgmt=item['managementLIF']
                        except:
                            self.result=1
                            self.reason="Missing name and/or managementLIF in configfile"
                            return
                        if nextsvm in allsvms:
                            self.result=1
                            self.reason="Duplicate SVM name " + nextsvm + " in configfile"
                            return
                        else:
                            allsvms.append(nextsvm)
                        if nextmgmt in allmgmtaddrs:
                            self.result=1
                            self.reason="Duplicate management address " + nextmgmt+ " in configfile"
                            return
                        else:
                            allmgmtaddrs.append(nextmgmt)
        
                    for item in configjson['ontap']['svm']:
                        if item['managementLIF'] == resourcename or item['name'] == resourcename or ('dataLIF' in item.keys() and resourcename in item['dataLIF'].split(',')):
                            if debug:
                                self.log.append("found entry for '" + resourcename + "' found in configFile")
                            try:
                                self.name=item['name']
                                self.username=item['username']
                                self.password=item['password']
                                self.mgmtaddr=item['managementLIF']
                                self.uuid=item['uuid']
                                if debug:
                                    self.log.append('username found in configFile')
                                    self.log.append('password found in configFile')
                                    self.log.append("management address '" + self.mgmtaddr + "' found in configFile")
                                self.error=0
                                self.result=0
                            except Exception as e:
                                self.result=1
                                self.reason="Corrupt 'ontap/svm' section detected in " + configFile
                                return
                            if 'dataLIF' in item.keys():
                                self.dataLIF=item['dataLIF'].split(',')
                            return
                elif self.resourcetype=='oracle':
                    allsids=[]
                    if len(configjson['oracle']['sid']) == 0:
                        self.result=1
                        self.reason="No ORACLE SIDs registered"
                        return
                    for item in configjson['oracle']['sid']:
                        try:
                            nextsid=item['name']
                            nextuser=item['username']
                            nextpwd=item['password']
                        except:
                            self.result=1
                            self.reason="Missing name, username, or password in configfile"
                            return
                        if nextsid in allsids:
                            self.result=1
                            self.reason="Duplicate SID " + nextsid + " in configfile"
                            return
                        else:
                            allsids.append(nextsid)

                    for item in configjson['oracle']['sid']:
                        if item['name'] == self.resourcename:
                            if debug:
                                self.log.append("found entry for '" + self.resourcename + "' found in configFile")
                            try:
                                self.name=item['name']
                                self.username=item['username']
                                self.password=item['password']
                                if debug:
                                    self.log.append('username found in configFile')
                                    self.log.append('password found in configFile')
                                self.error=0
                                self.result=0
                            except Exception as e:
                                self.result=1
                                self.reason="Corrupt 'oracle/sid' section detected in " + configFile
                                return

        except Exception as e:
            import sys
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.reason=str(exc_type) + " " + str(fname) + ", line " + str(exc_tb.tb_lineno)
            self.result=1
            return
