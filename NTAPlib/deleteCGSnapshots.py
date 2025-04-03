import doREST
import datetime
import time
import re
import sys
import userio
from getCGSnapshots import getCGSnapshots
from getCGs import getCGs

class deleteCGSnapshots:

    def __init__(self,svm,cgname,snapshots,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.svm=svm
        self.cgmatch=[]
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
        
        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']
        
        if 'force' in kwargs.keys():
            self.force=kwargs['force']

        if type(cgname) is str:
            self.cgmatch=cgname.split(',')
        else:
            try:
                newlist=list(cgname)
            except:
                print("Error: 'name' passed to deleteCGSnapshots with illegal type")
                sys.exit(1)
            for item in newlist:
                self.cgmatch.append(item)

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
            userio.message("Retriving CGs for " + ','.join(self.cgmatch),service=localapi + ":OP")

        mycgs=getCGs(self.svm,name=self.cgmatch,apicaller=localapi,debug=self.debug)
        if not mycgs.go():
            self.result=1
            self.reason=mycgss.reason
            self.stdout=mycgs.stdout
            self.stderr=mycgs.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)

        foundcgs=list(mycgs.cgs.keys())
        if self.debug & 1:
            userio.message("Retriving CG snapshots for " + ','.join(foundcgs),service=localapi + ":OP")
        snapshots=getCGSnapshots(self.svm,cgs=foundcgs,name=self.snapshotmatch,apicaller=localapi,debug=self.debug)

        if not snapshots.go():
            self.result=1
            self.reason=snapshots.reason
            self.stdout=snapshots.stdout
            self.stderr=snapshots.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
        else:
            targetlist=list(snapshots.snapshots.keys())
            targetlist.sort()
            for target in targetlist:
                snapshots2delete=[]
                snaplist=list(snapshots.snapshots[target]['snapshots'].keys())
                targetuuid=snapshots.snapshots[target]['uuid']
                snaplist.sort()
                for snap in snaplist:
                    snapuuid=snapshots.snapshots[target]['snapshots'][snap]['uuid']
                    epoch=snapshots.snapshots[target]['snapshots'][snap]['epoch']
                    if self.maxage:
                        if now - epoch > self.maxage:
                            if self.debug & 1:
                                userio.message("Snapshot " + target + ":" + snap + " exceeds max age",service=localapi + ":OP")
                            snapshots2delete.append((target,targetuuid,snap,snapuuid,epoch))
                    else:
                        snapshots2delete.append((target,targetuuid,snap,snapuuid,epoch))
            
                snapshots2delete.sort(key=lambda x: x[4], reverse=True)

                if self.maxage and (len(snaplist) - len(snapshots2delete) == 0) and not self.force and (self.snapshotmatch == '*' or self.snapshotmatch is None):
                    if self.debug & 1:
                        userio.message("Blocking deletion of last snapshot " + snapshots2delete[0][2] + " on " + target ,service=localapi + ":OP")
                    del snapshots2delete[0]

                if self.maxcount:
                    if self.debug & 1:
                        userio.message("Limiting snapshots on target " + target + " to " + str(self.maxcount),service=localapi + ":OP")
                    if len(snapshots2delete) > self.maxcount:
                        snapshots2delete=snapshots2delete[self.maxcount:]
                    else:
                        snapshots2delete=[]

                for item in snapshots2delete:
                    self.snapshots2delete.append(item)

            for target, targetdata, snapname, snapuuid, epoch in self.snapshots2delete:
                rest=doREST.doREST(self.svm, \
                                   'delete', \
                                   '/application/consistency-groups/' + targetdata['uuid'] + '/snapshots/' + snapuuid + '?return_timeout=60', \
                                   debug=self.debug)

                if rest.result == 200 and rest.reason=='OK':
                    if target in self.deleted.keys():
                        self.deleted[target].append(snapname)
                    else:
                        self.deleted[target]=[snapname]
                    if self.debug & 1:
                        userio.message("Deleted snapshot " + snapname + " on " + target,service=localapi + ":OP")
                else:
                    if self.debug & 1:
                        userio.message("Failed to delete snapshot " + snapname + " on " + target,service=localapi + ":OP")
                    if target in self.failed.keys():
                        self.failed[target].append(snapname)
                    else:
                        self.failed[target]=[snapname]
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
