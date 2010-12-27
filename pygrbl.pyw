#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import os
import platform
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import logging

#import helpform
#import newimagedlg

import helpform
import qrc_resources
import grblserial
from gcparser import gcParser
import ogl_window
from gcodeedit import gcodeEdit

logger = logging.getLogger('grblserial')

__version__ = "0.1.0"

(GE_EMPTY, GE_LOADING, GE_STOPPED, GE_RUNNING, GE_SINGLESTEP) = range(5) 


#***********************************************************************************
class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        #State:
        self.recentFiles = []
        self.activeLine =-1
        self.filename = 'cncweb.txt'
        self.play=False

        # Create the right hand widget, give it a layout
        # and put the viewer and the geometry/view controls into it.
        rwidget = QWidget()
        rlayout = QVBoxLayout(rwidget)
        self.gcViewer = ogl_window.GLWidget()#twidget)
        
        self.glWidgetArea = QScrollArea()
        self.glWidgetArea.setWidget(self.gcViewer)
        self.glWidgetArea.setWidgetResizable(True)
        self.glWidgetArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.glWidgetArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.glWidgetArea.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.glWidgetArea.setMinimumSize(600, 400)

        # Load a default file for debugging purposes:
        parser = gcParser()
        parser.load(self.filename)
        center, radius =  parser.getGLLimits(parser.gl_list)
        self.gcViewer.initDrawList(parser.gl_list)
#       print 'In pygrbl main, center: ', center, ', radius %.3f' % (radius,)
        self.gcViewer.setLimits(center, radius)
        self.gcViewer.setTopView()
        # self.gcViewer.resizeGL(self.gcViewer.width(), self.gcViewer.height())
        # self.gcViewer.setMinimumSize(300, 300)
        # self.gcViewer.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        self.grbl = grblserial.grblSerial()
        self.connect(self.grbl, SIGNAL('statusChanged'), self.updateStatus)
        self.connect(self.grbl, SIGNAL("CommandFailed(PyQt_PyObject)"), self.commandFailed)
        
        self.timerInterval = 500
        self.timer = QTimer() 
        self.connect(self.timer, SIGNAL("timeout()"), self.grbl.tick) 
        self.timer.start(self.timerInterval);
        
        viewTopAction = self.createAction("&Top", self.gcViewer.setTopView,
                 None, 'projection_top',
                 "View simulation from top")
        viewTopRotAction = self.createAction("Top &Right", self.gcViewer.setTopRotView,
                 None, 'projection_toprot',
                 "View simulation from top rotated")
        viewFrontAction = self.createAction("&Front", self.gcViewer.setFrontView,
                 None, 'projection_front',
                 "View simulation from front")
        viewLeftAction = self.createAction("&Front", self.gcViewer.setLeftView,
                 None, 'projection_left',
                 "View simulation from left")
        viewIsoAction = self.createAction("&Iso", self.gcViewer.setIsoView,
                 None, 'projection_iso',
                 "View simulation in isometric form")

        viewerToolbar = QToolBar("Views")
        viewerToolbar.setObjectName("ViewerToolBar")
        viewerToolbar.addAction(viewTopAction)
        viewerToolbar.addAction(viewTopRotAction)
        viewerToolbar.addAction(viewFrontAction)
        viewerToolbar.addAction(viewLeftAction)
        viewerToolbar.addAction(viewIsoAction)
        viewerToolbar.addSeparator()
        
        rlayout.addWidget(self.glWidgetArea)
        rlayout.addWidget(viewerToolbar)
        
# Create a left hand TAB widget that contains controls 
# and editing stuff

# Code entry page:

        self.codeEntryPage=QWidget()
        self.cepLayout = QVBoxLayout(self.codeEntryPage)
        historyLabel = QLabel("History:")
        self.historyText = QTextEdit()
        self.cepLayout.addWidget(historyLabel)
        self.cepLayout.addWidget(self.historyText)
        
        commandLabel = QLabel("Command:")
        self.commandLayout = QHBoxLayout()
        self.commandLine = QLineEdit()
        self.goButton =  QPushButton("Go")
        self.connect(self.goButton, SIGNAL('clicked()'), self.goOneLine)

        self.commandLayout.addWidget(self.commandLine)
        self.commandLayout.addWidget(self.goButton)
        
        self.cepLayout.addWidget(commandLabel)
        self.cepLayout.addLayout(self.commandLayout)


        self.Tabs = QTabWidget()
        self.Tabs.addTab(self.codeEntryPage, "Code Entry (F5)")

#Control page:
        self.controlPage = QWidget()
        self.controlLayout = QVBoxLayout(self.controlPage)
        clabel = QLabel("My controls")
        self.controlLayout.addWidget(clabel)
        
        
        self.Tabs.insertTab(0,self.controlPage, "Manual Control (F3)")


        font = QFont("Courier", 14)
        font.setFixedPitch(True)
#Bottom area that contains the text file:
        self.editor = gcodeEdit()
        self.editor.setFont(font)
        
# Create the splitters that manage space of all
# the sub places        
        
        self.leftrightSplit = QSplitter()
        self.leftrightSplit.addWidget(self.Tabs)
        self.leftrightSplit.addWidget(rwidget)
        self.mainsplit = QSplitter(Qt.Vertical)
        self.mainsplit.addWidget(self.leftrightSplit)
        self.mainsplit.addWidget(self.editor)
        self.setCentralWidget(self.mainsplit)

        self.printer = None

#Stuff across the bottom
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.sizeLabel.setAlignment(Qt.AlignLeft)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.sizeLabel)
        status.showMessage("Ready", 5000)
        
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignRight)
        self.progress.setMinimum(0)
        self.progress.setMaximum(80)
        self.progress.setValue(80)
         
        status.addPermanentWidget(self.progress)
        
        self.sizeLabel.setText('Label')
#         fileNewAction = self.createAction("&New...", self.fileNew,
#                 QKeySequence.New, "filenew", "Create an image file")
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                 QKeySequence.Open, "fileopen",
                 "Open an existing G-code file")
        fileSaveAction = self.createAction("&Save", self.fileSave,
                QKeySequence.Save, "filesave", "Save the gcode file")
        fileSaveAsAction = self.createAction("Save &As...",
                self.fileSaveAs, icon="filesaveas",
                tip="Save the gcode file using a new name")
#         filePrintAction = self.createAction("&Print", self.filePrint,
#                 QKeySequence.Print, "fileprint", "Print the image")
        fileQuitAction = self.createAction("&Quit", 
                self.fileQuit,
                 "Ctrl+Q", "filequit", "Close the application")
        fileQuitAction.MenuRole = QAction.QuitRole
        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, (fileOpenAction, fileSaveAction))#, 
                                   #None, fileSaveAsAction, fileQuitAction))

        emergencyStopAction = self.createAction("&Stop", 
                self.emergencyStop,
                 "Ctrl+X", "process-stop-2", "Stop the machine")

        helpAboutAction = self.createAction("&About Image Changer",
                self.helpAbout)
        helpHelpAction = self.createAction("&Help", self.helpHelp,
                QKeySequence.HelpContents)

        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpAboutAction, helpHelpAction))

        self.runPlayPause = self.createAction("&PlayPause", self.playPause,
                 None, "media-playback-start-2", 
                 "Play or pause G-Code file")
        self.runBackOne = self.createAction("&BackOne", self.decFrame,
                 None, "media-seek-backward-2", 
                 "Step back one line")
        self.runForwardOne = self.createAction("&ForwardOne", self.incFrame,
                 None, "media-seek-forward-2", 
                 "Step forward one line")

        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolBar")
        fileToolbar.setMovable(False)
        self.addActions(fileToolbar, (fileQuitAction, 
                                      fileOpenAction, 
                                      fileSaveAction,
                                      fileSaveAsAction))
        fileToolbar.addAction(fileQuitAction)
        fileToolbar.addSeparator()
        fileToolbar.addAction(self.runPlayPause)
        fileToolbar.addAction(self.runBackOne)
        fileToolbar.addAction(self.runForwardOne)

        fileToolbar.addSeparator()

        # fileToolbar.addAction(viewTopAction)
        # fileToolbar.addAction(viewTopRotAction)
        # fileToolbar.addAction(viewFrontAction)
        # fileToolbar.addAction(viewLeftAction)
        # fileToolbar.addAction(viewIsoAction)
        # fileToolbar.addSeparator()
        
        fileToolbar.addAction(emergencyStopAction)
        
#    def tick(self):
#        pass

    def updateStatus(self, status):
        self.gcViewer.setPosition(status)
        self.editor.setActiveLine(status.lineNumber)

    def playPause(self):
        if self.play:
            self.goPause()
        else:
            self.goPlay()
            
    def goPlay(self):
        cursorLine = self.editor.getActiveLine()
        self.editor.setState(GE_RUNNING)
        logger.debug('About to start goPlay()()()()()()()()()()()()()()()()()')
        self.play = True
        self.runPlayPause.setIcon(QIcon('images/media-playback-pause-2.png'))
        block = self.editor.document().begin()
        lineNumber = 1
        while block.isValid(): 
            if lineNumber >= cursorLine:
                self.grbl.queueCommand(str(block.text()), lineNumber=lineNumber)
            block = block.next()   
            lineNumber+=1
        logger.debug('Leaving goPlay()()()()()()()()()()()()()()()()()()()()')
            
        
    def goPause(self):
        self.editor.setState(GE_STOPPED)
        self.play = False;
        self.emergencyStop() 
        self.runPlayPause.setIcon(QIcon('images/media-playback-start-2.png'))

    def commandFailed(self, command):
#       self.emergencyStop()
#       if command[0]=='N':
#            i=1
#            while command[i].isdigit():
#                i+=1
#            lineNumber = int(command[1:i])
#                  
#               
#              command = 'N'+str(lineNumber)+command[i:]
#         
#         lineNum = command[1:

        QMessageBox.critical(self,
                             "Error in gcode",
                             "Error in line: "+str(command),
                             )

    def setLimits(self, centre, radius):
        for i in range(3):
            offset = centre[i]
            if i==0:
                slider = self.xOffsetSlider
            elif i==1:
                slider = self.yOffsetSlider
            else:
                slider = self.zOffsetSlider
            if offset>1:
                slider.setMaximum(0)
                slider.setMinimum(-offset*2)
                slider.setValue(-offset)
            elif offset<-1:
                slider.setMinimum(0)
                slider.setMaximum(-offset*2)
                slider.setValue(-offset)
            else:
                slider.setMinimum(-1)
                slider.setMaximum(1)
                slider.setValue(-offset)
        self.glWidget.setRadius(radius)

    def decFrame(self):
        pass
        
    def incFrame(self):
        pass

    # def viewTop(self):
    #   self.gcViewer.setTopView()
    #   # self.gcViewer.updateGL()
    # 
    # def viewTopRot(self):
    #   self.gcViewer.setTopRotView()
    #   # self.gcViewer.updateGL()
    #   
    # def viewFront(self):
    #   self.gcViewer.setFrontView()
    #   # self.gcViewer.updateGL()
    #   
    # def viewIso(self):
    #   self.gcViewer.setIsoView()
    #   # self.gcViewer.updateGL()
        
    def emergencyStop(self):
        self.grbl.emergencyStop()


    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon('./images/%s.png' % icon)) #":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
        
#----------------------------------------------------------------------
# Declan's utility routines

    def createButton(self, IconFile, Text, slotName):
        button = QPushButton(QIcon(IconFile), Text)
        button.setFixedSize(QSize(32,32))
        button.setIconSize(QSize(25,25))
        self.connect(button, SIGNAL('clicked()'),slotName)
        return button

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
 
 
    def goOneLine(self):
        self.grbl.queueCommand(str(self.commandLine.text()))
        self.historyText.append(self.commandLine.text())
        self.commandLine.setText('')
    

    def closeEvent(self, event):
        if self.okToContinue():
            settings = QSettings()
            filename = QVariant(QString(self.filename)) if self.filename is not None else QVariant()
            settings.setValue("LastFile", filename)
            recentFiles = QVariant(self.recentFiles) if self.recentFiles else QVariant()
            settings.setValue("RecentFiles", recentFiles)
            settings.setValue("MainWindow/Size", QVariant(self.size()))
            settings.setValue("MainWindow/Position",
                    QVariant(self.pos()))
            settings.setValue("MainWindow/State",
                    QVariant(self.saveState()))
        else:
            event.ignore()
# 
# 
    def okToContinue(self):
#         if self.dirty:
#             reply = QMessageBox.question(self,
#                             "Pygrbl - Unsaved Changes",
#                             "Save unsaved changes?",
#                             QMessageBox.Yes|QMessageBox.No|
#                             QMessageBox.Cancel)
#             if reply == QMessageBox.Cancel:
#                 return False
#             elif reply == QMessageBox.Yes:
#                 self.fileSave()
        return True
# 
# 
#     def loadInitialFile(self):
#         settings = QSettings()
#         fname = unicode(settings.value("LastFile").toString())
#         if fname and QFile.exists(fname):
#             self.loadFile(fname)
# 
# 
#     def updateStatus(self, message):
#         self.statusBar().showMessage(message, 5000)
#         self.listWidget.addItem(message)
#         if self.filename is not None:
#             self.setWindowTitle("Image Changer - %s[*]" % \
#                                 os.path.basename(self.filename))
#         elif not self.image.isNull():
#             self.setWindowTitle("Image Changer - Unnamed[*]")
#         else:
#             self.setWindowTitle("Image Changer[*]")
#         self.setWindowModified(self.dirty)
# 
# 
#     def updateFileMenu(self):
#         self.fileMenu.clear()
#         self.addActions(self.fileMenu, self.fileMenuActions[:-1])
#         current = QString(self.filename) \
#                 if self.filename is not None else None
#         recentFiles = []
#         for fname in self.recentFiles:
#             if fname != current and QFile.exists(fname):
#                 recentFiles.append(fname)
#         if recentFiles:
#             self.fileMenu.addSeparator()
#             for i, fname in enumerate(recentFiles):
#                 action = QAction(QIcon(":/icon.png"), "&%d %s" % (
#                         i + 1, QFileInfo(fname).fileName()), self)
#                 action.setData(QVariant(fname))
#                 self.connect(action, SIGNAL("triggered()"),
#                              self.loadFile)
#                 self.fileMenu.addAction(action)
#         self.fileMenu.addSeparator()
#         self.fileMenu.addAction(self.fileMenuActions[-1])
# 
# 
#     def fileNew(self):
#         if not self.okToContinue():
#             return
#         dialog = newimagedlg.NewImageDlg(self)
#         if dialog.exec_():
#             self.addRecentFile(self.filename)
#             self.image = QImage()
#             for action, check in self.resetableActions:
#                 action.setChecked(check)
#             self.image = dialog.image()
#             self.filename = None
#             self.dirty = True
#             self.showImage()
#             self.sizeLabel.setText("%d x %d" % (self.image.width(),
#                                                 self.image.height()))
#             self.updateStatus("Created new image")
# 
# 
    def fileOpen(self):
        #assert False
        dir = os.path.dirname(self.filename) if self.filename is not None else "."
        formats = ["*.nc", "*.txt", "*.ngc"]
        fname = unicode(QFileDialog.getOpenFileName(self, "Choose G-code file", dir,
                                    "G Code (%s)" % " ".join(formats)))
        if fname:
            self.filename=fname
            self.load()
   

    def load(self):
        exception = None
        fh = None
        try:
            fh = QFile(self.filename)
            if not fh.open(QIODevice.ReadOnly):
                raise IOError, unicode(fh.errorString())
            stream = QTextStream(fh)
            stream.setCodec("UTF-8")
            self.editor.clear()
            self.editor.setLineWrapMode(QTextEdit.NoWrap)
            self.editor.document().setModified(False)
            
            # using infile to temporarily store g-code for submission
            # to gcViewer. 
            file_contents = []
            while not stream.atEnd():
                a=stream.readLine()
                self.editor.append(a)
                file_contents.append(a)
            self.editor.cursorToLine(0)
            self.editor.setState(GE_STOPPED)
            
            
            parser = gcParser()
            parser.load(self.filename)
            center, radius =  parser.getGLLimits(parser.gl_list)
            self.gcViewer.initDrawList(parser.gl_list)
            self.gcViewer.setLimits(center, radius)
            self.gcViewer.setTopView()
            
        except (IOError, OSError), e:
            exception = e
        finally:
            if fh is not None:
                fh.close()
            if exception is not None:
                raise exception


     
#         if fname is None:
#             action = self.sender()
#             if isinstance(action, QAction):
#                 fname = unicode(action.data().toString())
#                 if not self.okToContinue():
#                     return
#             else:
#                 return
#         if fname:
#             self.filename = None
#             image = QImage(fname)
#             if image.isNull():
#                 message = "Failed to read %s" % fname
#             else:
#                 self.addRecentFile(fname)
#                 self.image = QImage()
#                 for action, check in self.resetableActions:
#                     action.setChecked(check)
#                 self.image = image
#                 self.filename = fname
#                 self.showImage()
#                 self.dirty = False
#                 self.sizeLabel.setText("%d x %d" % (
#                             image.width(), image.height()))
#                 message = "Loaded %s" % os.path.basename(fname)
#             self.updateStatus(message)
# 
# 
#     def addRecentFile(self, fname):
#         if fname is None:
#             return
#         if not self.recentFiles.contains(fname):
#             self.recentFiles.prepend(QString(fname))
#             while self.recentFiles.count() > 9:
#                 self.recentFiles.takeLast()
# 
# 
    def fileSave(self):
        if self.image.isNull():
            return
        if self.filename is None:
            self.fileSaveAs()
        else:
            if self.image.save(self.filename, None):
                self.updateStatus("Saved as %s" % self.filename)
                self.dirty = False
            else:
                self.updateStatus("Failed to save %s" % self.filename)


    def fileSaveAs(self):
        if self.image.isNull():
            return
        fname = self.filename if self.filename is not None else "."
        formats = ["*.%s" % unicode(format).lower() \
                   for format in QImageWriter.supportedImageFormats()]
        fname = unicode(QFileDialog.getSaveFileName(self,
                        "Image Changer - Save Image", fname,
                        "Image files (%s)" % " ".join(formats)))
        if fname:
            if "." not in fname:
                fname += ".png"
            self.addRecentFile(fname)
            self.filename = fname
            self.fileSave()
# 
# 
#     def filePrint(self):
#         if self.image.isNull():
#             return
#         if self.printer is None:
#             self.printer = QPrinter(QPrinter.HighResolution)
#             self.printer.setPageSize(QPrinter.Letter)
#         form = QPrintDialog(self.printer, self)
#         if form.exec_():
#             painter = QPainter(self.printer)
#             rect = painter.viewport()
#             size = self.image.size()
#             size.scale(rect.size(), Qt.KeepAspectRatio)
#             painter.setViewport(rect.x(), rect.y(), size.width(),
#                                 size.height())
#             painter.drawImage(0, 0, self.image)
    def fileQuit(self): 
        self.close()   
 
#     def editZoom(self):
#         if self.image.isNull():
#             return
#         percent, ok = QInputDialog.getInteger(self,
#                 "Image Changer - Zoom", "Percent:",
#                 self.zoomSpinBox.value(), 1, 400)
#         if ok:
#             self.zoomSpinBox.setValue(percent)
 
    def helpAbout(self):
        QMessageBox.about(self, "About PyGrbl",
                """<b>PyGrbl</b> v %s
                <p>Copyright &copy; 2010 bobgates 
                All rights reserved.
                <p>This application sequences g-code files for
                the grbl application running on Arduino that runs
                a CNC mill.
                <p>Python %s - Qt %s - PyQt %s on %s""" % (
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))
# 
#
    def helpHelp(self):
        form = helpform.HelpForm("index.html", self)
        form.show()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("TSC")
    app.setOrganizationDomain("github.com/bobgates")
    app.setApplicationName("G-code sequencer for GRBL")
    app.setWindowIcon(QIcon("images/icon.png"))
    form = MainWindow()
    form.show()
    sys.exit(app.exec_())

main()

