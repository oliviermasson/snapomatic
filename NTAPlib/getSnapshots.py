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

class getSnapshots:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.name=None
        self.cg=False
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

        if 'cg' in kwargs.keys():
            self.cg=kwargs['cg']

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
        
        self.api='/storage/volumes/*/snapshots'
        self.restargs='fields=uuid,' + \
                      'name,' + \
                      'create_time,' + \
                      'snapmirror_label,' + \
                      '&svm.name=' + self.svm


        if self.name is not None:
            if type(self.name) is str:
                self.restargs=self.restargs + '&name='+ self.name                 
            else:
                self.restargs=self.restargs + '&name='+ '|'.join(self.name)               

        print(self.cg)
        if self.cg:
            cgs=getCGs(self.svm,volumes=self.volumematch,apicaller=localapi,debug=self.debug)
            cgs.go()

        print(cgs.cgs)
        sys.exit(0)

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

        for volmatch in self.volumes:
            if volmatch not in self.snapshots.keys():
                self.snapshots[volmatch]={'snapshots':{},'recent':{},'uuid':matchingvolumes.volumes[volmatch]['uuid']}
            if self.debug & 1:
                userio.message("Retrieving snapshots for " + self.svm + ":" + volmatch,service=localapi + ":OP")
            rest=doREST.doREST(self.svm,'get',self.api,restargs=self.restargs + '&volume.name=' + volmatch,debug=self.debug)
            if rest.result == 0:
                for record in rest.response['records']:
                    uuid=record['uuid']
                    name=record['name']
                    volume=record['volume']['name']
                    voluuid=record['volume']['uuid']
                    voluuid=record['volume']['uuid']
                    createtime=record['create_time']
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
