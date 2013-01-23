# -*- coding: utf-8 -*-


from twisted.internet.protocol import Protocol, ClientFactory
import sys
import json
from cStringIO import StringIO


class ControllerProtocol(Protocol):
    def __init__(self):
        self.rec = StringIO()

    def connectionMade(self):
        sys.stdout.write("Success\n")

    def connectionLost(self, reason):
        from twisted.internet import reactor
        reactor.stop()

    def dataReceived(self, data):
        self.rec.write(data)
        self.rec.flush()
        self.rec = StringIO(self.rec.getvalue())
        pickling = True
        while pickling:
            try:
                result = json.load(self.rec)
            except ValueError:
                pickling = False
            except EOFError:
                self.rec.close()
                self.rec = StringIO()
                pickling = False
            except Exception as e:
                self.factory.fail(e)
                pickling = False
            else:
                keys = result.keys()
                if keys == ['welcome']:
                    print(result['welcome'])
                    self.send()
                elif keys == ['state']:
                    self.write(result['state'])
                    self.transport.loseConnection()
                self.rec = StringIO()

    def send(self):
        self.transport.write(json.dumps({'state': None}))

    def write(self, data):
        sys.stdout.write("Server state:\n{}".format(
            "".join(["{}: {}\n".format(k, v) for k, v in data.iteritems()])
        ))


class Controller(ClientFactory):
    protocol = ControllerProtocol

    def __init__(self):
        sys.stdout.write('Connecting to the server...')
        sys.stdout.flush()

    def clientConnectionFailed(self, connector, reason):
        connector.connect()


def run():
    if len(sys.argv) != 3:
        raise AttributeError(
            "Incorrect number of arguments."
            " Usage: <exec> <host> <port>"
        )
    from twisted.internet import reactor
    factory = Controller()
    reactor.connectTCP(sys.argv[1], int(sys.argv[2]), factory)
    reactor.run()
