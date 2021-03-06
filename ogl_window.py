#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##	 * Redistributions of source code must retain the above copyright
##	   notice, this list of conditions and the following disclaimer.
##	 * Redistributions in binary form must reproduce the above copyright
##	   notice, this list of conditions and the following disclaimer in
##	   the documentation and/or other materials provided with the
##	   distribution.
##	 * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##	   the names of its contributors may be used to endorse or promote
##	   products derived from this software without specific prior written
##	   permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


import sys
import math
import copy

from PyQt4 import QtCore, QtGui, QtOpenGL

from gcparser import gcParser

import logging
logger = logging.getLogger('grblserial')
hdlr = logging.FileHandler('_oglLog.txt')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)


try:
	from OpenGL.GL import *
except ImportError:
	app = QtGui.QApplication(sys.argv)
	QtGui.QMessageBox.critical(None, "OpenGL g-code viewer",
			"PyOpenGL must be installed to run this.")
	sys.exit(1)


class GLWidget(QtOpenGL.QGLWidget):
	xRotationChanged = QtCore.pyqtSignal(int)
	yRotationChanged = QtCore.pyqtSignal(int)
	zRotationChanged = QtCore.pyqtSignal(int)
	xOffsetChanged = QtCore.pyqtSignal(int)
	yOffsetChanged = QtCore.pyqtSignal(int)
	zOffsetChanged = QtCore.pyqtSignal(int)

	def __init__(self, parent=None):
		super(GLWidget, self).__init__(parent)

		self.cursor = 0
		self.drawList = 0
		
		self.xmin = -5
		self.xmax = 5
		self.ymin = -5
		self.ymax = 5
		self.zmin = -5
		self.zmax = 5
		
		self.pos = [0,0,0]
		self.countdown = 0
		self.xRot = 0
		self.yRot = 0
		self.zRot = 0
		self.xOffset = 0.0
		self.yOffset = 0.0
		self.zOffset = 0.0
		self.radius = 0.0
		self.centre = [0.,0.,0.]
		self.translate = -80
		
		self.coordFont = QtGui.QFont()
		self.coordFont.setPointSize(36)
		self.mouseFont = QtGui.QFont()
		self.mouseFont.setPointSize(12)
		self.showMouse = False
		
		self.mousePos = [0., 0.]

		self.aspect_ratio=1
		self.m_d_left_plane = -1.0
		self.m_d_width = 2.0
		self.m_d_bottom_plane = -1.0
		self.m_d_height = 2.0
		self.m_d_near_plane = 5.0
		self.m_d_far_plane = 900.0
		self.usePerspective = False
		
		self.lastPos = 0
		self.setMouseTracking(True)
		

		# timer = QtCore.QTimer(self)
		# timer.timeout.connect(self.advanceGears)
		# #timer.start(20)

	def __del__(self):
		self.makeCurrent()
		if self.cursor:
			glDeleteLists(self.cursor, 1)
		if self.drawList:
			glDeleteLists(self.drawList, 1)

	def setPosition(self, status):
		#print "in setPosition, y=",status.y
		self.pos[0]=status.x
		self.pos[1]=status.y
		self.pos[2]=status.z
		self.countdown = status.countdown
		self.updateGL()


	def setXRotation(self, angle):
		self.normalizeAngle(angle)

		if angle != self.xRot:
			self.xRot = angle
			self.xRotationChanged.emit(angle)
			self.updateGL()

	def setYRotation(self, angle):
		self.normalizeAngle(angle)

		if angle != self.yRot:
			self.yRot = angle
			self.yRotationChanged.emit(angle)
			self.updateGL()

	def setZRotation(self, angle):
		self.normalizeAngle(angle)

		if angle != self.zRot:
			self.zRot = angle
			self.zRotationChanged.emit(angle)
			self.updateGL()
			
	def setXOffset(self, Offset):
		if Offset != self.xOffset:
			# print 'glViewer: x Offset: ', Offset
			self.xOffset = Offset
			self.xOffsetChanged.emit(Offset)
			self.updateGL()

	def setYOffset(self, Offset):
		if Offset != self.yOffset:
			# print 'glViewer: y Offset: ', Offset
			self.yOffset = Offset
			self.yOffsetChanged.emit(Offset)
			self.updateGL()

	def setZOffset(self, Offset):
		if Offset != self.zOffset:
			# print 'glViewer: z Offset: ', Offset
			self.zOffset = Offset
			self.zOffsetChanged.emit(Offset)
			self.updateGL()
			
	def setRadius(self, radius):
		# print 'glWidget: setradius: ', radius
		radius = radius * 1.5
		self.m_d_left_plane = -radius/2.0
		self.m_d_width = radius
		self.m_d_bottom_plane = - radius/2.0
		self.m_d_height = radius
		self.updateGL()
		

	def initializeGL(self):
		lightPos = (5.0, 5.0, 10.0, 1.0)
		reflectance1 = (0.8, 0.1, 0.0, 1.0)
		reflectance2 = (0.0, 0.8, 0.2, 1.0)
		reflectance3 = (0.9, 0.9, 1.0, 0.2)

		glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_DEPTH_TEST)

		self.cursor = self.makePos(reflectance3)
		self.pos = [0,0,0]

		glEnable(GL_NORMALIZE)
		glClearColor(0.7, 0.7, 0.7, 1.0)

	def drawText(self):
		glColor3f(0.2, 0.2, 0.2)
		self.renderText(10, 40,	 'X: %.2f' % self.pos[0], self.coordFont)
		self.renderText(10, 80,	 'Y: %.2f' % self.pos[1], self.coordFont)
		self.renderText(10, 120, 'Z: %.2f' % self.pos[2], self.coordFont)
		
		if self.countdown>0:
			self.renderText(self.width()-200, 40, 'Wait: %.1f' % self.countdown, self.coordFont)

	def drawMouseText(self):
		glColor3f(0.2, 0.2, 0.2)
		xmax = self.width()
		ymax = self.height()
		if self.showMouse:
			self.renderText(xmax - 120, ymax,  'X: %.2f' % self.mousePos[0], self.mouseFont)
			self.renderText(xmax - 60, ymax ,'Y: %.2f' % self.mousePos[1], self.mouseFont)
		else: 
			self.renderText(xmax - 120, ymax,  '		', self.mouseFont)
			self.renderText(xmax - 60, ymax ,'		  ', self.mouseFont)
			
	def setLimits(self, centre, radius):
		self.centre = copy.copy(centre)
		self.radius = radius
		self.setXOffset(-centre[0])
		self.setYOffset(-centre[1])
		self.setZOffset(-centre[2])
		self.setRadius(radius)
		self.resizeGL(self.width(), self.height())
		# print 'In setLimits  *************************'

	def paintGL(self):
		#print 'In paintGL',
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		glPushMatrix()
		glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
		glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
		glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
		
		glTranslated(self.xOffset, self.yOffset, self.zOffset)

		self.drawCursor(self.pos[0], self.pos[1], self.pos[2])

		if self.drawList:
			self.drawDrawList(self.pos[0], self.pos[1], self.pos[2])

		glPopMatrix()
		self.drawText()
		self.drawMouseText()


	def resizeGL(self, width, height):
		side = min(width, height)
		if side <= 0:
			return

		glViewport(0, 0, width, height)
		self.aspect_ratio	=	float(self.width())/self.height();

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity();
		
		
		# print 'Resizing'
		# print 'Aspect ratio is: %.2f' % (self.aspect_ratio)
		# print 'left plane: %.2f, width: %.2f, aspect width: %.2f' % (self.m_d_left_plane, self.m_d_width, self.m_d_width*self.aspect_ratio)
		# print 'bottom plane: %.2f, height: %.2f' % (self.m_d_bottom_plane, self.m_d_height)
		# print 'near plane: %.2f, far plane: %.2f' % (self.m_d_near_plane, self.m_d_far_plane)
		# print 'Midpoints: xOffset: %.2f, yOffset: %.2f' % (-self.xOffset, -self.yOffset)
		# print
		
		if self.usePerspective:
			glFrustum(self.m_d_left_plane*self.aspect_ratio, (self.m_d_left_plane + self.m_d_width)*self.aspect_ratio,
					  self.m_d_bottom_plane, (self.m_d_bottom_plane + self.m_d_height),
					  self.m_d_near_plane, self.m_d_far_plane);
		else:
			glOrtho(self.m_d_left_plane*self.aspect_ratio, (self.m_d_left_plane + self.m_d_width)*self.aspect_ratio,
					self.m_d_bottom_plane, (self.m_d_bottom_plane + self.m_d_height),
					self.m_d_near_plane, self.m_d_far_plane);
		glMatrixMode( GL_MODELVIEW );
		self.updateGL();
		
		glLoadIdentity()
		glTranslated(0.0, 0.0, -80)
		
	def zoomIn(self):
		if max(self.m_d_width, self.m_d_height)<0.1:
			return
		self.m_d_left_plane	  *= 0.75
		self.m_d_width		  *= 0.75
		self.m_d_height		  *= 0.75
		self.m_d_bottom_plane *= 0.75
		self.resizeGL(self.width(), self.height())

	def zoomOut(self):
		if max(self.m_d_width, self.m_d_height)>1000:
			return
		self.m_d_left_plane	  *= 1.3333
		self.m_d_width		  *= 1.3333
		self.m_d_height		  *= 1.3333
		self.m_d_bottom_plane *= 1.3333
		self.resizeGL(self.width(), self.height())

	def wheelEvent(self, event):
		zoom = event.delta()/120	# gives 1 step of zoom
		if zoom>0:
			self.zoomIn()
		else:
			self.zoomOut()

	def mousePressEvent(self, event):
		self.lastPos = event.pos()

	def mouseMoveEvent(self, event):
		if self.lastPos==0:
			dx = event.x()
			dy = event.y()
		else:
			dx = event.x() - self.lastPos.x()
			dy = event.y() - self.lastPos.y()
		
		if not(event.buttons()):
			self.mousePos[0] = float(event.x())/self.width() * self.m_d_width *self.aspect_ratio \
								+ self.m_d_left_plane * self.aspect_ratio - self.xOffset
			self.mousePos[1] = ((self.height() - float(event.y()))/self.height() ) * self.m_d_height + \
								self.m_d_bottom_plane - self.yOffset
			self.showMouse = True
			self.updateGL()
		else:
			self.showMouse = False
			self.updateGL()

		if event.buttons() & QtCore.Qt.LeftButton:
			self.setXRotation(self.xRot + 8 * dy)
			self.setYRotation(self.yRot + 8 * dx)
		elif event.buttons() & QtCore.Qt.RightButton:
			self.m_d_left_plane	  -= float(self.m_d_width)/self.width()*dx
			self.m_d_bottom_plane += float(self.m_d_height)/self.height()*dy
			self.resizeGL(self.width(), self.height())
			
			# self.setXRotation(self.xRot + 8 * dy)
			# self.setZRotation(self.zRot + 8 * dx)

		self.lastPos = event.pos()

	def colorRule(self, gcode):
		if gcode == 1.0:
			glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (1.0, 0., 0., 1.0))
			glColor3f(1., 0., 0.)
		elif gcode == 2.0:
			glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (0.0, 0., 1.0, 1.0))
			glColor3f(0.0, 0.0, 1.0)
		elif gcode == 3.0:
			glColor3f(1.0, 1.0, 1.0)
			glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
		else:
			glColor3f(0., 1., 0.)
			glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (0.0, 1.0, 0.0, 1.0))
		


	def initDrawList(self, gl_list):
		''' This takes a parameter that is a list of shapes to draw.
		Each element of the list consists of a type number, followed
		by a line number it relates to, followed by a list of coordinates 
		for all the line segments to be drawn. The type number corresponds
		to the G code, ie 0, 1, 2 or 3.
		'''

		list = glGenLists(1)
		glNewList(list, GL_COMPILE)
		glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (1.0, 0., 0., 1.0))

		glShadeModel(GL_FLAT)
		glEnable(GL_LINE_SMOOTH)

		for item in gl_list:
			# print item
			
			glBegin(GL_LINES)
			if len(item)==1:
				line=item[0]
				# if pushNames:
				#	glPushMatrix()
				#	glPushName(line[1])
				#	#print line[1]
				#	#assert(False)
				self.colorRule(line[0])
				glVertex3f(line[2], line[3], line[4])
				glVertex3f(line[5], line[6], line[7])
				# if pushNames:
				#	glPopName()
				#	glPopMatrix()	 
			else:
				# if pushNames:
				#	glPushMatrix()
				#	glPushName(item[1])
				self.colorRule(item[0])
				for line in item[2:]:
					glVertex3f(line[0], line[1], line[2])
			glEnd()
				# if pushNames:
				#	glPopName()
				#	glPopMatrix()	 
		glEndList()
		self.drawList = list
		# print 'Drawlist created in initDrawList: ', list

	def xRotation(self):
		return self.xRot

	def yRotation(self):
		return self.yRot

	def zRotation(self):
		return self.zRot
		
	def drawCursor(self, x, y, z):
		glPushMatrix()
		glTranslated(x, y, z)
		glCallList(self.cursor)
		glPopMatrix()

	def drawDrawList(self, dx, dy, dz):
#		glPushMatrix()
#		glTranslated(dx, dy, dz)
		glCallList(self.drawList)
#		glPopMatrix()

	def makePos(self, reflectance):
		NO_SEGS=20
		DIAMETER=4.0
		CONE_HEIGHT=4.0
		CYLINDER_HEIGHT=6.0
	
		list = glGenLists(1)
		glNewList(list, GL_COMPILE)
		glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, reflectance)

		glShadeModel(GL_FLAT)
		glNormal3d(0.0, 0.0, 1)
		
		# Tip position. Always 0,0,0. Actual position
		# is determined by translation when drawing.
		x0 = 0.
		y0 = 0.
		z0 = 0.
		
		# Cone at tip
		glBegin(GL_TRIANGLE_FAN)	 
		glVertex3f(x0, y0, z0)
		z = z0+CONE_HEIGHT
		for i in range(NO_SEGS+1):
			start_angle = float(i)/NO_SEGS*2*math.pi
			x1 = x0+DIAMETER/2*math.cos(start_angle)
			y1 = y0+DIAMETER/2*math.sin(start_angle)
			glVertex3f(x1, y1, z)
		glEnd()

		# Closed end of cylinder:
		glBegin(GL_TRIANGLE_FAN)
		z = z0+CONE_HEIGHT+CYLINDER_HEIGHT	 
		glVertex3f(x0, y0, z)
		for i in range(NO_SEGS+1):
			start_angle = float(i)/NO_SEGS*2*math.pi
			x1 = x0+DIAMETER/2*math.cos(start_angle)
			y1 = y0+DIAMETER/2*math.sin(start_angle)
			glVertex3f(x1, y1, z)
		glEnd()

		# Cylinder:
		glBegin(GL_QUAD_STRIP)	 
		z1 = z0+CONE_HEIGHT
		z2 = z0+CONE_HEIGHT+CYLINDER_HEIGHT
		for i in range(NO_SEGS+1):
			start_angle = float(i)/NO_SEGS*2*math.pi
			x1 = x0+DIAMETER/2*math.cos(start_angle)
			y1 = y0+DIAMETER/2*math.sin(start_angle)
			glVertex3f(x1, y1, z1)
			glVertex3f(x1, y1, z2)
		glEnd()
		glEndList()
		return list	  

	def drawPos(self, dx, dy, dz, angle):
		glPushMatrix()
		glTranslated(dx, dy, dz)
		glRotated(angle, 0.0, 0.0, 1.0)
		glCallList(self.pos)
		glPopMatrix()

	def normalizeAngle(self, angle):
		while (angle < 0):
			angle += 360 * 16

		while (angle > 360 * 16):
			angle -= 360 * 16

	def setTopView(self):	
		self.setXRotation(0.)
		self.setYRotation(0.)
		self.setZRotation(0.)
		
	def setTopRotView(self):
		self.setXRotation(0.)
		self.setYRotation(0.)
		self.setZRotation(90.*16)
	
	def setLeftView(self):	
		self.setXRotation(270.*16)
		self.setYRotation(0.)
		self.setZRotation(90.*16)

	def setFrontView(self): 
		self.setXRotation(270.*16)
		self.setYRotation(0.)
		self.setZRotation(0.)

	def setIsoView(self):	
		self.setXRotation((360.-45)*16)
		self.setYRotation(0.)
		self.setZRotation(45.*16)

	def resetLimits(self):
		# print 'In reset limits'
		# print 'Centre: %.2f, %.2f, %2.f' % (self.centre[0], self.centre[1], self.centre[2])
		# print 'Radius: %.2f' % (self.radius)
		self.setXOffset(-self.centre[0])
		self.setYOffset(-self.centre[1])
		self.setZOffset(-self.centre[2])
		self.setRadius(self.radius)
		self.resizeGL(self.width(), self.height())
		
		


class MainWindow(QtGui.QMainWindow):
	def __init__(self):		   
		super(MainWindow, self).__init__()

		centralWidget = QtGui.QWidget()
        
		self.setCentralWidget(centralWidget)
		self.glWidget = GLWidget()

		self.glWidgetArea = QtGui.QScrollArea()
		self.glWidgetArea.setWidget(self.glWidget)
		self.glWidgetArea.setWidgetResizable(True)
		self.glWidgetArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.glWidgetArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.glWidgetArea.setSizePolicy(QtGui.QSizePolicy.Ignored,
				QtGui.QSizePolicy.Ignored)
		self.glWidgetArea.setMinimumSize(100, 100)

		xSlider = self.createSlider(self.glWidget.xRotationChanged,
				self.glWidget.setXRotation)
		ySlider = self.createSlider(self.glWidget.yRotationChanged,
				self.glWidget.setYRotation)
		zSlider = self.createSlider(self.glWidget.zRotationChanged,
				self.glWidget.setZRotation)

		self.xOffsetSlider = self.createSlider(self.glWidget.xOffsetChanged,
											   self.glWidget.setXOffset)
		self.yOffsetSlider = self.createSlider(self.glWidget.yOffsetChanged,
											   self.glWidget.setYOffset)
		self.zOffsetSlider = self.createSlider(self.glWidget.zOffsetChanged,
											   self.glWidget.setZOffset)
				
		buttonLayout = QtGui.QHBoxLayout()
		topButton = QtGui.QPushButton('Top')
		buttonLayout.addWidget(topButton)
		self.connect(topButton, QtCore.SIGNAL('clicked()'),self.glWidget.setTopView)
		
		topRotButton = QtGui.QPushButton('Top R')
		buttonLayout.addWidget(topRotButton)
		self.connect(topRotButton, QtCore.SIGNAL('clicked()'),self.glWidget.setTopRotView)
		
		leftButton = QtGui.QPushButton('Left')
		buttonLayout.addWidget(leftButton)
		self.connect(leftButton, QtCore.SIGNAL('clicked()'),self.glWidget.setLeftView)
		
		frontButton = QtGui.QPushButton('Front')
		buttonLayout.addWidget(frontButton)
		self.connect(frontButton, QtCore.SIGNAL('clicked()'),self.glWidget.setFrontView)

		isoButton = QtGui.QPushButton('Isometric')
		buttonLayout.addWidget(isoButton)
		self.connect(isoButton, QtCore.SIGNAL('clicked()'),self.glWidget.setIsoView)

		self.perspectiveButton = QtGui.QPushButton('Ortho')
		buttonLayout.addWidget(self.perspectiveButton)
		self.connect(self.perspectiveButton, QtCore.SIGNAL('clicked()'), self.setPerspective)

		self.resetViewButton = QtGui.QPushButton('Reset')
		buttonLayout.addWidget(self.resetViewButton)
		self.connect(self.resetViewButton, QtCore.SIGNAL('clicked()'), self.glWidget.resetLimits)

		self.createActions()
		self.createMenus()

		centralLayout = QtGui.QGridLayout()
		centralLayout.addWidget(self.glWidgetArea, 0, 0)
		centralLayout.addWidget(xSlider, 1, 0)
		centralLayout.addWidget(ySlider, 2, 0)
		centralLayout.addWidget(zSlider, 3, 0)
		centralLayout.addWidget(self.xOffsetSlider, 4, 0)
		centralLayout.addWidget(self.yOffsetSlider, 5, 0)
		centralLayout.addWidget(self.zOffsetSlider, 6, 0)
		centralLayout.addLayout(buttonLayout, 7, 0)
		
		centralWidget.setLayout(centralLayout)

		xSlider.setValue(15 * 16)
		ySlider.setValue(345 * 16)
		zSlider.setValue(0 * 16)

		self.setWindowTitle("Grabber")
		self.resize(400, 500)

	def setPerspective(self):
		if self.perspectiveButton.text()==QtCore.QString('Ortho'):
			self.perspectiveButton.setText('Perspective')
			self.glWidget.usePerspective = True 
		else:	
			self.perspectiveButton.setText('Ortho')
			self.glWidget.usePerspective = False
		self.glWidget.resizeGL(self.width(), self.height())

	def about(self):
		QtGui.QMessageBox.about(self, "About Grabber",
				"The <b>Grabber</b> example demonstrates two approaches for "
				"rendering OpenGL into a Qt pixmap.")

	def createActions(self):
		self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
				triggered=self.close)
	
		self.aboutAct = QtGui.QAction("&About", self, triggered=self.about)
	
		self.aboutQtAct = QtGui.QAction("About &Qt", self,
				triggered=QtGui.qApp.aboutQt)

	def createMenus(self):
		self.fileMenu = self.menuBar().addMenu("&File")
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.exitAct)

		self.helpMenu = self.menuBar().addMenu("&Help")
		self.helpMenu.addAction(self.aboutAct)
		self.helpMenu.addAction(self.aboutQtAct)

	def createSlider(self, changedSignal, setterSlot):
		slider = QtGui.QSlider(QtCore.Qt.Horizontal)
		slider.setRange(0, 360 * 16)
		slider.setSingleStep(16)
		slider.setPageStep(15 * 16)
		slider.setTickInterval(15 * 16)
		slider.setTickPosition(QtGui.QSlider.TicksRight)

		slider.valueChanged.connect(setterSlot)
		changedSignal.connect(slider.setValue)

		slider.setValue(0)
		return slider

	def initDrawList(self, gl_list):
		self.glWidget.initDrawList(gl_list)

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
		self.glWidget.setLimits(centre, radius)

if __name__ == '__main__':

	parser = gcParser()
	parser.load('cncweb.txt')
	center, radius =  parser.getGLLimits(parser.gl_list)

	app = QtGui.QApplication(sys.argv)
	mainWin = MainWindow()
	mainWin.initDrawList(parser.gl_list)
	mainWin.glWidget.setTopView()
	
	mainWin.glWidget.setLimits(center, radius)
	mainWin.show()
	
	sys.exit(app.exec_())	 
