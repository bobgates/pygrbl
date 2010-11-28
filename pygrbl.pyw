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
#import helpform
#import newimagedlg

import qrc_resources

import gc_parser


__version__ = "0.1.0"



class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

# Create the right hand widget, give it a layout
# and put the viewer and the geometry/view controls into it.
        rwidget = QWidget()
        rlayout = QVBoxLayout(rwidget)
        self.gcViewer = gc_parser.gcViewer()#twidget)

        self.filename = ''
        self.play=False
        file = open('cncweb.txt')
        a=file.readlines()
        file.close()
        self.gcViewer.setGLList(gc_parser.parse_file(a))

        self.gcViewer.goTopView()
        self.gcViewer.setMinimumSize(300, 300)
        self.gcViewer.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        viewTopAction = self.createAction("&Top", self.viewTop,
                 None, None,
                 "View simulation from top")
        viewFrontAction = self.createAction("&Front", self.viewFront,
                 None, None,
                 "View simulation from front")
        viewIsoAction = self.createAction("&Iso", self.viewIso,
                 None, None,
                 "View simulation in isometric form")

        viewerToolbar = QToolBar("Views")
        viewerToolbar.setObjectName("ViewerToolBar")
        viewerToolbar.addAction(viewTopAction)
        viewerToolbar.addAction(viewFrontAction)
        viewerToolbar.addAction(viewIsoAction)
        
        rlayout.addWidget(self.gcViewer)
        rlayout.addWidget(viewerToolbar)
        
# Create a left hand TAB widget that contains controls 
# and editing stuff

# Code entry page:

        self.codeEntryPage=QWidget()
        self.cepLayout = QVBoxLayout(self.codeEntryPage)
        historyLabel = QLabel("History:")
        self.historyText = QTextBrowser()
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



#Bottom area that contains the text file:
        self.editWidget = QTextEdit()
        
# Create the splitters that manage space of all
# the sub places        
        
        self.leftrightSplit = QSplitter()
        self.leftrightSplit.addWidget(self.Tabs)
        self.leftrightSplit.addWidget(rwidget)
        self.mainsplit = QSplitter(Qt.Vertical)
        self.mainsplit.addWidget(self.leftrightSplit)
        self.mainsplit.addWidget(self.editWidget)
        self.setCentralWidget(self.mainsplit)

# Editor and controls

#        self.editbar = QToolBar("EditTool")
#        self.addToolBar(Qt.LeftToolBarArea, self.editbar)
#        self.editbar.setObjectName("EditToolBar")
        
        
#                 self.actionbar = QToolBar("Actions")
#         self.addToolBar(Qt.BottomToolBarArea, self.actionbar)
#         self.actionbar.setObjectName("ActionToolBar")
#         self.actionbar.setAllowedAreas(Qt.BottomToolBarArea)
#         self.actionbar.setFloatable(False)
#         self.actionbar.setMovable(False)
# 
#        self.playpause = self.createButton('images/media-playback-start-2.png', 
#                                           '', self.playPause)
#         self.actionbar.addWidget(self.playpause)
#         self.actionbar.addSeparator()
#        self.backone = self.createButton('images/media-seek-backward-2.png','',self.decFrame)
#         self.actionbar.addWidget(self.backone)
# 
# 
#         self.frameslider = QSlider(Qt.Horizontal)
#         self.frameslider.setRange(1,100)
#         self.frameslider.setValue(50)
#         self.frameslider.setFixedWidth(100)
#         self.frameslider.setFixedHeight(32)
#         self.actionbar.addWidget(self.frameslider)
#         self.connect(self.frameslider, SIGNAL('valueChanged(int)'), self.setFrame)
# 
#        self.forwardone = self.createButton('images/media-seek-forward-2.png', '', self.incFrame)
#         self.actionbar.addWidget(self.forwardone)

#        self.editPage = QVBoxLayout()
#        self.editPage.addWidget(self.editWidget)
#        qtemp = QTabWidget()
#        qtemp.addLayout(self.editPage) 
        
#         self.editbar.addWidget(self.editWidget)
#         self.editbar.setAllowedAreas(Qt.LeftToolBarArea)
#         self.editbar.setFloatable(False)
#         self.editbar.setMovable(False)
#         self.editbar.addWidget(self.playpause)
#         self.editbar.addWidget(self.backone)
#         self.editbar.addWidget(self.forwardone)








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
   
   
   
   
        
        
# 
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
#         editInvertAction = self.createAction("&Invert",
#                 self.editInvert, "Ctrl+I", "editinvert",
#                 "Invert the image's colors", True, "toggled(bool)")

        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, (fileOpenAction, fileSaveAction, 
                                   None, fileSaveAsAction, fileQuitAction))
                                   
#        fileMenu.addSeparator()
#        fileMenu.addAction(fileQuitAction)
        
        
#                fileSaveAction, fileSaveAsAction, fileSaveAllAction,
#                None, fileQuitAction))



#    def addActions(self, target, actions):
#        for action in actions:
#            if action is None:
#                target.addSeparator()
#            else:
#                target.addAction(action)


#        self.fileMenu = self.menuBar().addMenu("&File")
#        self.addActions = (fileMenu, (fileOpenAction, fileQuitAction))
#                 fileSaveAction, fileSaveAsAction, None,
#                 filePrintAction, fileQuitAction)

#         self.fileMenuActions = (fileNewAction, fileOpenAction,
#                 fileSaveAction, fileSaveAsAction, None,
#                 filePrintAction, fileQuitAction)
#         self.connect(self.fileMenu, SIGNAL("aboutToShow()"),
#                      self.updateFileMenu)
#         editMenu = self.menuBar().addMenu("&Edit")
#         self.addActions(editMenu, (editInvertAction,
#                 editSwapRedAndBlueAction, editZoomAction))
#         mirrorMenu = editMenu.addMenu(QIcon(":/editmirror.png"),
#                                       "&Mirror")
#         self.addActions(mirrorMenu, (editUnMirrorAction,
#                 editMirrorHorizontalAction, editMirrorVerticalAction))
#         helpMenu = self.menuBar().addMenu("&Help")
#         self.addActions(helpMenu, (helpAboutAction, helpHelpAction))
# 


        self.runPlayPause = self.createAction("&PlayPause", self.playPause,
                 None, "media-playback-start-2", 
                 "Play or pause G-Code file")
        self.runBackOne = self.createAction("&BackOne", self.decFrame,
                 None, "media-seek-backward-2", 
                 "Step back one line")
        self.runForwardOne = self.createAction("&ForwardOne", self.incFrame,
                 None, "media-seek-forward-2", 
                 "Step forward one line")
#    def createAction(self, text, slot=None, 
#                     shortcut=None, icon=None,
#                     tip=None, checkable=False, signal="triggered()"):

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

        fileToolbar.addAction(viewTopAction)
        fileToolbar.addAction(viewFrontAction)
        fileToolbar.addAction(viewIsoAction)
        

        
         #fileNewAction, 
#                                       fileSaveAsAction))
#         editToolbar = self.addToolBar("Edit")
#         editToolbar.setObjectName("EditToolBar")
#         self.addActions(editToolbar, (editInvertAction,
#                 editSwapRedAndBlueAction, editUnMirrorAction,
#                 editMirrorVerticalAction,
#                 editMirrorHorizontalAction))
#         self.zoomSpinBox = QSpinBox()
#         self.zoomSpinBox.setRange(1, 400)
#         self.zoomSpinBox.setSuffix(" %")
#         self.zoomSpinBox.setValue(100)
#         self.zoomSpinBox.setToolTip("Zoom the image")
#         self.zoomSpinBox.setStatusTip(self.zoomSpinBox.toolTip())
#         self.zoomSpinBox.setFocusPolicy(Qt.NoFocus)
#         self.connect(self.zoomSpinBox,
#                      SIGNAL("valueChanged(int)"), self.showImage)
#         editToolbar.addWidget(self.zoomSpinBox)
# 
#         self.addActions(self.imageLabel, (editInvertAction,
#                 editSwapRedAndBlueAction, editUnMirrorAction,
#                 editMirrorVerticalAction, editMirrorHorizontalAction))
# 
#         self.resetableActions = ((editInvertAction, False),
#                                  (editSwapRedAndBlueAction, False),
#                                  (editUnMirrorAction, True))
# 
#         settings = QSettings()
#         self.recentFiles = settings.value("RecentFiles").toStringList()
#         size = settings.value("MainWindow/Size",
#                               QVariant(QSize(600, 500))).toSize()
#         self.resize(size)
#         position = settings.value("MainWindow/Position",
#                                   QVariant(QPoint(0, 0))).toPoint()
#         self.move(position)
#         self.restoreState(
#                 settings.value("MainWindow/State").toByteArray())
#         
#         self.setWindowTitle("Image Changer")
#         self.updateFileMenu()
#         QTimer.singleShot(0, self.loadInitialFile)
# 
# 
     
    def playPause(self):
        if self.play:
            self.goPause()
        else:
            self.goPlay()
            
    def goPlay(self):
#        if self.frame >= self.nframes:
#            self.frame=0
        self.play = True
#        self.playpause.setIcon(QIcon('images/media-playback-pause-2.png'))
        self.runPlayPause.setIcon(QIcon('images/media-playback-pause-2.png'))
#        self.timer.start(self.framedelay)
    
    def goPause(self):
        self.play = False;
        self.runPlayPause.setIcon(QIcon('images/media-playback-start-2.png'))
#        self.timer.stop()

    def decFrame(self):
        pass
    def incFrame(self):
        pass


    def viewTop(self):
        self.gcViewer.goTopView()
        self.gcViewer.updateGL()
        
    def viewFront(self):
        self.gcViewer.goFrontView()
        self.gcViewer.updateGL()
    	
    def viewIso(self):
        self.gcViewer.goIsoView()
        self.gcViewer.updateGL()


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
        QMessageBox.about(self, "Sending line", self.commandLine.text())
        
    
# 
#     def closeEvent(self, event):
#         if self.okToContinue():
#             settings = QSettings()
#             filename = QVariant(QString(self.filename)) \
#                     if self.filename is not None else QVariant()
#             settings.setValue("LastFile", filename)
#             recentFiles = QVariant(self.recentFiles) \
#                     if self.recentFiles else QVariant()
#             settings.setValue("RecentFiles", recentFiles)
#             settings.setValue("MainWindow/Size", QVariant(self.size()))
#             settings.setValue("MainWindow/Position",
#                     QVariant(self.pos()))
#             settings.setValue("MainWindow/State",
#                     QVariant(self.saveState()))
#         else:
#             event.ignore()
# 
# 
#     def okToContinue(self):
#         if self.dirty:
#             reply = QMessageBox.question(self,
#                             "Image Changer - Unsaved Changes",
#                             "Save unsaved changes?",
#                             QMessageBox.Yes|QMessageBox.No|
#                             QMessageBox.Cancel)
#             if reply == QMessageBox.Cancel:
#                 return False
#             elif reply == QMessageBox.Yes:
#                 self.fileSave()
#         return True
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
    
    
#         if not self.okToContinue():
#             return
#         dir = os.path.dirname(self.filename) \
#                 if self.filename is not None else "."
#         formats = ["*.%s" % unicode(format).lower() \
#                    for format in QImageReader.supportedImageFormats()]
#         fname = unicode(QFileDialog.getOpenFileName(self,
#                             "GCode sequencer - Choose design file", dir,
#                             "G Code (%s)" % " ".join(formats)))
#         if fname:
#             self.loadFile(fname)
# 
# 
#     def loadFile(self, fname=None):
#       self.

    def load(self):
        exception = None
        fh = None
        try:
            fh = QFile(self.filename)
            if not fh.open(QIODevice.ReadOnly):
                raise IOError, unicode(fh.errorString())
            stream = QTextStream(fh)
            stream.setCodec("UTF-8")
            self.editWidget.clear()
            self.editWidget.setLineWrapMode(QTextEdit.NoWrap)
            
            
            infile = []
            while not stream.atEnd():
                a=stream.readLine()
            	self.editWidget.append(a)
            	infile.append(a)
            self.gcViewer.setGLList(gc_parser.parse_file(infile))

            
            
#            self.setPlainText(stream.readAll())
#            self.document().setModified(False)
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
# 
# 
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
        QApplication.closeAllWindows()# 
# 
#     def editInvert(self, on):
#         if self.image.isNull():
#             return
#         self.image.invertPixels()
#         self.showImage()
#         self.dirty = True
#         self.updateStatus("Inverted" if on else "Uninverted")
# 
# 
#     def editSwapRedAndBlue(self, on):
#         if self.image.isNull():
#             return
#         self.image = self.image.rgbSwapped()
#         self.showImage()
#         self.dirty = True
#         self.updateStatus("Swapped Red and Blue" \
#                 if on else "Unswapped Red and Blue")
# 
# 
#     def editUnMirror(self, on):
#         if self.image.isNull():
#             return
#         if self.mirroredhorizontally:
#             self.editMirrorHorizontal(False)
#         if self.mirroredvertically:
#             self.editMirrorVertical(False)
# 
# 
#     def editMirrorHorizontal(self, on):
#         if self.image.isNull():
#             return
#         self.image = self.image.mirrored(True, False)
#         self.showImage()
#         self.mirroredhorizontally = not self.mirroredhorizontally
#         self.dirty = True
#         self.updateStatus("Mirrored Horizontally" \
#                 if on else "Unmirrored Horizontally")
# 
# 
#     def editMirrorVertical(self, on):
#         if self.image.isNull():
#             return
#         self.image = self.image.mirrored(False, True)
#         self.showImage()
#         self.mirroredvertically = not self.mirroredvertically
#         self.dirty = True
#         self.updateStatus("Mirrored Vertically" \
#                 if on else "Unmirrored Vertically")
# 
# 
#     def editZoom(self):
#         if self.image.isNull():
#             return
#         percent, ok = QInputDialog.getInteger(self,
#                 "Image Changer - Zoom", "Percent:",
#                 self.zoomSpinBox.value(), 1, 400)
#         if ok:
#             self.zoomSpinBox.setValue(percent)
# 
# 
#     def showImage(self, percent=None):
#         if self.image.isNull():
#             return
#         if percent is None:
#             percent = self.zoomSpinBox.value()
#         factor = percent / 100.0
#         width = self.image.width() * factor
#         height = self.image.height() * factor
#         image = self.image.scaled(width, height, Qt.KeepAspectRatio)
#         self.imageLabel.setPixmap(QPixmap.fromImage(image))
# 
# 
#     def helpAbout(self):
#         QMessageBox.about(self, "About Image Changer",
#                 """<b>Image Changer</b> v %s
#                 <p>Copyright &copy; 2007 Qtrac Ltd. 
#                 All rights reserved.
#                 <p>This application can be used to perform
#                 simple image manipulations.
#                 <p>Python %s - Qt %s - PyQt %s on %s""" % (
#                 __version__, platform.python_version(),
#                 QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))
# 
# 
#     def helpHelp(self):
#         form = helpform.HelpForm("index.html", self)
#         form.show()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("TSC")
    app.setOrganizationDomain("qtrac.eu")
    app.setApplicationName("G-code_sequencer_for_GRBL")
    app.setWindowIcon(QIcon(":/icon.png"))
    form = MainWindow()
    form.show()
    app.exec_()


main()

