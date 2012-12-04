# -*- coding: utf-8 -*-


import socket
from select import select
import cPickle as pickle
import sys
import time
from random import randint
from protocolObjects import Countdown, Map, Position


class Server(object):
    BACKLOG = 5

    def __init__(self, port, size, noOfPlayers):
        self.mines = list()
        self.players = list()
        self.playersPositions = list()
        self.noOfPlayers = noOfPlayers
        self.size = size
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', port))
        self.server.listen(Server.BACKLOG)
        self.running = True

    def run(self):
        while len(self.players) < self.noOfPlayers:
            try:
                sock, addr = self.server.accept()
                print("Received connection from {0}".format(addr))
                self.addClient(sock, addr)
            except (KeyboardInterrupt, socket.error):
                break
        if self.running:
            self.serve()
        print("Terminating...")

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
        self.sendMap(sock)

    def sendMap(self, sock):
        print("Sending map to {0}".format(sock.getpeername()))
        sock.sendall(pickle.dumps(Map(self.mines, self.playersPositions)))

    def serve(self):
        while self.running:
            try:
                input, _, _ = select(self.players, [], [])
                for i in input:
                    try:
                        data = pickle.loads(i.recv(4096))
                    except EOFError:
                        pass
                    else:
                        self.act(self.players.index(i), data.action)
                        self.sendMap(i)
            except KeyboardInterrupt:
                self.terminate()

    def act(self, player, action):
        position = self.playersPositions[player]
        if action == 'u':
            print("Player {0} wants to go up".format(player + 1))
            self.playersPositions[player] = self.move(position, -1, 0)
        elif action == 'd':
            print("Player {0} wants to go down".format(player + 1))
            self.playersPositions[player] = self.move(position, 1, 0)
        elif action == 'l':
            print("Player {0} wants to go left".format(player + 1))
            self.playersPositions[player] = self.move(position, 0, -1)
        elif action == 'r':
            print("Player {0} wants to go right".format(player + 1))
            self.playersPositions[player] = self.move(position, 0, 1)

    def move(self, position, y, x):
        ny = position.y + y
        nx = position.x + x
        if ny > 0 and ny < self.size.y:
            position.y = ny
        if nx > 0 and nx < self.size.x:
            position.x = nx
        return position

    def terminate(self):
        self.running = False
        for player in self.players:
            player.close()
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise AttributeError(
            "Incorrect number of arguments."
            " Usage: <exec> <port> <map_height> <map_width> <no_of_players>"
        )
    Server(
        int(sys.argv[1]),
        Position(int(sys.argv[2]), int(sys.argv[3])),
        int(sys.argv[4])
    ).run()
