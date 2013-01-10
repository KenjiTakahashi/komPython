# -*- coding: utf-8 -*-


from twisted.internet.protocol import Protocol
from twisted.protocols.policies import LimitTotalConnectionsFactory
import cPickle as pickle
import sys
from random import randint
from copy import copy
from protocolObjects import Countdown, Map, Position, Mine, Result
from protocolObjects import PlayerAction


class ServerProtocol(Protocol):
    def __init__(self):
        self.dead = False
        self.rec = ""

    def connectionMade(self):
        print("A client has connected")
        self.no = self.factory.addClient(self)
        self.position = self.factory.calculatePosition(self)
        countdown = Countdown(3, self.factory.getMapSize(), self.no)
        from twisted.internet import reactor
        for j, i in enumerate(range(3, 0, -1)):
            countdown.number = i
            reactor.callLater(
                j, self.transport.write, pickle.dumps(countdown)
            )
        reactor.callLater(3, self.factory.refresh)

    def connectionLost(self, reason):
        print("A client has disconnected")
        self.factory.removeClient(self)

    def dataReceived(self, data):
        if not self.factory.run:
            return
        self.rec += data
        try:
            result = pickle.loads(self.rec)
        except (EOFError, pickle.UnpicklingError, ValueError):
            self.rec += data
        else:
            if isinstance(result, PlayerAction) and not self.dead:
                self.serve(result.action)
            self.rec = ""

    def serve(self, action):
        if action == 'u':
            print("Player {0} wants to go up".format(self.no + 1))
            self.move(-1, 0)
        elif action == 'd':
            print("Player {0} wants to go down".format(self.no + 1))
            self.move(1, 0)
        elif action == 'l':
            print("Player {0} wants to go left".format(self.no + 1))
            self.move(0, -1)
        elif action == 'r':
            print("Player {0} wants to go right".format(self.no + 1))
            self.move(0, 1)
        elif action == 'm':
            print("Player {0} places mine at position {1}".format(
                self.no + 1, self.position
            ))
            self.factory.addMine(self.position, self.no)
        elif action == 'e':
            print("Player {0} wants to end the game".format(self.no + 1))
            self.factory.end(self.no)
        self.factory.refresh()

    def move(self, y, x):
        ny = self.position.y + y
        nx = self.position.x + x
        if self.factory.collided(ny, nx):
            return
        self.position = Position(ny, nx)
        print("Player {0} moved to position {1}".format(
            self.no + 1, self.position
        ))
        if self.factory.mined(self.position):
            print("Player {0} stepped on a mine".format(self.no + 1))
            self.dead = True
            self.factory.tryEnd()


class Server(LimitTotalConnectionsFactory):
    protocol = ServerProtocol

    def __init__(self, size, maxPlayers):
        self.endgame = None
        self.mines = list()
        self.players = list()
        Server.connectionLimit = maxPlayers
        self.size = size
        self.run = False

    def buildProtocol(self, addr):
        protocol = LimitTotalConnectionsFactory.buildProtocol(self, addr)
        if not self.run and self.connectionCount == Server.connectionLimit:
            self.run = True
        return protocol

    def refresh(self):
        print("Sending new maps")
        positions = [c.position for c in self.players]
        data = pickle.dumps(Map(self.mines, positions))
        for client in self.players:
            client.transport.write(data)

    def addClient(self, client):
        self.players.append(client)
        return len(self.players) - 1

    def removeClient(self, client):
        self.players.remove(client)

    def calculatePosition(self, client):
        while True:
            p = Position(randint(1, self.size.y), randint(1, self.size.x))
            for player in self.players:
                if player == client:
                    continue
                if player.position == p:
                    p = None
            if p:
                return p

    def getMapSize(self):
        return self.size

    def addMine(self, position, client):
        self.mines.append(Mine(copy(position), client))

    def collided(self, y, x):
        if Position(y, x) in [c.position for c in self.players]:
            return True
        if y < 1 or y > self.size.y:
            return True
        if x < 1 or x > self.size.x:
            return True
        return False

    def mined(self, position):
        for mine in self.mines:
            if mine.position == position:
                return True
        return False

    def tryEnd(self):
        cemetery = [c for c in self.players if c.dead]
        if len(self.players) - len(cemetery) <= 1:
            try:
                self.endgame = (
                    [(set(self.players) - set(cemetery)).pop().no], []
                )
            except KeyError:
                self.endgame = ([], [])
            self.sendResults()

    def end(self, player):
        scores = [0] * len(self.players)
        highest = 0
        winners = list()
        for i, client in enumerate(self.players):
            pos = client.position
            if client.dead:
                continue
            minesPositions = [m.position for m in self.mines]
            q = [pos]
            while q:
                n = q.pop()
                if n not in minesPositions:
                    minesPositions.append(Position(n.y, n.x))
                    scores[i] += 1
                    if n.x > 0:
                        q.append(Position(n.y, n.x - 1))
                        if n.y > 0:
                            q.append(Position(n.y - 1, n.x - 1))
                        if n.y < self.size.y - 1:
                            q.append(Position(n.y + 1, n.x - 1))
                    if n.x < self.size.x - 1:
                        q.append(Position(n.y, n.x + 1))
                        if n.y > 0:
                            q.append(Position(n.y - 1, n.x + 1))
                        if n.y < self.size.y - 1:
                            q.append(Position(n.y + 1, n.x + 1))
                    if n.y > 0:
                        q.append(Position(n.y - 1, n.x))
                    if n.y < self.size.y - 1:
                        q.append(Position(n.y + 1, n.x))
            if scores[i] > highest:
                highest = scores[i]
                winners = [i]
            elif scores[i] == highest and i != player:
                winners.append(i)
        self.endgame = (winners, scores)
        print("Game ended with results {0}".format(self.endgame))
        self.sendResults()

    def sendResults(self):
        print("Sending end results to all players")
        result = pickle.dumps(Result(*self.endgame))
        for player in self.players:
            player.transport.write(result)
        self.mines = list()
        self.endgame = None

    def stopFactory(self):
        print("Terminating...")
        self.run = False
        for player in self.players:
            player.transport.loseConnection()


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise AttributeError(
            "Incorrect number of arguments."
            " Usage: <exec> <port> <map_height> <map_width> <no_of_players>"
        )
    factory = Server(
        Position(int(sys.argv[2]), int(sys.argv[3])),
        int(sys.argv[4])
    )
    from twisted.internet import reactor
    reactor.listenTCP(int(sys.argv[1]), factory)
    reactor.run()
