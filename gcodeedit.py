import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *


(GE_EMPTY, GE_LOADING, GE_STOPPED, GE_RUNNING, GE_SINGLESTEP) = range(5) 

(GE_COL_STATUS, GE_COL_GCODE) = range(2)

class gcodeEdit(QTableWidget):
    '''A class that adds a few methods to QTextEdit to
       support gcode editing and control of gcode processing.
    '''

    def __init__(self, parent=None):
        super(gcodeEdit, self).__init__(parent)
        self.activeLine = -1
        self.oldCursorLine = -1
        self.oldCursorFormat = ''
#        self.connect(self, SIGNAL("cursorPositionChanged()"), self.highlightCursorLine)
        self.state = GE_EMPTY
        self.setSortingEnabled(False)

        font = QFont("Monaco", 12)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()

    def resizeEvent(self, event):
        self.setColumnWidth(1, event.size().width()-16)
        
    def loadNewFile(self, filename):
        file = open(filename)
        a=file.readlines()
        file.close()

        print len(a)

        self.clear()
        self.setSortingEnabled(False)
        self.setRowCount(len(a))
        self.setColumnCount(2)
        self.setColumnWidth(0,16)
        print 'Width', self.width()
        self.setColumnWidth(1, self.width()-16)
#        self.tableWidget.setHorizontalHeaderLabels(headers)


        self.clear()
        for i, line in enumerate(a):
            self.setItem(i,GE_COL_GCODE, QTableWidgetItem(line.strip('\n')))
            self.setRowHeight(i,16)
            
        self.setState(GE_STOPPED)
        self.setCurrentCell(0,GE_COL_GCODE)
#        self.resizeColumnsToContents()

#
    def cursorToLine(self, lineNumber):
        self.setCurrentCell(lineNumber, GE_COL_GCODE)

#        block = self.document().findBlockByNumber(lineNumber-1)
#        cursor = QTextCursor(block)
#        self.setTextCursor(cursor)
#
    def getLine(self, lineNumber):
#        block = self.document().findBlockByNumber(lineNumber-1)
        return str(self.item(lineNumber-1,GE_COL_GCODE).text())
#
    def setState(self, state):
        self.state = state

    def state(self):
        return self.state

    def highlightCursorLine(self):
        pass
#        if (self.state == GE_EMPTY) or (self.state == GE_RUNNING):
#            return
#
#        cursor = self.textCursor()
#        cursorLine = cursor.block().blockNumber()+1
#
#        if self.oldCursorLine == cursorLine:
#            return
#
#        if self.oldCursorLine>=0:
#            #print 'Restoring old cursor'
#            block = self.document().findBlockByNumber(self.oldCursorLine-1)
#            old_cursor = QTextCursor(block)
#            old_cursor.setBlockFormat(self.oldCursorFormat)
#
##        cursor = self.textCursor()
#        self.oldCursorFormat = cursor.blockFormat()
#        self.oldCursorLine = cursorLine
#        cursorLineFormat = QTextBlockFormat()
#        cursorLineFormat.setBackground(QColor(Qt.green))
#        #print 'Drawing green line'
#        cursor.setBlockFormat(cursorLineFormat)
#
    def getActiveLine(self):
        return self.currentRow()+1
#        cursor = self.textCursor()
#        return cursor.block().blockNumber()+1
#
    def setActiveLine(self, lineNumber):
        self.setCurrentCell(lineNumber-1,GE_COL_GCODE)


    def markSent(self, lineNumber):
        '''Mark this line as having been sent to grbl.
        '''
        self.item(lineNumber-1,GE_COL_GCODE).setTextColor(QColor(Qt.darkGreen))


    def markDone(self, lineNumber):
        '''Mark as having come back from grbl okay.
        '''
        self.item(lineNumber-1,GE_COL_GCODE).setTextColor(QColor(Qt.darkGray))

    def markError(self, lineNumber):
        self.item(lineNumber-1, GE_COL_GCODE).setTextColor(QColor(Qt.black))
        self.item(lineNumber-1, GE_COL_GCODE).setBackgroundColor(QColor(Qt.red))

        '''Mark line has having an error
        '''
        pass

#    def markLineActive(self, lineNumber):

    def markBreakpoint(self, lineNumber):
        '''Place a breakpoint at this line
        '''
        pass



#        '''Highlight the line in the text editor that has
#        the line number currently being executed. The line
#        number sent to grbl starts with 1, but corresponds
#        to line 0 in the text editor, hence the -1 in the
#        calls that set the highlight.
#
#        In QTextEdit, a block is the same as a \n delimited
#        line, as long as there are no images or tables in
#        the document.
#        '''
#
#        #print 'setActiveLine: ', lineNumber
#
#        #unhighlight old block, if it wasn't zero:
#        if lineNumber == self.activeLine:
#            return
#
#        keywordFormat = QTextBlockFormat()
#        if self.activeLine>0:
#            block = self.document().findBlockByNumber(self.activeLine-1)
#
#            format = block.blockFormat()
#            format.clearBackground()
#
#            cursor = QTextCursor(block)
#            cursor.setBlockFormat(format)
#
#        #highlight the new block, if it isn't zero:
#        self.activeLine = lineNumber
#        if self.activeLine>0:
#            block = self.document().findBlockByNumber(self.activeLine-1)
#            cursor = QTextCursor(block)
#            keywordFormat.setBackground(Qt.yellow)
#            cursor.setBlockFormat(keywordFormat)
#            self.setTextCursor(cursor)
#
#
    def lines(self, index=1):
        index=index-1
        while index<self.rowCount():
            block = self.item(index,GE_COL_GCODE)
            yield index+1, str(block.text())
            index+=1

class Form(QDialog):
    '''A test form for gcodeEdit.

    '''

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        self.editor = gcodeEdit()
        self.editor.setMinimumWidth(500)
        self.editor.setMinimumHeight(400)
        self.closeButton = QPushButton("Close")


        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        hl = QHBoxLayout()
        hl.addWidget(self.closeButton)
        hl.setAlignment(self.closeButton, Qt.AlignRight)
        layout.addLayout(hl)
        self.setLayout(layout)

#        self.connect(self.jog, SIGNAL("jogEvent(char, int)"), self.test_jog)
        self.connect(self.closeButton, SIGNAL("clicked()"), self.close)

        self.editor.loadNewFile('gcode files/cnc_circles.txt')


        self.editor.markDone(1)
        self.editor.markDone(2)
        self.editor.markError(3)
        self.editor.setActiveLine(4)
        self.editor.markSent(5)
        self.editor.markSent(6)
        self.editor.markBreakpoint(7)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    form.raise_()
    app.exec_()
