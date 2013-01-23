# -*- coding: utf-8 -*-


import sys
from server.protocolObjects import Position
from server import playServer, controlServer


def run():
    if len(sys.argv) != 5:
        raise AttributeError(
            "Incorrect number of arguments."
            " Usage: <exec> <port> <map_height> <map_width> <no_of_players>"
        )
    playFactory = playServer.Server(
        Position(int(sys.argv[2]), int(sys.argv[3])),
        int(sys.argv[4])
    )
    controlFactory = controlServer.Server(playFactory)
    from twisted.internet import reactor
    reactor.listenTCP(int(sys.argv[1]), playFactory)
    reactor.listenTCP(int(sys.argv[1]) + 1, controlFactory)
    reactor.run()
