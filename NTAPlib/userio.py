import sys
import getopt
import os
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

def validateoptions(sysargs,validoptions,**kwargs):
    returndict={}
    returndict['MODE']=None
    returndict['OPTS']={}
    passedargs=[]
    usage="Error: Unable to process arguments"
        
    if 'usage' in kwargs.keys():
        usage=kwargs['usage']

    if len(sysargs) < 2:
        fail(usage)

    if 'modes' in kwargs.keys():
        if len(sysargs) > 1 and sysargs[1] in kwargs['modes']:
            returndict['MODE']=sysargs[1]
        else:
            fail(usage)

    optionlist=[]
    if type(validoptions) is dict:
        if 'modes' in kwargs.keys():
            for mode in validoptions.keys():
                if mode == returndict['MODE']:
                    validoptions=validoptions[mode]
        else:
            validoptions=validoptions

    for option in validoptions:
        if validoptions[option] == 'bool':
            optionlist.append(option)
        else:
            optionlist.append(option + "=")

    if returndict['MODE'] is None:
        optlist=sysargs[1:]
    else:
        optlist=sysargs[2:]
    
    try:
        options,args = getopt.getopt(optlist,'',optionlist)
    except getopt.GetoptError as e:
        message(usage)
        fail(str(e))
    except Exception as e:
        fail(usage)

    for key,value in options:
        returndict['OPTS'][str(key).strip('=').strip('--')]=None

    for o, a in options:
        barearg=o
        if o.startswith('--'):
            barearg=o[2:]
        bareoption=set([barearg,barearg + "="]).intersection(validoptions.keys()).pop()
        if validoptions[bareoption] == 'str':
            truevalue=str(a)
        elif validoptions[bareoption] == 'int':
            truevalue=int(a)
        elif validoptions[bareoption] == 'bool':
            truevalue=True
        elif validoptions[bareoption] == 'duration':
            truevalue=duration2seconds(a)
            if not truevalue:
                fail("Illegal value for --" + barearg)
        elif validoptions[bareoption] == 'timestamp':
            try:
                timeformat='%Y-%m-%dT%H:%M:%S%z'
                truevalue=datetime.datetime.strptime(a,timeformat).timestamp()
            except:
                fail(["Format for " + a + " does not match YYYY.MM.DDTHH:MM:SS[TZ]",
                      "Example: May 1st 2019 at 1:35pm US Eastern Daylight Time is 2019-05-01T13:35:00-0400"])
        returndict['OPTS'][barearg]=truevalue
    
    if 'required' in kwargs.keys():
        if type(kwargs['required']) is list or type(kwargs['required']) is tuple:
            for item in kwargs['required']:
                if type(item) is str:
                    if item not in returndict['OPTS'].keys():
                        fail("--" + item.strip('=') + " is required")
                elif type(item) is list:
                    if not set(item).intersection(set(returndict['OPTS'].keys())):
                        fail("One of the following arguments is required: --" + ' --'.join(item).strip('='))
                    elif len(set(item).intersection(set(returndict['OPTS'].keys()))) > 1:
                        fail("Only one of the following arguments is allowed: --" + ' --'.join(item).strip('='))
        elif type(kwargs['required']) is dict:
            for mode in kwargs['required']:
                if mode == returndict['MODE']:
                    for option in kwargs['required'][mode]:
                        if type(option) is str:
                            if option not in returndict['OPTS'].keys():
                                fail("--" + option.strip('=') + " is required")
                        elif type(option) is list:
                            if not set(option).intersection(set(returndict['OPTS'].keys())):
                                fail("One of the following arguments is required: --" + ' --'.join(option).strip('='))
                        elif len(set(item).intersection(set(returndict['OPTS'].keys()))) > 1:
                            fail("Only one of the following arguments is allowed: --" + ' --'.join(item).strip('='))

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
    
    return(returndict)

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
        else:
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
        columnwidths[x]=len(listoflists[0][x])
    for y in range(0,totalrows):
        for x in range(0,totalcolumns):
            if listoflists[y][x] is not None and len(listoflists[y][x]) > columnwidths[x]:
                columnwidths[x] = len(listoflists[y][x])
    firstline=''
    secondline=''
    if 'noheader' in kwargs.keys() and kwargs['noheader']:
        for x in range(0,totalcolumns):
            firstline=firstline + listoflists[0][x] + " " * (columnwidths[x] - len(listoflists[0][x]) + 1) 
        message(firstline.rstrip(),service=service)
    else:
        for x in range(0,totalcolumns):
            firstline=firstline + listoflists[0][x].upper() + " " * (columnwidths[x] - len(listoflists[0][x]) + 1) 
            secondline=secondline + '-' * columnwidths[x] + " "
        message(firstline.rstrip(),service=service)
        message(secondline.rstrip(),service=service)
    for y in range(1,totalrows):
        nextline=''
        for x in range(0,totalcolumns):
            if listoflists[y][x] is not None:
                nextline=nextline + listoflists[y][x]
            if listoflists[y][x] is None:
                nextline=nextline + " " * (columnwidths[x]  + 1) 
            else:
                nextline=nextline + " " * (columnwidths[x] - len(listoflists[y][x]) + 1) 
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
