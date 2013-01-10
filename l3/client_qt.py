# -*- coding: utf-8 -*-


from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, ClientFactory
import sys
import cPickle as pickle
from cStringIO import StringIO

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignal

from protocolObjects import Countdown, Map, Result, PlayerAction


class ConnectionDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(ConnectionDialog, self).__init__(parent=parent)
        label = QtGui.QLabel('Please enter host and port:')
        self.host = QtGui.QLineEdit('127.0.0.1', parent=self)
        self.port = QtGui.QSpinBox(parent=self)
        self.port.setMinimum(1)
        self.port.setMaximum(65536)
        self.port.setValue(3333)
        self.msg = QtGui.QLabel()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.host)
        layout.addWidget(self.port)
        layout.addWidget(self.msg)
        layout.addStretch()
        cancel = QtGui.QPushButton('Cancel')
        cancel.clicked.connect(self.rejected)
        ok = QtGui.QPushButton('OK')
        ok.clicked.connect(self.oked)
        ok.setDefault(True)
        btnLayout = QtGui.QHBoxLayout()
        btnLayout.addWidget(cancel)
        btnLayout.addWidget(ok)
        layout.addLayout(btnLayout)
        self.setLayout(layout)

    def oked(self):
        split = self.host.text().split('.')
        if len(split) != 4:
            return self.wrongHost()
        for s in split:
            try:
                sint = int(s)
            except ValueError:
                return self.wrongHost()
            else:
                if sint > 255:
                    return self.wrongHost()
        self.accept()

    def wrongHost(self):
        self.msg.setText('Wrong host address!')

    def getHost(self):
        return str(self.host.text())

    def getPort(self):
        return self.port.value()


COLORS = [
    QtGui.QColor(Qt.red), QtGui.QColor(Qt.blue),
    QtGui.QColor(Qt.yellow), QtGui.QColor(Qt.magenta),
    QtGui.QColor(Qt.white)
]


class _Label(QtGui.QLabel):
    def __init__(self, w, h, parent=None):
        super(_Label, self).__init__(parent=parent)
        self.setFixedSize(w, h)
        self.setFrameShape(QtGui.QFrame.Box)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setAlignment(Qt.AlignCenter)


class Field(_Label):
    def __init__(self, parent=None):
        super(Field, self).__init__(20, 20, parent=parent)
        self.mineId = None
        self.playerId = None
        self.playerPath = QtGui.QPainterPath()
        self.playerPath.setFillRule(Qt.WindingFill)
        self.playerPath.addEllipse(5, 5, 10, 10)
        self.minePath = QtGui.QPainterPath()
        self.minePath.setFillRule(Qt.WindingFill)
        self.minePath.addEllipse(4, 4, 12, 12)
        self.minePath.addRect(1, 9, 18, 2)
        self.minePath.addRect(9, 1, 2, 18)

    def setMine(self, id):
        self.mineId = id
        self.update()

    def setPlayer(self, id):
        self.playerId = id
        self.update()

    def removePlayer(self):
        self.playerId = None
        self.update()

    def paintEvent(self, event):
        super(Field, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self.mineId is not None:
            painter.setBrush(QtGui.QBrush(COLORS[self.mineId]))
            painter.drawPath(self.minePath)
        if self.playerId is not None:
            painter.setBrush(QtGui.QBrush(COLORS[self.playerId]))
            painter.drawPath(self.playerPath)


class PlayerLabel(_Label):
    def __init__(self, id, parent=None):
        super(PlayerLabel, self).__init__(40, 40, parent=parent)
        self.setText("<font size='20' color='{}'>{}</font>".format(
            COLORS[id].name(), id
        ))


class CDLabel(_Label):
    def __init__(self, parent=None):
        super(CDLabel, self).__init__(40, 40, parent=parent)

    def setCD(self, cd):
        self.setText("<font size='20'>{}</font>".format(cd))


class ResultsLabel(_Label):
    def __init__(self, winners, scores, width=120, parent=None):
        super(ResultsLabel, self).__init__(width, 40, parent=parent)
        scoresStr = ", ".join([
            "{}: {}".format(i, s) for i, s in enumerate(scores)
        ])
        self.setText("winner(s): {}\nscores: {}".format(
            ", ".join(map(str, winners)), scoresStr or "last man standing"
        ))


class MapWidget(QtGui.QWidget):
    keyPressed = pyqtSignal(str)

    def __init__(self, w, h, parent=None):
        super(MapWidget, self).__init__(parent=parent)
        self.setMaximumSize(w, h)
        self.grabKeyboard()

    def clear(self):
        for field in self.children()[1:]:
            field.removePlayer()

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_Left:
            self.keyPressed.emit('l')
        elif k == Qt.Key_Right:
            self.keyPressed.emit('r')
        elif k == Qt.Key_Up:
            self.keyPressed.emit('u')
        elif k == Qt.Key_Down:
            self.keyPressed.emit('d')
        elif k == Qt.Key_Space:
            self.keyPressed.emit('m')
        elif k == Qt.Key_X:
            self.keyPressed.emit('e')
        elif k == Qt.Key_C:
            self.keyPressed.emit('c')


class GUI(QtGui.QMainWindow):
    def __init__(self, factory):
        super(GUI, self).__init__()
        self.factory = factory
        self.cdLabel = CDLabel()
        self.infoLayout = QtGui.QHBoxLayout()
        self.infoLayout.addWidget(self.cdLabel)
        self.infoLayout.addStretch()
        self.msg = QtGui.QLabel("Waiting for connection...")
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.msg)
        self.layout.addLayout(self.infoLayout)
        widget = QtGui.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)
        self.dirty = list()
        self.receive()

    def receive(self):
        d = self.factory.get()
        d.addCallbacks(self.serve, self.fail)

    def init(self, mapSize):
        self.msg.hide()
        if not hasattr(self, 'mapLayout'):
            self.mapLayout = QtGui.QGridLayout()
            self.mapLayout.setContentsMargins(0, 0, 0, 0)
            self.mapLayout.setSpacing(0)
            for i in range(mapSize.x):
                for j in range(mapSize.y):
                    self.mapLayout.addWidget(Field(), i, j)
            self.mapWidget = MapWidget(
                mapSize.x * 20, mapSize.y * 20, parent=self
            )
            self.mapWidget.setLayout(self.mapLayout)
            scrollArea = QtGui.QScrollArea()
            scrollArea.setWidget(self.mapWidget)

            def move(action):
                self.factory.send(action)
            self.mapWidget.keyPressed.connect(move)
            self.layout.addWidget(scrollArea)

    def update(self, mines):
        self.cdLabel.setText('')
        for mine in mines:
            pos = mine.position
            self.mapLayout.itemAtPosition(
                pos.y - 1, pos.x - 1
            ).widget().setMine(mine.playerId)

    def end(self, results):
        self.results = ResultsLabel(
            results.winners, results.scores,
            self.mapWidget.width() - 92
        )
        self.infoLayout.insertWidget(2, self.results)
        self.mapWidget.keyPressed.disconnect()

    def movePlayer(self, playerId, pos):
        self.mapLayout.itemAtPosition(
            pos.y - 1, pos.x - 1
        ).widget().setPlayer(playerId)
        self.dirty.append((pos.y - 1, pos.x - 1))

    def serve(self, data):
        if isinstance(data, Countdown):
            print("Received countdown")
            self.init(data.mapSize)
            if not hasattr(self, 'playerLabel'):
                self.playerId = data.playerId
                self.playerLabel = PlayerLabel(self.playerId)
                self.infoLayout.insertWidget(0, self.playerLabel)
            self.cdLabel.setCD(data.number)
        elif isinstance(data, Map):
            print("Received map")
            self.update(data.mines)
            for x, y in self.dirty:
                self.mapLayout.itemAtPosition(x, y).widget().removePlayer()
            for i, pos in enumerate(data.playersPositions):
                self.movePlayer(i, pos)
        elif isinstance(data, Result):
            print("Received results")
            self.end(data)
        self.receive()

    def fail(self, why):
        self.msg.setText("Failed to perform action: {}".format(why))
        self.receive()

    def closeEvent(self, event):
        self.factory.stop()


class ClientProtocol(Protocol):
    def __init__(self):
        self.rec = StringIO()

    def connectionMade(self):
        self.factory.run(self)

    def connectionLost(self, reason):
        self.factory.stop()

    def dataReceived(self, data):
        self.rec.write(data)
        self.rec.flush()
        self.rec = StringIO(self.rec.getvalue())
        pickling = True
        while pickling:
            try:
                result = pickle.load(self.rec)
            except (pickle.UnpicklingError, ValueError):
                pickling = False
            except EOFError:
                self.rec.close()
                self.rec = StringIO()
                pickling = False
            except Exception as e:
                self.factory.fail(e)
                pickling = False
            else:
                self.factory.notify(result)

    def send(self, obj):
        self.transport.write(pickle.dumps(obj))


class Client(ClientFactory):
    protocol = ClientProtocol

    def clientConnectionFailed(self, connector, reason):
        connector.connect()

    def run(self, client):
        self.client = client

    def stop(self):
        self.client = None
        from twisted.internet import reactor
        reactor.stop()
        sys.exit(0)

    def notify(self, data):
        self.d.callback(data)

    def fail(self, why):
        self.d.errback(why)

    def send(self, obj):
        self.client.send(PlayerAction(obj))

    def get(self):
        self.d = Deferred()
        return self.d


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('l3_client_qt')
    connDialog = ConnectionDialog()
    connDialog.exec_()

    if connDialog.result() == QtGui.QDialog.Accepted:
        factory = Client()
        main = GUI(factory)
        import qt4reactor
        qt4reactor.install()
        from twisted.internet import reactor
        main.show()
        reactor.connectTCP(connDialog.getHost(), connDialog.getPort(), factory)
        reactor.run()
