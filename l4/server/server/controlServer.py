# -*- coding: utf-8 -*-


from twisted.internet.protocol import Protocol, ServerFactory
import json


class ServerProtocol(Protocol):
    def __init__(self):
        self.welcome = {'welcome': 'Welcome to a game server!'}
        self.rec = ""

    def connectionMade(self):
        print("A controller has connected")
        self.transport.write(json.dumps(self.welcome))

    def connectionLost(self, reason):
        print("A controller has disconnected: {}".format(reason))

    def dataReceived(self, data):
        self.rec += data
        print("Sending data to controller")
        try:
            result = json.loads(self.rec)
        except (EOFError, ValueError):
            self.rec += data
        else:
            if ['state'] == result.keys():
                self.serve(result)
            self.rec = ""

    def serve(self, data):
        data['state'] = self.factory.getState()
        self.transport.write(json.dumps(data))


class Server(ServerFactory):
    protocol = ServerProtocol

    def __init__(self, playFactory):
        self.playFactory = playFactory

    def getState(self):
        return {
            'currently-connected-players':
            self.playFactory.controlConnectedPlayers(),
            'games-already-played': self.playFactory.controlGamesPlayed(),
            'messages-sent': self.playFactory.controlMessagesSent(),
            'messages-received': self.playFactory.controlMessagesReceived()
        }
