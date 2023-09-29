import os
import doREST

# NFS
#    FILESYSTEM name is key
#       SVM
#       VOLUME
#       VOLUME UUID
#       JUNCTION-PATH

class discoverNFS:

    def __init__(self,path,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=None
        self.stderr=None   
        self.paths=path
        self.exports={}
        self.nfs={}
        self.cache=None

        nasprotocols=['nfs','nfs4']

        if 'cache' in kwargs:
            store=kwargs['cache']


        if type(path) is str:
            self.paths=[path]

        for item in self.paths:
            if not os.path.exists(item):
                self.result=1
                self.reason="Path " + item + " does not exist"
                return
            if not item[0] == '/':
                self.result=1
                self.reason="Only absolute paths supported"
                return
        
        allmounts=open('/proc/mounts','r').readlines()
        mountpoint2server={}
        for item in allmounts:
            source,mountpoint,fstype=item.split(' ')[:3]    
            if fstype in nasprotocols :
                mountpoint2server[mountpoint]=source

        nfsservers={}
        for item in self.paths:
            realpath=os.path.realpath(item)
            if not os.path.exists(realpath):
                self.result=1
                self.reason="Cannot get canonical path for " + item
                self.nfs=None
                return
            while not os.path.ismount(realpath):
                realpath=os.path.dirname(realpath)
            self.nfs[item]={'MOUNTPOINT':realpath}

            try:
                server,junction=mountpoint2server[realpath].split(':')
                self.nfs[item]['JUNCTIONPATH']=junction
                self.nfs[item]['SERVERNAME']=server
                if server in nfsservers.keys():
                    nfsservers[server].append(junction)
                else:
                    nfsservers[server]=[junction]

            except Exception as e:
                self.result=1
                self.reason=e
                return

        restresponses={}
        for item in nfsservers.keys():
            api='/storage/volumes'
            restargs='fields=uuid,svm.name?nas.path=' + '|'.join(nfsservers[item])
            rest=doREST.doREST(item,'get',api,restargs,**kwargs)
            if rest.result == 0:
                restresponses[item]=rest.response
            else:
                self.result=1
                self.reason=rest.reason
                return

        known={}
        for servername in restresponses.keys():
            for record in restresponses[servername]['records']:
                svm=record['svm']['name']
                voluuid=record['uuid']
                volname=record['name']
                junctionpath=record['nas']['path']
                known[(servername,junctionpath)]={'SVM':svm,'VOLUUID':voluuid,'VOLNAME':volname}

                if cache:
                    if svm not in store.svm.keys():
                        store.svm[svm]


        
        for item in self.nfs.keys():
            self.nfs[item]=known[(self.nfs[item]['SERVERNAME'],self.nfs[item]['JUNCTIONPATH'])]

