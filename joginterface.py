# To change this template, choose Tools | Templates
# and open the template in the editor.

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

__author__="declan"
__date__ ="$Dec 29, 2010 1:59:32 PM$"

class JogInterfaceWidget(QFrame):
    '''
    A widget that provides a UI for the jog control

    The widget presents 12 buttons, which are up and
    down for each of 3 axes at each of two speeds.

    Each of the buttons corresponds to a cursor pad
    button (left, right, up, down, pgup and pgdown)
    or a numpad button (4, 6, 8, 2, -, +). In their
    unshifted state the buttons correspond to the
    smaller of the two UI arrows. Shift-button gives
    the larger of the two UI buttons. Apple/Cmd-button
    gives the smallest step size, only available via
    the keypad, not via the mouse buttons.

    This widget labels the step sizes 1, 2 and 4, and
    they're either positive or negative for right/left,
    and up/down.

    The widget has one event: jogEvent(char, int) which
    returns the axis, 'x', 'y' or 'z'; and the stepsize
    in the range: +- 1,2,4.
    '''
    def __init__(self, parent=None):
        super(JogInterfaceWidget, self).__init__(parent)

        # I had plans to use the second item in the list for
        # each dict entry to contain its hotkey, but went for
        # a case statement instead.

        self.btnList = {'xmm': ['arrow-left-double-3'],
                        'xm' : ['arrow-left-3'],
                        'xp' : ['arrow-right-3'],
                        'xpp': ['arrow-right-double-3'],
                        'ymm': ['arrow-down-double-3'],
                        'ym' : ['arrow-down-3'],
                        'yp' : ['arrow-up-3'],
                        'ypp': ['arrow-up-double-3'],
                        'zmm': ['arrow-down-double'],
                        'zm' : ['arrow-down'],
                        'zp' : ['arrow-up'],
                        'zpp': ['arrow-up-double'],
                        }

        self.setFocusPolicy(Qt.StrongFocus)

        self.setLineWidth(2)
        self.setMidLineWidth(3)
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Raised)
#        self.setFrameStyle()

#        self.grabKeyboard()

        layout = QVBoxLayout(self)
        masterLayout = QHBoxLayout()
        fourwayLayout = QHBoxLayout()
        zLayout = QVBoxLayout()

        leftLayout = QHBoxLayout()
        middleLayout = QVBoxLayout()
        rightLayout = QHBoxLayout()
        fourwayLayout.addLayout(leftLayout)
        fourwayLayout.addLayout(middleLayout)
        fourwayLayout.addLayout(rightLayout)

        xmm = self.makeButton('xmm')
        xm = self.makeButton('xm')
        xp = self.makeButton('xp')
        xpp = self.makeButton('xpp')
        leftLayout.addWidget(xmm)
        leftLayout.addWidget(xm)
        rightLayout.addWidget(xp)
        rightLayout.addWidget(xpp)

        ypp = self.makeButton('ypp')
        yp = self.makeButton('yp')
        ym = self.makeButton('ym')
        ymm = self.makeButton('ymm')
        middleLayout.addWidget(ypp)
        middleLayout.addWidget(yp)
        middleLayout.addWidget(ym)
        middleLayout.addWidget(ymm)

        zpp = self.makeButton('zpp')
        zp = self.makeButton('zp')
        zm = self.makeButton('zm')
        zmm = self.makeButton('zmm')
        zLayout.addWidget(zpp)
        zLayout.addWidget(zp)
        zLayout.addWidget(zm)
        zLayout.addWidget(zmm)
        masterLayout.addLayout(fourwayLayout)
        masterLayout.addLayout(zLayout)

        bottomLayout = QHBoxLayout()
        self.label = QLabel()
        self.label.setText(' ')
        bottomLayout.addWidget(self.label)
        bottomLayout.setAlignment(self.label, Qt.AlignRight)

        layout.addLayout(masterLayout)
        layout.addLayout(bottomLayout)


    def clicked(self):
        button = self.sender()
        if button is None or not isinstance(button, QToolButton):
            return
        text = str(button.text())
        axis = text[0]
        dir = text[1]
        # text contains axis, followed by m, mm, p or pp:
        stepSize = 2*(len(text)-1)     # ie 2 or 4, medium or large
        if dir == 'm':
            stepSize = -stepSize
        self.emit(SIGNAL("jogEvent(char, int)"), axis, stepSize)


    # I found that the keypad not having focus was
    # not obvious enough, so set up the focusEvents to
    # make it obvious. When active, the widget has a
    # frame and is labelled.

    def focusInEvent(self, FocusEvent):
        self.setFrameShape(QFrame.Panel)
        self.label.setText('Active')
        QFrame.focusInEvent(self, FocusEvent)

    def focusOutEvent(self, FocusEvent):
        self.setFrameShape(QFrame.NoFrame)
        self.label.setText(' ')
        QFrame.focusOutEvent(self, FocusEvent)
        
    def keyPressEvent(self, event):
        '''Process keys when widget has the focus.
        
        This routine captures key presses and generates
        a signal that matches the signal from the GUI.
        It required experimentation, perhaps I'm missing
        something, but it the event didn't seem to work
        properly according to the docs.
        
        The shifting system uses the apple key. I don't
        know what this will translate to on Windows or
        Linux machines. Since it is the micro-jog, and 
        not related to the GUI, it might not matter.
        '''

        processed = False
        modifier = event.nativeModifiers()
#        print 'key: ', event.key()
#        print 'modifier: ', modifier

        # modifier is only 0 if a modifier key has been pushed,
        # but no other key. This routine seems to receive the other
        # key unmodified???
        if modifier == 0:
            return

        # What follows is by experiment. On the mac, at least
        # 196608 is a constant modifier on the cursor keypad
        # and 65536 is a constant modifier on the numeric keypad.
        # 512 is what's left if that value is shifted. This is _not_
        # what the docs say, at least not the way I read them.
        shifted = False
        apple = False
        while modifier>65535:
            modifier-=65536
#        print 'modifier: ', modifier
        if modifier == 512:   #Qt.ShiftModifier:
            shifted = True
        if modifier == 256:
            apple = True
#            print 'Shifted ',

        key = event.key()
        if (key == Qt.Key_Left) or (key == Qt.Key_4):
            processed = True
            axis='x'
            stepSize=-2
#            print 'Left'
        elif (key == Qt.Key_Right) or (key == Qt.Key_6):
            axis='x'
            stepSize=2
            processed = True
#            print 'Right'
        elif (key == Qt.Key_Down) or (key == Qt.Key_2):
            axis='y'
            stepSize=-2
            processed = True
#            print 'Down'
        elif (key == Qt.Key_Up) or (key == Qt.Key_8):
            axis='y'
            stepSize=2
            processed = True
#            print 'Up'
        elif (key == Qt.Key_PageUp) or (key == Qt.Key_Minus):
            axis='z'
            stepSize=2
            processed = True
#            print 'z up'
        elif (key == Qt.Key_PageDown) or (key == Qt.Key_Plus):
            axis='z'
            stepSize=-2
            processed = True
#            print 'z down'

        if processed:
            if apple:
                stepSize /= 2
            if shifted:
                stepSize *= 2
#            print 'about to output ', axis, stepSize
            self.emit(SIGNAL("jogEvent(char, int)"), axis, stepSize)
        else:
            QFrame.keyPressEvent(self, event)

    def makeButton(self, name):
        icon = self.btnList[name][0]
#        shortcut = self.btnList[name][1]
        btn = QToolButton()
        btn.setText(name)
#        if shortcut:
#            print 'Setting shortcut: ', shortcut
#            btn.setShortcut(shortcut)
        btn.setIcon(QIcon('./images/%s.png' % icon))
        self.connect(btn, SIGNAL("clicked()"), self.clicked)
        return btn

class Form(QDialog):
    '''A test form for JogInterfaceWidget.


    Very simple dialog that allows for testing of
    the jogInterfaceWidget.
    '''

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        self.jog = JogInterfaceWidget()
        self.closeButton = QPushButton("Close")

        layout = QVBoxLayout()
        layout.addWidget(self.jog)
        layout.addWidget(self.closeButton)
        self.setLayout(layout)

        self.connect(self.jog, SIGNAL("jogEvent(char, int)"), self.test_jog)
        self.connect(self.closeButton, SIGNAL("clicked()"), self.close)

    def test_jog(self, axis, stepSize):
        print axis, stepSize


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    form.raise_()
    form.jog.grabKeyboard()
    app.exec_()
