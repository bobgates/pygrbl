'''
This file implements the serial routines that interface with grbl
running on the arduino. They're written assuming a mac/linux port 
naming scheme, but should be easy enough to change.
'''

import serial
import time
import sys
from PyQt4.QtCore import * #QTimer, QObject
import copy
import string

import logging
logger = logging.getLogger('grblserial')
hdlr = logging.FileHandler('log_.txt')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)


class grblStatusT(object):
    def __init__(self):
        super(grblStatusT, self).__init__()
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.countdown = 0.0
        self.lineNumber = 0
        self.bufferReady = False
        self.machineRunning = False
        self.autoMode = False
        self.waitMode = False

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False


class grblSerial(QObject):
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
    unsupported = ['G04', 'G43', 'G54']  

    def __init__(self):
        '''Initialize grblSerial object with default 
           serial port ID and set up object variables.
        '''
        super(grblSerial, self).__init__()
        #QObject.__init__(self)
        self.portname = '/dev/tty.usbserial-A700dXL8'
        try:
        	self.ser = self.openSerial(self.portname)
        except:
            self.ser = None
        self.commandQueue = []
        self.line_number = -1
        self.status = grblStatusT()
        self.timerInterval = 200     # milliseconds

#        self.timer = QTimer() 
#        self.connect(self.timer, SIGNAL("timeout()"), self.stick) 
#        self.timer.start(self.timerInterval);
        
      
    def openSerial(self, portname):
        '''Open serial port. This should reset grbl,
        which is checked for. If a grbl isn't found
        (or at least something that comes back with 
        'ok', then raise an exception
        '''
        ser = serial.Serial(portname, 115200, timeout=12)
        
        startedOk = False
        for i in range(5):
            line = ser.readline()
            logger.debug('in openSerial rx: ' + line)
            if 'ok' in line:
                startedOk = True
                break
       
        if not startedOk:
            logger.error('unable to open serial port connection to grbl')
            raise Exception('Unable to connect to grbl')
        
        return ser
    
    def send(self, line):
        '''Sends out the characters in a line with slight 
        delays between them, required by grbl
        '''
        if not self.ser:
            return
        for i, c in enumerate(line):
            if not self.ser.write(c):
                raise Exception('Failed to write byte in string: %s' % block)
            time.sleep(0.001)
            
    def updateStatus(self):
        '''Send a status query to grbl and update the
        status variable.
        
        Emits a signal if the status has changed in any
        way.
        '''   
        
        #status = copy.copy(self.status)
        logger.debug('updateStatus tx1: eq')
        self.send('eq\n')
        line = self.ser.readline()
        logger.debug('updateStatus rx1: ' + line)
        if not ('EQ' in line):
            logger.error('updateStatus : EQ message failed')
            return  # ie quietly ignore that EQ failed
            raise Exception("EQ command failed")
        line = self.ser.readline()
        logger.debug('updateStatus rx2: ' + line)
        self.status = self.parseStatus(line)

#        if status!=self.status:
#            print "Emitting signal"
#            self.emit(SIGNAL("statusChanged"), self.status)
            
            
    def parseStatus(self, line):
        '''Takes a line response from grbl to an 'eq' command,
        which is in the form: ORN0X0Y0Z0, and fills a grblStatusT
        class with the contents'''

#        print 'Status: ', line

        self.status.mode = line[0]
        self.status.bufferReady = (line[1] == 'R')
        self.status.machineRunning = not (line[0] == 'O')
        if self.status.machineRunning:
            self.status.autoMode = ((line[0] == 'A') or (line[0] == 'S'))
        else:
            self.status.autoMode = False;
        startn = line.find('N')
        startx = line.find('X')
        starty = line.find('Y')
        startz = line.find('Z')
        startl = line.find('L')
        
        if (startn < 0) or (startx < 0) or (starty < 0) or (startz < 0):
            raise Exception('Bad format from eq line: ' + line)
        self.status.lineNumber = int(line[startn + 1:startx])
        self.status.x = float(line[startx + 1:starty])
        self.status.y = float(line[starty + 1:startz])
        if startl >= 0:
            self.status.z = float(line[startz + 1:startl])
            self.status.countdown = float(line[startl + 1:]) / 10
            self.status.waitmode = True
        else:
            self.status.z = float(line[startz + 1:])
            self.status.waitmode = False
        return self.status    
       
       
    def getStatus(self):
        '''Use this call to get the status as last reported
        '''
        return self.status
        
    def getFreshStatus(self):
        '''Use this call to get grbl to update its status 
        before returning'''
        self.updateStatus()
        return self.status
    
        
       
    def stripWhitespace(self, str):
        line = str.replace(' ', '')
        line = line.replace('\t', '')
        line = line.replace('\r', '')
        line = line.replace('\n', '')
        return line
            
    def sendCommand(self, command):
		if not self.ser:
			print 'In sendCommand. No serial device connected. Command: ', command
			return
        
		command = self.stripWhitespace(command).upper()

		logger.debug('sendCommand tx: ' + command)

		self.send(command + '\n')

		line = self.ser.readline()
		logger.debug('sendCommand rx1: ' + line)


		line = self.stripWhitespace(line).upper()

		if line != command:
			logger.error('sendCommand: Response:_' + line + '_ does not equal command:_' + command + '_')
			raise Exception('Response:_' + line + '_ does not equal command:_' + command + '_')

		line = self.ser.readline()
		logger.debug('sendCommand rx2: ' + line)
		if not ('ok' in line):
			logger.error('sendCommand: response to command:_' + command + '_ not okay: ' + line)
			raise Exception('Response to command:_' + command + '_ not okay: ' + line)
		return 1
      
    def emergencyStop(self):
        self.sendCommand('ES\n')
        logger.debug('Emergency stop activated')
        while len(self.commandQueue) > 0:
            self.commandQueue.pop()
        logger.debug('Emergency stop routine left happily')
        
#    def stick(self):
#        logger.debug('in stick***********************************')
#        self.tick()
#         if status!=self.status:
#             logger.debug('in stick: emitting status')
#             self.emit(SIGNAL("statusChanged"), self.status)
        
        
    def tick(self):
        '''Timer update: checks if anything is in the
        command queue, and adds it to grbl, until
        either the queue is empty or grbl isn't accepting
        any further commands because its buffer is full.
        '''
        
        if not self.ser:
            return
        status = copy.copy(self.status)
        logger.debug('in tick------------------------------------')
        self.updateStatus()
        logger.debug('tick: after initial update')
        if len(self.commandQueue) > 0:
            while (self.status.bufferReady) and (len(self.commandQueue) > 0):
                command = self.commandQueue.pop(0)
                runCommand = True
                if len(self.stripWhitespace(command)) == 0:
					runCommand = False;
                for text in grblSerial.unsupported:
                    if command.find(text) != -1:
						runCommand = False
						break
                if runCommand:
                    try:
                        self.sendCommand(command)
                    except:
						self.commandQueue = []
						self.commandQueue.append(0, 'M0')
						self.emit(SIGNAL("CommandFailed(PyQt_PyObject)"), command)
                logger.debug('tick: before final updateStatus')
                self.updateStatus()
        if not status == self.status:   #I don't know why, but != doesn't work
            self.emit(SIGNAL("statusChanged"), self.status)
                
                        
    def bufferEmpty(self):
        return len(self.commandQueue) == 0
        
    def queueCommand(self, command, lineNumber=-1):
        '''Adds a g-code command to grbl's queue. If this is called
        without a line number, it processes the line as is. If
        there is a line number, sendCommand takes whatever 
        line number is in the command and replaces it with the
        given line number.
        '''
        if not self.ser:
            print 'In queueCommand, no real serial device. Command: ', command
            return

        if len(command) == 0:
            return
        
        if lineNumber != -1:
            if command[0] == 'N':
				i = 1
				while command[i].isdigit():
					i += 1
				command = 'N' + str(lineNumber) + command[i:]
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

	file = open('cncweb_short.txt')
	#file = open('geebeepath.txt')
	commands = file.readlines()
	file.close()

	grbl = grblSerial()

	for i, command in enumerate(commands):
		#        print 'adding'
		grbl.queueCommand(command, lineNumber=i)

	while not grbl.bufferEmpty():
		time.sleep(2)
		grbl.tick()
		result = grbl.getStatus()
		print result.lineNumber, ': ', result.x, result.y, result.z
		sys.stdout.flush()
    
	#Run program for ten more seconds after grbl's buffer goes
    #empty, because when the serial link is closed grbl resets, and
    # its display gets zeroed. This allows me to at least check what
    # it was displaying when the program ended.
	for i in range(100):
		time.sleep(2)
		#grbl.tick()
		result = grbl.getStatus()
		print result.lineNumber, ': ', result.x, result.y, result.z
		sys.stdout.flush()

	grbl.close()



    