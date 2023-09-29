import doREST
import datetime
import time
import re
import sys
import userio
from getSnapshots import getSnapshots

class deleteSnapshots:

    def __init__(self,svm,volumes,snapshots,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.volumematch=[]
        self.snapshotmatch=snapshots
        self.maxage=False
        self.maxcount=False
        self.debug=False
        self.deleted={}
        self.force=False
        self.failed={}
        self.snapshots2delete=[]

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        if type(volumes) is str:
            self.volumematch=[volumes]
        else:
            try:
                newlist=list(volumes)
            except:
                print("Error: 'volumes' passed to createSnapshots with illegal type")
                sys.exit(1)
            for item in newlist:
                self.volumematch.append(item)

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
        
        if 'force' in kwargs.keys():
            self.force=kwargs['force']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

        if 'maxage' in kwargs.keys() and type(kwargs['maxage']) is str:
            if kwargs['maxage'][-1].upper() == 'D':
                self.maxage=int(kwargs['maxage'][:-1])*24*60*60
                if self.debug & 1:
                    userio.message("Max age is days, value is " + str(self.maxage),service=localapi + ":OP")
            elif kwargs['maxage'][-1].upper() == 'H':
                self.maxage=int(kwargs['maxage'][:-1])*60*60
                if self.debug & 1:
                    userio.message("Max age is hours, value is " + str(self.maxage),service=localapi + ":OP")
            elif kwargs['maxage'][-1].upper() == 'M':
                self.maxage=int(kwargs['maxage'][:-1])*60
                if self.debug & 1:
                    userio.message("Max age is minutes, value is " + str(self.maxage),service=localapi + ":OP")
            elif kwargs['maxage'][-1].upper() == 'S':
                self.maxage=int(kwargs['maxage'][:-1])
                if self.debug & 1:
                    userio.message("Max age is seconds, value is " + str(self.maxage),service=localapi + ":OP")
            else:
                print("Illegal maxage passed")
                sys.exit(1)
            if self.debug & 1:
                userio.message("Snapshot age limit set at " + kwargs['maxage'])


        if 'maxcount' in kwargs.keys() and type(kwargs['maxcount']) is int:
            self.maxcount=kwargs['maxcount']
            if self.debug & 1:
                userio.message("Snapshot count limit set at " + str(kwargs['maxcount']))

    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):

        now=time.time()
        self.result=0
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        if self.debug & 1:
            userio.message("Retriving snapshots for " + ','.join(self.volumematch),service=localapi + ":OP")
        snapshots=getSnapshots(self.svm,volumes=self.volumematch,name=self.snapshotmatch,apicaller=localapi,debug=self.debug)
        if not snapshots.go():
            self.result=1
            self.reason=snapshots.reason
            self.stdout=snapshots.stdout
            self.stderr=snapshots.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            vollist=list(snapshots.snapshots.keys())
            vollist.sort()
            for volume in vollist:
                volsnapshots2delete=[]
                voluuid=snapshots.snapshots[volume]['uuid']
                snaplist=list(snapshots.snapshots[volume]['snapshots'].keys())
                snaplist.sort()
                for snap in snaplist:
                    snapuuid=snapshots.snapshots[volume]['snapshots'][snap]['uuid']
                    epoch=snapshots.snapshots[volume]['snapshots'][snap]['epoch']
                    if self.maxage:
                        if now - epoch > self.maxage:
                            if self.debug & 1:
                                userio.message("Snapshot " + volume + ":" + snap + " exceeds max age",service=localapi + ":OP")
                            volsnapshots2delete.append((volume,voluuid,snap,snapuuid,epoch))
                    else:
                        volsnapshots2delete.append((volume,voluuid,snap,snapuuid,epoch))
            
                volsnapshots2delete.sort(key=lambda x: x[4], reverse=True)
                
                if len(volsnapshots2delete) > 0 and not self.force and (self.snapshotmatch == '*' or self.snapshotmatch is None):
                    del volsnapshots2delete[0]
                    if self.debug & 1:
                        userio.message("Blocking deletion of last snapshot on " + volume ,service=localapi + ":OP")

                if self.maxcount:
                    if self.debug & 1:
                        userio.message("Limiting snapshots on volume " + volume + " to " + str(self.maxcount),service=localapi + ":OP")
                    if len(volsnapshots2delete) > self.maxcount:
                        volsnapshots2delete=volsnapshots2delete[self.maxcount:]
                    else:
                        volsnapshots2delete=[]

                for item in volsnapshots2delete:
                    self.snapshots2delete.append(item)

            for vol, voluuid, snap, snapuuid, epoch in self.snapshots2delete:
                rest=doREST.doREST(self.svm, \
                                   'delete', \
                                   '/storage/volumes/' + voluuid + '/snapshots/' + snapuuid + '?return_timeout=60', \
                                   debug=self.debug)

                if rest.result == 0 and rest.reason=='OK':
                    if vol in self.deleted.keys():
                        self.deleted[vol].append(snap)
                    else:
                        self.deleted[vol]=[snap]
                    if self.debug & 1:
                        userio.message("Deleted snapshot " + snap + " on volume " + vol,service=localapi + ":OP")
                else:
                    if self.debug & 1:
                        userio.message("Failed to delete snapshot " + snap + " on volume " + vol,service=localapi + ":OP")
                    if vol in self.failed.keys():
                        self.failed[vol].append(snap)
                    else:
                        self.failed[vol]=[snap]
                    self.result=1
                    self.reason=rest.reason
                    self.stdout=rest.stdout
                    self.stderr=rest.stderr
                    if self.debug & 4:
                        self.showDebug()

        if self.debug & 4:
            self.showDebug()
        if self.result == 0:
            return(True)
        elif self.result > 0:
            return(False)
