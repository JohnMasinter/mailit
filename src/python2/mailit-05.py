#!/usr/bin/python

import sys
import sockit

#--------------------------------------------------------------------------------

def myrecv(s):
    a = b = ''
    while not a[:1].isdigit():
        a = s.recvline()
        b += a
    c = int(a.split()[0])
    if c < 200 or c > 399:
        print "Bad SMTP code: %d" %c
	sys.exit(1)
    return b

#--------------------------------------------------------------------------------

#Host="ctdev84"
#Host="ctdev71"
#Host="im123.ctdev.net"

if len(sys.argv) != 2:
    print "\nUsage: %s [hostname]\n\nSend a test email via smtp to given host.\n" %sys.argv[0].split('/')[-1]
    sys.exit(1)
else:
    Host = sys.argv[1]

s = sockit.sockit()         # create socket
s.eoe(True)                 # auto exit on error
s.echo(True)                # echo data sent/recv
s.timeout(30)               # set short timeout for testing
s.connect(Host, 25)         # connect to server

myrecv(s)

s.send("HELO cookie\r\n")
myrecv(s)

s.send("MAIL FROM: me@ctdev.net\r\n")
myrecv(s)

s.send("RCPT TO: you@ctdev.net\r\n")
myrecv(s)

s.send("DATA\r\n")
myrecv(s)

s.send("this is a test\r\n.\r\n")
myrecv(s)

s.send("quit\r\n")
myrecv(s)

s.close()
#--------------------------------------------------------------------------------
