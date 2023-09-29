import doREST
import userio

class getLUNs:

    def __init__(self,svm,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=None
        self.stderr=None
        self.svm=svm
        self.lunfilter=None
        self.luns={}
        self.debug=False

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
        
        self.api='/storage/luns'
        self.restargs='fields=name,' + \
                 'uuid,' + \
                 'lun_maps.igroup.uuid,' + \
                 'lun_maps.igroup.name,' + \
                 'location.volume.uuid,' + \
                 'location.volume.name,' + \
                 'space.size,' + \
                 'svm.name,' + \
                 'svm.uuid,' + \
                 'os_type,' + \
                 'status.state,' + \
                 '&svm.name=' + svm \
    
        if 'name' in kwargs.keys():
            self.restargs = self.restargs + '&name=' + kwargs['name']
            self.lunfilter=kwargs['name']
            
        if 'cache' in kwargs.keys():
            cache=True
            store=kwargs['cache']
        else:
            cache=False

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

        if self.debug & 1:
            userio.message("Retrieving LUNs from svm " + self.svm ,service=localapi + ":OP")
            if self.lunfilter is not None:
                userio.message("LUN search list: " + self.lunfilter,service=localapi + ":OP")
        rest=doREST.doREST(self.svm,'get',self.api,restargs=self.restargs)
        if rest.result == 0:
            self.lunpath={}
            self.lunuuid={}
            for record in rest.response['records']:
                svmname=record['svm']['name']
                svmuuid=record['svm']['uuid']
                lunpath=record['name']
                lunuuid=record['uuid']
                volname=record['location']['volume']['name']
                voluuid=record['location']['volume']['uuid']

                self.luns[lunpath]={'uuid':lunuuid,
                                    'size':record['space']['size'],
                                    'svm':{'name':svmname,'uuid':svmuuid},
                                    'state':record['status']['state'],
                                    'igroup':[],
                                    'volume':{'uuid':voluuid,'name':volname}}

                if self.debug & 4:
                    userio.message("Found LUN " + str(self.luns[lunpath]) ,service=localapi + ":DATA")
                elif self.debug & 1:
                    userio.message("Found LUN " + self.luns[lunpath]['svm']['name'] + ":" + lunpath,service=localapi + ":DATA")


                if record['status']['state'] == 'online':
                    self.luns[lunpath]['ostype']=record['os_type']

                if 'lun_maps' in record.keys():
                    for item in record['lun_maps']:
                        self.luns[lunpath]['igroup'].append(item['igroup']['name'])

            #if cache:
            #    store.cacheLUNs(self.luns)
        else:
            self.result=1
            self.reason=rest.reason
            if self.debug:
                self.showdebug()
            return(False)
                    
        self.result=0
        self.reason=None
        if self.debug & 4:
            self.showDebug()
        return(True)

