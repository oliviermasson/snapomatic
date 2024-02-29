import requests
import urllib3
import os
import json
import userio
import time
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
        self.synchronous=False
        self.sleeptime=1
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

        if 'synchronous' in kwargs.keys():
            self.synchronous=kwargs['synchronous']

        if 'sleeptime' in kwargs.keys():
            self.sleeptime=kwargs['sleeptime']

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

        if response.ok and (self.result == 200 or (self.synchronous == False and self.result == 202)):
            try:
                convert2dict=response.json()
                self.result=0
                self.response=convert2dict
                return(True)
            except Exception as e:
                self.result=1
                self.reason=e
                return(False)
        elif response.ok and self.result == 202:
            tmpurl=self.url
            tmpjsonin=self.jsonin
            tmpapi=self.api
            tmprestargs=self.restargs
            tmpreqtype=self.reqtype
            tmpresponse=self.response
            self.jsonin=None
            try:
                convert2dict=response.json()
                jobuuid=convert2dict['job']['uuid']
            except:
                self.result=1
                self.reason="Unable to retrieve uuid for asynchronous operation"
                if self.debug & 2:
                    self.showDebug()
                return(False)
            
            running=True
            while running:
                time.sleep(self.sleeptime)
                self.api="/cluster/jobs/" + jobuuid
                self.url="https://" + self.mgmtaddr + "/api" + self.api
                self.restargs=["fields=state,message"]
                self.url=self.url + "?" + "&".join(self.restargs)
                self.call="GET " + self.url
        
                try:
                    jobrest=requests.get(self.url,auth=(username,password),verify=False)
                
                except Exception as e:
                    self.result=1
                    self.reason=str(e)
                    return(False)

                convert2dict=jobrest.json()
                self.jsonout=json.dumps(jobrest.json(),indent=1).splitlines()
                self.response=convert2dict
                self.result=jobrest.status_code
                self.reason=jobrest.reason
    
                if self.debug & 2:
                    self.showDebug()
                
                if not self.result == 200 or not self.response['state'] == 'running':
                    running=False
                
            if not self.result == 200:
                self.result=1
                self.reason="Job " + jobuuid + " failed"
                return(False)
            elif not self.response['state'] == 'success':
                self.result=1
                return(False)
            else:
                print("tock")
                self.result=0
                self.url=tmpurl
                self.jsonin=tmpjsonin
                self.api=tmpapi
                self.restargs=tmprestargs
                self.reqtype=tmpreqtype
                self.response=tmpresponse
                return(True)
                
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
    
