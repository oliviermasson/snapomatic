# Introduction

Snapomatic is a collection of python utilities to perform useful things using ONTAP REST calls on a linux OS. It does not use any components other than Python and standard OS commands.

The primary scripts are located in the NTAP directory. Many of them are extremely similar. Their function is to perform a RESTful operation and store the data in python lists and dictionaries. NetApp offers a python SDK for REST as well. The difference between that code and snapomatic is snapomatic is intended to be expanded.

You will also find some implementations of those NTAPlib modules in the root directory. For example, "snapomatic.snapshot" shows how to use the NTAPlib modules to list, create, and delete snapshots. The snapomatic.discover utility can perform discover operations on NFS, LVM, and raw devices (it's similar to the NetApp Host Utilities sanlun executable in that respect"

You can run one of those "snapomatic.*" commands with no arguments and see syntax guidance. Some utilities must be run as root because they perform root-level storage operations. 

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

# snapomatic.destroyVolume

This script does what it implies - it destroys a volume. There are no safeties. It will destroy the volume if the user credentials allow it. 

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

In this case, the script discovered that /myLVM was an LVM-based filesystem. It then made a call to `NTAPlib/discoverLVM.py' which mapped this filesystem to its logical volume, and then to the volume group, and then to the underlying physical volumes. It then sent a specially formatted SCSI command to the LUN device backing the PV and ONTAP responded with identifying information.

Finally, you can run this utility directly against the raw LUNs. This is useful for managing Oracle ASM or newly provisioned LUNs that are not yet part of a filesystem. 

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

This script is a wrapper around `NTAPlib/getVolume.py`. As with other scripts, there is a lot more information in the getVolume object. The wrapper shows the basics.

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

You can clone a volume

    [root@jfs0 current]# ./snapomatic.volume clone --target jfs_svm1 jfs0_oradata0 --name newclone
    Cloned newclone from jfs0_oradata0



