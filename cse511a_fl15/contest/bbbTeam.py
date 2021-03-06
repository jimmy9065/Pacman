__author__ = 'hongjing'
# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util
from game import Directions
import game
from util import nearestPoint
##from inference import InferenceModule
import sys



# inference.py

import util
import random
import game
import sys
import capture

class InferenceModule:
  def __init__(self):
    numParticles=10000
    self.setNumParticles(numParticles)
    self.Captured=False
    self.moveList=[(0,1),(0,-1),(1,0),(-1,0)]
    self.enemies=[]

  def setNumParticles(self, numParticles):
    self.numParticles = numParticles

  def initialize(self, gameState):
    "Initializes beliefs to a uniform distribution over all positions."
    self.legalPositions = [p for p in gameState.getWalls().asList(False) if p[1] > 1]
    self.initializeUniformly(gameState)

  def initializeUniformly(self, gameState):
    "Initializes a list of particles. Use self.numParticles for the number of particles"
    print "initialzed particles"
    self.Particles=[]
    for i in range(self.numParticles):
        pos1=random.choice(self.legalPositions)
        pos2=random.choice(self.legalPositions)
        self.Particles.append((pos1,pos2))

  def observe(self, noisyDistance, gameState,agentID):
    """
    Update beliefs based on the given distance observation.
    What if a ghost was eaten by agent?
    The former assumption will be reinitialized, which is apparently unnecssary.
    We need to find the method which can determine whether a certain agent is eaten, then like "go to jail", we just put them in the inital pos.gameState.getInitialAgentPosition(agentID)
    """
    AgentPosition = gameState.getAgentPosition(agentID)
    weights=[1 for i in range(self.numParticles)]
    for index in range(self.numParticles):
        for i in range(2):
            trueDistance=util.manhattanDistance(self.Particles[index][i],AgentPosition)
            weights[index]*=gameState.getDistanceProb(trueDistance,noisyDistance[self.enemies[i]])

    if sum(weights)==0:
        self.initializeUniformly(gameState)
        return
    else:
        newParticals=util.nSample(weights,self.Particles,self.numParticles)
        self.Particles=newParticals

  def elapseTime(self, gameState,agentID):
    """
    Update beliefs for a time step elapsing.
    """
    enemyID=((agentID+3)%4)/2 #(agentID+4-1)%4/2 calculating which agent just moved
    #print "agentID="+str(agentID)+"enemyID="+str(enemyID)
    newParticles = []
    for oldParticle in self.Particles:
        newParticle = list(oldParticle) # A list of ghost positions
        pos=newParticle[enemyID] # certain enemy's position
        newPosDistribution=util.Counter()
        for move in self.moveList: # get every move
            newPos=(pos[0]+move[0],pos[1]+move[1]) # get the new position
            if newPos in self.legalPositions: # if the posistion is illeagle, ingore it.
                newPosDistribution[newPos]=1
        newPosDistribution.normalize()
        newParticle[enemyID]=(util.sample(newPosDistribution))
        newParticles.append(tuple(newParticle))

    self.particles = newParticles

  def getBeliefDistribution(self):
    """
    Return the agent's current belief state, a distribution over
    ghost locations conditioned on all evidence and time passage.
    belief has two couter, store the enemies' position repectively
    """
    belief=[util.Counter(),util.Counter()]
    for p in self.Particles:
            belief[0][p[0]]+=1
            belief[1][p[1]]+=1

    belief[0].divideAll(self.numParticles*1.0) #this 1.0 may be unnecessarily
    belief[1].divideAll(self.numParticles*1.0)

    return belief




#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'ReflexCaptureAgent', second = 'DefensiveReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(first)(secondIndex)]

##########
# Agents #
##########


class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)
    self.team = {}
    self.target = {}
    A = self.getTeam(gameState)
    self.team[A[0]] = 1
    self.team[A[1]] = 2
    self.target[A[0]] = (-1,-1)
    self.target[A[1]] = (-1,-1)
    self.is_prepared = False
    ## each pacman agent has its own food target during attack, if food collision, they need to
    ##communicate and switch targets
    '''
    Your initialization code goes here, if you need any.
    '''
    #get enimies' number

    ##self.enimies=self.getOpponents(gameState)
    ##self.inference=InferenceModule();
    ##self.inference.initialize(gameState);
    ##self.inference.enemies=self.enimies
    #self.inferenceModules=[inferenceType(a) for a in
    ##One agent goes up and one agent goes down
    pos = []
    x = gameState.getWalls().width / 2
    y = gameState.getWalls().height / 2
    if self.red:
      x = x - 1
    self.start_point = (x, y)
    for i in xrange(y):
      if gameState.hasWall(x, y) == False:
        pos.append((x, y))
      y = y - 1
    myPos = gameState.getAgentState(self.index).getPosition()
    minDist = 999999
    minPos = None
    for location in pos:
      dist = self.getMazeDistance(myPos, location)
      if dist <= minDist:
        minDist = dist
        minPos = location
    self.Bstart_point = minPos
    ##print "self.Bstart_point:",self.Bstart_point

    x,y = self.start_point
    pos = []
    for i in xrange(gameState.getWalls().height-y):
      if gameState.hasWall(x, y) == False:
        pos.append((x, y))
      y = y + 1
    myPos = gameState.getAgentState(self.index).getPosition()
    minDist = 999999
    minPos = None
    for location in pos:
      dist = self.getMazeDistance(myPos, location)
      if dist <= minDist:
        minDist = dist
        minPos = location
    self.Astart_point = minPos
    ##print "self.Astart_point:",self.Astart_point

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    ##start = time.time()
    ##self.inference.elapseTime(gameState,self.index)
    ##self.inference.observe(gameState.getAgentDistances(),gameState,self.index)
    actions = gameState.getLegalActions(self.index)
    ##actions.remove(Directions.STOP)
    # You can profile your evaluation time by uncommenting these lines
    values = [self.evaluate(gameState, a) for a in actions]
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    ##print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
    return random.choice(bestActions)


  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    L = gameState.getAgentState(self.index)
    enemyPos = []
    for enemyI in self.getOpponents(gameState):
      pos = gameState.getAgentPosition(enemyI)
      #Will need inference if None
      if pos != None:
        enemyPos.append((enemyI, pos))

    ##belief=self.inference.getBeliefDistribution()
    ##self.debugClear()
    ##for index in range(2):
    ##    for pos in belief[index]:
     ##       self.debugDraw(pos,[0,belief[index][pos],0])

    if len(enemyPos) > 0:
      for enemyI, pos in enemyPos:
        if self.getMazeDistance(L.getPosition(), pos) <= 8 and L.isPacman==False and gameState.getAgentState(self.index).scaredTimer<=0:
            ##print "In defense!"
            ##print "self.getMazeDistance(L.getPosition(), pos)",self.getMazeDistance(L.getPosition(), pos)
            ##print "self postion:",L.getPosition()
            return self.getDefenseFeatures(gameState,action)
    if self.getMazeDistance(L.getPosition(), gameState.getInitialAgentPosition(self.index)) == 0:
       self.is_prepared = False
    if self.is_prepared == False:
        return self.getStartFeatures(gameState,action)
    else:
        return self.getOffensiveFeatures(gameState,action)

  def getWeights(self, gameState, action):
    L = gameState.getAgentState(self.index)
    enemyPos = []
    for enemyI in self.getOpponents(gameState):
      pos = gameState.getAgentPosition(enemyI)
      #Will need inference if None
      if pos != None:
        enemyPos.append((enemyI, pos))

    if len(enemyPos) > 0:
      for enemyI, pos in enemyPos:
        if self.getMazeDistance(L.getPosition(), pos) <= 8 and L.isPacman==False and gameState.getAgentState(self.index).scaredTimer<=0:
            return self.getDefenseWeights(gameState,action)

    if self.is_prepared == False:
        return self.getStartWeights(gameState,action)
    else:
        return self.getOffensiveWeights(gameState,action)


  def getStartFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    if self.team[self.index] == 1: ##GOES UP
        self.start_point = self.Astart_point
    else:                          ##GOES DOWN
        self.start_point = self.Bstart_point
    dist = self.getMazeDistance(myPos, self.start_point)
    features['Start_dist'] = dist
    if myPos == self.start_point:
      features['atCenter'] = 1
      self.is_prepared = True

    return features

  def getStartWeights(self, gameState, action):
    return {'Start_dist': -1, 'atCenter': 500}

  def getOffensiveFeatures(self,gameState,action):
    features = util.Counter()
    successor = self.getSuccessor(gameState,action)
    features['successorScore'] = self.getScore(successor)
    foodList = self.getFood(successor).asList()
    myPos = successor.getAgentState(self.index).getPosition()
    minDistance = 0
    if len(foodList) > 0:
      dis_dict = {}
      for food in foodList:
          dis_dict[food] = self.getMazeDistance(myPos, food)
      minDistance = min(dis_dict.values())
      for key in dis_dict.keys():
          if dis_dict[key] == minDistance:
              food_pos = key
      peer_target = self.target[(self.index+2)%4]
      self.target[self.index] = food_pos
      if peer_target == (-1,-1):
          peer_dis = 100000
      else:
          peer_dis = self.getMazeDistance(myPos, peer_target)
      features['distanceToFood'] = minDistance
      while peer_dis <= minDistance and self.target[self.index] == self.target[(self.index+2)%4] and \
                      abs(self.target[self.index][0]-self.target[(self.index+2)%4][0])<=2  and abs(self.target[self.index][1]-self.target[(self.index+2)%4][1])<=2:
          ##self re choose
          my_pos = successor.getAgentState(self.index).getPosition()
          pminDistance = 0
          foodList.remove(self.target[self.index])
          if len(foodList) == 0:
              break
          if len(foodList) > 0:
            dis_dict = {}
            for food in foodList:
                dis_dict[food] = self.getMazeDistance(myPos, food)
            minDistance = min(dis_dict.values())
            for key in dis_dict.keys():
                if dis_dict[key] == minDistance:
                    food_pos = key
          features['distanceToFood'] = minDistance
          self.target[self.index] = food_pos

      capList = self.getCapsules(successor)
      features['capsure_num'] = len(capList)
      if len(capList) > 0:
          minDistance = min([self.getMazeDistance(myPos, cap) for cap in capList])
      if minDistance == 0:
          minDistance = 0.1
      features['cap_distance'] = float(1)/float(minDistance)
      agent_dis = gameState.getAgentDistances()
      minD = min(agent_dis[(self.index+1)%4],agent_dis[(self.index+3)%4])
      if minD <= 8:
          features['enemy_dis'] = 1
          if agent_dis[(self.index+1)%4] == minD:
              if gameState.getAgentState((self.index+1)%4).scaredTimer > 0:
                 features['enemy_dis'] = 0
          else:
              if gameState.getAgentState((self.index+3)%4).scaredTimer > 0:
                 features['enemy_dis'] = 0
        ##features['cap_distance'] = features['cap_distance']*10
        ##if in danger do not eat any food!
      else:
        features['enemy_dis'] = 0
      if action == Directions.STOP:
        features['stop'] = 1
      rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
      if action == rev: features['reverse'] = 1
      return features

  def getOffensiveWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1, 'capsure_num': -1000, 'cap_distance': 150, 'enemy_dis': -800,
             'stop': -1000, 'reverse': 0}

  def getDefenseFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
      ##print "Found! ENEMY",features['invaderDistance']

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features


  def getDefenseWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -1, 'reverse': 0}

