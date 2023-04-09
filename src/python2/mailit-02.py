#!/usr/bin/python

import sys
import socket

def connect(host,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(60)
    try:
        s.connect((host,port))
    except socket.error, msg:
        s.close()
        s = None
        print "Error: ", msg
    return s

def send(msg):
    print "send: ", msg
    i = s.send(msg)
    if i == 0:
       raise RuntimeError, "send: socket connection broken"

def recv(max):
    b = s.recv(max)
    if b == '':
        raise RuntimeError, "recv: socket connection broken"
    print "recv: ", b
    return b

# main ------------------------------------------------------------

s = connect("ctdev84", 8825)
if s is None: sys.exit(1)

send("HELO cookie\r\n")
recv(1000)

send("MAIL FROM: me@ctdev.net\r\n")
recv(1000)

send("RCPT TO: you@ctdev.net\r\n")
recv(1000)

send("DATA\r\n")
recv(1000)

send("this is a test\r\n.\r\n")
recv(1000)

send("quit\r\n")
recv(1000)

