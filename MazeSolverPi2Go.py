# Importing the repositories needed for the robot:
import pi2go
import time

# Importing the repositories needed for the tree:
import sys
import tty
import termios
import time

# Code needed to read keyboard presses.
def readChar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    if ch == '0x03':
        raise KeyboardInterrupt
    return ch

def readkey(getchar_fn=None):
    getchar = getchar_fn or readChar
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return ord(c3) - 65

# Defining the Tree Structure: 
class SearchTree:
    def __init__(self,rootObj):
        self.key = rootObj
        self.turnLeft = None
        self.turnStraight = None
        self.turnRight = None
        self.parent = None
        self.counter = 0
        self.time = time.time()

    # Define code to process a turn, updating the tree as required
    # Parameter turnType indicates type of turn, e.g. straight, left or right
    def insertTurn(self,newNode,turnType):
        self.time = time.time()
        if turnType == 'Straight':
            # Insert dummy dead end for left node if there is no left turn
            if self.turnLeft == None:
                self.turnLeft = SearchTree(newNode)
                self.turnLeft.key = 'Dead End'
            # Insert dummy dead end for straight node if there is no straight turn
            elif self.turnStraight == None:
                self.turnStraight = SearchTree(newNode)
                self.turnStraight.key = 'Dead End'
            # Insert dead end for right node
            # And goto to parent and set parent node to dead end all to indicate that this path has no solution
            elif self.turnRight == None:
                self.turnRight = SearchTree(newNode)
                self.turnRight.key = 'Dead End'
                if self.turnLeft.key == 'Dead End' and self.turnStraight.key == 'Dead End' and self.turnRight.key == 'Dead End':
                    self.parent.key = 'Dead End All'
                return self.parent           
        # Insert turns for left, straight and right
        if self.turnLeft == None:
            self.turnLeft = SearchTree(newNode)
            self.turnLeft.parent = self
            self.counter = self.counter + 1
            return self.turnLeft
        elif self.turnStraight == None:
            self.turnStraight = SearchTree(newNode)
            self.turnStraight.parent = self
            self.counter = self.counter + 1
            return self.turnStraight
        elif self.turnRight == None:
            self.turnRight = SearchTree(newNode)
            self.turnRight.parent = self
            self.counter = self.counter + 1
            return self.turnRight
        else:
            if self.parent == None:
                return self
            else:
                return self.parent
    
    # Defining the code needed to return to the Parent node after a dead end is detected.        
    def gotoParent(self):
        if self.parent == None:
            return self
        else:
            self.parent.key = 'Dead End'
            return self.parent.parent
    
    # Defining the code needed to go to the Child node after making a decision on the second run.         
    def gotoChild(self):
        if self.key == turnLeft:
          return self.turnLeft
        if self.key == turnStraight:
          return self.turnStraight
        if self.key == turnRight:
          return self.turnRight
            
    # define code to goto child nodes of current node
    def getTurnLeft(self):
        return self.turnLeft
    def getTurnStraight(self):
        return self.turnStraight
    def getTurnRight(self):
        return self.turnRight
    def getRootCounter(self):
        return self.counter

    # Define code to create new tree
    def setRootVal(self,obj):
        self.key = obj
    # Define code to return to root node of tree = start of maze
    def getRootVal(self):
        return self.key
		
# Defining the Print function for the tree
def printexp(tree,level,turnx):
  sVal = ""
  if tree:
      sVal = '' + str(tree.time) + ' '
      for x in range(0,level):
        sVal = sVal + ' - '
      level = level + 1
      sVal = sVal + str(tree.key) + ' turn-' + str(turnx) + ' counter-' + str(tree.counter)
      sVal = sVal + '\n'
      if tree.turnLeft != None:
        sVal = sVal + printexp(tree.getTurnLeft(),level,1) 
      if tree.turnStraight != None:
        sVal = sVal + printexp(tree.getTurnStraight(),level,2) 
      if tree.turnRight != None:
        sVal = sVal + printexp(tree.getTurnRight(),level,3) 
      sVal = sVal + '\n'
  return sVal


# Initialising the Search Tree before starting the learning run:
rootNode = SearchTree('Start')
currentNode = rootNode
		
# Initialise the Pi2Go:
pi2go.init()

# Variables needed for movement:
# Forward speed
speed = 25
# Adjustment and turn rotation speed:
turnSpeed = 30
# Rotation speed for junctions
speedForward = 80
speedReverse = -30
# Rotation speed for dead end 180 turn
deadEndSpeedForward = 25
deadEndSpeedReverse = -25

# variables needed to ensure junctions are recognised and processed correctly
ctrSpinLeft = 0
ctrSpinRight = 0
ctrSpinGo = 0
tickCount = 3.5
tickStart = time.time()
turn = '|'

#
#
# Main body of code needed to read a sensor input and react according to the input. 
#

try:
  
  # keyp = l for learn mode
  # keyp = o for optimum mode
  keyp = readkey()
  
  #
  #
  # Process learning maze mode
  while keyp=='l':

    # Defining the sensors on the bottom of the Pi2Go
    left = pi2go.irLeftLine()
    right = pi2go.irRightLine()
    
    # If an dead end is detected, turn around 180 degrees and go back to parent: 
    if pi2go.irCentre():
      currentNode = currentNode.insertTurn('dead end','')    
      currentNode = currentNode.gotoParent()
      tickStart = time.time()
      # Code required to find the line again during a 180 degree turn
      while pi2go.irRightLine() == True:
        pi2go.go(deadEndSpeedForward,deadEndSpeedReverse)

    # If both line sensors do not detect the line, and there are no obstacles, move forward: 
    elif left == True and right == True and not pi2go.irCentre(): 
      pi2go.forward(speed)
      
    # If both sensors (i.e T junction, crossroads or end of maze) detect a line spin left:  
    elif left == False and right == False:
       pi2go.go(speedReverse,speedForward)   
       # Extra test to distinguish between a junction and minor direction corrections
       if time.time() > tickStart + tickCount:
        ctrSpinGo = ctrSpinGo + 1
        if ctrSpinLeft > ctrSpinRight:
          turn = 'Left'
        elif ctrSpinLeft < ctrSpinRight:
          turn = 'Straight'
        else:
          turn = 'Right'
        if time.time()-tickStart>4:
          currentNode = currentNode.insertTurn('Turn ',turn)
        ctrSpinLeft = 0
        ctrSpinRight = 0
        tickStart = time.time()
       # End of maze detected, end learn mode in preparation for optimum run
       elif pi2go.getDistance() <= 9:
        print ('Exit is found! ending programme...')
        keyp = 'o'

    # If the left sensor is on, spin right:    
    elif left == True: 
      pi2go.spinRight(turnSpeed)
      ctrSpinRight = ctrSpinRight + 1
    
    #If the right sensor is on, spin left:
    elif right == True: 
      pi2go.spinLeft(turnSpeed)
      ctrSpinLeft = ctrSpinLeft + 1

  # Process learning maze mode
  if keyp!='l':
   secondrunchoice = raw_input('Would you like to begin the second run using the optimum path (y), or end the program (n)?')
   if secondrunchoice =='y':
     print ('Beginning optimum run!')
     keyp = 'o'
   elif secondrunchoice == 'n':
     print ('Ending Program')
     pi2go.cleanup
     pi2go.stop()     

  #
  #
  # Optimum maze run mode, re-run the maze ignoring any paths that lead to dead ends

  # Position current node to start of tree
  currentNode = rootNode
  
  while keyp == 'o':
  
    # Defining the sensors on the bottom of the Pi2Go
    left = pi2go.irLeftLine()
    right = pi2go.irRightLine()
       
    # If both line sensors do not detect the line, and there are no obstacles, move forward: 
    if left == True and right == True and not pi2go.irCentre(): 
      pi2go.forward(speed)
      
    # If both sensors (i.e T junction, crossroads or end of maze) detect a line determine direction to turn from the tree
    elif left == False and right == False:
       pi2go.go(speedReverse,speedForward)   
       # Extra test to distinguish between a junction and minor direction corrections
       if time.time() > tickStart + tickCount:
        # Process required turn
        if time.time()-tickStart>3:
          if currentNode.key == turnLeft:
            pi2go.go(speedReverse,speedForward)
          elif currentNode.key == turnRight:
            pi2go.go(speedForward,speedReverse)
          elif currentNode.key == turnStraight:
            pi2go.forward(speed)
            time.sleep(sleepTimes[iOpt])
          gotoChild(self)
        tickStart = time.time()
       
       # Exit of maze found
       elif pi2go.getDistance() <= 9:
        print ('Exit is found! ending programme...')

    # If the left sensor is on, spin right:    
    elif left == True: 
      pi2go.spinRight(turnspeed)
      ctrSpinRight = ctrSpinRight + 1
    #If the right sensor is on, spin left:
    elif right == True: 
      pi2go.spinLeft(turnspeed)
      ctrSpinLeft = ctrSpinLeft + 1

    
# Code needed to end the project and stop the robot:
finally: 
  pi2go.cleanup()
  pi2go.stop()
  print(printexp(rootNode,0,0))