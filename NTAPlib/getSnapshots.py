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

class getSnapshots:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.name=None
        self.volumematch=[]
        self.volumes=[]
        self.snapshots={}
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'volumes' in kwargs.keys():
            if type(kwargs['volumes']) is str:
                self.volumematch=[kwargs['volumes']]
            else:
                try:
                    newlist=list(kwargs['volumes'])
                except:
                    print("Error: 'volumes' passed to getSnapshots with illegal type")
                    sys.exit(1)
                for item in newlist:
                    self.volumematch.append(item)
        else:
            self.volumematch='*'
        
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
        self.cgrestargs='fields=snapshot_volumes.volume.name,' + \
                        'snapshot_volumes.volume.uuid,' + \
                        'snapshot_volumes.snapshot.uuid' + \
                        '&svm.name=' + self.svm
        
        self.volapi='/storage/volumes/*/snapshots'
        self.volrestargs='fields=uuid,' + \
                         'name,' + \
                         'create_time,' + \
                         'snapmirror_label,' + \
                         '&svm.name=' + self.svm


        if self.name is not None:
            if type(self.name) is str:
                self.volrestargs=self.volrestargs + '&name='+ self.name                 
            else:
                self.volrestargs=self.volrestargs + '&name='+ '|'.join(self.name)               

        if self.debug & 1:
            userio.message("Retriving volumes on " + self.svm,service=localapi + ":OP")
            userio.message("Volume search list: " + ','.join(self.volumematch),service=localapi + ":OP")
        matchingvolumes=getVolumes(self.svm,volumes=self.volumematch,apicaller=localapi,debug=self.debug)
        if not matchingvolumes.go():
            self.result=1
            self.reason=matchingvolumes.reason
            self.stdout=matchingvolumes.stdout
            self.stderr=matchingvolumes.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            self.volumes=list(matchingvolumes.volumes.keys())

        if len(self.volumes) == 0:
            self.result=1
            self.reason="No matching volumes"
            return(False)

        if self.debug & 1:
            userio.message("Retriving CG data on " + self.svm,service=localapi + ":OP")
        cgs=getCGs(self.svm,volumes=self.volumes,apicaller=localapi,debug=self.debug)

        if cgs.go():
            self.cgs=cgs.cgs
            cgsnaps=[]
            for cgname in self.cgs.keys():
                nextapi=self.cgapi.replace('{UUID}',self.cgs[cgname]['uuid'])
                if self.debug & 1:
                    userio.message("Retriving CG snapshots for CG " + cgname,service=localapi + ":OP")
                rest=doREST.doREST(self.svm,'get',nextapi,restargs=self.cgrestargs,debug=self.debug)
                if rest.result == 200:
                    for record in rest.response['records']:
                        for subrecord in record['snapshot_volumes']:
                            volume=subrecord['volume']['name']
                            voluuid=subrecord['volume']['uuid']
                            snapuuid=subrecord['snapshot']['uuid']
                            cgsnaps.append((volume,voluuid,snapuuid))
                else:
                    self.result=1
                    self.reason=rest.reason
                    self.stdout=rest.stdout
                    self.stderr=rest.stderr
                    if self.debug & 4:
                        self.showDebug()
                    return(False)
        else:
            self.result=1
            self.reason=cgs.reason
            self.stdout=cgs.stdout
            self.stderr=cgs.stderr
            if self.debug & 4:
                self.showDebug()
            return(False)

        for volmatch in self.volumes:
            if volmatch not in self.snapshots.keys():
                self.snapshots[volmatch]={'snapshots':{},'recent':{},'uuid':matchingvolumes.volumes[volmatch]['uuid']}
            if self.debug & 1:
                userio.message("Retrieving snapshots for " + self.svm + ":" + volmatch,service=localapi + ":OP")
            rest=doREST.doREST(self.svm,'get',self.volapi,restargs=self.volrestargs + '&volume.name=' + volmatch,debug=self.debug)
            if rest.result == 200:
                for record in rest.response['records']:
                    uuid=record['uuid']
                    name=record['name']
                    volume=record['volume']['name']
                    voluuid=record['volume']['uuid']
                    createtime=record['create_time']
                    if ((volume,voluuid,uuid)) not in cgsnaps:
                        if createtime[-3] == ':':
                            fmttime=createtime[:-3] + createtime[-2:]
                        fmttime=fmttime.replace('T',' ',1)
                        epoch=datetime.datetime.strptime(fmttime,'%Y-%m-%d %H:%M:%S%z').timestamp()
    
                        self.snapshots[volume]['snapshots'][name]={'createtime':createtime,
                                                                   'epoch':epoch,
                                                                   'date':fmttime,
                                                                   'uuid':uuid}
                recent=0
                preordered=[]
                for name in self.snapshots[volmatch]['snapshots'].keys():
                    if self.snapshots[volmatch]['snapshots'][name]['epoch'] > recent:
                        preordered.append((name,self.snapshots[volmatch]['snapshots'][name]['epoch']))
                        recent=self.snapshots[volmatch]['snapshots'][name]['epoch']
                        self.snapshots[volmatch]['recent'] = name
                self.snapshots[volmatch]['ordered']=sorted(preordered, reverse=True, key=lambda x: int(x[1]))
                if self.debug & 1:
                    snaplist=[['Name','Date']]
                    for name,time in self.snapshots[volmatch]['ordered']:
                        snaplist.append([name,self.snapshots[volmatch]['snapshots'][name]['date']])
                    userio.grid(snaplist,service=localapi + ":DATA")
                    userio.message("Total matches: " + str(len(snaplist)-1),service=localapi + ":DATA")
            else:
                self.result=1
                self.reason=rest.reason
                self.stdout=rest.stdout
                self.stderr=rest.stderr
                if self.debug & 4:
                    self.showDebug()
                return(False)


        self.result=0
        if self.debug & 4:
            self.showDebug()
        return(True)
