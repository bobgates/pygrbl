#!/usr/bin/env python

# Filename: gcparser
#
# Based on gc_parser, but just the parsing is done here, not the display

import copy

from PyQt4.QtGui import *
from PyQGLViewer import *
#from qgllogo import *
import OpenGL.GL as ogl
import math
#import grblserial
import logging
logger = logging.getLogger('grblserial')
# hdlr = logging.FileHandler('log_.txt')
# formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# hdlr.setFormatter(formatter)
# logger.addHandler(hdlr) 
# logger.setLevel(logging.ERROR)


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


class gcParser():
	

	int_words = ['N', 'G', 'M', 'T']
	cmd_words = ['G', 'M']
	float_words = ['X', 'Y', 'Z', 'U', 'V', 'W', 'A', 'B', 'C', 'D', 'F', 'H', 
					'I', 'J', 'K', 'P', 'Q', 'R', 'S']

	coord_words = ['X', 'Y', 'Z', 'U', 'V', 'W', 'A', 'B', 'C', 'F']

	nonmodalGroup = ['G4', 'G10', 'G28', 'G30', 'G53', 'G92', 'G92.1', 'G92.2', 'G92.3']   #Non-modal  M100 to M199
	modalGroups = [['G0', 'G1', 'G2', 'G3', 'G33', 'G38.x', 'G73', 'G76', 'G80', 'G81',
					  'G82', 'G83', 'G84', 'G85', 'G86', 'G87', 'G88', 'G89'],	#Motion
					['G17', 'G18', 'G19'],	# Plane selection
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
					['M8', 'M9'],	# Coolant. M7 and M8 may both be active at same time
					['M48', 'M49'],	 #Override switches
				   ]

	CURVE_RESOLUTION = 0.1

	#Set the current/startup modal state to the first state in each of the above groups
	
	
	def __init__(self):
		self.current_state = state()
		
		self.modalState = []
		for line in gcParser.modalGroups:
			self.modalState.append(line[0])
		
		self.gl_list=[]
		
		
	def load(self, filename):
		file = open(filename)
		a=file.readlines()
		file.close()
		self.gl_list = self.parse_file(a)
		
#-------------------------------------------------------------------------------------------				

	def addCommand(self, motion, start, finish, lineNum):
		''' Takes a type of motion, with start and finish
		and creates a structure with drawing commands in it.
		'''

		if motion == 'G0':
			type = 'Fast line'
			return [[0.0, lineNum, float(start.x),	float(start.y),	 float(start.z), 
						float(finish.x), float(finish.y), float(finish.z)]]

		elif motion == 'G1':
			type = 'Mill line'
			return [[1.0, lineNum, float(start.x),	float(start.y),	 float(start.z), 
						float(finish.x), float(finish.y), float(finish.z)]]

		elif motion == 'G2' or motion=='G3':
			type = 'CW circular'
			result = 2.0
			if self.current_state.plane == 'G17':

				i = finish.i
				j = finish.j
				k = finish.k
				r = finish.r			

	#			 print 'ijkr', i, j, k, r

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

					arc_length = math.sqrt((sx-fx)**2 + (sy-fy)**2 + (sz-fz)**2)
					if arc_length < 0.0001:
						return []

					centrex = sx + i
					centrey = sy + j

					sdx = sx-centrex
					sdy = sy-centrey

					fdx = fx - centrex
					fdy = fy - centrey

					r = math.sqrt(sdx**2 + sdy**2)		  
					fr = math.sqrt(fdx**2 + fdy**2)		   
				
					logger.debug('Line number is ' + str(lineNum))
					logger.debug('centre: %f, %f, start: %f,%f,%f,	finish: %f, %f, %f,	 rs: %f, %f' % (centrex, centrey, sx, sy, sz, fx,fy, fz, r,fr))
				
					if (fr/r-1.0)>1e-4:			#1e-4 is tolerance. Too small doesn't work
						raise Exception('Centre given by I, J isn''t at equal radius to start and finish')
				
					sangle = math.atan2(sdy, sdx)
					fangle = math.atan2(fdy, fdx)
				
					logger.debug('start angle: '+str(sangle)+' finish angle: '+str(fangle))
				
					if motion == 'G2':
						result = 2.0
						dangle = -2*math.sin(gcParser.CURVE_RESOLUTION/2/r)
					else:		# ie G3
						result = 3.0
						dangle = 2*math.sin(gcParser.CURVE_RESOLUTION/2/r)
					lines = [result, lineNum]
				
					angle = sangle - fangle
				
					if angle<-math.pi:
						angle += math.pi
					
					if angle>math.pi:
						angle -= math.pi
				
				
					logger.debug('In go(motion), r is %f, angle is %f and dangle is %f' % (r, angle, dangle))
								
					n = abs(angle/dangle)
					dz = (fz-sz)/n		
					n = int(n)
				
					for i in range(n):		# int produces a floor int
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
	def update_position(self, position, segs):
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
	def parse_file(self, file):
		'''Takes a g-code file and compiles
		it into a draw list
		''' 

		current_position = coord()
		new_position = coord()
		gl_list=[]

		#file = open('cncweb.txt')
	
		#print len(file)
	
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
				if seg[0] in gcParser.cmd_words:
					number = seg[1]
					while number[0]=='0' and len(number)>1:
						number = number[1:]
					commands.append(seg[0]+number)
					segs[i] = seg[0]+number
				else:
					commands.append(seg[0])
				
			# Gets here with segs holding a structure with [[cmd, var], cmd, etc
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
			for group in gcParser.modalGroups:
				count = 0
				for command in commands:
					if command in group:
						count += 1
				if count>1:
					raise Exception('Two commands from one modal group in one line')

			# I'm NOT checking for "It is an error to put a G-code from group 1 and a G-code 
			#						from group 0 on the same line if both of them use axis words."
		
			for command in commands:
				if command in gcParser.modalGroups[groupName.MOTION]:
					self.current_state.motion = command
				elif command in gcParser.modalGroups[groupName.PLANE]:
					self.current_state.plane = command
				elif command in gcParser.modalGroups[groupName.DISTANCE]:
					self.current_state.distance = command
				elif command in gcParser.modalGroups[groupName.UNITS]:
					self.current_state.units = command
				
			go_somewhere = False;
			for command in commands:
				if command in gcParser.coord_words:
					go_somewhere = True
					break
		
			if go_somewhere:
				new_position = copy.deepcopy(current_position)
				self.update_position(new_position, segs)
			
				list = self.addCommand(self.current_state.motion, 
				               			current_position, 
				               			new_position, 
				               			lineNum)
			
				if list:
					gl_list.append(list)
				current_position = copy.deepcopy(new_position)
			
		return gl_list			
					 
	#-------------------------------------------------------------------------------------------				
	def getGLLimits(self, gl_list):

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
				xmin=min(xmin, line[2])
				ymin=min(ymin, line[3])
				zmin=min(zmin, line[4])
				xmax=max(xmax, line[2])
				ymax=max(ymax, line[3])
				zmax=max(zmax, line[4])
				xmin=min(xmin, line[5])
				ymin=min(ymin, line[6])
				zmin=min(zmin, line[7])
				xmax=max(xmax, line[5])
				ymax=max(ymax, line[6])
				zmax=max(zmax, line[7])
			else:
				for line in item[2:]:
					xmin=min(xmin, line[0])
					ymin=min(ymin, line[1])
					zmin=min(zmin, line[2])
					xmax=max(xmax, line[0])
					ymax=max(ymax, line[1])
					zmax=max(zmax, line[2])
			
		center = [(xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2]
		range = [xmax-xmin, ymax-ymin, zmax-zmin]
		radius = max(range)/2.0
			
		return center, radius

#-------------------------------------------------------------------------------------------				

if __name__ == '__main__':

	parser = gcParser()
	parser.load('cncweb.txt')
	print 'Processed %d g-code lines' % (len(parser.gl_list),)


