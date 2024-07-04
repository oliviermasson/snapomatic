import doREST
import sys
import userio
import re

class getVolumes:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.volumes={}
        self.volmatch='*'
        self.debug=False
        self.volumesmatch={}
        
        self.api='/storage/volumes'
        self.restargs='fields=uuid,' + \
                        'size,' + \
                        'svm.name,' + \
                        'svm.uuid,' + \
                        'nas.path,' + \
                        'aggregates,' + \
                        'type'
        
        
        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller'] 
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
    
        if 'volumes' in kwargs.keys():
            if type(kwargs['volumes']) is str:
                self.restargs=self.restargs + "&name=" + kwargs['volumes']
                self.volmatch=kwargs['volumes']
            elif type(kwargs['volumes']) is list:
                self.restargs=self.restargs + "&name=" + '|'.join(kwargs['volumes'])
                self.volmatch=','.join(kwargs['volumes'])
            else:
                self.volumes=kwargs['volumes']

        self.restargs=self.restargs + "&svm.name=" + svm

        if 'cache' in kwargs.keys():
            self.cache=True
            store=kwargs['cache']
        else:
            self.cache=False

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.debug & 1:
            userio.message("Retrieving volumes on " + self.svm,service=localapi + ":OP")
            if self.volmatch is not None:
                userio.message("Volume search list: " + self.volmatch,service=localapi + ":OP")

        rest=doREST.doREST(self.svm,'get',self.api,restargs=self.restargs,debug=self.debug)
        if rest.result == 200:
            for record in rest.response['records']:
                svmname=record['svm']['name']
                if not svmname == self.svm:
                    sys.stderr.write("svm name mismatch in getVolumes")
                    sys.exit(1)
                svmuuid=record['svm']['uuid']
                name=record['name']
                uuid=record['uuid']
                aggrs=[]
                for item in record['aggregates']:
                    aggrs.append(item['name'])
                aggrs.sort()
                aggrlist=','.join(aggrs)

                volumematch=False
                if len(self.volumes) > 0:
                    for pattern in self.volumes:
                        if pattern == '*':
                            volumematch=True
                            break
                        protected_groups = {}
                        def protect_group(match):
                            placeholder = f"\0{len(protected_groups)}\0"
                            protected_groups[placeholder] = match.group(0)
                            return placeholder

                        pattern = re.sub(r'\([^)]*\)', protect_group, pattern)
                        pattern = pattern.replace('*', '.*')
                        for placeholder, original in protected_groups.items():
                            pattern = pattern.replace(placeholder, original)
                        regex = re.compile(pattern)
                        if re.findall(regex,name):
                            volumematch = True
                            break
                else:
                    volumematch=True

                if self.debug & 1:
                    userio.message("Found volume " + name,service=localapi + ":OP")
                if volumematch:
                    self.volumesmatch[name]={'uuid':uuid,
                                        'size':record['size'],
                                        'aggrs':aggrlist,
                                        'svm':{'name':svmname,'uuid':svmuuid},
                                        'type':record['type']}

                    try:
                        self.volumesmatch[name]['junction-path']=record['nas']['path']
                    except:
                        self.volumesmatch[name]['junction-path']=None
        else:
            self.result=1
            self.reason=rest.reason
            return(False)


        if self.result == 1:
            self.result=1
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            self.result=0
            if self.debug & 1:
                self.showDebug()
            return(True)

