#!/usr/bin/python
#encoding: utf-8

import sys
import socket
from select import select
from struct import pack, unpack

host = "192.168.0.137"
port = 2000
bufsize = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
msgs = []
inputs = [sock, sys.stdin]

def recv(connection):
    data = connection.recv(2)
    if data:
        size = unpack(">H", data)[0]
        data = connection.recv(size)
    return data

def send(message):
    message = pack(">H", len(message)) + message # Prepends 2 bytes of size info
    msgs.append(message)

def main():
    print "connecting to server..."
    sock.connect((host, port))
    print "connected!"
    send("USERNAME" + sys.argv[1])

    running = True

    while running:
        outputs = []
        if msgs:
            outputs.append(sock)
        rlist, wlist, xlist = select(inputs, outputs, [])

        ## Sending messages
        if msgs:
            if sock in wlist:
                for m in msgs + []:
                    sock.send(m)
                    msgs.remove(m)

        ## Reading input
        for s in rlist:
            if s == sock:
                data = recv(s)
                if data:
                    if data.startswith("JOINED"):
                        print "%s joined" % data[6:]
                    elif data.startswith("LEFT"):
                        print "%s left" % data[4:]
                    elif data.startswith("MSG"):
                        print "%s: %s" % tuple(data[3:].split(";"))
                else:
                    print "server shutting down..."
                    running = False

            elif s == sys.stdin:
                msg = sys.stdin.readline()[:-1] # removes the newline
                if msg:
                    send("MSG" + msg)
                else:
                    running = False

def cleanup():
    print "closing connection..."
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: %s [username]" % sys.argv[0])

    try:
        main()
    except socket.error, e:
        print e.strerror

    cleanup()
