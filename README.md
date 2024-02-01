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

== ONTAP Credentials

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


