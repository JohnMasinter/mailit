#!/usr/bin/python3
"""
mailit-01.py

simple test of sending an email msg in python.

0.1, 02/10/2008, john@masinter.net, simple email test
"""
import socket

# find an MX'er to test against, or set this to your MX'er.
# dig -t MX gmail.com
# gmail.com. 2066 IN MX 40 alt4.gmail-smtp-in.l.google.com.
# dig -t A alt4.gmail-smtp-in.l.google.com
# alt4.gmail-smtp-in.l.google.com. 120 IN A 172.217.197.26"
mxer = "172.217.197.26"

# open connection to smtp svr
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((mxer, 25))

# smtp step 1: send "helo [my-hostname]" to initiate session
Msg = "HELO cookie\r\n" # helo with arbitrary hostname
print("send: ", Msg)
rc = s.send(Msg)
if rc == 0:
    raise Exception("socket connection broken")

# smtp step 2: recv status of okay to continue
Ret = s.recv(1000)
if Ret == '':
    raise Exception("socket connection broken")

print("recv: ", Ret)

