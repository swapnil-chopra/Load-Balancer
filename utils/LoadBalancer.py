
from functools import cache
import os
import random
from select import select
import socket
import sys
from settings import *
import psutil
from itertools import cycle
import utils.algorithms as algorithms


class LoadBalancer(object):
    if ALGORITHM == 'ROUND_ROBIN':
        ITER = cycle(SERVER_POOL)
    flow_table = dict()
    sockets = list()
    CONNECTIONS = dict().fromkeys(SERVER_POOL, 0)

    def __init__(self, ip, port) -> None:
        self.ip = ip
        self.port = port
        self.algorithm = ALGORITHM
        self.cs_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)      # create a socket for load balancer using ipv4 and tcp.
        self.cache = self.CONNECTIONS
        # Set the socket options.
        self.cs_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the LoadBalancer at the specified ip and port
        self.cs_socket.bind((self.ip, self.port))
        print(f'init client socket{self.cs_socket.getsockname()}')
        self.cs_socket.listen(10)
        self.sockets.append(self.cs_socket)

    def start(self):
        try:
            while True:

                read_list, write_list, exception_list = select(
                    self.sockets, [], [])
                for sock in read_list:
                    if sock == self.cs_socket:
                        # print('='*40+'flow start'+'='*40)
                        self.on_accept()
                        break
                    else:
                        try:
                            data = sock.recv(4096)
                            if data:
                                self.on_recv(sock, data)
                            else:
                                self.on_close(sock)
                                break
                        except:
                            sock.on_close(sock)
                            break
        except KeyboardInterrupt:
            print("Ctrl C - Stopping load_balancer")
            sys.exit(1)

    def on_accept(self):
        client_socket, client_addr = self.cs_socket.accept()
        print(
            f'client connected {client_addr} <==> {self.cs_socket.getsockname()}')
        server_ip, server_port = self.select_server()
        ss_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            ss_socket.connect((server_ip, server_port))
            # print(f'init server side socket {ss_socket.getsockname()}')
            # print(
            #     f'server connected: {ss_socket.getsockname()} <==> {(socket.gethostbyname(server_ip), server_port)}')
        except:
            print("Can't establish connection with remote server, err: %s" %
                  sys.exc_info()[0])
            print("Closing connection with client socket %s" % (client_addr,))
            client_socket.close()
            return
        self.sockets.append(client_socket)
        self.sockets.append(ss_socket)
        print(ss_socket)
        # print(client_socket.getsockopt(1, socket.AF_INET))

        self.flow_table[client_socket] = ss_socket
        self.flow_table[ss_socket] = client_socket

    def on_recv(self, sock, data):
        pid = os.getpid()
        python_process = psutil.Process(pid)
        # memory use in GB...I think
        memoryUse = python_process.memory_info()[0]/2.**30
        # print('memory use:', memoryUse)
        # print('recving packets: %-20s ==> %-20s' %
        #       (sock.getpeername(), sock.getsockname(), ))
        # data can be modified before forwarding to server
        # lots of add-on features can be added here
        remote_socket = self.flow_table[sock]
        remote_socket.send(data)

        # print(remote_socket)

        # print('sending packets: %-20s ==> %-20s' %
        #       (remote_socket.getsockname(), remote_socket.getpeername()))

    def on_close(self, sock):
        pid = os.getpid()
        python_process = psutil.Process(pid)
        # memory use in GB...I think
        memoryUse = python_process.memory_info()[0]/2.**30
        # print('memory use:', memoryUse)
        # print('client %s has disconnected' % (sock.getpeername(),))
        # print('='*41+'flow end'+'='*40)

        ss_socket = self.flow_table[sock]

        self.sockets.remove(sock)
        self.sockets.remove(ss_socket)

        if ss_socket.getpeername() in self.cache.keys():
            self.cache[ss_socket.getpeername(
            )] = self.cache[(ss_socket.getpeername())]-1
        print('removed', self.cache)
        sock.close()  # close connection with client
        ss_socket.close()  # close connection with server

        del self.flow_table[sock]
        del self.flow_table[ss_socket]

    def select_server(self):
        if ALGORITHM == 'ROUND_ROBIN':
            return algorithms.round_robin(self.ITER)
        elif ALGORITHM == 'LEAST_CONN':
            return algorithms.least_conn(self.cache)
