'''
This file implements the serial routines that interface with grbl
running on the arduino. They're written assuming a mac/linux port 
naming scheme, but should be easy enough to change.
'''

import serial
import time
import sys

class grbl_serial():
    def __init__(self):
        self.commandQueue = []
        self.line_number=-1
       
      
    def push(command):
        self.commandQueue.push(command)
        


def send(block):
    for i,c in enumerate(block):
        if not ser.write(c):
            raise Exception('Failed to write byte in string: %s' % block)
        time.sleep(0.001)
    
class grblStatusT():
    x = 0.0;
    y = 0.0;
    z = 0.0;
    lineNumber = 0;
    bufferReady = False;
    machineRunning = False;
    autoMode = False;
    
def parseStatus(line):
    '''Takes a line response from grbl to an 'eq' command,
    which is in the form: ORN0X0Y0Z0, and fills a grblStatusT
    class with the contents'''
    
    result = grblStatusT()
    
    result.mode = line[0]
    result.bufferReady = (line[1]=='R')
    result.machineRunning = not (line[0]=='O')
    if result.machineRunning:
        result.autoMode = (line[0]=='A')
    else:
        result.autoMode = False;
    startn = line.find('N')
    startx = line.find('X')
    starty = line.find('Y')
    startz = line.find('Z')
    
    if (startn<0) or (startx<0) or (starty<0) or (startz<0):
        raise Exception('Bad format from eq line')
    result.lineNumber = int(line[startn+1:startx])
    result.x = float(line[startx+1:starty])
    result.y = float(line[starty+1:startz])
    result.z = float(line[startz+1:])
    
    return result    
   
def stripWhitespace(str):
    line = str.replace(' ','')
    line = line.replace('\t','')
    line = line.replace('\r','')
    line = line.replace('\n','')
    return line
   
def getStatus():    
    send('eq\n')
    line = ser.readline()
    if not ('EQ' in line):
        raise Exception("EQ command failed")
    line = ser.readline()
    return parseStatus(line)
        
def sendCommand(command):
    command = stripWhitespace(command).upper()
    send(command+'\n')
       
    line = ser.readline()
    line = stripWhitespace(line).upper()
       
    if line != command:
        return 0
        raise Exception('Response:_'+line+'_ does not equal command:_'+command+'_')
        
    line = ser.readline()
    if not ('ok' in line):
        return 0
        raise Exception('Response to command:_'+command+'_ not okay: '+line)
    return 1
        
def openSerial(portname):
    ser = serial.Serial(portname,115200, timeout=3)
    
    startedOk= False
    for i in range(5):
        line = ser.readline()
        print str(i)+': '+str(line)
        if 'ok' in line:
            startedOk = True
            break
   
    if not startedOk:
        raise Exception('Unable to connect to grbl')
    
    return ser
        
if __name__ == '__main__':
    ser = openSerial('/dev/tty.usbserial-A700dXL8')
    
        
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
        
        
#    for command in commands:
#        sendCommand(command)

  
    #file = open('cncweb.txt')
    file = open('geebeepath.txt')
    commands = file.readlines()
    file.close()
    #print commands  
      
    unsupported = ['G04', 'G43']  
      
            
    oldLineNumber = 0
    while True:
        time.sleep(0.1)
        result = getStatus()
        if len(commands)>0:
            while result.bufferReady:
                command = commands.pop(0)
                #print command
                
                runCommand = True
                #print 'Command:',command,'_'
                if len(stripWhitespace(command))==0:
                   runCommand = False;
                for text in unsupported:
                    if command.find(text)!=-1:
                       runCommand = False
                       break
                #print runCommand      
                if runCommand:
                    print '\nSending: ',command
                    if  not sendCommand(command):
                        commands.insert(0, command)
                result = getStatus()
                        
        if oldLineNumber != result.lineNumber:
            oldLineNumber = result.lineNumber
            print
        print '\r', result.lineNumber, result.x, result.y, result.z,
        sys.stdout.flush()
        if (not result.machineRunning) and (oldLineNumber!=0):
            break    
    
    
    #time.sleep(10)
    
    ser.close()



    