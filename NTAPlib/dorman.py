###########################################################################
# (c) 2019 NetApp Inc. (NetApp), All Rights Reserved
#
# NetApp disclaims all warranties, excepting NetApp shall provide
# support of unmodified software pursuant to a valid, separate,
# purchased support agreement.  No distribution or modification of
# this software is permitted by NetApp, except under separate
# written agreement, which may be withheld at NetApp's sole
# discretion.
#
# THIS SOFTWARE IS PROVIDED BY NETAPP "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NETAPP BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Created by Jeffrey Steiner, jfs@netapp.com
#
###########################################################################

import sys
import os
import userio
import subprocess
import pwd
import grp
from xml.etree import ElementTree as ET

def dorman(sid,useraccount,oraclehome,rmancommands):
    commandblock=''
    stdout=[]
    stderr=[]
    returnhash={}
    for line in rmancommands:
        commandblock=commandblock + line + "\n"
    mypath="/bin:/usr/bin:/usr/local/bin:" + oraclehome + "/bin"
    myldlibrarypath=oraclehome + "/lib"
    myenv={"PATH": mypath, "LD_LIBRARY_PATH": myldlibrarypath, "ORACLE_HOME": oraclehome, "ORACLE_SID": sid}
    rmancmd=subprocess.Popen(['rman','target','/','nocatalog'],preexec_fn=changeuser(useraccount),stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, env=myenv)
    out, err =rmancmd.communicate(input=commandblock)
    outtext=str(out)
    lines=outtext.split('\n')
    for line in lines:
        if len(line) > 1:
            stdout.append(line)
    errtext=str(err)
    errlines=errtext.split('\n')
    for line in errlines:
        if len(line) > 1:
            stderr.append(line)
    returnhash['out']=stdout
    returnhash['err']=stderr
    return(returnhash)

def changeuser(user, **kwargs):
    if 'showchange' in kwargs.keys():
        showchange = kwargs['showchange']
    else:
        showchange = False
    userinfo = pwd.getpwnam(user)
    newuid = userinfo.pw_uid
    newgid = userinfo.pw_gid
    grouplist = [newgid]
    allgroups = grp.getgrall()
    for item in allgroups:
        if user in item[3]:
            grouplist.append(item[2])

    def set_ids():
        if showchange:
            userio.message("Changing GID to " + str(newgid))
        os.setgid(newgid)
        if showchange:
            userio.message("Changing group memberships to " + str(grouplist))
        os.setgroups(grouplist)
        if showchange:
            userio.message("Changing user to " + user)
        os.setuid(newuid)
    return set_ids

