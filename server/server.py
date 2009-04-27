#!/usr/bin/python
#encoding: utf-8

import sys
import socket
from select import select
from struct import pack, unpack

host = "" #"192.168.0.137"
port = 2000
bufsize = 1024

srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srvsock.bind((host, port))
srvsock.listen(5)

clients = []
msgs = {}

def send(connection, message):
    message = pack(">H", len(message)) + message # Prepends 2 bytes of size info
    if connection in msgs: msgs[connection] += message
    else:                  msgs[connection] = message

def recv(connection):
    data = connection.recv(2)
    if data:
        size = unpack(">H", data)[0]
        data = connection.recv(size)
    return data

class client:
    def __init__(self, connection, address):
        self.sock = connection
        self.addr = address
        self.name = "%s-%s" % (address[0], self.fileno())

    def fileno(self): # for use in select()
        return self.sock.fileno()

    def recv(self):
        data = recv(self.sock)
        if not data:
            return False

        if data.startswith("USERNAME"):
            print '%s-%s changed name to "%s"' % (self.addr[0], self.fileno(), data[8:])
            self.name = data[8:]
            for c in clients:
                if c != self:
                    send(c.sock, "JOINED" + self.name)
        elif data.startswith("MSG"):
            print '%s sent message "%s"' % (self.name, data[3:])
            for c in clients:
                if c != self:
                    send(c.sock, "MSG%s;%s" % (self.name, data[3:]))
        else:
            print '%s sent unknown command "%s"' % (self.name, data)

        return True

    def close(self):
        self.sock.close()

def main():
    print "server running..."
    running = True

    while running:
        outputs = []
        for conn in msgs:
            outputs.append(conn)

        rlist, wlist, xlist = select([srvsock, sys.stdin] + clients, outputs, [])

        ## Sending data
        for conn in msgs.keys():
            if conn in wlist:
                conn.send(msgs.pop(conn))

        ## Reading input
        for s in rlist:
            if s == srvsock:     ## A client is trying to connect
                conn, addr = s.accept()
                clients.append(client(conn, addr))
                print "got connection %s from %s" % (conn.fileno(), addr[0])
                send(conn, "Hello, client!")

            elif s == sys.stdin: ## User input at terminal
                sys.stdin.readline() # clear junk, nödvändigt?
                running = False

            else:                ## A client has sent data
                if not s.recv():
                    print "connection %s from %s (%s) hung up" % (s.fileno(), s.addr[0], s.name)
                    s.close()
                    clients.remove(s)
                    for c in clients:
                        send(c.sock, "LEFT%s" % s.name)

def cleanup():
    print "shutting down..."
    for c in clients + [srvsock]:
        c.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except BaseException, e:
        print e

    cleanup()
