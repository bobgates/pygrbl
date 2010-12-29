# To change this template, choose Tools | Templates
# and open the template in the editor.

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

__author__="declan"
__date__ ="$Dec 29, 2010 1:59:32 PM$"

class JogInterfaceWidget(QWidget):
    '''
    A widget that lays out all the buttons for a jog control
    '''
    def __init__(self, parent=None):
        super(JogInterfaceWidget, self).__init__(parent)

        self.btnList = {'xmm': ['arrow-left-double-3',''],
                        'xm' : ['arrow-left-3',''],
                        'xp' : ['arrow-right-3','QKeySequence.MoveToNextChar'],
                        'xpp': ['arrow-right-double-3','QKeySequence.MoveToNextWord'],
                        'ymm': ['arrow-down-double-3',''],
                        'ym' : ['arrow-down-3',''],
                        'yp' : ['arrow-up-3',''],
                        'ypp': ['arrow-up-double-3',''],
                        'zmm': ['arrow-down-double',''],
                        'zm' : ['arrow-down',''],
                        'zp' : ['arrow-up',''],
                        'zpp': ['arrow-up-double',''],
                        }

        self.setFocusPolicy(Qt.StrongFocus)

#        self.grabKeyboard()

        masterLayout = QHBoxLayout(self)
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


    def clicked(self):
        button = self.sender()
        if button is None or not isinstance(button, QToolButton):
            return
        text = str(button.text())
        axis = text[0]
        dir = text[1]
        speed = len(text)-1     # ie 1 or 2, slow or fast
        if dir == 'm':
            speed = -speed
        self.emit(SIGNAL("jogEvent(char, int)"), axis, speed)


#        print axis, speed

    def keyPressEvent(self, event):
        processed = False

        modifier = event.nativeModifiers()
#        print 'modifier: ', modifier

        # What follows is by experiment. On the mac, at least
        # 196608 is a constant modifier on the cursor keypad
        # and 65536 is a constant modifier on the numeric keypad.
        # 512 is what's left if that value is shifted. This is _not_
        # what the docs say, at least not the way I read them.
        shifted = False
        while modifier>65535:
            modifier-=65536
        if modifier == 512:   #Qt.ShiftModifier:
            shifted = True
#            print 'Shifted ',

        key = event.key()
        if (key == Qt.Key_Left) or (key == Qt.Key_4):
            processed = True
            axis='x'
            speed=-1
#            print 'Left'
        elif (key == Qt.Key_Right) or (key == Qt.Key_6):
            axis='x'
            speed=1
            processed = True
#            print 'Right'
        elif (key == Qt.Key_Down) or (key == Qt.Key_2):
            axis='y'
            speed=-1
            processed = True
#            print 'Down'
        elif (key == Qt.Key_Up) or (key == Qt.Key_8):
            axis='y'
            speed=1
            processed = True
#            print 'Up'
        elif (key == Qt.Key_PageUp) or (key == Qt.Key_Minus):
            axis='z'
            speed=-1
            processed = True
#            print 'z up'
        elif (key == Qt.Key_PageDown) or (key == Qt.Key_Plus):
            axis='z'
            speed=1
            processed = True
#            print 'z down'

        if processed:
            if shifted:
                speed*=2
#            print 'about to output ', axis, speed
            self.emit(SIGNAL("jogEvent(char, int)"), axis, speed)
        else:
            QMainWindow.keyPressEvent(self, event)

    def makeButton(self, name):
        icon = self.btnList[name][0]
        shortcut = self.btnList[name][1]
        btn = QToolButton()
        btn.setText(name)
        if shortcut:
            print 'Setting shortcut: ', shortcut
            btn.setShortcut(shortcut)
        btn.setIcon(QIcon('./images/%s.png' % icon))
        self.connect(btn, SIGNAL("clicked()"), self.clicked)
        return btn

class Form(QDialog):
    '''
    Very simple dialog that allows for testing of the jogInterfaceWidget
    '''

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        self.width = 1
        self.beveled = False
        self.style = "Solid"

        self.jog = JogInterfaceWidget()
        self.closeButton = QPushButton("Close")

        layout = QVBoxLayout()
        layout.addWidget(self.jog)
        layout.addWidget(self.closeButton)
        self.setLayout(layout)

        self.connect(self.jog, SIGNAL("jogEvent(char, int)"), self.test_jog)
        self.connect(self.closeButton, SIGNAL("clicked()"), self.close)

    def test_jog(self, axis, speed):
        print axis, speed


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    form.jog.grabKeyboard()
    app.exec_()
