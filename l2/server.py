# -*- coding: utf-8 -*-


import socket
from select import select
import cPickle as pickle
import sys
import time
from random import randint
from copy import copy
from protocolObjects import Countdown, Map, Position, Mine, Result


class Server(object):
    BACKLOG = 5

    def __init__(self, port, size, noOfPlayers):
        self.endgame = None
        self.mines = list()
        self.players = list()
        self.cemetery = list()
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

    def calculatePosition(self):
        while True:
            p = Position(randint(1, self.size.y), randint(1, self.size.x))
            if p not in self.playersPositions:
                return p

    def addClient(self, sock, addr):
        self.players.append(sock)
        self.playersPositions.append(self.calculatePosition())
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

    def sendResults(self):
        print("Sending end results to all players")
        result = pickle.dumps(Result(*self.endgame))
        for player in self.players:
            player.sendall(result)

    def serve(self):
        while self.running:
            try:
                input, _, _ = select(self.players, [], [])
                for i in input:
                    try:
                        data = pickle.loads(i.recv(4096))
                    except (EOFError, socket.error):
                        self.running = False
                    else:
                        index = self.players.index(i)
                        if not index in self.cemetery:
                            self.act(index, data.action)
                        if self.endgame:
                            self.sendResults()
                        else:
                            self.sendMap(i)
            except KeyboardInterrupt:
                self.running = False
        self.terminate()

    def act(self, player, action):
        position = self.playersPositions[player]
        if action == 'u':
            print("Player {0} wants to go up".format(player + 1))
            self.move(player, position, -1, 0)
        elif action == 'd':
            print("Player {0} wants to go down".format(player + 1))
            self.move(player, position, 1, 0)
        elif action == 'l':
            print("Player {0} wants to go left".format(player + 1))
            self.move(player, position, 0, -1)
        elif action == 'r':
            print("Player {0} wants to go right".format(player + 1))
            self.move(player, position, 0, 1)
        elif action == 'm':
            print("Player {0} places mine at position {1}".format(
                player + 1, position
            ))
            self.mines.append(Mine(copy(position), player))
        elif action == 'e':
            print("Player {0} wants to end the game".format(player + 1))
            self.end(player)

    def move(self, player, position, y, x):
        ny = position.y + y
        nx = position.x + x
        if ny > 0 and ny <= self.size.y:
            position.y = ny
        if nx > 0 and nx <= self.size.x:
            position.x = nx
        mined = None
        for mine in self.mines:
            if mine.position == position:
                mined = mine
                break
        print("Player {0} moved to position {1}".format(player + 1, position))
        if mined:
            print("Player {0} stepped on a mine".format(player + 1))
            self.cemetery.append(player)
            if len(self.players) - len(self.cemetery) == 1:
                self.endgame = ([(
                    set(range(len(self.players))) - set(self.cemetery)
                ).pop()], [])

    def end(self, player):
        minesPositions = [m.position for m in self.mines]
        scores = [0] * len(self.players)
        highest = 0
        winners = list()
        for i, pos in enumerate(self.playersPositions):
            q = [pos]
            while q:
                n = q.pop()
                if n not in minesPositions:
                    minesPositions.append(Position(n.y, n.x))
                    q.append(Position(n.y, n.x - 1))
                    q.append(Position(n.y, n.x + 1))
                    q.append(Position(n.y - 1, n.x))
                    q.append(Position(n.y + 1, n.x))
                    scores[i] += 1
            if scores[i] > highest:
                highest = scores[i]
                winners = [i]
            elif scores[i] == highest:
                winners.append(i)
        self.endgame = (winners, scores)
        print("Game ended with results {0}".format(self.endgame))

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
