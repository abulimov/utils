#!/usr/bin/env python
#
# Visualize /proc/meminfo cache stats
# ===
#
# Copyright 2014 Alexander Bulimov <lazywolf0@gmail.com>
#
# Released under the MIT license, see LICENSE for details.
import sys
from PySide import QtGui, QtCore


class MemoryDrawer(QtGui.QWidget):

    def __init__(self):
        super(MemoryDrawer, self).__init__()

        self.initUI()
        self.data = dict()
        self.getData()

    def initUI(self):

        self.setWindowTitle('/proc/meminfo visualizer')
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onTimer)
        self.timer.start(100)
        self.show()

    def paintEvent(self, e):

        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRectangles(qp)
        qp.end()

    def drawRectangles(self, qp):

        height = self.geometry().height()
        width = self.geometry().width()
        dataSet = [('MemFree:', 'darkGreen'),
                   ('Active(file):', 'darkMagenta'),
                   ('Inactive(file):', 'darkRed'),
                   ('Cached:', 'darkCyan')]
        offset = 20
        count = len(dataSet)
        sizeX = (width - (count + 1) * offset) // count

        sizeY = height - 2 * offset

        x = offset
        y = offset

        for pos, (data, colorName) in enumerate(dataSet):
            x = (pos + 1) * offset + pos * sizeX
            color = QtGui.QColor(colorName)
            pixmap = self.drawGraph(sizeX, sizeY, data, color)
            qp.drawPixmap(x, y, pixmap)

    def drawGraph(self, width, height, dataKey, color):
        memTotal = self.data['MemTotal:']
        kbPerPixel = height / memTotal

        dataValue = self.data[dataKey]
        drawData = dataValue * kbPerPixel

        pixmap = QtGui.QPixmap(width, height)
        qp = QtGui.QPainter()
        qp.begin(pixmap)
        qp.setBrush(QtGui.QColor(255, 255, 255))
        qp.drawRect(0, 0, width, height)
        qp.setBrush(color)
        qp.drawRect(0, height - drawData, width, height)
        qp.drawText(QtCore.QPoint(5, 20), dataKey)
        qp.drawText(QtCore.QPoint(5, 40), "%s kb" % dataValue)
        qp.end()
        return pixmap

    def getData(self):
        with open('/proc/meminfo') as f:
            for line in f.readlines():
                if line:
                    splitted = line.split()
                    self.data[splitted[0]] = int(splitted[1])

    def onTimer(self):
        self.getData()
        self.update()


def main():
    app = QtGui.QApplication(sys.argv)
    drawer = MemoryDrawer()
    drawer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
