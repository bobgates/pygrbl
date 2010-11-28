#!/usr/bin/env python

import copy

from PyQt4.QtGui import *
from PyQGLViewer import *
from qgllogo import *
import OpenGL.GL as ogl
import math


int_words = ['N', 'G', 'M', 'T']
cmd_words = ['G', 'M']
float_words = ['X', 'Y', 'Z', 'U', 'V', 'W', 'A', 'B', 'C', 'D', 'F', 'H', 
                'I', 'J', 'K', 'P', 'Q', 'R', 'S']

coord_words = ['X', 'Y', 'Z', 'U', 'V', 'W', 'A', 'B', 'C', 'F']

nonmodalGroup = ['G4', 'G10', 'G28', 'G30', 'G53', 'G92', 'G92.1', 'G92.2', 'G92.3']   #Non-modal  M100 to M199
modalGroups = [['G0', 'G1', 'G2', 'G3', 'G33', 'G38.x', 'G73', 'G76', 'G80', 'G81',
                  'G82', 'G83', 'G84', 'G85', 'G86', 'G87', 'G88', 'G89'],  #Motion
                ['G17', 'G18', 'G19'],  # Plane selection
                ['G7','G8'], #Diameter/radius for lathes
                ['G90', 'G91'], #Distance mode
                ['G93', 'G94'], #Feed rate mode
                ['G20', 'G21'], # Units
                ['G40', 'G41', 'G42', 'G41.1', 'G42.1'],  #Cutter radius compensation
                ['G43', 'G43.1', 'G49'], #Tool length offset
                ['G98', 'G99'], # Return mode in canned cycles
                ['G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G59.1', 'G59.2', 'G59.3'],
                ['M0', 'M1', 'M2', 'M30', 'M60'], #Stopping
                ['M6', 'T0', 'T1', 'T2', 'T3', 'T4'], # Tool change, can go to Tn
                ['M3', 'M4', 'M5'], # Spindle turning
                ['M7', 'M9'],
                ['M8', 'M9'],   # Coolant. M7 and M8 may both be active at same time
                ['M48', 'M49'],  #Override switches
               ]

CURVE_RESOLUTION = 0.1

#Set the current/startup modal state to the first state in each of the above groups
modalState = []
for line in modalGroups:
    modalState.append(line[0])
    
class groupName:
    MOTION = 0
    PLANE = 1
    DISTANCE = 3
    UNITS = 5
            
class coord:
    x = 0.0;
    y = 0.0;
    z = 0.0;
    i = 0.0;
    j = 0.0;
    k = 0.0;
    f = 0.0;
    r = 0.0;
    def __str__(self):
        return str(self.x) + ','+str(self.y)+','+str(self.z)

class state:
    motion = 'G0'
    plane = 'G17'
    distance = 'G90'
    units = 'G20'
    
    
current_state = state()

#-------------------------------------------------------------------------------------------                

def go(motion, start, finish, lineNum):

    if motion == 'G0':
        type = 'Fast line'
        return [[0.0, lineNum, float(start.x),  float(start.y),  float(start.z), 
                    float(finish.x), float(finish.y), float(finish.z)]]

    elif motion == 'G1':
        type = 'Mill line'
        return [[1.0, lineNum, float(start.x),  float(start.y),  float(start.z), 
                    float(finish.x), float(finish.y), float(finish.z)]]

    elif motion == 'G2' or motion=='G3':
        type = 'CW circular'
        result = 2.0
        if current_state.plane == 'G17':

            i = finish.i
            j = finish.j
            k = finish.k
            r = finish.r            

#            print 'ijkr', i, j, k, r

            if r!=0.0:
                raise Exception('Curves with radius are not supported yet. Change to I, J form')
            else:
                #s for start, f for finish, d for delta
                            
                sx = float(start.x)
                sy = float(start.y)
                sz = float(start.z)

                fx = float(finish.x)
                fy = float(finish.y)
                fz = float(finish.z)

                centrex = sx + i
                centrey = sy + j

                sdx = sx-centrex
                sdy = sy-centrey

                fdx = fx - centrex
                fdy = fy - centrey

                r = math.sqrt(sdx**2 + sdy**2)        
                fr = math.sqrt(fdx**2 + fdy**2)        
                
                #print 'centre', centrex, centrey, 'start', sx, sy, sz, 'finish', fx,fy, fz, 'rs',r,fr
                
                if (fr/r-1.0)>1e-4:         #1e-4 is tolerance. Too small doesn't work
                    raise Exception('Centre given by I, J isn''t at equal radius to start and finish')
                
                sangle = math.atan2(sdy, sdx)
                fangle = math.atan2(fdy, fdx)
                if motion == 'G2':
                    result = 2.0
                    dangle = -2*math.sin(CURVE_RESOLUTION/2/r)
                else:       # ie G3
                    result = 3.0
                    dangle = 2*math.sin(CURVE_RESOLUTION/2/r)
                lines = [result, lineNum]
                
                angle = sangle - fangle
                
                if angle<-math.pi:
                    angle += 2*math.pi
                
                n = abs(angle/dangle)
                dz = (fz-sz)/n      
                n = int(n)
                
                for i in range(n):      # int produces a floor int
                    lines.append([centrex + r*math.cos(sangle + i*dangle),
                                  centrey + r*math.sin(sangle + i*dangle),
                                  sz+i*dz ])
                lines.append([fx, fy, fz])

        else:
            raise Exception('Only G17 curves supported at present')
                
        return lines

    else:
        raise Exception('Undefined type of motion')
        

#-------------------------------------------------------------------------------------------                
def update_position(position, segs):
    for seg in segs:
        if seg[0] == 'X':
            position.x = float(seg[1])
        elif seg[0] == 'Y':
            position.y = float(seg[1])
        elif seg[0] == 'Z':
            position.z = float(seg[1])
        elif seg[0] == 'I':
            position.i = float(seg[1])
        elif seg[0] == 'J':
            position.j = float(seg[1])
        elif seg[0] == 'K':
            position.k = float(seg[1])
        elif seg[0] == 'F':
            position.f = float(seg[1])               
        elif seg[0] == 'R':
            position.r = float(seg[1])               
 
        
        
#-------------------------------------------------------------------------------------------                
def parse_file(file):

    current_position = coord()
    new_position = coord()
    gl_list=[]

    #file = open('cncweb.txt')
    
    for lineNum, qline in enumerate(file):
        line = str(qline)
        line = line.strip('\n\r\t ')
        line = line.replace(' ','')
        line = line.replace('\t','')
        line = line.upper()
        
        # Remove bracket comments. These can legally contain ;
        while '(' in line:
            startpos = line.find('(')
            if ')' in line:
                endpos = line.find(')')+1
            else:
                endpos = len(line)
            line = line[:startpos]+line[endpos:]
            
        # Remove ; comments
        if ';' in line:
            line = line[:line.find(';')]
                
        #print line
    
        if not line:
            continue
    
        first = True
        oldbreak=0
        segs = []

        for idx,c in enumerate(line):
            if c.isalpha():
                if first:
                    first = False
                else:
                    cmd = line[oldbreak:idx]
                    segs.append([cmd[0],cmd[1:]])
                oldbreak=idx
        cmd = line[oldbreak:]
        segs.append([cmd[0],cmd[1:]])
        
        numbers = []
        commands = []
        for i, seg in enumerate(segs):
            numbers.append(seg[1])
            if seg[0] in cmd_words:
                number = seg[1]
                while number[0]=='0' and len(number)>1:
                    number = number[1:]
                commands.append(seg[0]+number)
                segs[i] = seg[0]+number
            else:
                commands.append(seg[0])
                
        # Comes out of here with segs holding a structure with [[cmd, var], cmd, etc
        # where either an entry contains a single command, or a command with its variable
        # There's also a commands array that just contains the commands, because it
        # is useful in the validity checking that follows.

        # Validate: up to four M commands; any number of G commands; 
        # N must be first command, only 1 of any other command
        
        if commands.count('M')>4:
            raise Exception('More than 4 M commands in line')

        for command in commands:
            if commands.count(command)>1 and command !='G' and command!='M':
                raise Exception('More than one command with one letter in line')

        if 'N' in commands and commands[0]!='N':
            raise Exception('Line number must be first command in line')
        
        # check for duplicate modal commands
        for group in modalGroups:
            count = 0
            for command in commands:
                if command in group:
                    count += 1
            if count>1:
                raise Exception('Two commands from one modal group in one line')

        # I'm NOT checking for "It is an error to put a G-code from group 1 and a G-code 
        #                       from group 0 on the same line if both of them use axis words."
        
        for command in commands:
            if command in modalGroups[groupName.MOTION]:
                current_state.motion = command
            elif command in modalGroups[groupName.PLANE]:
                current_state.plane = command
            elif command in modalGroups[groupName.DISTANCE]:
                current_state.distance = command
            elif command in modalGroups[groupName.UNITS]:
                current_state.units = command
                
        go_somewhere = False;
        for command in commands:
            if command in coord_words:
                go_somewhere = True
                break
        
        if go_somewhere:
            new_position = copy.deepcopy(current_position)
            update_position(new_position, segs)
            
            list = go(current_state.motion, current_position, new_position, lineNum)
            
            gl_list.append(list)
            current_position = copy.deepcopy(new_position)
            
    return gl_list          
        
#-------------------------------------------------------------------------------------------                
def draw_gl_list(gl_list, selected=-1, pushNames=False):

    ogl.glClearColor(0.9, 0.9, 0.9, 0.0) 
    ogl.glClear(ogl.GL_COLOR_BUFFER_BIT)
    ogl.glEnable(ogl.GL_LINE_SMOOTH)

    for item in gl_list:
        #print item
        if len(item)==1:
            line=item[0]
            if pushNames:
                ogl.glPushMatrix()
                ogl.glPushName(line[1])
                #print line[1]
                #assert(False)
            ogl.glBegin(ogl.GL_LINES)
            if line[0] == 1.0:
                ogl.glColor3f(1., 0., 0.)
            elif line[0] == 2.0:
                ogl.glColor3f(0.0, 0.0, 1.0)
            elif line[0] == 3.0:
                ogl.glColor3f(1.0, 1.0, 1.0)
            else:
                ogl.glColor3f(0., 1., 0.)
            ogl.glVertex3f(line[2], line[3], line[4])
            ogl.glVertex3f(line[5], line[6], line[7])
            ogl.glEnd()
            if pushNames:
                ogl.glPopName()
                ogl.glPopMatrix()    
        else:
            if pushNames:
                ogl.glPushMatrix()
                ogl.glPushName(item[1])
            ogl.glBegin(ogl.GL_LINE_STRIP)
            if item[0] == 1.0:
                ogl.glColor3f(1., 0., 0.)
            elif item[0] == 2.0:
                ogl.glColor3f(0.0, 0.0, 1.0)
            elif item[0] == 3.0:
                ogl.glColor3f(1.0, 1.0, 1.0)
            else:
                ogl.glColor3f(0., 1., 0.)
            for line in item[2:]:
                ogl.glVertex3f(line[0], line[1], line[2])
            ogl.glEnd()
            if pushNames:
                ogl.glPopName()
                ogl.glPopMatrix()    
                     
#-------------------------------------------------------------------------------------------                
def getGLLimits(gl_list):

    first = gl_list[0]
    if len(first)==1:
        line=first[0]
        xmin=xmax=line[1]
        ymin=ymax=line[2]
        zmin=zmax=line[3]
    else:
        line=first[1]
        xmin=xmax = line[0]
        ymin=ymax = line[1]
        zmin=zmax = line[2]

    for item in gl_list:
        if len(item)==1:
            line=item[0]
            ogl.glBegin(ogl.GL_LINES)
            if line[0] == 1.0:
                ogl.glColor3f(1., 0., 0.)
            elif line[0] == 2.0:
                ogl.glColor3f(0.0, 0.0, 1.0)
            elif line[0] == 3.0:
                ogl.glColor3f(1.0, 1.0, 1.0)
            else:
                ogl.glColor3f(0., 1., 0.)
            ogl.glVertex3f(line[2], line[3], line[4])
            xmin=min(xmin, line[2])
            ymin=min(ymin, line[3])
            zmin=min(zmin, line[4])
            xmax=max(xmax, line[2])
            ymax=max(ymax, line[3])
            zmax=max(zmax, line[4])
            ogl.glVertex3f(line[5], line[6], line[7])
            xmin=min(xmin, line[5])
            ymin=min(ymin, line[6])
            zmin=min(zmin, line[7])
            xmax=max(xmax, line[5])
            ymax=max(ymax, line[6])
            zmax=max(zmax, line[7])
            ogl.glEnd()
        else:
            ogl.glBegin(ogl.GL_LINE_STRIP)
            if item[0] == 1.0:
                ogl.glColor3f(1., 0., 0.)
            elif item[0] == 2.0:
                ogl.glColor3f(0.0, 0.0, 1.0)
            elif item[0] == 3.0:
                ogl.glColor3f(1.0, 1.0, 1.0)
            else:
                ogl.glColor3f(0., 1., 0.)
            for line in item[2:]:
                ogl.glVertex3f(line[0], line[1], line[2])
                xmin=min(xmin, line[0])
                ymin=min(ymin, line[1])
                zmin=min(zmin, line[2])
                xmax=max(xmax, line[0])
                ymax=max(ymax, line[1])
                zmax=max(zmax, line[2])
            ogl.glEnd()
            
    center = Vec((xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2)
    range = Vec(xmax-xmin, ymax-ymin, zmax-zmin)
    radius = max(range)/2.0
            
    return center, radius
#-------------------------------------------------------------------------------------------                
class gcViewer(QGLViewer):

    def __init__(self,parent = None):
        QGLViewer.__init__(self,parent)
                
        #self.setStateFileName('.pygrbl.xml')    
            
        self.drawing = [] 
        self.center = 0.0
        self.radius = 0.0
        self.selected = -1.0
        
        self.orig= Vec()
        self.dir= Vec()
        self.selectedPoint = Vec()

        #self.goIsoView()
        #self.setAxisIsDrawn(True)
        #self.setGridIsDrawn(True)
        
    def setGLList(self, drawing_data):
        self.drawing = drawing_data
        self.center, self.radius = getGLLimits(self.drawing)
        #print 'Center: ', self.center, '  radius: ', self.radius
        #assert(False)
        self.updateGL()
        
    def goTopView(self):
        self.constraint = WorldConstraint()
        self.constraint.setRotationConstraintType(AxisPlaneConstraint.FREE)
        self.camera().frame().setConstraint(self.constraint)

        position = self.center  # Vec(25.0, 12.5, 25)
        
        self.camera().loadModelViewMatrix(True)
        self.camera().loadProjectionMatrix(True)
        self.camera().setPosition(position)
        self.camera().setUpVector(Vec(0.,1.0,0.))
        self.setSceneCenter(self.center) 
        self.setSceneRadius(self.radius)
        
        self.camera().lookAt(self.center) #self.sceneCenter())

        self.camera().setType(Camera.ORTHOGRAPHIC)
        self.camera().showEntireScene()

            # Forbid rotation
        self.constraint.setRotationConstraintType(AxisPlaneConstraint.FORBIDDEN)
        self.camera().frame().setConstraint(self.constraint)
        self.draw()
        
    def goFrontView(self):
        self.constraint = WorldConstraint()
        self.constraint.setRotationConstraintType(AxisPlaneConstraint.FREE)
        self.camera().frame().setConstraint(self.constraint)

        position = self.center
#        position[2]=0.0
        #position = Vec(0.0, 12.5, 0.0)
        self.camera().loadModelViewMatrix(True)
        self.camera().loadProjectionMatrix(True)
        self.camera().setPosition(position)#position[view_type])
        self.camera().setUpVector(Vec(0.,0.,1.))
        self.setSceneCenter(self.center)
        self.setSceneRadius(self.radius)
        
        self.camera().lookAt(self.center) #self.sceneCenter())

        self.camera().setType(Camera.ORTHOGRAPHIC)
        self.camera().showEntireScene()

            # Forbid rotation
        self.constraint.setRotationConstraintType(AxisPlaneConstraint.FORBIDDEN)
        self.camera().frame().setConstraint(self.constraint)
        self.draw()
        
# The values used here come from experiment:
# print self.camera().position()
# Vec(-13.5005,-23.5383,29.3551)
# print self.camera().upVector()
# Vec(0.272689,0.415509,0.867752)
# print self.camera().viewDirection()
# Vec(0.637896,0.597103,-0.48637)
# print self.camera().rightVector()
# Vec(0.720228,-0.686164,0.102228)
# print self.camera().orientation()
# Quaternion(0.452313,-0.228533,-0.296071,0.809646)

    def goIsoView(self):
        self.constraint = WorldConstraint()
        self.constraint.setRotationConstraintType(AxisPlaneConstraint.FREE)
        self.camera().frame().setConstraint(self.constraint)
        
        position = self.center

        self.camera().loadModelViewMatrix(True)
        self.camera().loadProjectionMatrix(True)
        self.camera().setPosition(self.center)  
        self.camera().setUpVector(Vec(0.272689,0.415509,0.867752))
#        v = Vec(0.707,0.707, 0.816)
#        v= Vec(0.281369,0.64599,0.709598)
#        #v = v/(math.sqrt(v[0]**2+v[1]**2+v[2]**2))
#        self.camera().setUpVector(v)
        self.setSceneCenter(self.center) 
        self.setSceneRadius(self.radius)
        
        self.camera().lookAt(self.center) #self.sceneCenter())

        self.camera().setType(Camera.ORTHOGRAPHIC)
        self.camera().showEntireScene()

        self.draw()
       
    def draw(self):
        if self.drawing:
            draw_gl_list(self.drawing, self.selected, False)
        #QMessageBox.information(self, "In draw","In draw routine")
        #print self.camera().upVector()

    def drawWithNames(self):
        if self.drawing:
            draw_gl_list(self.drawing, self.selected, True)
                
        QMessageBox.information(self, "In drawWithNames","In drawWithNames routine")


    def postSelection(self,point):
        # Compute orig and dir, used to draw a representation of the intersecting line
        self.orig, self.dir = self.camera().convertClickToLine(point)

        # Find the selectedPoint coordinates, using camera()->pointUnderPixel().
        self.selectedPoint, found = self.camera().pointUnderPixel(point)
        self.selectedPoint -= 0.01*self.dir # Small offset to make point clearly visible.
        # Note that "found" is different from (selectedObjectId()>=0) because of the size of the select region.

        if self.selectedName() == -1:
            QMessageBox.information(self, "No selection",
                 "No object selected under pixel " + str(point.x()) + "," + str(point.y()))
        else:
            QMessageBox.information(self, "Selection",
                 "Spiral number " + str(self.selectedName()) + " selected under pixel " +
                 str(point.x()) + "," + str(point.y()))

    def init(self):
        pass
        #self.restoreStateFromFile()
        #self.help()
    def helpString(self):
        return '' #helpstr
    def closeEvent(self,event):
        helpwidget = self.helpWidget()
        if not helpwidget is None and helpwidget.isVisible() :
            helpwidget.hide()
        QGLViewer.closeEvent(self,event)

def main():
    qapp = QApplication([])
    viewer = gcViewer()
    
    file = open('cncweb.txt')
    a=file.readlines()
    file.close()

    
    viewer.setGLList(parse_file(a))
    viewer.goIsoView()
    viewer.setWindowTitle("qglViewer")
    viewer.show()
    qapp.exec_()


if __name__ == '__main__':
    main()
#   read_test()        

#   list = read_test()
