import requests
import urllib3
import os
import json
import userio
urllib3.disable_warnings()

headers = {'content-type': "application/json",
           'accept': "application/json"}

class doREST():

    def __init__(self,svm,reqtype,api,**kwargs):

        self.mgmtaddr=svm
        self.reqtype=reqtype
        self.api=api
        self.restargs=None
        self.json=None
        self.url=None
        self.result=None
        self.reason=None
        self.response=None
        self.stdout=[]
        self.stderr=[]
        self.debug=0
        username=None
        password=None

        self.apibase=self.__class__.__name__

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''

        if os.getenv("SNAPOMATIC_CREDENTIAL_PATH") is not None:
            configFile=os.getenv("SNAPOMATIC_CREDENTIAL_PATH")
        elif os.name=='posix':
            configFile='/etc/snapomatic/config.json'
        elif os.name=='nt':
            configFile='c:\snapomatic\config.json'

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if 'username' in kwargs.keys():
            username=kwargs['username']
            try:
                password=kwargs['password']
            except Exception as e:
                self.result=1
                self.reason="Failed to supply password with username"
                self.stdout=None
                self.stderr=None
                return
        else:
            if 'config' in kwargs.keys():
                configFile=kwargs['config']
                if not os.path.isfile(self.configFile):
                    self.result=1
                    self.reason="Path to configfile does not exist"
                    self.stdout=None
                    self.stderr=None
                    return

            import getCredentials
            credential=getCredentials.getCredential('ontap',svm,debug=self.debug)
            if credential.result == 0:
                self.mgmtaddr=credential.mgmtaddr
            else:
                self.result=1
                self.reason="Unable to get credentials for " + svm 
                self.stdout=credential.stdout
                self.stderr=credential.stderr
                return
 
        if 'restargs' in kwargs.keys():
            if type(kwargs['restargs']) is list:
                self.restargs=kwargs['restargs']
            elif type(kwargs['restargs']) is str:
                self.restargs=[kwargs['restargs']]
            elif type(kwargs['restargs']) is tuple:
                self.restargs=[str(''.join(kwargs['restargs']))]

        if 'json' in kwargs.keys():
            self.json=kwargs['json']

        if username is not None:
            self.go(username,password,authtype='pass')
        elif credential.username is not None:
            self.go(credential.username,credential.password,authtype='pass')
        elif credential.cert is not None:
            self.go(credential.cert,credential.key,authtype='pass')

    def showDebug(self):
        userio.debug(self)

    def go(self,username,password,**kwargs):
        self.url="https://" + self.mgmtaddr + "/api" + self.api
        if self.restargs is not None:
            self.url=self.url + "?" + "&".join(self.restargs)
        self.call=self.reqtype.upper() + " " + self.url
        self.jsonin=str(self.json)

        try:
            if self.reqtype=="get":
                response=requests.get(self.url,auth=(username,password),verify=False)
            elif self.reqtype=="post":
                response=requests.post(self.url,auth=(username,password),json=self.json,verify=False,headers=headers)
            elif self.reqtype=="patch":
                response=requests.patch(self.url,auth=(username,password),json=self.json,verify=False)
            elif self.reqtype=="delete":
                response=requests.delete(self.url,auth=(username,password),verify=False)
            else:
                self.result=1
                self.reason="Unsupported request type"
                return(False)
        
        except Exception as e:
            self.result=1
            self.reason=str(e)
            return(False)
        
        self.jsonout=json.dumps(response.json(),indent=1).splitlines()

        self.result=response.status_code
        self.reason=response.reason
        self.response=response.text
        
        if self.debug & 2:
            self.showDebug()
    
        if response.ok:
            try:
                convert2dict=response.json()
                self.result=0
                self.response=convert2dict
                return(True)
            except Exception as e:
                self.result=1
                self.reason=e
                return(False)
        else:
            self.result=response.status_code
            self.reason=response.reason
            self.response=response.text
            try:
                convert2dict=response.json()
                self.response=convert2dict
            except:
                pass
            return(False)
    
