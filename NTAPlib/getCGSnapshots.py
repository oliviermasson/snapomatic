#
# CAUTION: if a name pattern match used, all snapshot operations are filted
#          for that pattern, including the recent snapshot
#
# snapshots.snapshots
#      = snapshots stored in dict based on volume name
#
# snapshots.snapshots[volume]['snapshots']
#      = dict of individual snapshot information using snapshot name as key
#
# snapshots.snapshots[volume]['snapshots'][name]['createtime']
#      = creation time as reported by ONTAP
#
# snapshots.snapshots[volume]['snapshots'][name]['date']
#      = creation time using normal python fmttime
#
# snapshots.snapshots[volume]['snapshots'][name]['uuid'] 
#      = uuid of snapshot
#
# snapshots.snapshots[volume]['snapshots'][name]['epoch']
#      = epoch seconds of snapshot
#
# snapshots.snapshots[volume]['recent'] 
#      = name of most recent snapshot on that volume
#
# snapshots.snapshots[volume]['uuid'] 
#      = volume UUID
#
import doREST
import datetime
import re
import sys
import userio
from getCGs import getCGs
from getVolumes import getVolumes

class getCGSnapshots:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.name=None
        self.cg=False
        self.cgs={}
        self.cghierarchy={}
        self.cgmatch=[]
        self.volumes=[]
        self.snapshots={}
        self.debug=False
        

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'cg' in kwargs.keys():
            self.cg=kwargs['cg']

        if 'cgs' in kwargs.keys():
            if type(kwargs['cgs']) is str:
                self.cgmatch=[kwargs['cgs']]
            else:
                try:
                    newlist=list(kwargs['cgs'])
                except:
                    print("Error: 'cgs' passed to getSnapshots with illegal type")
                    sys.exit(1)
                for item in newlist:
                    self.cgmatch.append(item)
        else:
            self.cgmatch='*'

        if 'name' in kwargs.keys() and kwargs['name'] is not None:
            self.name=kwargs['name']

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
        
        self.cgapi='/application/consistency-groups/{UUID}/snapshots'
        self.cgrestargs='fields=uuid,' + \
                        'name,' + \
                        'create_time,' + \
                        'snapshot_volumes.volume.name,' + \
                        'snapshot_volumes.volume.uuid,' + \
                        'snapshot_volumes.snapshot.name,' + \
                        'snapshot_volumes.snapshot.uuid,' + \
                        'snapmirror_label,' + \
                        '&svm.name=' + self.svm
        
        if self.name is not None:
            if type(self.name) is str:
                self.cgrestargs=self.cgrestargs + '&snapshot_volumes.snapshot.name='+ self.name                 
            else:
                self.cgrestargs=self.cgrestargs + '&snapshot_volumes.snapshot.name='+ '|'.join(self.name)               
        
        if self.debug & 1:
            userio.message("Retriving CG data on " + self.svm,service=localapi + ":OP")

        cgs=getCGs(self.svm,name=self.cgmatch,apicaller=localapi,debug=self.debug)
        if cgs.go():
            self.cgs=cgs.cgs
            for cgname in self.cgs.keys():
                if cgname not in self.snapshots.keys():
                    self.snapshots[cgname]={'snapshots':{},
                                            'volumes':{},
                                            'uuid':self.cgs[cgname]}
                nextapi=self.cgapi.replace('{UUID}',self.cgs[cgname]['uuid'])
                if self.debug & 1:
                    userio.message("Retriving CG snapshots for CG " + cgname,service=localapi + ":OP")
                rest=doREST.doREST(self.svm,'get',nextapi,restargs=self.cgrestargs,debug=self.debug)
                if rest.result == 200:
                    for record in rest.response['records']:
                        uuid=record['uuid']
                        name=record['name']
                        createtime=record['create_time']
                        if createtime[-3] == ':':
                            fmttime=createtime[:-3] + createtime[-2:]
                        fmttime=fmttime.replace('T',' ',1)
                        epoch=datetime.datetime.strptime(fmttime,'%Y-%m-%d %H:%M:%S%z').timestamp()
                        self.snapshots[cgname]['snapshots'][name]={'createtime':createtime,
                                               'epoch':epoch,
                                               'date':fmttime,
                                               'uuid':uuid}
                        for subrecord in record['snapshot_volumes']:
                            volume=subrecord['volume']['name']
                            voluuid=subrecord['volume']['uuid']
                            snapname=subrecord['snapshot']['name']
                            snapuuid=subrecord['snapshot']['uuid']
                            if volume not in self.snapshots[cgname]['volumes'].keys():
                                self.snapshots[cgname]['volumes'][volume]={'uuid':voluuid}
                            if self.debug & 1:
                                userio.message("Found snapshot " + volume + ":" + snapname + " on CG " + cgname,service=localapi + ":OP")
                else:
                    self.result=1
                    self.reason=rest.reason
                    self.stdout=rest.stdout
                    self.stderr=rest.stderr
                    if self.debug & 4:
                        self.showDebug()
                    return(False)

            for cgname in self.snapshots.keys():
                recent=0
                preordered=[]
                for name in self.snapshots[cgname]['snapshots'].keys():
                    if self.snapshots[cgname]['snapshots'][name]['epoch'] > recent:
                        preordered.append((name,self.snapshots[cgname]['snapshots'][name]['epoch']))
                        recent=self.snapshots[cgname]['snapshots'][name]['epoch']
                        self.snapshots[cgname]['recent'] = name
                self.snapshots[cgname]['ordered']=sorted(preordered, reverse=True, key=lambda x: int(x[1]))
                if self.debug & 1:
                    snaplist=[['Name','Date']]
                    for name,time in self.snapshots[cgname]['ordered']:
                        snaplist.append([name,self.snapshots[cgname]['snapshots'][name]['date']])
                    userio.grid(snaplist,service=localapi + ":DATA")
                    userio.message("Total matches: " + str(len(snaplist)-1),service=localapi + ":DATA")
        else:
            self.result=1
            self.reason=cgs.reason
            self.stdout=cgs.stdout
            self.stderr=cgs.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)
        return(True)

