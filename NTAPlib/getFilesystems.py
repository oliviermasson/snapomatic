class getFilesystems:

    def __init__(self,**kwargs):
        self.reason=None
        self.result=None
        self.nfs={}
        self.sanfs={}
        self.lvm={}
        self.luns={}
        self.unknownfs={}
        self.foreignluns=[]

        pathargs=None

        if 'path' in kwargs.keys():
            if type(fs) is str:
                pathargs=[kwargs['path']]
            else:
                pathargs=kwargs['path']

        discover=['nfs','nfs4','ext4','xfs']
        nasprotocols=['nfs','nfs4']
        discoversan=True
        debug=[]
        if 'cache' in kwargs.keys():
            cache=True
            store=kwargs['cache']
        else:
            cache=False
    
        if 'nfs' in kwargs.keys() and kwargs['nfs'] == False:
            discover.remove('nfs')
            discover.remove('nfs4')
        if 'san' in kwargs.keys() and kwargs['san'] == False:
            discover.remove('xfs')
            discover.remove('ext4')
            discoversan = False
    
        
        allmounts=open('/proc/mounts','r').readlines()
        if pathargs:
            filteredmounts=[]
            for item in allmounts:
                source,mountpoint,fstype=item.split(' ')[:3]
                if mountpoint in pathargs:
                    filteredmounts.append(item)
                    if fstype not in nasprotocols:
                        discoversan=True
            allmounts=filteredmounts
        
        if discoversan:
            import doProcess
            lvs=doProcess.doProcess(['/usr/sbin/lvs',
                           '--noheadings',
                           '--separator', ':::',
                           '--options', 'vg_name,lv_name'])
            for line in lvs.stdout:
                vgname,lvname=line.lstrip(' ').split(':::')[:2]
                if vgname not in self.lvm.keys():
                    self.lvm[vgname]={'LV':{},'PV':{}}
                else:
                    self.lvm[vgname]['LV'][lvname]={}
    
            pvs=doProcess.doProcess(['/usr/sbin/pvs',
                           '--noheadings',
                           '--separator', ':::',
                           '--options', 'vg_name,pv_name'])
            for line in pvs.stdout:
                vgname,pvname=line.lstrip(' ').split(':::')[:2]
                self.lvm[vgname]['PV'][pvname]={}
                self.luns[pvname]={}
            
            if cache:
                store.lvm=self.lvm.copy()
    
        for item in allmounts:
            source,mountpoint,fstype,options=item.split(' ')[:4]
            if fstype in discover:
                debug.append([1,"Discovered " + fstype + " filesystem " + mountpoint])
    
                if fstype in nasprotocols:
                    server,export=source.split(':')
                    self.nfs[mountpoint]={'SERVER':server,'EXPORT':export}
                    if cache:
                        store.nfs[mountpoint]=self.nfs[mountpoint].copy()
                else:
                    lvs=doProcess.doProcess(['/usr/sbin/lvs',
                                   source,
                                   '--noheadings',
                                   '--separator', ':::',
                                   '--options', 'vg_name,lv_name'])
                    if lvs.result> 0:
                        self.unknownfs[mountpoint]={'DEVICE':source,'FSTYPE':fstype,'OPTIONS':options}
                        if cache:
                            store.unknownfs[mountpoint]=self.unknownfs[mountpoint].copy()
                    else:
                        vgname,lvname=lvs.stdout[0].lstrip(' ').split(':::')[:2]
                        self.sanfs[mountpoint]={'TYPE':'LVM','VG':vgname,'LV':lvname}
                        if cache:
                            store.sanfs[mountpoint]=self.sanfs[mountpoint].copy()
    
        if len(self.luns)>0:
            import discoverLUN
            for lunpath in self.luns.keys():
                lunDiscovery=discoverLUN.discoverLUN(lunpath)
                if lunDiscovery.result == 0: 
                    self.foreignluns.append(lunpath)
                    if cache:
                        store.foreignluns.append(lunpath)
                else:
                    self.luns[lunpath]=lunDiscovery
                    if cache:
                        store.luns[lunpath]=lunDiscovery
    
    
        self.result=0
