import doREST
import re
import userio

class getSnapmirror:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.volumes=[]
        self.snapmirror=None
        self.snapmirrorSources={}
        self.snapmirrorDestinations={}
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/snapmirror/relationships'
        self.restargs='fields=uuid,' + \
                      'state,' + \
                      'destination.path,' +  \
                      'destination.svm.name,' +  \
                      'destination.svm.uuid,' +  \
                      'source.path,' + \
                      'source.svm.name,' +  \
                      'source.svm.uuid'
        
        self.restargs=self.restargs + '&query_fields=source.svm.name,destination.svm.name' + \
                                      '&query=' + svm

        if 'volumes' in kwargs.keys():
            if type(kwargs['volumes']) is str:
                self.volumes=[kwargs['volumes']]
            else:
                self.volumes=kwargs['volumes']

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

        return
    
    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.debug & 1:
            userio.message("Retrieving Snapmirror destinations on " + self.svm,service=localapi + ":OP")
            if len(self.volumes) > 0:
                userio.message("Volume search list: " + ','.join(self.volumes),service=localapi)
        rest=doREST.doREST(self.svm,'get',self.api,restargs=self.restargs,debug=self.debug)
        if rest.result == 200:
            for record in rest.response['records']:
                uuid=record['uuid']
                srcsvm,srcvol=record['source']['path'].split(':')
                dstsvm,dstvol=record['destination']['path'].split(':')

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
                        # elif re.findall(r'[?*.^$]',pattern):
                        #     try:
                        #         volpatternmatch=re.compile(pattern)
                        #     except:
                        #         self.result=1
                        #         self.reason="Illegal volume name match"
                        #         return(False)
                        # else:
                        #     volpatternmatch=re.compile('^' + pattern + '$')

                        if re.findall(regex,srcvol) or re.findall(regex,dstvol):
                            volumematch = True
                            break
                else:
                    volumematch=True
                
                if volumematch and (srcsvm == self.svm or dstsvm == self.svm):
                    state=record['state']
    
                    if srcsvm not in self.snapmirrorSources.keys():
                        self.snapmirrorSources[srcsvm]={'volumes':{},
                                                        'uuid':record['source']['svm']['uuid']}
                    if dstsvm not in self.snapmirrorDestinations.keys():
                        self.snapmirrorDestinations[dstsvm]={'volumes':{},
                                                             'uuid':record['destination']['svm']['uuid']}
    
                    if srcvol not in self.snapmirrorSources[srcsvm]['volumes'].keys():
                        self.snapmirrorSources[srcsvm]['volumes'][srcvol]=[]
                   
                    if dstvol not in self.snapmirrorDestinations[dstsvm]['volumes'].keys():
                        self.snapmirrorDestinations[dstsvm]['volumes'][dstvol]=[]
    
                    self.snapmirrorSources[srcsvm]['volumes'][srcvol].append({'volume':dstvol,
                                                                             'state':state,
                                                                             'svmuuid':record['destination']['svm']['uuid'],
                                                                             'svm':dstsvm})
                    
                    self.snapmirrorDestinations[dstsvm]['volumes'][dstvol].append({'volume':srcvol,
                                                                                  'state':state,
                                                                                  'svmuuid':record['source']['svm']['uuid'],
                                                                                  'svm':srcsvm})

            if self.debug & 1:
                matches=[['Source','Destination','State']]
                sourcesvms=list(self.snapmirrorSources.keys())
                sourcesvms.sort()
                for svm in sourcesvms:
                    sourcevols=self.snapmirrorSources[svm]['volumes'].keys()
                    for vol in sourcevols:
                        for dest in self.snapmirrorSources[svm]['volumes'][vol]:
                            matches.append([svm + ":" + vol, 
                                           dest['svm'] + ":" + dest['volume'],
                                           dest['state']])
                userio.grid(matches,service=localapi + ":DATA")
                userio.message("Total matches: " + str(len(matches)-1),service=localapi+ ":DATA")

            self.result=0
            if self.debug & 4:
                self.showDebug()
            return(True)
        else:
            self.result=1
            self.reason=rest.reason
            self.stdout=rest.stdout
            self.stderr=rest.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)

