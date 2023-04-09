#!/usr/bin/env python
"""
This is a flexible mail test client used to send email messages.
"""

import thread
import sys
import os
import time
import signal
import socket
import traceback
import random

import sockit

#import pdb

VER = "0.12"

TODO = """
    Fix RSET functionality (currently broken)
    Option to exit program if 'x' connections are refused/dropped.
    Option to save output of sessions, each in its own file.
    Option to display stat output in table, with colum headers.
    Option to display TID before timestamp on log lines
"""

SMTP_PORT = 25
ARG_GOOD, ARG_USAGE, ARG_ERROR = range(1,4)
CHUNK = (128*1024)

### Global messages counters
g_msgcnt  = 0  # global count of total messages, shared by all threads for one process
g_msggood = 0  # count of successful msgs
g_msgbad  = 0  # count of failed msgs (timeouts, network errors, etc.)
g_proc    = 0  # proc arg
g_intcnt  = 0  # count ctl-C keys
g_quit    = False  # set True for orderly shutdown
### End globals

### Text used for auto-generated msg body

SAMPLE1 = "This is a mailit.py auto-generated test message.\r\n"

SAMPLE2 = "\
This is a mailit.py auto-generated test message.\r\n\
\r\n\
Soldiers of my Old Guard: I bid you farewell. For twenty years I have constantly \r\n\
accompanied you on the road to honor and glory. In these latter times, as in the days \r\n\
of our prosperity, you have invariably been models of courage and fidelity. With men \r\n\
such as you our cause could not be lost; but the war would have been interminable; \r\n\
it would have been civil war, and that would have entailed deeper misfortunes on France.\r\n\
I have sacrificed all of my interests to those of the country.\r\n\
I go, but you, my friends, will continue to serve France. Her happiness was my only \r\n\
thought. It will still be the object of my wishes. Do not regret my fate; if I have \r\n\
consented to survive, it is to serve your glory. I intend to write the history of the \r\n\
great achievements we have performed together. Adieu, my friends. Would I could press you \r\n\
all to my heart.\r\n\
Napoleon Bonaparte - April 20, 1814\r\n\
\r\n\
"

# Sample exip command, if user requests auto-generated exip, we just use this literal text.
EXIP=":$$10.15.25.250$$15$$d.UNK-LNXAArvq4P_uK2fhwNAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.AAAAAAAAAAAAAAAAAAApZ9vu7Nc-UpnQKBbshwvslHUr_mC0sJC_gR3PcE8P.o9rJ09TcvIjhAAAAAAA7RVNkARqPPiMqqIyV6-XOJ_DfFkbA$$0"

#--------------------------------------------------------------------------------

def ExceptionInfo(maxTBlevel=5):
    """Print human readable exception info."""
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)

#--------------------------------------------------------------------------------

def print_usage(verdict):
    """Print usage and exit."""

    cmd = sys.argv[0].split('/')[-1] # get basename of program (chop off any path)

    if verdict == ARG_USAGE:
        print """

Usage: %s [hostname]
       RFC821:  {from=me@ctdev.net} {to=you@ctdev.net} {helo=cookie.ctdev.net} 
       RFC822:  {subject=testing} {date=...} {file=None} {size=100}
       Counts:  {timeout=30} {count=1} {rate=0.5} {drate=0} {lrate=0} {[no]rset}
       IronMail:{exip=...}
       Process: {proc=1} {thread=1} {lag=0} {[no]error} {bind=ip1,ip2,...}
       Display: {[no]echo} {[no]body} {[no]time} {line=0} {dot=1} {stat=10} 
                {debug} 

A simple and easy to use test email client. It simply sends test emails. 
The only required argument is the hostname to which to deliver mail.
All other mail options will be generated if not provided.

hostname,  required, the mail server to which we connect and send the msg.
           E.g. "im123.ctdev.net" "10.14.2.123" "mydev:443" etc.

RFC 821 OPTIONS:
from       RFC 821 smtp header
to         RFC 821 smtp header, multiple rcpt's separated by commas.
helo       use helo and optionally specify the hostname.
ehlo       use ehlo and optionally specify hostname.

RFC 822 OPTIONS:
subject    RFC 822 header, subject="This is a teset"
date       RFC 822 header, date="Fri, 12 Oct 2007 09:59:07 -0500"
size       If auto-generating test msg body, this sets msg size in bytes.
           E.g. 100 (bytes), 50K (kb), 10M (mb).
file       File to use for the email RFC 822 body, instead of the default
           program generated test body. If file is a directory, then all
           files in directory are used round-robin.

COUNTS:
timeout,   the seconds to wait on a response before quiting.
count,     how many emails to send. 1=default, 0=stress test.
rate,      pause for x seconds between emails. 0.5, 1, etc.
drate,     pause for x seconds after DATA cmd, 0.5, 1, etc.
lrate,     pause for x seconds after each body line, 0.5, 1, etc.
[no]rset,  do/do not reuse the current connection with RSET cmd.

IRONMAIL:
exip,      send an exip cmd after rcpt to, using provided text.
           If given as "", then send auto-generated exip.

PROCESS CONTROL:
proc,      number of simultaneous processes. (not recommended)
thread,    number of threads per processes. (works great)
lag,       seconds to pause between starting each thread, e.g. 0.05 etc.
[no]error, do/do not quit on smtp error nor network error.
bind,      IP to which we bind for outboud connection.
           Give comma separated list to round-robin.

DISPLAY OPTIONS:
[no]echo,  do/do not echo smtp data to stdout.
[no]body,  do/do not echo the msg body \"DATA\" section to stdout.
[no]time,  do/do not print timestamps on each smtp output line.
dot,       print one dot for each 'x' mails sent.
line,      print msg total after each 'x' mails sent, 0 to disable
stat,      print stats every x seconds, 0 to disable.
debug,     print out extra program debug info.

TO-DO List for future versions: %s

Simple test:  %s smtp01
More detail:  %s smtp01 from=me@ctdev.net to=you@ctdev.net file=junk.txt
Stress test:  %s smtp01 count=0 thread=100
Stress test output:
   cnt: 3671, sec: 10, longest: 0, msgs/sec: 367.....................................
   cnt: 3699, sec: 10, longest: 0, msgs/sec: 369......................................
   cnt: 3777, sec: 10, longest: 0, msgs/sec: 377.....................................
Notes: Each '.' = 10 msgs sent. cnt = msgs sent since last update, sec = seconds since
last update, longest = longest time in seconds to send a single message.

Version v%s, Copyright (c) 2007 Secure Computing Corporation. 
Bugs to John_Masinter@SecureComputing.com

""" %(cmd, TODO, cmd,cmd,cmd,VER)

    elif verdict == ARG_ERROR:
        print "For help: %s -h\n" %cmd

    sys.exit(1)

#--------------------------------------------------------------------------------

def write_log(msg, ARG):
    tid = tim = ""
    if ARG['TIME']: tim = time.strftime("%H:%M.%S:") 
    if ARG['TID']:  tid = "%s:" % thread.get_ident()
    print "%s%s%s:" % (tid, tim, msg)

#--------------------------------------------------------------------------------

def get_size(txt):
    """return int value for strings like "100", "100K", "100M". """
    val = 0
    for i in range(len(txt)):
        ch = txt[i:i+1].lower()
        if ch >= "0" and ch <= "9":
            val = (val*10) + int(ch)
        elif ch == "k":
            val = val * 1024
        elif ch == "m":
            val = val * 1024 * 1024
    return val

#--------------------------------------------------------------------------------

def parse_params():
    """Parse the command line options."""
    # default values
    ARG = { "HOST":None, "PORT":SMTP_PORT, 
            "FROM":"me@ctdev.net", "TO":"you@ctdev.net", "HELO":None, "EHLO":None,
            "SUB":"Testing message", "DATE":"Not Implemented", 
            "FILE":None, "FILELIST":[], "FILEPOS":0,
            "TIMEOUT":30, "SIZE":0, "COUNT":1, "RATE":0, "DRATE":0, "LRATE":0,
            "PROC":1, "THREAD":1, "LAG":0, "EOE":True, "TEXTB":None, "TEXTL":[],
            "ECHO":True, "BODY":False, "TIME":True, "SOCKMSG":False,
            "DOT":1, "LINE":0, "STAT":10.0, 
            "DEBUG":False, "RSET":False, "CONNECTED":False, 
            "BIND":[], "BINDCNT":0, "EXIP":None, "TID":False
    }
    # Notes: TEXTB is a block of default auto-generated text for messge body.
    #        TEXTL is same text, but stored as a list of individual lines.

    verdict = ARG_GOOD
    host = None

    # check number of args
    argc = len(sys.argv)
    if argc < 2:
        verdict = ARG_USAGE

    # get hostname for helo cmd
    if verdict==ARG_GOOD:
        hname = socket.gethostname().split(".")[0]
        if len(hname) < 1:
            print "System hostname not set. Using name=cookie"
            hname="cookie"

    # help requested?
    if verdict==ARG_GOOD and sys.argv[1] in ("-h","-?","--help"):
        verdict = ARG_USAGE

    # parse each cmd line arg
    if verdict==ARG_GOOD:
        for i in range (1, argc):
            arg = sys.argv[i].split("=",1)

            # hostname (does not require "host=" tag)
            if len(arg) == 1 and not ARG['HOST']:
                ARG['HOST'] = arg[0]

            # text values
            elif arg[0] == "from":
                ARG['FROM'] = arg[1]
            elif arg[0] == "to":
                ARG['TO'] = arg[1]
            elif arg[0][0:3] == "sub":
                ARG['SUB'] = arg[1]
            elif arg[0] == "file":
                ARG['FILE'] = arg[1]
            elif arg[0] == "helo":
                if len(arg) > 1: ARG['HELO'] = arg[1]
                else:            ARG['HELO'] = hname
            elif arg[0] == "ehlo":
                if len(arg) > 1: ARG['EHLO'] = arg[1]
                else:            ARG['EHLO'] = hname
            elif arg[0] == "host":
                ARG['HOST'] = arg[1]
            elif arg[0] == "bind":
                ARG['BIND'] = arg[1].split(',')
            elif arg[0] == "exip":
                ARG['EXIP'] = arg[1]

            # integer values
            elif arg[0] == "size":
                ARG['SIZE'] = get_size(arg[1])
            elif arg[0] == "count":
                ARG['COUNT'] = int(arg[1])
            elif arg[0] == "timeout":
                ARG['TIMEOUT'] = int(arg[1])
            elif arg[0] == "rate":
                ARG['RATE'] = float(arg[1])
            elif arg[0] == "drate":
                ARG['DRATE'] = float(arg[1])
            elif arg[0] == "lrate":
                ARG['LRATE'] = float(arg[1])
            elif arg[0][0:4] == "proc":       # match proc or procs
                ARG['PROC'] = int(arg[1])
            elif arg[0][0:6] == "thread":     # match thread or threads
                ARG['THREAD'] = int(arg[1])
            elif arg[0] == "dot":
                ARG['DOT'] = int(arg[1])
            elif arg[0] == "stat":
                ARG['STAT'] = float(arg[1])
            elif arg[0] == "line":
                ARG['LINE'] = int(arg[1])
            elif arg[0] == "lag":
                ARG['LAG'] = float(arg[1])

            # [no]option values
            elif arg[0] == "debug":   ARG['DEBUG'] = True
            elif arg[0] == "nodebug": ARG['DEBUG'] = False

            elif arg[0] == "echo":   ARG['ECHO'] = True
            elif arg[0] == "noecho": ARG['ECHO'] = False

            elif arg[0] == "body":   ARG['BODY'] = True
            elif arg[0] == "nobody": ARG['BODY'] = False

            elif arg[0] == "time":   ARG['TIME'] = True
            elif arg[0] == "notime": ARG['TIME'] = False

            elif arg[0] == "error":   ARG['EOE'] = True
            elif arg[0] == "noerror": ARG['EOE'] = False

            elif arg[0] == "sockmsg":   ARG['SOCKMSG'] = True
            elif arg[0] == "nosockmsg": ARG['SOCKMSG'] = False

            elif arg[0] == "rset":   ARG['RSET'] = True
            elif arg[0] == "norset": ARG['RSET'] = False

            # bad argument?
            else:
                print "\nError: Bad argument: %s" %sys.argv[i]
                verdict = ARG_ERROR
                break

    # set sensible defaults for params not explicitly set on cmd line
    if verdict==ARG_GOOD:

        argstr = "%s" % sys.argv
        count = ARG['COUNT'] * ARG['THREAD']

        if argstr.find("dot=") < 0:
            if   count ==  0: ARG['DOT']=0
            elif count < 100: ARG['DOT']=1
            else:             ARG['DOT']=10

        if count > 0:
            ARG['TID']=True

        if argstr.find("echo") < 0:
            if count != 1:   ARG['ECHO']=False

        if argstr.find("body") < 0:
            if ARG['SIZE'] < 500 and not ARG['FILE']: ARG['BODY'] = True

        if not ARG['HELO'] and not ARG['EHLO']:
            ARG['HELO']=hname

    # parse params
    if verdict==ARG_GOOD:

        # parse hostname:port
        if ARG['HOST']:
            host = ARG['HOST']
            if host.find(":") >= 0:
                ARG['HOST'] = host.split(':')[0]
                ARG['PORT'] = int(host.split(':')[1])

        if not ARG['HOST']:
            print "\nError: host is a required parameter."
            verdict = ARG_ERROR

        # validate file / read directory
        if ARG['FILE']:
            verdict = read_file(ARG)

        if ARG['DEBUG']:
            print "Args: %s" %ARG

    if verdict != ARG_GOOD:
        print_usage(verdict)

    global g_proc
    g_proc = ARG['PROC'] # used by interrupt handler

    return ARG

#--------------------------------------------------------------------------------

def read_file(ARG):
    """validate file or directory name. create list of filenames"""
    verdict=ARG_GOOD

    # validate filename
    if os.path.isfile(ARG['FILE']):
        ARG['FILELIST'].append(ARG['FILE']) # list of one file

    # validate directory
    elif os.path.isdir(ARG['FILE']):
        if ARG['FILE'][-1:] != '/':
            ARG['FILE'] = ARG['FILE'] + "/"

    # bad param
    else:
        print "\nError: File or directory not found: %s" % ARG['FILE']
        verdict = ARG_ERROR

    # if directory, read list of files
    if verdict == ARG_GOOD and ARG['FILE'][-1:] == "/":
        # read list of files
        for item in os.listdir('.'):
            if os.path.isfile(item):
                ARG['FILELIST'].append(item)

    # debug
    if ARG['DEBUG']:
        if ARG['FILE'][-1:] == "/":
            print "Using %d files from directory %s: %s" % ( len(ARG['FILELIST']), ARG['FILE'], ARG['FILELIST'] )
        else:
            print "Using file: %s" % ARG['FILE']

    return verdict

#--------------------------------------------------------------------------------

def send_headers(s,ARG):
    """Send the RFC 821 headers"""

    s.send("MAIL FROM: %s\r\n" %ARG['FROM'])
    s.recvsmtp()

    # multiple recipients separated by commas
    lst = ARG['TO'].split(',')
    for i in xrange(len(lst)):
        lst[i] = lst[i].strip()

    for i in xrange(len(lst)):
        s.send("RCPT TO: %s\r\n" %lst[i])
        s.recvsmtp()

    # send exip cmd if requested
    if ARG['EXIP'] is not None:
        if ARG['EXIP']: # user provided text
            s.send("EXIP %s\r\n" % ARG['EXIP'])
        else:           # auto-generated text
            s.send("EXIP %s\r\n" % EXIP)
        s.recvsmtp()

#--------------------------------------------------------------------------------

def auto_gen(ARG):
    """auto generate a test message of desired size"""
    msg = []

    # 822 headers
    # Date: Tue, 27 Nov 2007 16:04:50 -0500
    today = time.strftime("%a, %d %b %Y %H:%M:%S -0500", time.localtime())
    ranstr = str(random.random())[2:]
    msgid = "%s%s%s" % ("adsalkjasdfljd",ranstr,"@ctdev.net")
    msg.append(\
          "Subject: %s\r\n" %ARG['SUB'] + \
          "Date: %s\r\n" % today + \
          "Message-ID: %s\r\n" % msgid + \
          "From: %s\r\n" %ARG['FROM'] + \
          "To: %s\r\n" %ARG['TO'] + \
          "\r\n")
    siz = len(msg[0])

    # Body part

    # If no size specified, just use regular one-liner body
    if ARG['SIZE'] == 0:
        msg.append(SAMPLE1)
        siz += len(msg[-1])
        ARG['SIZE'] = siz+2  # count cr-lf added by term block

    # If size specified, use bigger text sample
    else:
        while siz+2 < ARG['SIZE']:
            rem = ARG['SIZE'] - (siz+2)
            msg.append(SAMPLE2[:rem])
            siz += len(msg[-1])

    # terminate data block
    msg.append("\r\n.\r\n")

    # save it
    ARG['TEXTB'] = "".join(msg)
    ARG['TEXTL'] = ARG['TEXTB'].splitlines(1)

    # DEBUG *** DEBUG *** DEBUG *** DEBUG *** DEBUG *** 
    #print "ARG:SIZE: %s (should be 3 less than textb size.)" % ARG['SIZE']
    #print "TEXTB:SIZE: %s" % len(ARG['TEXTB'])
    #print "TEXTB >>>%s<<<" % ARG['TEXTB']
    #print "TEXTL >>>%s<<<" % ARG['TEXTL']

    # sanity check, just to double check ourselves
    if ARG['SIZE']+3 != len(ARG['TEXTB']):
        print "ERROR: Auto-generated message: Requested size = %d, Actual size = %d" % (ARG['SIZE'], len(ARG['TEXTB'])-3)

#--------------------------------------------------------------------------------

def send_body_auto(s,ARG):
    """Send default text for email body"""

    # sending, pause between each line
    if ARG['LRATE']:
        for i in range(len(ARG['TEXTL'])): 
            s.send(ARG['TEXTL'][i])
            time.sleep(ARG['LRATE'])

    # sending in big chunks
    else:
        s.send(ARG['TEXTB'])

    return ARG['SIZE']

#--------------------------------------------------------------------------------

def send_body_file(s,ARG):
    """Send a file for email body"""

    # get next filename
    pos = ARG['FILEPOS']
    cnt = len(ARG['FILELIST'])
    if cnt > 1:
        if pos+1 >= cnt: 
            ARG['FILEPOS'] = 0
        else:                           
            ARG['FILEPOS'] = pos+1
    fil_nam = ARG['FILELIST'][pos]

    # debug
    if ARG['DEBUG']:
        print "Reading file: ", fil_nam

    # open file
    try:

        f=open(fil_nam, 'r')
    except:
        print "*** Error: Can not open file %s. Sending sample text instead." % fil_nam
        s.send("this is a test\r\n.\r\n")
    else:
        siz=0

        # sending, pause between each line
        if ARG['LRATE']:
            buf = f.readlines(16384)
            for i in range(len(buf)): 
                s.send(buf[i])
                siz += len(buf[i])
                time.sleep(ARG['LRATE'])

        # sending in big chunks
        else:
            buf=f.read(CHUNK)
            while buf:
                s.send(buf)
                siz += len(buf)
                las = buf[-2:]
                buf=f.read(CHUNK)

        # terminate data block (add crlf if needed)
        if las == "\r\n":
            s.send(".\r\n")
        else:
            s.send("\r\n.\r\n")

        # close up, report stats
        f.close()

    # bytes sent
    return siz

#--------------------------------------------------------------------------------

def send_body(s,ARG):
    """Send the mail msg body text."""

    # start data phase
    s.send("DATA\r\n")
    s.recvsmtp()

    # data stage pause
    if ARG['DRATE']: 
        time.sleep(ARG['DRATE'])

    #pdb.set_trace()

    # turn off echo just for sending body
    if not ARG['BODY'] and ARG['ECHO']:
        s.echo(False) 

    # auto-generate msg body
    if ARG['FILE'] is None:
        siz = send_body_auto(s,ARG)

    # use file for msg body
    else:
        siz = send_body_file(s,ARG)

    # turn on echo after body if needed
    if not ARG['BODY'] and ARG['ECHO']:
        s.echo(True)

    # report byte count sent
    if ARG['ECHO']:
        siz = sockit.commify(siz)
        write_log ("info: Sent %s bytes of DATA." % (siz), ARG)

    # receive acknowledgment
    s.recvsmtp()

#--------------------------------------------------------------------------------

def mailbind(ARG,s):
    """bind outbound socket to a specific IP (if any) and rotate thru list"""

    lenip = len(ARG['BIND'])   # len of ip list
    if lenip < 1:              # nothing to do?
        return

    cntip = ARG['BINDCNT']     # current index into ip list
    if (cntip+1 < lenip):      # next value
        ARG['BINDCNT'] = cntip+1
    else:                      # wrap around
        ARG['BINDCNT'] = 0

    adrip = ARG['BIND'][cntip]
    if ARG['ECHO']:
        write_log ("sock: Binding to %s" % adrip, ARG)
    try:
        s.s.bind((adrip,0))
    except:
        print ExceptionInfo()
        rc = 1

#--------------------------------------------------------------------------------

def mailone(ARG):
    """send one mail msg. return 0 if success, !0 otherwise."""
    rc = 0
    if ARG['ECHO']:
        print "------------------------------------------------------------"
        if ARG['TIME']:
            write_log ("stup:", ARG)

    try:
        #if len(sock) > 0:
        #    s = sock[0]                                # fetch existing socket
        #else:
        if True:
            s = sockit.sockit()                        # create socket
            if ARG['EOE']: s.eoe(True)                 # auto exit on error
            s.echo(ARG['ECHO'])                        # echo data sent/recv
            s.time(ARG['TIME'])                        # timestamp with data
            s.timeout(ARG['TIMEOUT'])                  # timeout reading from server
            s.raize(True)                              # raise exception on error
            if ARG['SOCKMSG']: s.msg(True)             # print socket error msgs
            mailbind(ARG,s)                            # bind outbound socket to IP
            #if ARG['RSET']:
            #    sock.append(s)

        #if not ARG['CONNECTED']:
        if True:
            s.connect(ARG['HOST'], ARG['PORT'])    # connect to server
            #ARG['CONNECTED'] = True
            s.recvsmtp()                           # receive smtp welcome banner
            if ARG['HELO']:
                s.send("HELO %s\r\n" %ARG['HELO'])
            else:
                s.send("EHLO %s\r\n" %ARG['EHLO'])
            s.recvsmtp()                           # receive helo response

        send_headers(s,ARG)                        # send 821 hdrs (helo, mail from, etc)
        send_body(s,ARG)                           # send 822 body

        if ARG['RSET']:
            s.send("rset\r\n")                     # send quit
            s.recvsmtp()                           # recv acknowledgment
        else:
            s.send("quit\r\n")                     # send quit
            s.recvsmtp()                           # recv acknowledgment
            s.close()                              # close socket
            #ARG['CONNECTED'] = False
            # del sock[:]

    #except socket.error, msg:
    #    print "Socket Error in mailone: %s" % msg
    #except IOError, e:
    #    print "IO Error in mailone: %s" % e
    except SystemExit:
        rc = 1  # normal condition, when recvsmtp() doesn't get good smtp code.
    except:
        print ExceptionInfo()
        rc = 1

    return rc

#--------------------------------------------------------------------------------

def run(ARG, Parent):
    """Loop sending mail"""

    global g_msgcnt,g_msggood,g_msgbad,g_quit # global message count shared by all threads
    x,y,z = 0.0,0.0,0.0         # x,y,z = start,end of single trans, longest trans
    s = time.time()             # s   = start,end time of 10 sec block
    a,b = 0,0                   # a,b = msg cnt in 10 sec, start msg num of 10 sec block
    i,j = 1,ARG['COUNT']        # i,j = curr msg, max msg
    #sock = []                   # socket to server

    while j==0 or i <= j:       # main loop to send emails

        # pause, if any
        if i>1 and ARG['RATE']:
            time.sleep(ARG['RATE'])

        # send one message, and time it.
        if ARG['ECHO']: print "Message %d " %i
        x = time.time()
        rc = mailone(ARG) # (sock,ARG)
        y = time.time()
        
        # print some stats
        if ARG['TIME'] and ARG['ECHO']: 
            print "time: %0.2f" %(y-x)
        if not ARG['ECHO'] and ARG['LINE']==0 and ARG['DOT'] > 0 and i%ARG['DOT']==0: 
            sys.stderr.write(".")
        if ARG['LINE'] > 0 and i%ARG['LINE']==0:
            print "Message %d sent." % i

        # calc and prints statistics (only one line per process please)
        if Parent:
            if y-x > z: z=y-x  # longest time to send a single message
            c = y - s          # elapsed sec
            if ARG['STAT'] > 0 and c >= ARG['STAT']: # has time block elapsed yet?
                a = g_msgcnt - b  # num of messages in last 10 sec
                print >> sys.stderr, "\nhost: %s tot_msgs: %s bad-msg: %s msgs/sec: %7.1f interval-cnt: %5s, interval: %4.1fs, slowest-msg: %4.1f" \
                                      % (ARG['HOST'],sockit.commify("%s"%g_msgcnt),sockit.commify(g_msgbad),a/c,sockit.commify(a),c,z),
                b = g_msgcnt   # reset count of next time block
                s = y          # reset time  of next time block
                z = 0.0        # reset longest msg time

        # count number of messages sent
        i += 1

        # add to global msg cnt
        ARG['LOCK'].acquire()
        g_msgcnt += 1
        if rc==0: g_msggood+= 1
        else:     g_msgbad += 1
        ARG['LOCK'].release()

        # interrupt?
        if g_quit: break

    # remove self from thread count
    if ARG['THREAD'] > 1:
        if ARG['DEBUG']:
            print "Thread %s ending." % (thread.get_ident())
        pid=os.getpid()
        try: ARG[pid].remove(thread.get_ident())
        except KeyError: pass # uhh... dunno why this happens in very high proc/thread count.

    return 0

#--------------------------------------------------------------------------------

def start_threads(ARG):
    """start 'num' number of threads within each processes"""
    num=ARG['THREAD']
    tidlst=[]
    tidlst.append(thread.get_ident())
    count=1
    tid=0
    ARG['LOCK'] = thread.allocate_lock()

    for each in xrange(1, num):
        try:
            tid = thread.start_new_thread(run, (ARG,False))
        except:
            print >> sys.stderr, "Error, can not start thread number %s." % count
            break
        tidlst.append(tid)
        if ARG['LAG']: 
            time.sleep(ARG['LAG'])
        count += 1

    if num > 1:
        pid=os.getpid()
        ARG[pid]=tidlst
        if ARG['DEBUG']:
            print "PID %s running %d threads: %s" % (pid, count, tidlst)

#--------------------------------------------------------------------------------

def wait_threads(ARG):
    """wait for all threads in current pid to finish"""
    if ARG['THREAD'] > 1:
        pid=os.getpid()
        if ARG['DEBUG']:
            print "WAIT: pid %s waiting on threads: %s" % (pid,ARG[pid])
        while True:
            if len(ARG[pid]) == 0:
                break
            time.sleep(0.25)
        if ARG['DEBUG']:
            print "PID %s: All threads ended." % pid

    # all done
    global g_msgcnt,g_msggood,g_msgbad # global message count shared by all threads
    if ARG['DOT']: print ""
    print >> sys.stderr, "Proc %s Done. Msgs: %s total,  %s success,  %s failed." % \
        (os.getpid(), sockit.commify("%s"%g_msgcnt), sockit.commify("%s"%g_msggood), sockit.commify("%s"%g_msgbad))

#--------------------------------------------------------------------------------

def start_procs(ARG):
    """start 'num' number of parallel processes.  Should be called BEFORE start_threads, 
    becuase we init each proc's ARG[pid] with that procs list of thread TID's. """

    ARG['PARENT']=False
    num=ARG['PROC']
    pid = os.getpid()
    ARG[pid] = []
    pidlst=[]
    pidlst.append(pid)
    count=1
    pid=0

    for each in xrange(1, num):
        pid = os.fork()
        if pid == 0: # child
            break
        else:        # parent
            pidlst.append(pid)
            count += 1

    if pid > 0:
        ARG['PARENT']=True
        ARG['PIDLST']=pidlst
        if ARG['DEBUG']:
            print "Running %d processes: %s" % (count, pidlst)

#--------------------------------------------------------------------------------

def wait_procs(ARG):
    """wait for all processes to finish"""
    num=len(ARG['PIDLST'])
    if num > 1:
        for each in xrange(1, num):
            if ARG['DEBUG']:
                print "WAIT: parent pid %s waiting on child proc: %s" % (os.getpid(),ARG['PIDLST'][0],ARG['PIDLST'][each])
            os.waitpid(ARG['PIDLST'][each],0)
        #tot= sockit.commify("%s"%(ARG['THREAD']*ARG['PROC']*ARG['COUNT']))
        tot= sockit.commify("%s"%(g_msgcnt*ARG['PROC']))
        print >> sys.stderr, "All %s procs done. Approximately %s messages sent." % (num,tot)

#--------------------------------------------------------------------------------

def handle_INT(signo, frame):
    """catch and exit on ctl-C"""
    global g_intcnt, g_quit
    g_intcnt += 1
    if g_intcnt < 2:
        print >> sys.stderr, "\nSetting QUIT flag for orderly shutdown. Please wait a few seconds."
        g_quit = True
    else:
        print >> sys.stderr, "\nOkay already! Killing processes. Approx %s Messages sent." % (sockit.commify("%s"%(g_msgcnt*g_proc)))
        sys.exit(0)

#--------------------------------------------------------------------------------

def main(argv=None):
    """main entry point"""
    if argv is None:
        argv = sys.argv

    ARG = parse_params()    # get cmd line options

    signal.signal(signal.SIGINT, handle_INT)

                            # auto-generate msg of desired size if needed
    if ARG['TEXTB'] is None and ARG['FILE'] is None:
        auto_gen(ARG)

    start_procs(ARG)        # parallel clients, multi-process

    start_threads(ARG)      # parallel clients, multi-threads per process

    run(ARG,True)           # even me (parent) runs a thread

    wait_threads(ARG)       # wait for all threads to finish

    if ARG['PARENT']:
        wait_procs(ARG)     # wait for all processes to finish

#--------------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())

#--------------------------------------------------------------------------------
