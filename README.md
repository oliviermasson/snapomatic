# Introduction

Snapomatic is a collection of python utilities to perform useful things using ONTAP REST calls on a linux OS. It does not use any components other than Python and standard OS commands. These scripts were written by a longtime sysadmin with no programming education, just an interest in reliably automating as much work as possible.

The primary scripts are located in the NTAP directory. Many of them are extremely similar. Their function is to perform a RESTful operation and store the data in python lists and dictionaries. NetApp offers a python SDK for REST as well. The difference between that code and snapomatic is snapomatic is intended to be expanded.

You will also find some implementations of those NTAPlib modules in the root directory. For example, "snapomatic.snapshot" shows how to use the NTAPlib modules to list, create, and delete snapshots. The snapomatic.discover utility can perform discover operations on NFS, LVM, and raw devices (it's similar to the NetApp Host Utilities sanlun executable in that respect"

You can run one of those "snapomatic.*" commands with no arguments and see syntax guidance. Some utilities must be run as root because they perform root-level storage operations. 

The key to these scripts is the debug option

## --debug

The example scripts accept a --debug argument to print more information about what's happening in the workflow. They also may print the OS commands being executed and display the stdin and stdout. 

## --restdebug

The --restdebug argument is especially useful for anyone looking to automate REST. This flag will display the REST converation, including API calls, JSON, arguments, and responses. It will also show you the polling calls for those APIs that are not synchronous. You can use this information in your own scripts, whether you're using Python, Java, or even basic curl.

# Note

This is a work in progress. If you have questions, please open an Issue and I'll see what I can do to help. 

# Credentials

One important utility is snapomatic.credential. This is used to populate a file that defaults to /etc/snapomatic to store credentials for ONTAP and other systems. The result is a password that is stored in plaintext. This is somewhat unavoidable. The password could be stored encrypted, but these utilities are python scripts, and could be easily modified to simply print the password once decrypted. If you'd like to see certificates used, please let me know. 

You should also use a username/password that has REST access only, and limit the access only to those RESTful APIs required for your project.

Many functions require root access in order to perform low-level OS operations. If you do not want to store your credentials in /etc or you do not want to use root, you can set an alternate credential file location by exporting SNAPOMATIC_CREDENTIAL_PATH and select a different location.

When you first run it, you'll see this:

    [root@jfs0 current]# ./snapomatic.credential
    ERROR: Unable to access /etc/snapomatic/config.json

You can initialize the file as follows:

    [root@jfs0 current]$ ./snapomatic.credential INIT
    Credential cache initialized

You can then add account information.

## ONTAP Credentials

ONTAP credentials are SVM-scoped. This helps avoid user errors. 

    [oracle@jfs0 current]$ ./snapomatic.credential
    Select one of the following
    (1) Manage ONTAP credentials
    (2) Manage Oracle databases
    Selection: (1-2): 1
    Select one of the following
    (1) List credentials
    (2) Add credential
    (3) Edit credential
    (4) Delete credential
    Selection: (1-4): 2
    Enter SVM name: jfsCloud4
    Enter new management interface: 10.63.147.209  <- Not real
    Enter new username: username_with_required_api_access
    Enter new password:
    Enter new data interface(s), if any: a200B-nfs1,a200B-nfs2,a200B-iscsi1,a200B-iscsi2
    /etc/snapomatic/config.json updated

The result is snapomatic now has credentials for an SVM called `jfsCloud4`, and it knows that this is the SVM providing data services on the four specified data interfaces. 

# debugging

Most of the scripts include flags for --debug and --restdebug. The --debug flag will print details of the modules behavior and stdin/stdout. The --restdebug will show the REST conversations between the host and ONTAP system.

# The --target argument

Many scripts require the user to specify an target. The syntax for a target is one of the following, depending on the command:

* svm volume [volume]
* svm cg-name
* path to a file
* path to a LUN

**Not all target types are fully supported. I'm adding them incrementally**

# snapomatic.destroyVolume

This script is a wrapped that illustrates how to use NTAPlib/destroyVolumes.py 

It does what it implies - it destroys a volume. There are no safeties. It will destroy the volume if the user credentials allow it. The volume will still be available in the recover-queue until expired.


    [root@jfs0 current]# ./snapomatic.destroyVolume
    ERROR: Version dev
              --target
              (svm volume)
    
              [--debug]
              (show debug output)
    
              [--restdebug]
              (show REST API calls and responses)

The script itself is basically a wrapper around the `NTAPlib/destroyVolumes.py` module. 

# snapomatic.discover

This script users several of the NTAPlib modules to perform basic discovery. For example:

    [root@jfs0 current]# ./snapomatic.discover --target /oradata0
    PATH      MOUNTPOINT FS   VG LV PV SVM      EXPORT         VOLUME        LUN
    --------- ---------- ---- -- -- -- -------- -------------- ------------- ---
    /oradata0 /oradata0  nfs4          jfs_svm1 /jfs0_oradata0 jfs0_oradata0

What happened here, is the script took the filesystem argument of `/oradata0`, discovered it was an NFS filesystem that originated at a LIF that was registered to the SVM called `jfs_svm1`, and it made a few RESTful calls to get information about this volume. It used `NTAPlib/discoverNFS.py` for most of the work. There's more information about this volume stored in the discoverNFS object too.

Here's a slightly more advanced example:

    [root@jfs0 current]# ./snapomatic.discover --target /myLV
    PATH  MOUNTPOINT FS  VG   LV   PV                                            SVM      EXPORT VOLUME       LUN
    ----- ---------- --- ---- ---- --------------------------------------------- -------- ------ ------------ ----
    /myLV /myLV      xfs myVG myLV /dev/mapper/3600a0980383041327a2b55676c547173 jfs_svm1        jfs0_lvmtest LUN0
                                   /dev/mapper/3600a0980383041327a2b55676c547174 jfs_svm1        jfs0_lvmtest LUN1
                                   /dev/mapper/3600a0980383041327a2b55676c547175 jfs_svm1        jfs0_lvmtest LUN2

In this case, the script discovered that /myLVM was an LVM-based filesystem. It then made a call to `NTAPlib/discoverLVM.py' which mapped this filesystem to its logical volume, and then to the volume group, and then to the underlying physical volumes. It then used NTAPlib/discoverLUN.py to send a specially formatted SCSI command to the LUN device backing the PV and ONTAP responded with identifying information.

Finally, you can run this utility directly against the raw LUNs. This is useful for managing Oracle ASM or newly provisioned LUNs that are not yet part of a filesystem. This script leverages NTAPlib/discoverLUN.py to probe the LUN itself for data. 

    [root@jfs0 current]# ./snapomatic.discover --target /dev/mapper/*
    PATH                                          MOUNTPOINT FS    VG LV PV SVM      EXPORT VOLUME       LUN
    --------------------------------------------- ---------- ----- -- -- -- -------- ------ ------------ ------
    /dev/mapper/3600a0980383041327a2b55676c547173            block          jfs_svm1        jfs0_lvmtest LUN0
    /dev/mapper/3600a0980383041327a2b55676c547174            block          jfs_svm1        jfs0_lvmtest LUN1
    /dev/mapper/3600a0980383041327a2b55676c547175            block          jfs_svm1        jfs0_lvmtest LUN2
    /dev/mapper/3600a0980383041334a3f55676c697278            block          jfs_svm1        lvm_convert  bigLUN
    /dev/mapper/3600a0980383041334a3f55676c697279            block          jfs_svm1        lvm_convert  small0
    /dev/mapper/3600a0980383041334a3f55676c69727a            block          jfs_svm1        lvm_convert  small1
    /dev/mapper/3600a0980383041334a3f55676c697330            block          jfs_svm1        lvm_convert  small2
    /dev/mapper/3600a0980383041334a3f55676c697331            block          jfs_svm1        lvm_convert  small3
    /dev/mapper/3600a0980383041334a3f55676c697332            block          jfs_svm1        lvm_convert  small4
    /dev/mapper/3600a0980383041334a3f55676c697333            block          jfs_svm1        lvm_convert  small5
    /dev/mapper/3600a0980383041334a3f55676c697334            block          jfs_svm1        lvm_convert  small6
    /dev/mapper/3600a0980383041334a3f55676c697335            block          jfs_svm1        lvm_convert  small7
    /dev/mapper/bigVG-bigLV                                  block          jfs_svm1        lvm_convert  bigLUN
    /dev/mapper/myVG-myLV                                    block          jfs_svm1        jfs0_lvmtest LUN0
    /dev/mapper/rhel-root                         ?          ?     ?  ?  ?  ?        ?      ?            ?
    /dev/mapper/rhel-swap                         ?          ?     ?  ?  ?  ?        ?      ?            ?
    /dev/mapper/control                           ?          ?     ?  ?  ?  ?        ?      ?            ?
    
Most of these LUNs were identified as being ONTAP-hosted LUNs. Some of them are unknown. In this case, they are VMware virtual LUNs.

# snapomatic.volume

This script is a wrapper around `NTAPlib/getVolumes.py`, `NTAPlib/cloneVolumes.py`, and `NTAPlib/createSnapshots.py`. As with other scripts, there is a lot more information in the getVolume object. The wrapper shows the basics.

## show

    [root@jfs0 current]# ./snapomatic.volume show --target jfs_svm1 jfs0_oradata0
    VOLUME        SIZE (GB) AGGREGATE
    ------------- --------- ------------------
    jfs0_oradata0 256000.0  rtp_a700s_01_SSD_1

Wildcards are also supported. Make sure you enclose the arguments in quotes or the shell will expand them. 

    [root@jfs0 current]# ./snapomatic.volume show --target jfs_svm1 'jfs0_*'
    VOLUME        SIZE (GB) AGGREGATE
    ------------- --------- ------------------
    jfs0_arch     102400.0  rtp_a700s_01_SSD_1
    jfs0_lvmtest  20480.0   rtp_a700s_01_SSD_1
    jfs0_orabin   73728.0   rtp_a700s_01_SSD_1
    jfs0_oradata0 256000.0  rtp_a700s_01_SSD_1
    jfs0_oradata1 256000.0  rtp_a700s_02_SSD_1
    jfs0_oradata2 256000.0  rtp_a700s_01_SSD_1
    jfs0_oradata3 256000.0  rtp_a700s_02_SSD_1
    jfs0_oratmp0  102400.0  rtp_a700s_01_SSD_1
    jfs0_oratmp1  102400.0  rtp_a700s_02_SSD_1
    jfs0_redo0    10240.0   rtp_a700s_01_SSD_1
    jfs0_redo1    10240.0   rtp_a700s_02_SSD_1

## clone

You can clone a volume too.

    [root@jfs0 current]# ./snapomatic.volume clone --target jfs_svm1 jfs0_oradata0 --name newclone
    Cloned newclone from jfs0_oradata0

I'll destroy it before I forget it's there.

    [root@jfs0 current]# ./snapomatic.destroyVolume --target jfs_svm1 newclone
    Destroyed jfs_svm1:newclone

# snapomatic.snapshot

This script is a wrapper around various `NTAPlib/` modules.

    [root@jfs0 current]# ./snapomatic.snapshot
    ERROR: Version DEV
    snapshot show
            [--target]
            (svm [filesystem, LUN, or volume]
    
            (Optional. Name for snapshot. Wildcards accepted.)
    
            [--cg]
            (Restrict search to CG snapshots. Wildcards accepted.)
    
            [--debug]
            (show debug output)
    
            [--restdebug]
            (show REST API debug output)
    
    snapshot create
            [--target]
            (svm [filesystem, CG, LUN, or volume]
    
            [--name||prefix]
            (Name or prefix for snapshot)
    
            [--label|]
            (Snapmirror label for the snapshot)
    
            [--cg]
            (Create CG snapshots.)
    
            [--debug]
            (show debug output)
    
            [--restdebug]
            (show REST API debug output)
    
    snapshot delete
            [--target]
            (svm [filesystem, LUN, or volume]
    
            [--name]
            (Optional. Name of snapshot. Wildcards accepted)
    
            [--maxcount]
            (Optional. Maximum number of snapshots to retain)
    
            [--maxage]
            (Optional. Maximum age of snapshots to retain.
            (Accepts d[ays]/h[ours]/m[inutes]/[s]econds
    
            [--force]
            (Override all safeguards)
    
            [--debug]
            (show debug output)
    
            [--restdebug]
            (show REST API debug output)

## show

For example, I can view the snapshots like this:

    [root@jfs0 current]# ./snapomatic.snapshot show --target jfs_svm1 jfs0_oradata0
    VOLUME        SNAPSHOT                           DATE
    ------------- ---------------------------------- -------------------------
    jfs0_oradata0 clone_newclone.2024-02-01_204436.0 2024-02-01T20:44:36+00:00

**Note: This only reports regular snapshots, not CG snapshots. 

This could easily be done on the ONTAP CLI too. The point of this script is not to demonstrate how to script such a basic option, the point is to lead you to  understand how the ability to retrieve snapshots via Python can be incorporated into other scripts with more advanced workflows.

If I wanted to view CG snapshots, I need to use the `--target svm cg-name` syntax.
    
    [root@jfs0 current]# ./snapomatic.snapshot show --target jfs_svm1 jfs0 --cg 
    CG   PARENT VOLUME        SNAPSHOT                                                    DATE
    jfs0        jfs0_arch     every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_arch     every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_orabin   every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_orabin   every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_oradata0 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_oradata0 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_oradata1 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_oradata1 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_oradata2 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_oradata2 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_oradata3 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_oradata3 every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_oratmp0  every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_oratmp0  every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_oratmp1  every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_oratmp1  every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_redo0    every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_redo0    every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00
    jfs0        jfs0_redo1    every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1921 2024-02-01T19:21:00+00:00
    jfs0        jfs0_redo1    every5_c1af0dc4-6143-11ee-ae6e-00a098f7d731.2024-02-01_1931 2024-02-01T19:31:00+00:00

## create

Creation of snapshot is similarly intutive. Here's creation of five snapshots, `test0`, `test1`, `test2`, `test3` and `test4`

    [root@jfs0 current]# ./snapomatic.snapshot create --target jfs_svm1 jfs0_oradata0 --name test0
    Success
    VOLUME        SNAPSHOT STATUS
    ------------- -------- -------
    jfs0_oradata0 test0    Success
    [root@jfs0 current]# ./snapomatic.snapshot create --target jfs_svm1 jfs0_oradata0 --name test1
    Success
    VOLUME        SNAPSHOT STATUS
    ------------- -------- -------
    jfs0_oradata0 test1    Success
    [root@jfs0 current]# ./snapomatic.snapshot create --target jfs_svm1 jfs0_oradata0 --name test2
    Success
    VOLUME        SNAPSHOT STATUS
    ------------- -------- -------
    jfs0_oradata0 test2    Success
    [root@jfs0 current]# ./snapomatic.snapshot create --target jfs_svm1 jfs0_oradata0 --name test3
    Success
    VOLUME        SNAPSHOT STATUS
    ------------- -------- -------
    jfs0_oradata0 test3    Success
    [root@jfs0 current]# ./snapomatic.snapshot create --target jfs_svm1 jfs0_oradata0 --name test4
    Success
    VOLUME        SNAPSHOT STATUS
    ------------- -------- -------
    jfs0_oradata0 test4    Success

## delete

I can also delete snapshots based on age or count. For example, I just created 5 snapshots with a name of `snapshot*`.

I can delete those snapshots (wildcards supported) using a maxcount of 4:

    [root@jfs0 current]# ./snapomatic.snapshot delete --target jfs_svm1 jfs0_oradata0 --name 'test*' --maxcount 4
    Success
    VOLUME        SNAPSHOT STATUS
    ------------- -------- -------
    jfs0_oradata0 test0    Deleted

The `test0` snapshot was the oldest snapshot, which is why it was deleted. The youngest 4 snapshots were retained.


# snapomatic.splitClone

This is a wrapper for `NTAPlib/splitClones.py`.

[root@jfs0 current]# ./snapomatic.splitClones
ERROR: Version dev
          --target
          (svm volume)

          --synchronous
          (wait for split to complete)

          [--debug]
          (show debug output)

          [--restdebug]
          (show REST API calls and responses)


The example below shows the operation run with `--restdebug`. This demonstrates how multiple NTAPlib modules can be used in concert.

[root@jfs0 current]# ./snapomatic.splitClones --target jfs_dev1 myclone --restdebug
->doREST:REST:API: GET https://10.192.160.40/api/storage/volumes?fields=uuid,size,svm.name,svm.uuid,nas.path,aggregates,type&name=myclone&svm.name=jfs_dev1
->doREST:REST:JSON: None
->doREST:REST:RESPONSE: {
->doREST:REST:RESPONSE:  "records": [
->doREST:REST:RESPONSE:   {
->doREST:REST:RESPONSE:    "uuid": "2288f071-d692-11ee-8ab0-00a098f7d731",
->doREST:REST:RESPONSE:    "name": "myclone",
->doREST:REST:RESPONSE:    "size": 53687091200,
->doREST:REST:RESPONSE:    "type": "rw",
->doREST:REST:RESPONSE:    "aggregates": [
->doREST:REST:RESPONSE:     {
->doREST:REST:RESPONSE:      "name": "rtp_a700s_01_SSD_1",
->doREST:REST:RESPONSE:      "uuid": "bb561960-4829-4b0e-bfab-baeb7b4ba3be"
->doREST:REST:RESPONSE:     }
->doREST:REST:RESPONSE:    ],
->doREST:REST:RESPONSE:    "svm": {
->doREST:REST:RESPONSE:     "name": "jfs_dev1",
->doREST:REST:RESPONSE:     "uuid": "ac509ea6-fa33-11ed-ae6e-00a098f7d731",
->doREST:REST:RESPONSE:     "_links": {
->doREST:REST:RESPONSE:      "self": {
->doREST:REST:RESPONSE:       "href": "/api/svm/svms/ac509ea6-fa33-11ed-ae6e-00a098f7d731"
->doREST:REST:RESPONSE:      }
->doREST:REST:RESPONSE:     }
->doREST:REST:RESPONSE:    },
->doREST:REST:RESPONSE:    "_links": {
->doREST:REST:RESPONSE:     "self": {
->doREST:REST:RESPONSE:      "href": "/api/storage/volumes/2288f071-d692-11ee-8ab0-00a098f7d731"
->doREST:REST:RESPONSE:     }
->doREST:REST:RESPONSE:    }
->doREST:REST:RESPONSE:   }
->doREST:REST:RESPONSE:  ],
->doREST:REST:RESPONSE:  "num_records": 1,
->doREST:REST:RESPONSE:  "_links": {
->doREST:REST:RESPONSE:   "self": {
->doREST:REST:RESPONSE:    "href": "/api/storage/volumes?fields=uuid,size,svm.name,svm.uuid,nas.path,aggregates,type&name=myclone&svm.name=jfs_dev1"
->doREST:REST:RESPONSE:   }
->doREST:REST:RESPONSE:  }
->doREST:REST:RESPONSE: }
->doREST:RESULT: 200
->doREST:REASON: OK
->doREST:REST:API: PATCH https://10.192.160.40/api/storage/volumes/2288f071-d692-11ee-8ab0-00a098f7d731
->doREST:REST:JSON: {'clone.split_initiated': 'true'}
->doREST:REST:RESPONSE: {
->doREST:REST:RESPONSE:  "job": {
->doREST:REST:RESPONSE:   "uuid": "0efdf999-d694-11ee-8ab0-00a098f7d731",
->doREST:REST:RESPONSE:   "_links": {
->doREST:REST:RESPONSE:    "self": {
->doREST:REST:RESPONSE:     "href": "/api/cluster/jobs/0efdf999-d694-11ee-8ab0-00a098f7d731"
->doREST:REST:RESPONSE:    }
->doREST:REST:RESPONSE:   }
->doREST:REST:RESPONSE:  }
->doREST:REST:RESPONSE: }
->doREST:RESULT: 202
->doREST:REASON: Accepted
->doREST:REST:API: GET https://10.192.160.40/api/cluster/jobs/0efdf999-d694-11ee-8ab0-00a098f7d731?fields=state,message
->doREST:REST:JSON: None
->doREST:REST:RESPONSE: {
->doREST:REST:RESPONSE:  "uuid": "0efdf999-d694-11ee-8ab0-00a098f7d731",
->doREST:REST:RESPONSE:  "state": "running",
->doREST:REST:RESPONSE:  "message": "Clone split initiated.",
->doREST:REST:RESPONSE:  "_links": {
->doREST:REST:RESPONSE:   "self": {
->doREST:REST:RESPONSE:    "href": "/api/cluster/jobs/0efdf999-d694-11ee-8ab0-00a098f7d731"
->doREST:REST:RESPONSE:   }
->doREST:REST:RESPONSE:  }
->doREST:REST:RESPONSE: }
->doREST:RESULT: 200
->doREST:REASON: OK
Clone split initiated.

The first API validated that the target volume myclone exists.

/api/storage/volumes?fields=uuid,size,svm.name,svm.uuid,nas.path,aggregates,type&name=myclone&svm.name=jfs_dev1

The second API call started the split operation 

->doREST:REST:API: PATCH https://10.192.160.40/api/storage/volumes/2288f071-d692-11ee-8ab0-00a098f7d731
->doREST:REST:JSON: {'clone.split_initiated': 'true'}

This API returned a result code of 202, which means the call was accepted. The final API call used the job UUID to verify that the split operation was running.

->doREST:REST:API: GET https://10.192.160.40/api/cluster/jobs/0efdf999-d694-11ee-8ab0-00a098f7d731?fields=state,message

When run without --synchronous, this script doesn't wait to check whether the operation completed, it only checked to see if the operation got to the point where it was running, as indicated by the "state" field by the response.


# NTAPlib module debug settings

0000 0001 | Show basic workflow information
0000 0010 | Show REST output performed by doREST.py
0000 0100 | Show extra workflow steps beyond just the basics
0000 1000 | Show exec() calls including stdin/stdout performed by doProcess.py
0001 0000 | Show sqlplus related information, mostly within doSqlplus.py and doRMAN.py
