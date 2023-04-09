#!/usr/bin/python

import sys
import sockit

#--------------------------------------------------------------------------------

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

s.recvsmtp()

s.send("HELO cookie\r\n")
s.recvsmtp()

s.send("MAIL FROM: me@ctdev.net\r\n")
s.recvsmtp()

s.send("RCPT TO: you@ctdev.net\r\n")
s.recvsmtp()

s.send("DATA\r\n")
s.recvsmtp()

s.send("this is a test\r\n.\r\n")
s.recvsmtp()

s.send("quit\r\n")
s.recvsmtp()

s.close()
#--------------------------------------------------------------------------------
