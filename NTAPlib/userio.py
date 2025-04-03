import sys
import os
import argparse
import getpass
import random
import datetime

single='1'
multi='any'

def randomtoken(*args):
    if len(args) > 0:
        total=args[0]
    else:
        total=1
    tokens=[]
    for x in range(0,total):
        tokens.append(''.join(random.choice('0123456789abcdef') for _ in range(64)))
    if total==1:
        return(tokens[0])
    else:
        return(tokens)

def mklist(item):
    if type(item) is str or type(item) is int or type(item) is float:
        return([item])
    elif type(item) is list:
        return(item)
    elif type(item) is dict:
        return(list(item.dict.keys()))
    else:
        fail("Illegal type passed to mklist")

def checkdate(field):
    try:
        timeformat='%Y-%m-%dT%H:%M:%S%z'
        truevalue=datetime.datetime.strptime(field,timeformat).timestamp()
        return(truevalue)
    except:
        msg = "Format for " + field + " does not match YYYY-MM-DDTHH:MM:SS[TZ]"
        raise argparse.ArgumentTypeError(msg)

def validateoptions(sysargs,validoptions,**kwargs):
    mode=None
    passedargs=[]
    usage="Error: Unable to process arguments"
        
    if 'usage' in kwargs.keys():
        usage=kwargs['usage']

    if len(sysargs) < 2:
        fail(usage)

    parser=argparse.ArgumentParser(prog=sys.argv[0],description=usage,epilog='')

    dicts=0
    nondicts=0
    for item in validoptions.keys():
        if type(validoptions[item]) is dict:
            dicts+=1
        else:
            nondicts+=1
    if dicts > 0 and nondicts == 0:
        modal=True
        mode=sysargs[1]
        parser.add_argument('mode')
    elif dicts == 0 and nondicts > 0:
        modal=False
    else:
        fail("Corrupt validoptions dictionary passed")
    
    if not modal and 'acceptpaths' in kwargs.keys() and kwargs['acceptpaths']:
        parser.add_argument('paths',nargs='+',default=None)
        
    for item in sysargs:
        if item[:2] == '--':
            passedargs.append(item[2:])
    passedargs=set(passedargs)

    if 'required' in kwargs.keys():
        if modal:
            try:
                requiredoptions=kwargs['required'][mode]
            except:
                fail("Please specify mode: " + '|'.join(list(kwargs['required'].keys())))
        else:
            requiredoptions=kwargs['required']
        for option in requiredoptions:
            if type(option) is list:
                if not set(option).intersection(passedargs):
                    fail("One of the following arguments is required: --" + ' --'.join(option))
    else:
        requiredoptions=False

    if modal:
        validoptions=validoptions[mode]
    else:
        validoptions=validoptions

    for option in validoptions.keys():
        if type(option) is str:
            if requiredoptions and option in requiredoptions:
                requirement=True
            else:
                requirement=False
        else:
            requirement=False
        if validoptions[option] == 'bool':
            parser.add_argument('--' + option, \
                                required=requirement, \
                                action='store_true')
        elif validoptions[option] == 'int':
            parser.add_argument('--' + option, \
                                nargs='?',
                                type=int,
                                default=None,
                                required=requirement)
        elif validoptions[option] == 'str':
            parser.add_argument('--' + option, \
                                nargs='?',
                                default=None,
                                required=requirement)
        elif validoptions[option] == 'multistr':
            parser.add_argument('--' + option, \
                                nargs='+',
                                required=requirement)
        elif validoptions[option] == 'timestamp':
            parser.add_argument('--' + option, \
                                 nargs='?',
                                 default=None,
                                 required=requirement,
                                 type=checkdate)

    args=parser.parse_args()
    
    if 'mutex' in kwargs.keys():
        for item in kwargs['mutex']:
            if len(item) < 1:
                fail("Corrupt mutex lists")
            if len(passedargs.intersection(set(item))) > 1:
                fail("Arguments " + ','.join(item) + " are mutually exclusive")
    
    if 'dependent' in kwargs.keys():
        for key in kwargs['dependent'].keys():
            if key in returndict['OPTS'].keys():
                for item in kwargs['dependent'][key]:
                    if type(item) is str:
                        if item not in returndict['OPTS'].keys():
                            fail("Argument --" + key + " requires the use of ---" + item)
                    elif type(item) is list:
                        if not set(item).intersection(set(returndict['OPTS'].keys())):
                            fail("Argument --" + key + " requires one of the following arguments: --" + ' --'.join(item))
    
    return(args)

def basicmenu(**kwargs):
    returnnames=False
    localchoices=list(kwargs['choices'])
    if 'control' in kwargs.keys():
        localcontrol=kwargs['control']
    else:
        localcontrol=single
    if 'header' in kwargs.keys():
        localheader=kwargs['header']
    if localcontrol == multi:
        localheader="Select one or more of the following"
    else:
        localheader="Select one of the following"
    if 'prompt' in kwargs.keys():
        localprompt=kwargs['prompt']
    else:
        localprompt='Selection'
    if 'sort' in kwargs.keys():
        if kwargs['sort']:
            localchoices.sort()
    if 'returnnames' in kwargs.keys():
        if kwargs['returnnames']:
            returnnames=kwargs['returnnames']
    if 'nowait' in kwargs.keys():
        nowait=kwargs['nowait']
    else:
        nowait=False
        localchoices.append('Continue')

    proceed=False
    selected=[]
    while not proceed:
        message(localheader)
        for x in range(0,len(localchoices)):
            if nowait:
                field="(" + str(x+1) + ") "
                message(field +  localchoices[x])
            else:
                field=str(x+1) + ". "
                if x+1 in selected:
                    message("[X] " + field + localchoices[x])
                else:
                    message("[ ] " + field + localchoices[x])
        number=selectnumber(len(localchoices),prompt=localprompt)
        if nowait:
            if number <= len(localchoices):
                selected=[number]
                proceed=True
        else:
            if number==len(localchoices):
                if len(selected) < 1:
                    linefeed()
                    message("Error: Nothing selected")
                    linefeed()
                else:
                    proceed=True
            elif number in selected:
                if localcontrol==multi:
                    selected.remove(number)
            else:
                if localcontrol==multi:
                    selected.append(number)
                elif localcontrol==single:
                    selected=[number]
    if returnnames:
        newlist=[]
        for item in selected:
            newlist.append(localchoices[item-1])
        return(newlist)
    return(selected)

def ctrlc(signal,frame):
    sys.stdout.write("\nSIGINT received, exiting...\n")
    sys.exit(1)

def banner(message):
    width=80
    fullstring=''
    borderstring=''
    for x in range(0,width): fullstring=fullstring+'#'
    for x in range(0,width-6): borderstring=borderstring + " "
    sys.stdout.write(fullstring + "\n")
    sys.stdout.write("###" + borderstring + "###\n")
    if type(message) is str:
        padding=''
        for x in range(0,width-8-len(message)): padding=padding + ' '
        messagestring=message + padding + "###"
        sys.stdout.write("###  " + messagestring + "\n")
    elif type(message) is list:
        for line in message:
            padding=''
            for x in range(0,width-8-len(line)): padding=padding + ' '
            messagestring=line + padding + "###"
            sys.stdout.write("###  " + messagestring + "\n")
    sys.stdout.write("###" + borderstring + "###\n")
    sys.stdout.write(fullstring + "\n")
    sys.stdout.flush()

def debug(obj):
    
    try:
        message(obj.call,service='->'.join([obj.apicaller,obj.apibase]) + ":REST:API")
    except Exception as e:
        pass

    try:
        message(obj.jsonin,service='->'.join([obj.apicaller,obj.apibase]) + ":REST:JSON")
    except Exception as e:
        pass

    try:
        message(obj.jsonout,service='->'.join([obj.apicaller,obj.apibase]) + ":REST:RESPONSE")
    except Exception as e:
        pass

    try:
        message(obj.result,service='->'.join([obj.apicaller,obj.apibase]) + ":RESULT")
    except Exception as e:
        message(e,service='->'.join([obj.apicaller,obj.apibase]) + ":RESULT")
        
    try:
        message(obj.reason,service='->'.join([obj.apicaller,obj.apibase]) + ":REASON")
    except Exception as e:
        message(e,service='->'.join([obj.apicaller,obj.apibase]) + ":REASON")
    
    try:
        message(obj.stdout,service='->'.join([obj.apicaller,obj.apibase]) + ":STDOUT")
    except Exception as e:
        message(e,service='->'.join([obj.apicaller,obj.apibase]) + ":STDOUT")

    try:
        message(obj.stderr,service='->'.join([obj.apicaller,obj.apibase]) + ":STDERR")
    except Exception as e:
        message(e,service='->'.join([obj.apicaller,obj.apibase]) + ":STDERR")

def message(*args,**kwargs):    
    if 'prenewline' in kwargs.keys():
        if kwargs['prenewline']:
            linefeed()
    leader=''
    if 'service' in kwargs.keys() and kwargs['service'] is not None:
        leader=leader + kwargs['service'] + ": "
    if len(args) > 0:
        if type(args[0]) is list:
            for line in args[0]:
                sys.stdout.write(leader + line.rstrip() + "\n")
                sys.stdout.flush()
        else:
            sys.stdout.write(leader + str(args[0]).rstrip() + "\n")
            sys.stdout.flush()

def error(args,**kwargs):
    if type(args) is list:
        for line in args:
            sys.stdout.write("ERROR: " + line + "\n")
    else:
        sys.stdout.write("ERROR: " + args + "\n")

def fail(args,**kwargs):
    if type(args) is list:
        for line in args:
            sys.stdout.write("ERROR: " + line + "\n")
    else:
        sys.stdout.write("ERROR: " + args + "\n")
    sys.exit(1)

def warn(args,**kwargs):
    if 'prenewline' in kwargs.keys():
        if kwargs['prenewline']:
            linefeed()
    if type(args) is list:
        for line in args:
            sys.stdout.write("WARNING: " + line + "\n")
            sys.stdout.flush()
    else:
        sys.stdout.write("WARNING: " + args + "\n")
        sys.stdout.flush()

def justexit():
    sys.stdout.write("Exiting... \n")
    sys.exit(0)

def linefeed():
    sys.stdout.write("\n")
    sys.stdout.flush()

def yesno(string):
    answer=None
    while answer is None:
        usersays=input(string + " (y/n) ").lower()
        if usersays == 'y':
            answer=True
        elif usersays == 'n':
            answer=False
    return(answer)

def ask(string,**kwargs):
    answer=None
    if 'default' in kwargs.keys():
        defaultstring=' [' + kwargs['default'] + ']'
    else:
        defaultstring=''
    if 'hide' in kwargs.keys() and kwargs['hide']:
        usersays=getpass.getpass(string + defaultstring + ": ")
    else:
        usersays=input(string + defaultstring + ": ")
    if usersays=='' and not defaultstring=='':
        return(kwargs['default'])
    else:
        return(usersays)

def selectnumber(*args,**kwargs):
    answer=0
    maximum=args[0]
    if 'prompt' in kwargs.keys():
        prompt=kwargs['prompt']
    else:
        prompt="Selection"
    while answer < 1 or answer > maximum:
        try:
            answer=int(input(prompt + ": (1-" + str(maximum) + "): "))
        except KeyboardInterrupt:
            justexit()
        except Exception as e:
            answer=0
    return(answer)

def providenumber(maximum):
    answer=0
    while answer < 1 or answer > maximum:
        try:
            answer=int(input("(1-" + str(maximum) + "): "))
        except KeyboardInterrupt:
            justexit()
        except Exception as e:
            answer=0
    return(answer)

def grid(listoflists,**kwargs):
    if 'service' in kwargs.keys():
        service=kwargs['service']
    else:
        service=None
    totalcolumns=len(listoflists[0])
    totalrows=len(listoflists)
    columnwidths={}
    for x in range(0,totalcolumns):
        columnwidths[x]=len(str((listoflists[0][x])))
    for y in range(0,totalrows):
        for x in range(0,totalcolumns):
            if listoflists[y][x] is not None and len(str(listoflists[y][x])) > columnwidths[x]:
                columnwidths[x] = len(listoflists[y][x])
    firstline=''
    secondline=''
    if 'noheader' in kwargs.keys() and kwargs['noheader']:
        for x in range(0,totalcolumns):
            firstline=firstline + str(listoflists[0][x]) + " " * (columnwidths[x] - len(str(listoflists[0][x])) + 1) 
        message(firstline.rstrip(),service=service)
    else:
        for x in range(0,totalcolumns):
            firstline=firstline + str(listoflists[0][x]).upper() + " " * (columnwidths[x] - len(str(listoflists[0][x])) + 1) 
            secondline=secondline + '-' * columnwidths[x] + " "
        message(firstline.rstrip(),service=service)
        message(secondline.rstrip(),service=service)
    for y in range(1,totalrows):
        nextline=''
        for x in range(0,totalcolumns):
            if listoflists[y][x] is not None:
                nextline=nextline + str(listoflists[y][x])
            if listoflists[y][x] is None:
                nextline=nextline + " " * (columnwidths[x]  + 1) 
            else:
                nextline=nextline + " " * (columnwidths[x] - len(str(listoflists[y][x])) + 1) 
        message(nextline.rstrip(),service=service)

def duration2seconds(value):
    if not value[-1].isalpha:
        value=value + 'd'
    if value[-1] == 's':
        return(int(a[:-1]))
    elif value[-1] == 'm':
        return(int(a[:-1])*60)
    elif value[-1] == 'h':
        return(int(a[:-1])*60*60)
    elif value[-1] == 'd':
        return(int(value[:-1])*60*60*24)
    else:
        return(None)
