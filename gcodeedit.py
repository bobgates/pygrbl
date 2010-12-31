from PyQt4.QtCore import *
from PyQt4.QtGui import *


(GE_EMPTY, GE_LOADING, GE_STOPPED, GE_RUNNING, GE_SINGLESTEP) = range(5) 

class gcodeEdit(QTextEdit):
    '''A class that adds a few methods to QTextEdit to
       support gcode editing and control of gcode processing.
    '''

    def __init__(self, parent=None):
        super(gcodeEdit, self).__init__(parent)
        self.activeLine = -1
        self.oldCursorLine = -1
        self.oldCursorFormat = ''
        self.connect(self, SIGNAL("cursorPositionChanged()"), self.highlightCursorLine) 
        self.state = GE_EMPTY
        
    def cursorToLine(self, lineNumber):
        block = self.document().findBlockByNumber(lineNumber-1)  
        cursor = QTextCursor(block)
        self.setTextCursor(cursor)

    def getLine(self, lineNumber):
        block = self.document().findBlockByNumber(lineNumber-1)      
        return str(block.text())

    def setState(self, state):
        self.state = state

    def state(self):
        return self.state

    def highlightCursorLine(self):
        if (self.state == GE_EMPTY) or (self.state == GE_RUNNING):
            return

        cursor = self.textCursor()
        cursorLine = cursor.block().blockNumber()+1
    
        if self.oldCursorLine == cursorLine:
            return
        
        if self.oldCursorLine>=0:
            #print 'Restoring old cursor'
            block = self.document().findBlockByNumber(self.oldCursorLine-1)  
            old_cursor = QTextCursor(block)
            old_cursor.setBlockFormat(self.oldCursorFormat)
            
#        cursor = self.textCursor()
        self.oldCursorFormat = cursor.blockFormat()
        self.oldCursorLine = cursorLine
        cursorLineFormat = QTextBlockFormat()
        cursorLineFormat.setBackground(QColor(Qt.green))
        #print 'Drawing green line'
        cursor.setBlockFormat(cursorLineFormat)

    def getActiveLine(self):
        cursor = self.textCursor()
        return cursor.block().blockNumber()+1 
        
    def setActiveLine(self, lineNumber):
        '''Highlight the line in the text editor that has
        the line number currently being executed. The line
        number sent to grbl starts with 1, but corresponds
        to line 0 in the text editor, hence the -1 in the 
        calls that set the highlight.
        
        In QTextEdit, a block is the same as a \n delimited
        line, as long as there are no images or tables in 
        the document.
        '''

        #print 'setActiveLine: ', lineNumber

        #unhighlight old block, if it wasn't zero:
        if lineNumber == self.activeLine:
            return

        keywordFormat = QTextBlockFormat()
        if self.activeLine>0:
            block = self.document().findBlockByNumber(self.activeLine-1) 
            
            format = block.blockFormat()
            format.clearBackground()
            
            cursor = QTextCursor(block)
            cursor.setBlockFormat(format)

        #highlight the new block, if it isn't zero:        
        self.activeLine = lineNumber
        if self.activeLine>0:
            block = self.document().findBlockByNumber(self.activeLine-1)  
            cursor = QTextCursor(block)
            keywordFormat.setBackground(Qt.yellow)
            cursor.setBlockFormat(keywordFormat)
            self.setTextCursor(cursor)
            
#        self.getActiveLine()
