# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="bobgates"
__date__ ="$Dec 28, 2010 3:32:25 PM$"

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class QLineEditArrows(QLineEdit):
    '''Subclass QLineEdit so that use of the
    up or down keys triggers an event.'''
    
    def __init__(self, parent = None):
        super(QLineEditArrows, self).__init__(parent)
        self.key = QString()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.emit(SIGNAL('keyUpDown'), 'up')
            print 'Key up pressed'
        if event.key() == Qt.Key_Down:
            self.emit(SIGNAL('keyUpDown'), 'down')
            pass

        QLineEdit.keyPressEvent(self, event)

#----------------------------------------------------------------------
class CommandWidget(QWidget):
    '''
    Widget that displays two windows, a command
    history and a current command. It works like a
    very simple command line with some memory:
    Commands are put into history on pressing enter.
    Using the up and down arrows changes the contents
    of the command line to the appropriate line from
    the history.
    '''
    def __init__(self, parent=None):
        super(CommandWidget, self).__init__(parent)

        # Build up widget from subwidgets:
        self.cepLayout = QVBoxLayout(self)
        historyLabel = QLabel("History:")
        self.historyText = QTextEdit()
        self.cepLayout.addWidget(historyLabel)
        self.cepLayout.addWidget(self.historyText)

        print 'added history label'

        commandLabel = QLabel("Command:")
        self.commandLayout = QHBoxLayout()
        self.commandLine = QLineEditArrows()
        self.goButton = QPushButton("Go")
        self.connect(self.commandLine, SIGNAL('returnPressed()'), self.goOneLine)
        self.connect(self.commandLine, SIGNAL('keyUpDown'), self.commandKeyPress)
        self.connect(self.goButton, SIGNAL('clicked()'), self.goOneLine)

        self.commandLayout.addWidget(self.commandLine)
        self.commandLayout.addWidget(self.goButton)

        self.cepLayout.addWidget(commandLabel)
        self.cepLayout.addLayout(self.commandLayout)

        #Maintain state:
        self.historyLine = -1

    def countHistoryLines(self):
        lines = self.historyText.document().toPlainText()
        lines = lines.split("\n")
        return len(lines)-1

    def returnHistoryLine(self, lineNumber):
        lines = self.historyText.document().toPlainText()
        lines = lines.split("\n")
        return lines[lineNumber]

    def goOneLine(self):
        self.emit(SIGNAL('goCommand'), self.commandLine.text())
        self.historyText.append(self.commandLine.text())
        self.commandLine.setText('')
        self.historyLine = -1

    def commandKeyPress(self, keyStr):
        '''Implements a simple history
        for the command entry line, using the history window.
        '''

        numLines = self.countHistoryLines()

        if (self.historyLine == -1):
            if keyStr=='up':
                self.historyLine = numLines     # point to most recent line
        else:
            if (keyStr == 'up') and (self.historyLine>0):
                self.historyLine -= 1
            if (keyStr == 'down') and (self.historyLine<numLines):
                self.historyLine += 1

        self.commandLine.setText(self.returnHistoryLine(self.historyLine))


if __name__ == "__main__":
    print "Hello World"
