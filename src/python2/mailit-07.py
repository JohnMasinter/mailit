#!/usr/bin/python

import sys
import os
import sockit

ARG_GOOD, ARG_USAGE, ARG_ERROR = range(1,4)

#--------------------------------------------------------------------------------

def print_usage(verdict):
    """Print usage and exit."""

    cmd = sys.argv[0].split('/')[-1] # get basename of program (chop off any path)

    if verdict == ARG_USAGE:
        print "\
\n\
Usage: %s [host={hostname}] [from={from_addr}] [to={to_addr}]\n\
              [file={body_file}] [helo={helo_text}]\n\
\n\
Send an email via smtp. The host parameter is required. The other data will be\n\
faked if not provided. If host is the only parameter given, the 'host=' maybe\n\
omitted.\n\
\n\
Example 1: %s ctdev84\n\
Example 2: %s host=ctdev84 from=me@ctdev.net to=you@ctdev.net file=junk.txt\n\
" %(cmd,cmd,cmd)

    elif verdict == ARG_ERROR:
        print "For help: %s -h\n" %cmd

    sys.exit(1)

#--------------------------------------------------------------------------------

def parse_params():
    """Parse the command line options."""
    # default values
    HOST, FROM, TO, FILE, HELO = (None, "me@ctdev.net", "you@ctdev.net", None, "cookie")
    verdict = ARG_GOOD

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

            if arg[0] == "host":
                HOST = arg[1]
            elif arg[0] == "from":
                FROM = arg[1]
            elif arg[0] == "to":
                TO = arg[1]
            elif arg[0] == "file":
                FILE = arg[1]
            elif arg[0] == "helo":
                HELO = arg[1]
            elif argc == 2 and len(arg) == 1:
                HOST = arg[0]  # if host is only param given, then 'host=' maybe omitted
            else:
                print "\nError: Bad argument: %s" %sys.argv[i]
                verdict = ARG_ERROR
                break

    if verdict==ARG_GOOD and not HOST:
        print "\nError: host is a required parameter."
        verdict = ARG_ERROR

    if FILE and not os.path.isfile(FILE):
        print "\nError: File not found: %s" %FILE
        verdict = ARG_ERROR

    if verdict != ARG_GOOD:
        print_usage(verdict)

    return (HOST,FROM,TO,FILE,HELO)

#--------------------------------------------------------------------------------

def send_body(s,FILE):
    """Send the mail msg body text."""
    if FILE is None:
        s.send("this is a test\r\n.\r\n")
    else:
        try:
            f=open(FILE, 'r')
        except:
            print "*** Error: Can not open file %s. Sending sample text instead." %FILE
            s.send("this is a test\r\n.\r\n")
        else:
            s.send(f.read())
            s.send("\r\n.\r\n")
            f.close()
    s.recvsmtp()

#--------------------------------------------------------------------------------

def main(argv=None):
    """main entry point"""
    if argv is None:
        argv = sys.argv

    COUNT=0
    (HOST,FROM,TO,FILE,HELO) = parse_params()       # get cmd line options
    
    print "Debug: host=%s,from=%s,to=%s,file=%s,helo=%s,count=%d" %(HOST,FROM,TO,FILE,HELO,int(COUNT))

    s = sockit.sockit()         # create socket
    s.eoe(True)                 # auto exit on error
    s.echo(True)                # echo data sent/recv
    s.timeout(30)               # set short timeout for testing
    s.connect(HOST, 25)         # connect to server
    
    s.recvsmtp()
    
    s.send("HELO %s\r\n" %HELO)
    s.recvsmtp()
    
    s.send("MAIL FROM: %s\r\n" %FROM)
    s.recvsmtp()
    
    s.send("RCPT TO: %s\r\n" %TO)
    s.recvsmtp()
    
    s.send("DATA\r\n")
    s.recvsmtp()
    
    send_body(s,FILE)
    
    s.send("quit\r\n")
    s.recvsmtp()
    
    s.close()

    return 0
    
#--------------------------------------------------------------------------------
    
if __name__ == "__main__":
    sys.exit(main())

#--------------------------------------------------------------------------------
