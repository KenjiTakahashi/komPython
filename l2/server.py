# -*- coding: utf-8 -*-


import socket
from select import select
import cPickle as pickle
import sys
import time
from random import randint
from threading import Thread
from protocolObjects import Countdown, Map, Position


class Server(object):
    BACKLOG = 5

    def __init__(self, port, size):
        self.players = list()
        self.playersPositions = list()
        self.size = size
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', port))
        self.server.listen(Server.BACKLOG)
        self.running = True

    def run(self):
        t = Thread(target=self.serve)
        t.start()
        while self.running:
            try:
                sock, addr = self.server.accept()
                print("Received connection from {0}".format(addr))
                self.addClient(sock, addr)
            except (KeyboardInterrupt, socket.error):
                pass
        t.join()

    def addClient(self, sock, addr):
        self.players.append(sock)
        self.playersPositions.append(Position(
            randint(1, self.size.y), randint(1, self.size.x)
        ))  # FIXME: Prevent players from collapsing on each other
        countdown = Countdown(3, self.size, self.players.index(sock))
        for i in range(3, 0, -1):
            countdown.number = i
            print("Sending countdown {0} to {1}".format(i, addr))
            sock.sendall(pickle.dumps(countdown))
            time.sleep(1)
        print("Sending map to {0}".format(addr))
        sock.sendall(pickle.dumps(Map([], self.playersPositions)))

    def serve(self):
        while self.running:
            input, _, _ = select(self.players + [sys.stdin], [], [])
            for i in input:
                if i == sys.stdin:
                    sys.stdin.readline()
                    self.terminate()
                else:
                    print(pickle.loads(input))

    def terminate(self):
        self.running = False
        for player in self.players:
            player.close()
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise AttributeError(
            "Incorrect number of arguments."
            " Usage: <exec> <port> <map_height> <map_width>"
        )
    Server(
        int(sys.argv[1]),
        Position(int(sys.argv[2]), int(sys.argv[3]))
    ).run()
