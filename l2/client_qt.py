# -*- coding: utf-8 -*-

import sys
import socket
from select import select
import cPickle as pickle
from time import sleep

from PyQt4 import QtGui
from PyQt4.QtCore import QTimer, Qt

from protocolObjects import Countdown, Map, Result


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
        return unicode(self.host.text())

    def getPort(self):
        return self.port.value()


class _Label(QtGui.QLabel):
    def __init__(self, w, h, parent=None):
        super(_Label, self).__init__(parent=parent)
        self.setMinimumSize(w, h)
        self.setMaximumSize(w, h)
        self.setFrameShape(QtGui.QFrame.Box)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setAlignment(Qt.AlignCenter)


class Field(_Label):
    def __init__(self, parent=None):
        super(Field, self).__init__(15, 15, parent=parent)

    def setMine(self, color):
        self.setText("<font color='{}'>M</font>".format(color.name()))

    def setPlayer(self, color):
        self.setText("<font color='{}'>P</font>".format(color.name()))


class PlayerLabel(_Label):
    def __init__(self, id, color, parent=None):
        super(PlayerLabel, self).__init__(30, 30, parent=parent)
        self.setText("<font color='{}'>{}</font>".format(color.name(), id))


class CDLabel(_Label):
    def __init__(self, parent=None):
        super(CDLabel, self).__init__(30, 30, parent=parent)

    def setCD(self, cd):
        self.setText(str(cd))


class Client(QtGui.QMainWindow):
    def __init__(self, host, port):
        super(Client, self).__init__()
        self.host = host
        self.port = port
        self.colors = [
            QtGui.QColor(Qt.red), QtGui.QColor(Qt.blue),
            QtGui.QColor(Qt.yellow), QtGui.QColor(Qt.magenta),
            QtGui.QColor(Qt.white)
        ]
        self.cdLabel = CDLabel()
        self.infoLayout = QtGui.QHBoxLayout()
        self.infoLayout.addWidget(self.cdLabel)
        self.infoLayout.addStretch()
        self.msg = QtGui.QLabel()
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.msg)
        self.layout.addStretch()
        self.layout.addLayout(self.infoLayout)
        widget = QtGui.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)
        self.connected = False
        self.loop = QTimer(self)
        self.loop.timeout.connect(self.run)
        self.loop.start(0)
        self.running = True

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while not self.connected and self.running:
            try:
                self.socket.connect((self.host, self.port))
                self.connected = True
            except Exception as e:
                print(e)
                for i in range(5, -1, -1):
                    self.msg.setText(
                        "Cannot connect to server!"
                        " Will try again in {}".format(i)
                    )
                    QtGui.QApplication.processEvents()
                    sleep(1)
        self.socket.setblocking(0)

    def send(self, obj):
        _, toWrite, _ = select([], [self.socket], [])
        res = toWrite[0].sendall(pickle.dumps(obj))
        if res:
            raise Exception("Problem sending a message to socket: %s" % res)

    def receive(self):
        toRead, _, _ = select([self.socket], [], [], 0.01)
        if not toRead:
            return None
        rec = toRead[0].recv(4096)
        if len(rec) == 0:
            return None
        data = None
        while data is None:
            try:
                data = pickle.loads(rec)
            except (EOFError, pickle.UnpicklingError, ValueError):
                rec += toRead[0].recv(4096)
            QtGui.QApplication.processEvents()
        return data

    def init(self, mapSize):
        if not hasattr(self, 'mapLayout'):
            self.mapLayout = QtGui.QGridLayout()
            self.mapLayout.setContentsMargins(0, 0, 0, 0)
            self.mapLayout.setSpacing(0)
            for i in range(mapSize.x):
                for j in range(mapSize.y):
                    self.mapLayout.addWidget(Field(), i, j)
            mapWidget = QtGui.QWidget(parent=self)
            mapWidget.setLayout(self.mapLayout)
            mapWidget.setMaximumSize(mapSize.x * 15, mapSize.y * 15)
            self.layout.addWidget(mapWidget)

    def update(self, mines):
        self.cdLabel.setText('')
        for mine in mines:
            pos = mine.position
            self.mapLayout.itemAtPosition(
                pos.x - 1, pos.y - 1
            ).widget().setMine(self.colors[mine.playerId])

    def movePlayer(self, playerId, pos):
        self.mapLayout.itemAtPosition(
            pos.x - 1, pos.y - 1
        ).widget().setPlayer(self.colors[playerId])

    def run(self):
        if not self.connected:
            self.connect()
        if not self.running:
            return
        data = self.receive()
        if data is None:
            return
        if isinstance(data, Countdown):
            print("Received Countdown object")
            self.init(data.mapSize)
            if not hasattr(self, 'playerLabel'):
                self.playerId = data.playerId
                self.playerLabel = PlayerLabel(
                    self.playerId, self.colors[self.playerId]
                )
                self.infoLayout.insertWidget(0, self.playerLabel)
            self.cdLabel.setCD(data.number)
        elif isinstance(data, Map):
            print("Received Map object")
            self.update(data.mines)
            for i, pos in enumerate(data.playersPositions):
                self.movePlayer(i, pos)
        elif isinstance(data, Result):
            print("Received results")
            self.end(data)

    def kill(self):
        print("KILLING TIME!")
        self.running = False


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('l2_client_qt')
    connDialog = ConnectionDialog()
    connDialog.exec_()

    if connDialog.result() == QtGui.QDialog.Accepted:
        main = Client(connDialog.getHost(), connDialog.getPort())
        main.show()
        app.lastWindowClosed.connect(main.kill)
        sys.exit(app.exec_())
