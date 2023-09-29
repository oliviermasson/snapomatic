# SVM name is key
#    UUID
#    VOLUME name is key: VOLUMEUUID
#    LUNS lunpath is key: LUNUUID
#    IGROUP
#       NAME
#       UUID
#
# VOLUMEUUID is key
#    NAME
#    SIZE
#    SVM
#    TYPE
#    JUNCTIONPATH
#
# LUNUUID uuid is key
#    LUNPATH
#    SVM
#    IGROUP
#    SIZE
#    OSTYPE
#    IGROUP
#
# EXPORTS path is key
#    VOLUUID
#
# FILESYSTEM mountpath is key
#    PROTOCOL
#    OPTIONS
#
# NFS mountpath is key
#    SERVER
#    EXPORT
#
# SANFS mountpath is key
#    TYPE (LVM or LUN)
#    LV (None if regular LUN)
#    VG (None if regular LUN)
#
# VG name is key
#    LV:name is key
#    PV:name is key
#        LUN:path
#
# LUN path is key
#    SVM
#    SVMPATH
#    IGROUP
#    SIZE
#            
# UNKNOWNFS
#    FILESYSTEM is key
#
# FOREIGNLUNS
#    LUN path is list

import sys

class smCache():
    
    def __init__(self,**kwargs):
        self.filesystems={}
        self.supportedFilesystems=['nfs','nfs4','ext4','xfs']
        self.unmountedFilesystems=[]
        self.recentUnmountedFilesystems=[]
        self.nfs={}
        self.sanfs={}
        self.unknownfs={}
        self.lun={}
        self.lvm={}
        self.foreignlun=[]
        
        self.svm={}
        self.volumeuuid={}
        self.lunuuid={}
        self.exports={}

    def cacheVolumes(self,volumes):
        for volname in volumes.keys():
            voluuid=volumes[volname]['uuid']
            svmname=volumes[volname]['svm']['name']
            svmuuid=volumes[volname]['svm']['uuid']
            if svmname not in self.svm.keys():
                self.svm[svmname]={'uuid':svmuuid,
                               'volumes':{}}

            if not svmuuid == self.svm[svmname]['uuid']:
                sys.stderr.write("SVM uuid mismatch in smCache, environment may have duplicate SVM names")
                sys.exit(1)
            self.svm[svmname]['volumes'][volname]=voluuid
            self.volumeuuid[voluuid]=volumes[volname].copy()
            del self.volumeuuid[voluuid]['uuid']
            self.volumeuuid[voluuid]['name']=volname
        return

    def cacheLUNs(self,luns):
        for lunpath in luns.keys():
            svmname=luns[lunpath]['svm']['name']
            svmuuid=luns[lunpath]['svm']['uuid']
            lunuuid=luns[lunpath]['uuid']
            if svmname not in self.svm.keys():
                self.svm[svmname]={'uuid':svmuuid,
                                   'luns':{}}

            if not svmuuid == self.svm[svmname]['uuid']:
                sys.stderr.write("SVM uuid mismatch in smCache, environment may have duplicate SVM names")
                sys.exit(1)

            self.svm[svmname]['luns'][lunpath]=lunuuid
            self.lunuuid[lunuuid]=luns[lunpath].copy()
            del self.lunuuid[lunuuid]['uuid']
            self.lunuuid[lunuuid]['lunpath']=lunpath
        return
