#!/usr/bin/python3
"""
mailit-01-tls.py

simple test of sending an email msg in python.

0.1, 02/10/2008, john@masinter.net, simple email test
"""
import socket
import ssl
import sys

#mxhs = "alt4.gmail-smtp-in.l.google.com"
#mxip = "142.250.112.26"
#mxpt = 25

mxhs = "smtp.centurylink.net"
mxip = "209.67.129.100"
mxpt = 587 # centurylink defines smtp port: 587

#----------------------------------------
context = ssl.create_default_context()
with socket.create_connection((mxhs, mxpt)) as sock:
        with context.wrap_socket(sock, server_hostname=mxhs) as ssock:
                    print(ssock.version())
sys.exit(1)

#----------------------------------------
# PROTOCOL_TLS_CLIENT requires valid cert chain and hostname
pem = "/opt/local/etc/openssl/cert.pem"
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations(pem)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        with context.wrap_socket(sock, server_hostname=mxhs) as ssock:
                    print(ssock.version())
sys.exit(1)

#----------------------------------------
# open connection to smtp svr
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((mxip, mxpt))

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

