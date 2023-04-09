#!/usr/bin/python

import sys
#import sockf
from sockf import *

s = connect("ctdev84", 25)

send(s, "HELO cookie\r\n")
recv(s,1000)

send(s,"MAIL FROM: me@ctdev.net\r\n")
recv(s,1000)

send(s,"RCPT TO: you@ctdev.net\r\n")
recv(s,1000)

send(s,"DATA\r\n")
recv(s,1000)

send(s,"this is a test\r\n.\r\n")
recv(s,1000)

send(s,"quit\r\n")
recv(s,1000)

close(s)

