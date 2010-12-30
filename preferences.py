# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="bobgates"
__date__ ="$Dec 30, 2010 11:53:33 AM$"

import copy
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class prefsClass():
    def __init__(self):
        self.smallJogSize = 0.01
        self.mediumJogSize = 0.1
        self.largeJogSize = 1.0

    def jogSizeByIndex(self, index):
        i = abs(index)
        sign = i/index  # -1 or 1
        if i==2:
            return sign*self.mediumJogSize
        elif i==4:
            return sign*self.largeJogSize
        else:
            return sign*self.smallJogSize

    def __str__(self):
        return 'small jog size: %.2f\nmedium: %.2f\nlarge: %.2f' % \
                (self.smallJogSize,
                 self.mediumJogSize,
                 self.largeJogSize,)

class PreferencesDialog(QDialog):
    def __init__(self, prefs, parent = None):
        super(PreferencesDialog, self).__init__(parent)

        self.prefs = copy.copy(prefs)

        jogLabel = QLabel('<b>Jog step size settings</b>')
        jogLabel.setTextFormat(Qt.RichText)
        #jogLabel.setText('<b>Jog step size settings</b>')
        smallLabel = QLabel('&Small (mm):')
        mediumLabel = QLabel('&Medium (mm):')
        largeLabel = QLabel('&Large (mm):')
        self.smallInput = QLineEdit()
        smallLabel.setBuddy(self.smallInput)
        self.mediumInput = QLineEdit()
        mediumLabel.setBuddy(self.mediumInput)
        self.largeInput = QLineEdit()
        largeLabel.setBuddy(self.largeInput)
        punctuationRe = QRegExp(r"[0-9]*\.[0-9]*")
        self.smallInput.setValidator(
                QRegExpValidator(punctuationRe, self))
        self.mediumInput.setValidator(
                QRegExpValidator(punctuationRe, self))
        self.largeInput.setValidator(
                QRegExpValidator(punctuationRe, self))



        self.setWindowTitle("Set Preferences")
        self.setPrefs()

        jogLayout = QGridLayout()
        jogLayout.addWidget(jogLabel, 0,0)

        jogLayout.addWidget(smallLabel, 1,0)
        jogLayout.addWidget(self.smallInput, 1,1)
        jogLayout.addWidget(mediumLabel, 2,0)
        jogLayout.addWidget(self.mediumInput, 2,1)
        jogLayout.addWidget(largeLabel, 3,0)
        jogLayout.addWidget(self.largeInput, 3,1)


        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                     QDialogButtonBox.Cancel)
        self.connect(buttonBox, SIGNAL("accepted()"), self, SLOT("accept()"))
        self.connect(buttonBox, SIGNAL("rejected()"), self, SLOT("reject()"))
        buttonBox.button(QDialogButtonBox.Ok).setDefault(True)

        jogLayout.addWidget(buttonBox, 4, 1, 1, 1)

        self.setLayout(jogLayout)

    def setPrefs(self):
        self.smallInput.setText(str(self.prefs.smallJogSize))
        self.mediumInput.setText(str(self.prefs.mediumJogSize))
        self.largeInput.setText(str(self.prefs.largeJogSize))

    def getPrefs(self):
        return self.prefs

    def accept(self):
        try:
            self.prefs.smallJogSize = float(str(self.smallInput.text()))
            self.prefs.mediumJogSize = float(str(self.mediumInput.text()))
            self.prefs.largeJogSize = float(str(self.largeInput.text()))
        except: # ValueError, e:
            QMessageBox.warning(self, 'Error',
                                'Error converting to floating point')
            return
        QDialog.accept(self)

    def rejectChanges(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    prefs = prefsClass()
    form = PreferencesDialog(prefs)
    if form.exec_():
        prefs = form.getPrefs()
        print prefs
    else:
        print 'Rejected'
