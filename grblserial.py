'''
This file implements the serial routines that interface with grbl
running on the arduino. They're written assuming a mac/linux port 
naming scheme, but should be easy enough to change.
'''

import serial
import time
import sys
from PyQt4.QtCore import * #QTimer, QObject


class grblStatusT:
    x = 0.0;
    y = 0.0;
    z = 0.0;
    lineNumber = 0;
    bufferReady = False;
    machineRunning = False;
    autoMode = False;


class grblSerial:
    ''' Class that provides queue acccess to grbl
    
    Is initialized with a default serial port, but
    if that doesn't work out, it can be called with
    openSerial(portname) and a different port name.
    
    Commands are sent to grbl on a timer tick, generated
    by a QTimer, set to a 20ms period by default. Also at
    each timer tick the status is updated.
    
    grblSerial maintains a command fifo queue, limited only
    by available memory. It then attempts on each tick to run
    recent commands out to grbl, if grbl is accepting commands.
    
    Immediate commands are sent outside of the command loop.
    '''
    

    # Unsupported g-codes are simply not sent to grbl.
    unsupported = ['G04', 'G43']  

    def __init__(self):
        '''Initialize grblSerial object with default 
           serial port ID and set up object variables.
        '''
        self.portname = '/dev/tty.usbserial-A700dXL8'
        self.ser = self.openSerial(self.portname)
        self.commandQueue = []
        self.line_number=-1
        self.status = grblStatusT
        self.timerInterval = 20		# milliseconds
        self.timer = QTimer() 
        QObject.connect(self.timer, SIGNAL("timeout()"), self.tick) 
        self.timer.start(self.timerInterval);
        
    def openSerial(self, portname):
        '''Open serial port. This should reset grbl,
        which is checked for. If a grbl isn't found
        (or at least something that comes back with 
        'ok', then raise an exception
        '''
        ser = serial.Serial(portname,115200, timeout=6)
        
        startedOk= False
        for i in range(5):
            line = ser.readline()
            #print str(i)+': '+str(line)
            if 'ok' in line:
                startedOk = True
                break
       
        if not startedOk:
            raise Exception('Unable to connect to grbl')
        
        return ser
    
    def send(self, line):
        '''Sends out the characters in a line with slight 
        delays between them, required by grbl
        '''
    
        for i,c in enumerate(line):
            if not self.ser.write(c):
                raise Exception('Failed to write byte in string: %s' % block)
            time.sleep(0.001)
            
    def updateStatus(self):
        '''Send a status query to grbl and update the
        status variable.
        '''    
        self.send('eq\n')
        line = self.ser.readline()
        if not ('EQ' in line):
            raise Exception("EQ command failed")
        line = self.ser.readline()
        self.status = self.parseStatus(line)

    def parseStatus(self, line):
        '''Takes a line response from grbl to an 'eq' command,
        which is in the form: ORN0X0Y0Z0, and fills a grblStatusT
        class with the contents'''
        self.status.mode = line[0]
        self.status.bufferReady = (line[1]=='R')
        self.status.machineRunning = not (line[0]=='O')
        if self.status.machineRunning:
            self.status.autoMode = (line[0]=='A')
        else:
            self.status.autoMode = False;
        startn = line.find('N')
        startx = line.find('X')
        starty = line.find('Y')
        startz = line.find('Z')
        
        if (startn<0) or (startx<0) or (starty<0) or (startz<0):
            raise Exception('Bad format from eq line')
        self.status.lineNumber = int(line[startn+1:startx])
        self.status.x = float(line[startx+1:starty])
        self.status.y = float(line[starty+1:startz])
        self.status.z = float(line[startz+1:])
        return self.status    
       
       
    def getStatus(self):
        '''Use this call to get the status, because
        it updates the status from grbl before returning.
        '''
        self.updateStatus()
        return self.status
       
    def stripWhitespace(self, str):
        line = str.replace(' ','')
        line = line.replace('\t','')
        line = line.replace('\r','')
        line = line.replace('\n','')
        return line
            
    def sendCommand(self, command):
        command = self.stripWhitespace(command).upper()
        self.send(command+'\n')
           
        line = self.ser.readline()
        line = self.stripWhitespace(line).upper()
           
        if line != command:
            return 0
            raise Exception('Response:_'+line+'_ does not equal command:_'+command+'_')
            
        line = self.ser.readline()
        if not ('ok' in line):
            return 0
            raise Exception('Response to command:_'+command+'_ not okay: '+line)
        return 1
        
        
    def tick(self):
        '''Timer update: checks if anything is in the
        command queue, and adds it to grbl, until
        either the queue is empty or grbl isn't accepting
        any further commands because its buffer is full.
        '''
        self.updateStatus()
        if len(self.commandQueue)>0:
            while self.status.bufferReady:
                command = self.commandQueue.pop(0)
                #print command
                
                runCommand = True
                #print 'Command:',command,'_'
                if len(self.stripWhitespace(command))==0:
                   runCommand = False;
                for text in grblSerial.unsupported:
                    if command.find(text)!=-1:
                       runCommand = False
                       break
                #print runCommand      
                if runCommand:
                    print '\nSending: ',command
                    if  not self.sendCommand(command):
                        self.commandQueue.insert(0, command)
                self.updateStatus()
                        
                        
    def bufferEmpty(self):
        return len(self.commandQueue)==0
        
    def addCommand(self, command):
        self.commandQueue.append(command)

    def close(self):
        self.ser.close()

        
if __name__ == '__main__':

    '''Test program that creates a grblSerial object and
    sends it a number of commands, either a short default
    set or a longer set from a file.
    '''
            
    commands = ['F60N120G1x3y0z0', 
                'F30N130g1x3y3z0',
                'N140x0y3',
                'n150x0y0',
                'n160z1',
                'n170g0x1y1.5',
                'n175g1z0',
                'n180g2x2i.5',
                'n190x1i-0.5',
                'n200g0z1',
                'n210x0y0',
                ]

#     file = open('cncweb.txt')
#     #file = open('geebeepath.txt')
#     commands = file.readlines()
#     file.close()


    grbl = grblSerial()

    for command in commands:
#        print 'adding'
        grbl.addCommand(command)

    while not grbl.bufferEmpty():
        time.sleep(0.1)
        grbl.tick()
        result = grbl.getStatus()
        print result.lineNumber,': ', result.x, result.y, result.z
        sys.stdout.flush()
    
    #Run program for ten more seconds after grbl's buffer goes
    #empty, because when the serial link is closed grbl resets, and
    # its display gets zeroed. This allows me to at least check what
    # it was displaying when the program ended.
    for i in range(100):
        time.sleep(0.1)
        #grbl.tick()
        result = grbl.getStatus()
        print result.lineNumber,': ', result.x, result.y, result.z
        sys.stdout.flush()

    grbl.close()



    