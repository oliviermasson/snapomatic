import os
import doREST
import fileio
import userio

class discoverNFS:

    def __init__(self,path,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=None
        self.stderr=None   
        self.paths=path
        self.nfs={}
        self.svms={}
        self.unknown=[]
        self.supportedNFS=['nfs','nfs4']
        self.debug=False

        nasprotocols=['nfs','nfs4']

        if type(path) is str:
            self.paths=[path]
        elif type(path) is list:
            self.paths=path

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])

        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")

    def go(self,**kwargs):

        for item in self.paths:
            if not item[0] == '/':
                self.result=1
                self.reason="Only absolute paths supported"
                return(False)

        nfsservers={}
        fsinfo=fileio.getFilesystems(self.paths)
        for path in fsinfo.keys():
            if fsinfo[path]['fstype'] in self.supportedNFS:
                device,exportpath=fsinfo[path]['device']
                if device not in nfsservers.keys():
                    nfsservers[device]=[exportpath]
                else:
                    nfsservers[device].append(exportpath)

        for item in nfsservers.keys():
            nfsservers[item]=set(nfsservers[item])

        restresponses={}
        for device in nfsservers.keys():
            api='/storage/volumes'
            restargs='fields=size,uuid,aggregates,type,svm.name,svm.uuid,nas.path&nas.path=' + '|'.join(nfsservers[device])
            rest=doREST.doREST(device,'get',api,restargs=restargs,debug=self.debug)
            if rest.result == 0:
                restresponses[device]=rest.response
            else:
                self.result=1
                self.reason=rest.reason
                return

        for servername in restresponses.keys():
            for record in restresponses[servername]['records']:
                svm=record['svm']['name']
                svmuuid=record['svm']['uuid']
                size=record['size']
                aggrs=record['aggregates']
                voluuid=record['uuid']
                volname=record['name']
                junctionpath=record['nas']['path']
                if svm not in self.svms.keys():
                    self.svms[svm]={'uuid':record['svm']['uuid'],'volumes':{}}
                self.svms[svm]['volumes'][volname]={'uuid':voluuid,
                                                    'size':size,
                                                    'name':volname,
                                                    'aggrs':aggrs,
                                                    'svm':{'name':svm,'uuid':svmuuid},
                                                    'junction-path':junctionpath}

                for path in fsinfo.keys():
                    if fsinfo[path]['device'] == (servername, junctionpath):
                        self.nfs[(servername,junctionpath)] = {'volumes':self.svms[svm]['volumes'][volname]}
                        break

        for path in self.paths:
            if path not in self.nfs.keys():
                self.unknown.append(path)

        self.result=0
        return(True)
