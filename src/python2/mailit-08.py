#!/usr/bin/python
# was !/ct/apps/python/bin/python

import thread
import sys
import os
import sockit
import time
import signal

VER = "0.4"
SMTP_PORT = 25
ARG_GOOD, ARG_USAGE, ARG_ERROR = range(1,4)
CHUNK = (128*1024)

#--------------------------------------------------------------------------------

def print_usage(verdict):
    """Print usage and exit."""

    cmd = sys.argv[0].split('/')[-1] # get basename of program (chop off any path)

    if verdict == ARG_USAGE:
        print """

Usage: %s [hostname] {from=me@ctdev.net} {to=you@ctdev.net} {sub=testing}
                 {file=None} {helo=cookie.ctdev.net} {timeout=30} {count=1} {rate=0.5}
                 {echo} {body} {stat} {debug} {time}

A simple and easy to use test email client. It simply sends test emails.
The host is the target IronMail server, and is required. All other data
will be generated if not provided.

hostname,  required, mail server to which we connect and send the msg.
from/sub,  specify headers for auto-generated test messages.
to         specify header, multiple recipients can be separated by commas.
helo,      specify the helo/ehlo hostname.
file       a file to use for the email body.
count,     how many emails to send. 1=default, 0=stress test.
rate,      pause for given seconds between emails.
proc,      number of simultaneous processes.
echo,      do not echo smtp data to stdout.
body,      also echo the msg body \"DATA\" section to stdout.
timeout,   the seconds to wait on a response before quiting.
stat,      print one-line confirmation for each mail sent.
debug,     print out extra program debug info.
time,      do not print timestamps on each smtp output line.

Simple test:  %s ctdev84
More detail:  %s ctdev84 from=me@ctdev.net to=you@ctdev.net file=junk.txt
Stress test:  %s ctdev84 count=0 echo=off
Stress test output:
   cnt: 3671, sec: 10, longest: 0, msgs/sec: 367.....................................
   cnt: 3699, sec: 10, longest: 0, msgs/sec: 369......................................
   cnt: 3777, sec: 10, longest: 0, msgs/sec: 377.....................................
Notes: Each '.' = 10 msgs sent. cnt = msgs sent since last update, sec = seconds since
last update, longest = longest time in seconds to send a single message.

Version v%s, Copyright (c) 2007 Secure Computing Corporation. 
Bugs to John_Masinter@SecureComputing.com
""" %(cmd,cmd,cmd,cmd,VER)

    elif verdict == ARG_ERROR:
        print "For help: %s -h\n" %cmd

    sys.exit(1)

#--------------------------------------------------------------------------------

def parse_params():
    """Parse the command line options."""
    # default values
    ARG = { "HOST":None, "PORT":SMTP_PORT, "FROM":"me@ctdev.net", "TO":"you@ctdev.net", 
            "FILE":None, "HELO":"cookie", "COUNT":1, "PROC":1, "ECHO":True, "BODY":True, 
            "TIMEOUT":30, "DEBUG":False, "TIME":True, "RATE":0, "SUB":"Testing message", 
            "STAT":False }
    verdict = ARG_GOOD
    host = None

    # check number of args
    argc = len(sys.argv)
    if argc < 2:
        verdict = ARG_USAGE

    # help requested?
    if verdict==ARG_GOOD and sys.argv[1] in ("-h","-?","--help"):
        verdict = ARG_USAGE

    # parse each cmd line arg
    if verdict==ARG_GOOD:
        for i in range (1, argc):
            arg = sys.argv[i].split("=")

            # special case: if host is only param given, then 'host=' maybe omitted
            #if len(arg) != 2:
            #    print "\nError: Bad argument: %s" %sys.argv[i]
            #    verdict = ARG_ERROR
            #    break

            if arg[0] == "from":
                ARG['FROM'] = arg[1]
            elif arg[0] == "to":
                ARG['TO'] = arg[1]
            elif arg[0][0:3] == "sub":
                ARG['SUB'] = arg[1]
            elif arg[0] == "file":
                ARG['FILE'] = arg[1]
            elif arg[0] == "helo":
                ARG['HELO'] = arg[1]

            elif arg[0] == "count":
                ARG['COUNT'] = int(arg[1])
            elif arg[0] == "timeout":
                ARG['TIMEOUT'] = int(arg[1])
            elif arg[0] == "rate":
                ARG['RATE'] = float(arg[1])
            elif arg[0] == "proc":
                ARG['PROC'] = int(arg[1])

            elif arg[0] == "debug":
                ARG['DEBUG'] = True
            elif arg[0] == "echo":
                ARG['ECHO'] = False
            elif arg[0] == "body":
                ARG['BODY'] = False
            elif arg[0] == "time":
                ARG['TIME'] = False
            elif arg[0] == "host":
                host = arg[1]
            elif arg[0] == "stat":
                ARG['STAT'] = True

            elif len(arg) == 1 and not ARG['HOST']:
                host = arg[0] # 'host=' maybe omitted

            else:
                print "\nError: Bad argument: %s" %sys.argv[i]
                verdict = ARG_ERROR
                break

            if host:
                if host.find(":") >= 0:
                    ARG['HOST'] = host.split(':')[0]
                    ARG['PORT'] = int(host.split(':')[1])
                else:
                    ARG['HOST'] = host
                host = None

    if verdict==ARG_GOOD and not ARG['HOST']:
        print "\nError: host is a required parameter."
        verdict = ARG_ERROR

    if ARG['FILE'] and not os.path.isfile(ARG['FILE']):
        print "\nError: File not found: %s" %ARG['FILE']
        verdict = ARG_ERROR

    if verdict != ARG_GOOD:
        print_usage(verdict)

    if ARG['DEBUG']:
        print "Args: %s" %ARG

    return ARG

#--------------------------------------------------------------------------------

def send_body(s,ARG):
    """Send the mail msg body text."""
    if ARG['FILE'] is None:
        msg = "From: %s\r\n" %ARG['FROM'] + \
              "To: %s\r\n" %ARG['TO'] + \
              "Subject: %s\r\n" %ARG['SUB'] + \
              "\r\n" + \
              "This is a test message from mailit.py.\r\n" + \
              ".\r\n"
        s.send(msg)
    else:
        try:
            f=open(ARG['FILE'], 'r')
        except:
            print "*** Error: Can not open file %s. Sending sample text instead." %ARG['FILE']
            s.send("this is a test\r\n.\r\n")
        else:
            if ARG['BODY'] and ARG['ECHO']:
                s.echo(False) # turn off echo just for sending body

            siz=0
            buf=f.read(CHUNK)
            while buf:
                s.send(buf)
                siz += len(buf)
                buf=f.read(CHUNK)

            s.send("\r\n.\r\n")
            f.close()
            if ARG['BODY'] and ARG['ECHO']:
                t = ""
                if ARG['TIME']: t = time.strftime("%H:%M.%S:")
                siz = sockit.commify(siz)
                print "%sinfo: Sent %s bytes, not displayed." % (t,siz)
                s.echo(True)
    s.recvsmtp()

#--------------------------------------------------------------------------------

def mailone(ARG):

    if ARG['ECHO']:
        print "------------------------------------------------------------"
        if ARG['TIME']:
            print "%sstup:" % time.strftime("%H:%M.%S:")

    s = sockit.sockit()                   # create socket
    s.eoe(True)                           # auto exit on error
    s.echo(ARG['ECHO'])                   # echo data sent/recv
    s.time(ARG['TIME'])                   # timestamp with data
    s.timeout(ARG['TIMEOUT'])             # timeout reading from server
    s.connect(ARG['HOST'], ARG['PORT'])   # connect to server

    s.recvsmtp()

    s.send("HELO %s\r\n" %ARG['HELO'])
    s.recvsmtp()

    s.send("MAIL FROM: %s\r\n" %ARG['FROM'])
    s.recvsmtp()

    # multiple recipients separated by commas
    lst = ARG['TO'].split(',')
    for i in xrange(len(lst)):
        lst[i] = lst[i].strip()
    for i in xrange(len(lst)):
        s.send("RCPT TO: %s\r\n" %lst[i])
        s.recvsmtp()

    s.send("DATA\r\n")
    s.recvsmtp()

    send_body(s,ARG)

    s.send("quit\r\n")
    s.recvsmtp()

    s.close()

#--------------------------------------------------------------------------------

def handle_INT(signo, frame):
    print >> sys.stderr, "\nExiting..."
    sys.exit(0)

#--------------------------------------------------------------------------------

def main(argv=None):
    """main entry point"""
    if argv is None:
        argv = sys.argv

    ARG = parse_params()            # get cmd line options

    signal.signal(signal.SIGINT, handle_INT)

    x,y,z = 0.0,0.0,0.0         # x,y,z = start,end of single trans, longest trans
    s = time.time()             # s   = start,end time of 10 sec block
    a,b = 0,0                   # a,b = msg cnt in 10 sec, start msg num of 10 sec block
    i,j = 1,ARG['COUNT']        # i,j = curr msg, max msg

    while j==0 or i <= j:       # main loop to send emails

        # pause, if any
        if i>1 and ARG['RATE']>0.0 :
            time.sleep(ARG['RATE'])

        # log message count
        if ARG['ECHO']: print "Message %d " %i
        #if i%100 == 0: print >> sys.stderr, "%d " %i,
        if i%100 == 0: sys.stderr.write(".")

        # send one message, and time it.
        x = time.time()
        mailone(ARG)
        y = time.time()
        if ARG['TIME'] and ARG['ECHO']: 
            print "time: %0.2f" %(y-x)
        if ARG['STAT']:
            print "Message %d sent." % i

        # calc and prints statistics
        if y-x > z: z=y-x  # longest time to send a single message
        c = y - s          # elapsed sec
        if c >= 10.0:      # has 10 sec elapsed yet?
            a = i - b      # num of messages in last 10 sec
            print >> sys.stderr, "\ncnt: %d, sec: %0.2f, longest: %0.2f, msgs/sec: %0.2f" %(a,c,z,a/c),
            b = i          # reset count of next 10 sec block
            s = y          # reset time  of next 10 sec block
            z = 0.0        # reset longest msg time

        # count number of messages sent
        i += 1

    # all done
    print >> sys.stderr, "\nDone. %d Messages sent.\n" %(i-1)
    return 0


#--------------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())

#--------------------------------------------------------------------------------
