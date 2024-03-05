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

In this case, the script discovered that /myLVM was an LVM-based filesystem. It then made a call to `NTAPlib/discoverLVM.py` which mapped this filesystem to its logical volume, and then to the volume group, and then to the underlying physical volumes. It then used NTAPlib/discoverLUN.py to send a specially formatted SCSI command to the LUN device backing the PV and ONTAP responded with identifying information.

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

# snapomatic.cloneSAN4DR

This is a more complicated workflow created for a customer POC. It illustrates stringing together multiple modules. The full details will be covered in a future project, but the basic requirement was this:

* The ability to select one or more snapmirrored volumes, and
* Clone the volumes. Do NOT break the mirrors. This was required so DR can be tested without interrupting replication.
* Create the clone of the target volumes to a timepoint that is immediately *after* or immediately *before* the desired recovery point. 
* Map all LUNs
* Bring up databases, but this action is performed by a 2nd script. Keep reading to find that example...

This script works as follows:

[root@jfs0 current]# ./snapomatic.cloneSAN4DR
clone4DR --target
          (name of target svm and volumes)
          (syntax: svm volume or svm volume/lun, wildcards accepted)

          --snapshot_prefix
          (optionally restrict search to snapshots with a prefix_ syntax)
          --igrouptoken
          (identifies the _ delimited position of the igroup)

          --recoverypoint
          (recovery timestamp in YYYY-MM-DDTHH:MM:SS+ZZZZ)

          --after|--before
          (used with --recoverypoint)
          (look for snapshots before|after specified recoverypoint)
          (default behavior is AFTER)

          [--igroupname]
          (optionally specifies the igroup name, %=token

          [--split]
          (split the cloned volumes)

          [--debug]
          (show debug output)

          [--restdebug]
          (show REST API calls and responses)

As an example, the command could be run like this:

    [root@jfs0 current]# ./snapomatic.cloneSAN4DR --target jfs_dev2 'ora_DRcluster_*' \ 
                                                  --recoverypoint 2024-02-20T12:30:00+0500 \
                                                  --before \
                                                  --igrouptoken 2

The logic would then do this:

1. Identify all snapmirrored volumes on `jfs_dev` matching the pattern `ora_DRcluster_*`
2. Identify the snapshot immediately *before* the specified timestamp
3. Create a clone of those volumes. It will prepend the string `failover_` to the clone name
4. Because we are not breaking the mirrors, that clone will be created using the identified snapshot
5. Enumerate all of the LUNs in the newly cloned volumes
6. Extract the 2nd token of the original _ character delimted volume name to be used as the igroup name
7. In this case, map the LUNs to the igroup "DRcluster" because that was the 2nd token in the volume name

We also had a requirement to selectively clone only certain LUNs. As SnapMirror works on the volume level, we still clone all LUNs but only matching LUNs are mapped. The syntax for this operation is as follows:


    [root@jfs0 current]# ./snapomatic.cloneSAN4DR --target jfs_dev2 'ora_DRcluster_*/LUN2' \ 
                                                  --recoverypoint 2024-02-20T12:30:00+0500 \
                                                  --before \
                                                  --igrouptoken 2

In this example, the script is looking for a volume/LUN pattern match of oraDRcluster_*/LUN2.

As an example of running this at large scale, the following two commands could be run:


    [root@jfs0 current]# ./snapomatic.cloneSAN4DR --target jfs_dev2 'ora_DRcluster_.*dbf' \ 
                                                  --recoverypoint 2024-03-03T12:30:00+0500 \
                                                  --before \
                                                  --igrouptoken 2
    
    [root@jfs0 current]# ./snapomatic.cloneSAN4DR --target jfs_dev2 'ora_DRcluster_.*logs' \ 
                                                  --recoverypoint 2024-03-03T12:30:00+0500 \
                                                  --after \
                                                  --igrouptoken 2

The result of this two commands are the following LUNs, mapped, inside of cloned volumes. The LUNs in the `_dbf` volumes were cloned from a snapshot created *prior* to the desired recoverypoint, and the LUNS in the `_logs` volumes were cloned from a snapshot created immediately *after* the desired recoverypoint. This is the starting point for Oracle and most database recovery operations - you start with a copy of datafiles prior to the point-in-time recovery mark, and a copy of logs from after the PIT mark. You then replay logs to the desired point.

    rtp-a700s-c02::> lun show -vserver jfs_dev2 -fields path /vol/fail*
    vserver  path
    -------- ----------------------------------------
    jfs_dev2 /vol/failover_ora_DRcluster_BII_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_BII_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_BII_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_BII_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_BII_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_BII_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_CRM_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_CRM_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_CRM_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_CRM_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_CRM_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_CRM_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_DEV_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_DEV_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_DEV_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_DEV_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_DEV_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_DEV_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_DWH_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_DWH_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_DWH_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_DWH_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_DWH_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_DWH_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_ERP_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_ERP_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_ERP_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_ERP_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_ERP_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_ERP_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_FCST_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_FCST_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_FCST_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_FCST_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_FCST_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_FCST_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_HRS_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_HRS_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_HRS_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_HRS_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_HRS_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_HRS_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_SPC_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_SPC_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_SPC_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_SPC_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_SPC_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_SPC_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_TST_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_TST_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_TST_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_TST_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_TST_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_TST_logs/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_UAT_dbf/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_UAT_dbf/LUN1
    jfs_dev2 /vol/failover_ora_DRcluster_UAT_dbf/LUN2
    jfs_dev2 /vol/failover_ora_DRcluster_UAT_dbf/LUN3
    jfs_dev2 /vol/failover_ora_DRcluster_UAT_logs/LUN0
    jfs_dev2 /vol/failover_ora_DRcluster_UAT_logs/LUN1
    60 entries were displayed.
    
# snapomatic.RACfailover

This next script is the next step after using snapmatic.clone4DR. The purpose of clone4DR was to identify and clone the volumes and snapshots that made up a usable DR copy of the database at the desired recoverypoint. The purpose of RACfailover is to discover the contents of the newly cloned LUNs and register and recovery the databases.

Syntax:

    snapmatic.RACfailover --volpattern
              (target volume pattern)

              --recoverypoint
              (recovery timestamp in YYYY-MM-DDTHH:MM:SS[TZ])

                --debug
              (print process STDOUT and STDERR)

                --iscsi
              (Scan for iSCSI LUNs)

                --noscan
              (Bypass LUN scanning)

                --noafd
              (Bypass ASM Filter Driver scanning)

                --noasmlib
              (Bypass ASMlib scanning)


The following output shows the results of completing the failover of the 10 databases that were cloned in the clone4DR step.

The command is just this:

    [root@jfs8 current]# ./snapomatic.RACfailover --volpattern 'failover_ora_DRcluster_*' --iscsi --recoverypoint 2024-03-03T12:30:00+0500
    Updating iSCSI targets

This is going to trigger the following steps:

1. Rescan all LUNs, including an iSCSI refresh (the test environment uses iSCSI)
2. Perform discovery on all LUNs that are hosted on volumes matching the pattern "failover_ora_DRcluster". The clone4DR script cloned volumes matching ora_DRcluster* and prepended failover_ onto the volumes. The RACfailover script will look for LUNs matching this pattern.
3. Attempt to discover ASMlib and ASM Filter Driver signatures on the LUNs and build ASMlib/AFD devices if required
4. Mount all discovered ASM diskgroups on all hosts in the RAC cluster
5. Read the contents of those ASM diskgroups. The script is looking for directories containing an spfile and a passwd file. If those files are found, that means the containing directory is the name of a database that has been cloned and should be brought online.
6. Identify all installed versions of Oracle Database. There could be multiple versions. The script will walk the versions and attempt to read the spfile discovered on the ASM diskgroups. Once the script can succesfully read this data, the script can determine the correct version of Oracle for that database.
7. Register the databases with RAC using srvctl.
8. Mount the database
9. Recover the database to the specified recoverypoint
10. Open the database.

The output looks like this:

    Sleeping for 10 seconds while multipath maps are built

This sleep step is required to avoid race conditions between multipathd and optional packages such as the ASM Filter Driver.

    Discovering AFD devices...
    Refreshing AFD configuration

    Refreshing ASMlib configuration
    Unable to scan ASMlib disks on host jfs8

Some of the ASM diskgroups may have been under the control of AFD or ASMlib. The required administrative commands to rescan for those devices was invoked. In this test environment, ASMlib was not installed so an error was reported.

    Retrieving ASM diskgroup names
    >> Identified diskgroup HRLOGS
    >> Identified diskgroup DWHDATA
    >> Identified diskgroup SUPPLYLOGS
    >> Identified diskgroup CRMLOGS
    >> Identified diskgroup UATDATA
    >> Identified diskgroup DEVLOGS
    >> Identified diskgroup TSTLOGS
    >> Identified diskgroup ERPLOGS
    >> Identified diskgroup FORECASTDATA
    >> Identified diskgroup TSTDATA
    >> Identified diskgroup DEVDATA
    >> Identified diskgroup BILOGS
    >> Identified diskgroup CRMDATA
    >> Identified diskgroup HRDATA
    >> Identified diskgroup FORECASTLOGS
    >> Identified diskgroup SUPPLYDATA
    >> Identified diskgroup ERPDATA
    >> Identified diskgroup DWHLOGS
    >> Identified diskgroup BIDATA
    >> Identified diskgroup UATLOGS

The names of the ASM diskgroups were identified using kfed, Oracle's low-level disk scanning utility. Once we have the name of the diskgroups, they can be mounted. It's possible this script was run more than once, so before attempting to mount, the script will check on which are already mounted.

    Identifying currently mounted ASM diskgroups
    
    Mounting ASM diskgroups...
    Mounting HRLOGS on host jfs8
    Mounting DWHDATA on host jfs8
    Mounting SUPPLYLOGS on host jfs8
    Mounting CRMLOGS on host jfs8
    Mounting UATDATA on host jfs8
    Mounting DEVLOGS on host jfs8
    Mounting TSTLOGS on host jfs8
    Mounting ERPLOGS on host jfs8
    Mounting FORECASTDATA on host jfs8
    Mounting TSTDATA on host jfs8
    Mounting DEVDATA on host jfs8
    Mounting BILOGS on host jfs8
    Mounting CRMDATA on host jfs8
    Mounting HRDATA on host jfs8
    Mounting FORECASTLOGS on host jfs8
    Mounting SUPPLYDATA on host jfs8
    Mounting ERPDATA on host jfs8
    Mounting DWHLOGS on host jfs8
    Mounting BIDATA on host jfs8
    Mounting UATLOGS on host jfs8

In this case, the databases were divided into a datafile and a log ASM diskgroup. This is required for PIT recovery as explained above. The copy of the datafile needs to be from an earlier point in time than the logs. 
    
    Discovering contents of ASM diskgroup
    Retrieving contents of diskgroups...
    >> Running asmcmd...
    >> Found directory HRU on diskgroup +HRDATA
    >> Found directory BIU on diskgroup +BILOGS
    >> Found directory CRMU on diskgroup +CRMLOGS
    >> Found directory DEVU on diskgroup +DEVLOGS
    >> Found directory DWHU on diskgroup +DWHLOGS
    >> Found directory ERPU on diskgroup +ERPLOGS
    >> Found directory FCSTU on diskgroup +FORECASTLOGS
    >> Found directory HRU on diskgroup +HRLOGS
    >> Found directory SUPPLYU on diskgroup +SUPPLYLOGS
    >> Found directory TSTU on diskgroup +TSTLOGS
    >> Found directory UATU on diskgroup +UATLOGS
    >> Found directory BIU on diskgroup +BIDATA
    >> Found directory CRMU on diskgroup +CRMDATA
    >> Found directory DEVU on diskgroup +DEVDATA
    >> Found directory DWHU on diskgroup +DWHDATA
    >> Found directory ERPU on diskgroup +ERPDATA
    >> Found directory FCSTU on diskgroup +FORECASTDATA
    >> Found directory SUPPLYU on diskgroup +SUPPLYDATA
    >> Found directory TSTU on diskgroup +TSTDATA
    >> Found directory UATU on diskgroup +UATDATA
    >> Found directory HRSU on diskgroup +HRDATA
    >> Identified database HRU
    >> Identified database BIU
    >> Identified database CRMU
    >> Identified database DEVU
    >> Identified database DWHU
    >> Identified database ERPU
    >> Identified database FCSTU
    >> Identified database SUPPLYU
    >> Identified database TSTU
    >> Identified database UATU

The output above reflects a search for directories containing an spfile and a passwd file. If those two files exist, then the name of the database should be the containing directory. The script has now identified at least part of a database, but there's no guarantee all LUNs were cloned at this point. There's also no way to know which version of Oracle is associated with this database. 
    
    Oracle version map: {'19.0.0.0.0': '/orabin19', '19.18.0.0.0': '/orabin19'}
    Extracting spfiles...
    >>  Attempting to create pfile from spfile +HRDATA/HRU/PARAMETERFILE/spfile.268.1144254031
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database HRU configured for 19.0.0
    >> Database HRU has db_name of NHRU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for HRU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +BIDATA/BIU/PARAMETERFILE/spfile.267.1132063661
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database BIU configured for 19.0.0
    >> Database BIU has db_name of NBIU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for BIU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +CRMDATA/CRMU/PARAMETERFILE/spfile.259.1132093037
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database CRMU configured for 19.0.0
    >> Database CRMU has db_name of NCRMU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for CRMU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +DEVDATA/DEVU/PARAMETERFILE/spfile.267.1132086883
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database DEVU configured for 19.0.0
    >> Database DEVU has db_name of NDEVU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for DEVU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +DWHDATA/DWHU/PARAMETERFILE/spfile.267.1132093245
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database DWHU configured for 19.0.0
    >> Database DWHU has db_name of NDWHU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for DWHU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +ERPDATA/ERPU/PARAMETERFILE/spfile.267.1132101237
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database ERPU configured for 19.0.0
    >> Database ERPU has db_name of NERPU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for ERPU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +FORECASTDATA/FCSTU/PARAMETERFILE/spfile.267.1132102107
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database FCSTU configured for 19.0.0
    >> Database FCSTU has db_name of NFCSTU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for FCSTU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +SUPPLYDATA/SUPPLYU/PARAMETERFILE/spfile.267.1132102147
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database SUPPLYU configured for 19.0.0
    >> Database SUPPLYU has db_name of NSUPPLYU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for SUPPLYU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +TSTDATA/TSTU/PARAMETERFILE/spfile.267.1132140189
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database TSTU configured for 19.0.0
    >> Database TSTU has db_name of NTSTU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for TSTU
      >> Database registration successful
    
    >>  Attempting to create pfile from spfile +UATDATA/UATU/PARAMETERFILE/spfile.267.1132140185
      >> Using ORACLE_HOME /orabin19
      >> Parsing pfile
    >> Database UATU configured for 19.0.0
    >> Database UATU has db_name of NUATU
      >> Compatible ORACLE_HOME found at /orabin19
    >> Creating directory structure
      >> Running mkdir commands on host jfs8
    >> Running svrctl add for UATU
      >> Database registration successful
    
The output above showed the script first identifying all installed versions of Oracle Database on the server, followed by and attempt to create a pfile from the text spfile. The spfile cannot be reliably read directly. It must be converted to a text pfile first. In the unlikely event that a given version of Oracle was unable to read the spfile, another version of Oracle will be used. 

Eventually, the version of Oracle for each database will be identified. Once this happens, a `srvctl add database` command is performed. You can see the "Database registration succesful" message above.

The next step is mounting the databases. They cannot be directly opened because the state of the datafiles and the state of the log files do not match.
    
    Starting databases...
    >> Mounting database HRU
      >> Database mounted
    >> Mounting database BIU
      >> Database mounted
    >> Mounting database CRMU
      >> Database mounted
    >> Mounting database DEVU
      >> Database mounted
    >> Mounting database DWHU
      >> Database mounted
    >> Mounting database ERPU
      >> Database mounted
    >> Mounting database FCSTU
      >> Database mounted
    >> Mounting database SUPPLYU
      >> Database mounted
    >> Mounting database TSTU
      >> Database mounted
    >> Mounting database UATU
      >> Database mounted
    
The next step is issuing the recovery command. 

In this case, the command is recover `database until time '2024-03-03 07:30:00';` That timestamp does *not* match the timestamp provided at the CLI exactly. The sqlplus command needs to use the local timezone of the server, which in this case was EST, five hours earlier than the 12:00 time provided at the CLI. 

    Recovering databases...
    >> Recovering database HRU
    Media recovery complete.
    >> Database HRU recovery complete
    >> Recovering database BIU
    Media recovery complete.
    >> Database BIU recovery complete
    >> Recovering database CRMU
    Media recovery complete.
    >> Database CRMU recovery complete
    >> Recovering database DEVU
    Media recovery complete.
    >> Database DEVU recovery complete
    >> Recovering database DWHU
    Media recovery complete.
    >> Database DWHU recovery complete
    >> Recovering database ERPU
    Media recovery complete.
    >> Database ERPU recovery complete
    >> Recovering database FCSTU
    Media recovery complete.
    >> Database FCSTU recovery complete
    >> Recovering database SUPPLYU
    Media recovery complete.
    >> Database SUPPLYU recovery complete
    >> Recovering database TSTU
    Media recovery complete.
    >> Database TSTU recovery complete
    >> Recovering database UATU
    Media recovery complete.
    >> Database UATU recovery complete

As long as recovery completed, the databases are then opened:

    Opening databases...
    >> Opening database HRU
    >> Database HRU is open
    >> Opening database BIU
    >> Database BIU is open
    >> Opening database CRMU
    >> Database CRMU is open
    >> Opening database DEVU
    >> Database DEVU is open
    >> Opening database DWHU
    >> Database DWHU is open
    >> Opening database ERPU
    >> Database ERPU is open
    >> Opening database FCSTU
    >> Database FCSTU is open
    >> Opening database SUPPLYU
    >> Database SUPPLYU is open
    >> Opening database TSTU
    >> Database TSTU is open
    >> Opening database UATU
    >> Database UATU is open

A final summary of confirmed failovers is then printed.

    Results:
    Database HRU failover complete
    Database BIU failover complete
    Database CRMU failover complete
    Database DEVU failover complete
    Database DWHU failover complete
    Database ERPU failover complete
    Database FCSTU failover complete
    Database SUPPLYU failover complete
    Database TSTU failover complete
    Database UATU failover complete

There are many options for how to complete this procedure. If you can think of something you'd like to see demonstrated, let me know, but the scripts themselves are intended to be modified as required and should be reasonably self-explanatory if you understand the logical workflow being performed.
    
# NTAPlib module debug settings

The following list shows the debug settings when using the NTAPlib modules. 

    0000 0001 | Show basic workflow information
    0000 0010 | Show REST output performed by doREST.py
    0000 0100 | Show extra workflow steps beyond just the basics
    0000 1000 | Show exec() calls including stdin/stdout performed by doProcess.py
    0001 0000 | Show sqlplus related information, mostly within doSqlplus.py and doRMAN.py
