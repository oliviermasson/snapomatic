import os
import sys
import doProcess
import json
import re

class removeMultipath:

    def __init__(self,pathmatch,**kwargs):
        self.result=None
        self.reason=None
        self.removed=[]
        self.inuse=[]
        self.stdout=[]
        self.stderr=[]
        self.debug=False
        self.path=pathmatch
        self.pathmaps={}
        self.flush=[]
        self.flushed=[]
        self.unflushed=[]
        verbose=0

        singlepaths2flush=[]

        if pathmatch == '*':
            patternmatch=re.compile('^.*.$')
        elif re.findall(r'[?*.^$]',pathmatch):
            patternmatch=re.compile(pathmatch)
        else:
            patternmatch=re.compile('^' + pathmatch + '$')
        
        if 'cache' in kwargs.keys():
            store=kwargs['cache']
            cache=True
        else:
            cache=False
        
        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if 'verbose' in kwargs.keys():
            verbose=kwargs['verbose']

        self.pathmaps={}

        multipath=doProcess.doProcess("/usr/sbin/multipathd list multipaths json ",debug=self.debug)
    
        if multipath.result > 0:
            self.result=1
            self.reason="Cannot execute /usr/sbin/multipathd " 
            self.stdout=multipath.stdout
            self.stderr=multipath.stderr
            return

        pathdict=json.loads(''.join(multipath.stdout)) 

        for item in pathdict['maps']:
            mpathname=item['name']
            self.pathmaps[mpathname]={'sysfs':item['sysfs'],'paths':{}}
            for pathgroup in item['path_groups']:
                for path in pathgroup['paths']:
                    self.pathmaps[mpathname]['paths'][path['dev']]=path['chk_st']

        for item in self.pathmaps.keys():
            if re.match(patternmatch,'/dev/mapper/' + item) :
                self.flush.append(('/dev/mapper/' + item,self.pathmaps[item]['paths']))
            elif re.match(patternmatch,'/dev/' + self.pathmaps[item]['sysfs']):
                self.flush.append(('/dev/' + self.pathmaps[item]['sysfs'],self.pathmaps[item]['paths']))

        if len(self.flush) == 0:
            self.result=1
            self.reason="Unable to find multipath device " + self.path
            return

        self.result=0
        for device,paths in self.flush:
            if verbose > 0:
                print("Removing multipath " + device + "...",end='')
            flushmultipath=doProcess.doProcess("/usr/sbin/multipath -f " + device,debug=self.debug)
            if flushmultipath.result > 0:
                if verbose > 0:
                    print("  failed")
                self.result=2
                self.reason="Unable to flush at least one device"
                for line in flushmultipath.stdout:
                    self.stdout.append(line)
                for line in flushmultipath.stderr:
                    self.stderr.append(line)
                self.unflushed.append(device)
            else:
                if verbose > 0:
                    print("  complete")
                self.flushed.append(device)
                for item in paths.keys():
                    singlepaths2flush.append(item)

        for singlepath in singlepaths2flush:
            blockdev=doProcess.doProcess("/usr/sbin/blockdev --flushbufs /dev/" + singlepath,debug=self.debug)
            if len(blockdev.stderr) > 0:
                self.result=1
                self.reason=("Error running /usr/sbin/blockdev --flushbufs /dev/" + singlepath)
            
            if verbose > 1:
                print("Removing LUN /dev/" + singlepath + "...", end='')
            try:
                fd=open("/sys/block/" + singlepath + "/device/delete",'w').write('1')
            except Exception as e:
                print(e)
            if 1== 0:
                if verbose > 1:
                    print("  failed")
                self.result=1
                self.reason("Error running deleting /sys/block/" + singlepath + "/device/delete")
            else:
                if verbose > 1:
                    print("  complete")

        return 
