import os
import pwd
import grp
from doprocess import doprocess
from dosqlplus import dosqlplus

def deletedatabase(oraclesid,**kwargs):
   if 'home' in kwargs.keys():
      oraclehome=kwargs['home']
   else:
      oraclehome=getoraclehome(oraclesid)
      if oraclehome is None:
         return({'RESULT':1,'STDOUT':[],'STDERR':['Unable to get ORACLE_HOME for ' + oraclesid]})

   if 'user' in kwargs.keys():
      oracleuser=kwargs['user']
   else:
      oracleuser=getoracleuser(oraclehome)
      if oracleuser is None:
         return({'RESULT':1,'STDOUT':[],'STDERR':['Unable to get Oracle user for ' + oraclehome]})

   if 'password' in kwargs.keys():
      deletepwd=kwargs['password']
   else:
      deletepwd='oracle'

   out=doprocess("dbca -silent -deleteDatabase -sourceDB " + oraclesid,input="oracle",user=oracleuser,env={'PATH':oraclehome+"/bin",'ORACLE_HOME':oraclehome,'ORACLE_SID':oraclesid},printstdout=True)

   return({'RESULT':out['RESULT'],'STDOUT':out['STDOUT'],'STDERR':out['STDERR']})
