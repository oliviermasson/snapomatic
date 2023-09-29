import doREST

class breakSnapmirror:

    def __init__(self,addr,smvolumes,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.broken={}
        self.failed={}

        if type(smvolumes) is str:
            smvolumes=[smvolumes]

        
        api='/snapmirror/relationships'
        restargs={'fields':'uuid,' +
                           'state,' +
                           'destination.path,' + 
                           'source.path'}
    
        rest=doREST.doREST(addr,'get',api,restargs,**kwargs)
        if rest.result == 0:
            for record in rest.response['records']:
                uuid=record['uuid']
                srcsvm,srcvol=record['source']['path'].split(':')
                dstsvm,dstvol=record['destination']['path'].split(':')
                state=record['state']

                if srcsvm not in self.snapmirrorSources.keys():
                    self.snapmirrorSources[srcsvm]={'volumes':{}}
                if dstsvm not in self.snapmirrorDestinations.keys():
                    self.snapmirrorDestinations[dstsvm]={'volumes':{}}

                self.snapmirrorSources[srcsvm]['volumes'][srcvol]={'state':state}
                self.snapmirrorDestinations[dstsvm]['volumes'][dstvol]={'state':state,
                                                                        'uuid':uuid}

            self.result=0
        else:
            self.result=1
            self.reason=rest.reason
                    
        return

