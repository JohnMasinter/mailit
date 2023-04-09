#!/usr/bin/env python
"""
Simply cmd line util to send an email msg.
email john_masinter@mcafee.com with problems.

ChangeLog:
0.1, 10-Feb-2010, initial release
0.2, 16-Feb-2010, provide mesg body from file or stdin.
0.3, 31-May-2018, add debug cmd line option, add smtp debug output, add to/from to msg body
0.4, 21-Nov-2019, "to=" cmd line arg maybe a comma-delimited list of email addresses
"""
VER = "0.4"

# possible mcafee smtp servers: exapp.mcafee.com, mail.na.nai.com, mail.eur.nai.com

import sys
import os
import time
import random
import exceptions

from socket import gethostname
import smtplib
import email

#import pdb
#pdb.set_trace()

#DEF_HOST = "gmail-smtp-in.l.google.com" # mail sent TO gmail.com addr
DEF_HOST = "mx1.comcast.net" # mail sent from xfinity / comcast
SMTP_PORT = 25
SECURE_PORT = 465

#--------------------------------------------------------------------------------

def print_usage():
    """Print usage and exit."""

    cmd = sys.argv[0].split('/')[-1] # get basename of program (chop off any path)

    print """

Usage: %s to="you@ctdev.net"  # comma-delimited list, or multiple "to=" args
          [from=do_not_reply@ctdev.net] [subject="No Subject"] [host="mail.na.nai.com:25"]
          [mesg="test of msg."]   # body of mssage on cmd line, OR
          [file="mymesg.dat"]     # body of mssage in file,     OR
          [file="/dev/stdin"]     # body of mssage on stdin.

A simple cmd line util to send an email.

from       sender email
to         recipient email(s)
subject    text of mesg subject
host       host or IP of smtp server, and optionally port also.
           The host defaults to mail.na.nai.com (old: ice.scur.com)
mesg       text of mesg body provided on command line.
file       test of mesg body provided as file.
           file="/dev/stdin" will read msg from stdin.

Version v%s, Copyright (c) 2007-2020 McAfee LLC
Bugs to john_masinter@mcafee.com

""" %(cmd, VER)

    sys.exit(1)

#--------------------------------------------------------------------------------

def parse_params():
    """Parse the command line options."""

    # default values
    ARG = { "HOST":DEF_HOST, "PORT":SMTP_PORT, 
            "FROM":"do_not_reply@ctdev.net", "TO":[], "SUB":"No Subject",  
            "MESG":"", "FILE":"", 
            "DEBUG":False
    }
    # Note:  "TO" is a python list of email addresses
    #        "FILE" and "MESG" are mutually exclusive

    aokay = True
    host = None

    # check number of args
    argc = len(sys.argv)
    if argc < 2:
        aokay = False

    # get hostname for helo cmd
    if aokay:
        hname = gethostname().split(".")[0]
        if len(hname) < 1:
            print "System hostname not set. Using name=cookie"
            hname="cookie"

    # help requested?
    if aokay and sys.argv[1] in ("-h","-?","--help"):
        verdict = False

    # parse each cmd line arg
    if aokay:
        for i in range (1, argc):
            arg = sys.argv[i].split("=",1)

            if arg[0] == "host":
                ARG['HOST'] = arg[1]
            elif arg[0] == "from":
                ARG['FROM'] = arg[1]
            elif arg[0] == "to":
                # "to=" arg is a comma sep list, multiple "to=" allowed
                ARG['TO'] = ARG['TO'] + arg[1].split(",")
            elif arg[0][0:3] == "sub":
                ARG['SUB'] = arg[1]
            elif arg[0] == "mesg":
                ARG['MESG'] = arg[1]
            elif arg[0] == "file":
                ARG['FILE'] = arg[1]
            elif arg[0] == "debug":
                ARG['DEBUG'] = True
            else:
                print "\nError: Bad argument: %s" %sys.argv[i]
                aokay = False
                break

    # parse params
    if aokay:

        # parse port from hostname (if given)
        if ARG['HOST']:
            host = ARG['HOST']
            if host.find(":") >= 0:
                ARG['HOST'] = host.split(':')[0]
                ARG['PORT'] = int(host.split(':')[1])
        else:
            print "\nError: a mail host is required."
            aokay = False

        if aokay and len(ARG['TO']) < 1:
            print "\nError: a TO email address is required."
            aokay = False

        if  aokay and not ARG['MESG'] and not ARG['FILE']:
            print "\nError: must specify either mesg or file."
            aokay = False

        if aokay and ARG['MESG'] and ARG['FILE']:
            print "\nError: may not specify both mesg and file."
            aokay = False

        if aokay and ARG['FILE']:
            aokay = read_file(ARG)

        if aokay and ARG['DEBUG']:
            print "Args: %s" %ARG

    if not aokay:
        print_usage()

    return ARG

#--------------------------------------------------------------------------------
# read file of mesg body into arg MESG

def read_file(ARG):

    aokay = True
    try:
        fp = open(ARG['FILE'], 'rb')
        ARG['MESG'] = fp.read()
        fp.close()
    except:
        aokay = False
        print "Unable to open file " + ARG['FILE']
    return aokay

#--------------------------------------------------------------------------------

def sendmail(ARG):
    """send the mesg via smtp"""

    mailmsg = "subject: "+ARG['SUB']+'\n'+"from: "+ARG['FROM']+'\n'+"to: "+",".join(ARG['TO'])+'\n\n'+ARG['MESG']
    errmsg = ""
    try:
        s = smtplib.SMTP(ARG['HOST'])
        if ARG['DEBUG']:
           s.set_debuglevel(True)
        s.sendmail(ARG['FROM'], ARG['TO'], mailmsg)
        s.quit()
    except smtplib.SMTPRecipientsRefused:
        errmsg="All recipients were refused."
    except smtplib.SMTPHeloError:
        errmsg="Bad reply to our HELO greeting."
    except smtplib.SMTPSenderRefused:
        errmsg="The server didn't accept the from_addr."
    except smtplib.SMTPDataError:
        errmsg="The server replied with an unexpected error code (other than a refusal of a recipient)."
    except:
        errmsg="An Unexpected error occured."

    return (len(errmsg),errmsg)

#--------------------------------------------------------------------------------

def main(argv=None):
    """main entry point"""
    if argv is None:
        argv = sys.argv

    ARG = parse_params()    # get cmd line options

    (rc,msg) = sendmail(ARG)
    if rc==0: print "\nMessage has been sent.\n"
    else:     print "\n"+msg+"\n"

    return rc

#--------------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())

#--------------------------------------------------------------------------------
