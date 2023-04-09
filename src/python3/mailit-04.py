#!/usr/bin/python

import sys
import sockit

s = sockit.sockit()         # create socket
s.eoe(True)                 # auto exit on error
s.connect("ctdev84",   25)  # connect to server

s.send("HELO cookie\r\n")
s.recv(1000)

s.send("MAIL FROM: me@ctdev.net\r\n")
s.recv(1000)

s.send("RCPT TO: you@ctdev.net\r\n")
s.recv(1000)

s.send("DATA\r\n")
s.recv(1000)

s.send("this is a test\r\n.\r\n")
s.recv(1000)

s.send("quit\r\n")
s.recv(1000)

s.close()
