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
import sys

class FoodPlan:
  def __init__(self):
    self.AgentFoodList=[util.Counter(),util.Counter()]
    self.FoodList=[]
    self.flag=True

  def generateFoodList(self, gameState, agentID):
    bias=0
    if gameState.isOnRedTeam(agentID):
      bias=1
      Foodmap=gameState.getRedFood();
    else:
      Foodmap=gameState.getBlueFood();

    height=Foodmap.height
    width=Foodmap.width

    for y in range(height):
      for x in range(width):
        if Foodmap[x][y]:
          self.FoodList.append((x+width*bias,y))

foodPlan=FoodPlan()

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'ReflexCaptureAgent', second = 'DefensiveReflexAgent'):
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
    A = self.getTeam(gameState)
    self.team[A[0]] = 1
    self.team[A[1]] = 2
    self.target = {}
    print "initialize"
    self.target[self.index] = (-1,-1)
    self.is_prepared = False
    ## each pacman agent has its own food target during attack, if food collision, they need to
    ##communicate and switch targets
    '''
    Your initialization code goes here, if you need any.
    '''
    global foodPlan

    self.foodplan=foodPlan
    self.foodplan.generateFoodList(gameState,self.index)

    self.enemies=self.getOpponents(gameState)

    #One agent goes up and one agent goes down
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

    if self.foodplan.flag:
      self.foodplan.flag=False
      self.debugDraw(self.foodplan.FoodList,[0.7,0.8,0])

    if len(enemyPos) > 0:
      for enemyI, pos in enemyPos:
        if self.getMazeDistance(L.getPosition(), pos) <= 5 and L.isPacman==False and gameState.getAgentState(self.index).scaredTimer<=0:
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
        if self.getMazeDistance(L.getPosition(), pos) <= 5 and L.isPacman==False and gameState.getAgentState(self.index).scaredTimer<=0:
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

    ##
    ##add code to filter the dead end, spawn points and choke points
    ##
    myPos = successor.getAgentState(self.index).getPosition()
    peerPos = successor.getAgentState((self.index+2)%4).getPosition()
    minDistance = 0
    """
    if len(foodList) > 0:
      dis_dict = {}
      for food in foodList:
          dis_dict[food] = self.getMazeDistance(myPos, food)
      minDistance = min(dis_dict.values())
      for key in dis_dict.keys():
          if dis_dict[key] == minDistance:
              food_pos = key

      if self.team[self.index] == 1: ##GOES UP
          features['distanceToFood'] = minDistance
      else:
          partner_pos = successor.getAgentState((self.index+2)%4).getPosition()
          pminDistance = 0
          if len(foodList) > 0:
            dis_dict = {}
            for food in foodList:
              dis_dict[food] = self.getMazeDistance(partner_pos, food)
              pminDistance = min(dis_dict.values())
              for key in dis_dict.keys():
                if dis_dict[key] == pminDistance:
                    pfood_pos = key
          features['distanceToFood'] = minDistance
          if successor.getAgentState((self.index+2)%4).isPacman == True:
              stop = 0
              while  stop == 0 and pfood_pos == food_pos or (abs(pfood_pos[0] - food_pos[0])==1 and abs(pfood_pos[0] - food_pos[0])==0) or (abs(pfood_pos[0] - food_pos[0])==0 and abs(pfood_pos[0] - food_pos[0])
              ==1) or (abs(pfood_pos[0] - food_pos[0])==1 and abs(pfood_pos[0] - food_pos[0])==1):
                  ##print "SAME TARGET! WARNNING!"
                  ##if same target or target is adjacant, repeatedly swtich!
                  myPos = successor.getAgentState(self.index).getPosition()
                  minDistance = 0
                  if len(foodList) > 0:
                    dis_dict = {}
                    foodList.remove(food_pos)
                    for food in foodList:
                        dis_dict[food] = self.getMazeDistance(myPos, food)
                    if len(dis_dict.values()) == 0:
                        features['distanceToFood'] = minDistance
                        stop = 1
                        break
                    minDistance = min(dis_dict.values())
                    for key in dis_dict.keys():
                        if dis_dict[key] == minDistance:
                            food_pos = key

          features['distanceToFood'] = minDistance
    """
    if len(foodList) > 0:

      A = self.getTeam(gameState)
      dis_dict = {}
      peer_dis = {}
      for food in foodList:
          dis_dict[food] = self.getMazeDistance(myPos, food)
          peer_dis[food] = self.getMazeDistance(peerPos,food)
      minDistance = min(dis_dict.values())
      PminDistance = min(peer_dis.values())
      for key in dis_dict.keys():
          if dis_dict[key] == minDistance:
              food_pos = key
      for key in peer_dis.keys():
          if peer_dis[key] == PminDistance:
              pfood_pos = key
      peer_target = pfood_pos
      self.target = food_pos
      if peer_target == (-1,-1) or successor.getAgentState((self.index+2)%4).isPacman == 0:
          peer_dis = 100000
      else:
          peer_dis = self.getMazeDistance(peerPos, peer_target)
      features['distanceToFood'] = minDistance
      temp = self.target
      while peer_dis <= minDistance and self.target == peer_target:
          ##self re choose
          ##print "same target!!!!!!!:",self.target,"peer:",peer_target
          my_pos = successor.getAgentState(self.index).getPosition()
          pminDistance = 0
          foodList.remove(self.target)
          ##remove all the adjacent point of this target

          for i in range(1,4):
            if (temp[0],temp[1]+i) in foodList:
              foodList.remove((temp[0],temp[1]+i))
            if (temp[0],temp[1]-i) in foodList:
              foodList.remove((temp[0],temp[1]-i))
            if (temp[0]+i,temp[1]) in foodList:
              foodList.remove((temp[0]+i,temp[1]))
            if (temp[0]-i,temp[1]) in foodList:
              foodList.remove((temp[0]-i,temp[1]))
            if (temp[0]+i,temp[1]+i) in foodList:
              foodList.remove((temp[0]+i,temp[1]+i))
            if (temp[0]+i,temp[1]-i) in foodList:
              foodList.remove((temp[0]+i,temp[1]-i))
            if (temp[0]-i,temp[1]-i) in foodList:
              foodList.remove((temp[0]-i,temp[1]-i))
            if (temp[0]-i,temp[1]+i) in foodList:
              foodList.remove((temp[0]-i,temp[1]+i))
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
          self.target = food_pos


    capList = self.getCapsules(successor)
    features['capsure_num'] = len(capList)
    if len(capList) > 0:
      minDistance = min([self.getMazeDistance(myPos, cap) for cap in capList])
      if minDistance == 0:
        minDistance = 0.1
      features['cap_distance'] = float(1)/float(minDistance)

    ## keep distance to ghost!

    agent_dis = gameState.getAgentDistances()
    minD = min(agent_dis[(self.index+1)%4],agent_dis[(self.index+3)%4])
    if minD <= 6:
        features['enemy_dis'] = 1
        if agent_dis[(self.index+1)%4] == minD:
            if gameState.getAgentState((self.index+1)%4).scaredTimer > 0 or gameState.getAgentState((self.index+1)%4).isPacman == 1:
                features['enemy_dis'] = 0
                ##print "no worry"
        else:
            if gameState.getAgentState((self.index+3)%4).scaredTimer > 0 or gameState.getAgentState((self.index+3)%4).isPacman == 1:
                features['enemy_dis'] = 0
                ##print "no worry"
        ##features['cap_distance'] = features['cap_distance']*10
        ##if in danger do not eat any food!
    else:
        features['enemy_dis'] = 0

    Wall = gameState.getWalls().asList()
    myPos = successor.getAgentState(self.index).getPosition()
    count = 0
    if (myPos[0]+1,myPos[1]) in Wall:
      count += 1
    if (myPos[0]-1,myPos[1]) in Wall:
      count += 1
    if (myPos[0],myPos[1]+1) in Wall:
      count += 1
    if (myPos[0],myPos[1]-1) in Wall:
      count += 1
    features['place_score'] = 4-count
    if features['enemy_dis'] == 1:
      if features['place_score'] <= 1 and myPos in foodList:
        features['successorScore'] = features['successorScore']-1
        print "nonono"
    ##if features['enemy_dis'] == 1:
      ##print "indanger!!!!!","agentID",self.index,"place_score",features['place_score']
      ##features['place_score'] = features['place_score']*2
      ##features['successor'] = float(features['successor']/2)
    ## Do not stop and hesitate!
    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    ##run in right way:
    if features['enemy_dis'] == 1:
      Ip = gameState.getInitialAgentPosition(self.index)
      features
      x = gameState.getWalls().width / 2
      if self.red:
        x = x - 1
      if x > Ip[0]:
        features['run_in_right_way'] = myPos[0]-x
      else:
        features['run_in_right_way'] = x-myPos[0]
    return features

  def getOffensiveWeights(self, gameState, action):
    weights = {}
    successor = self.getSuccessor(gameState,action)
    foodList = self.getFood(successor).asList()
    df = -1
    if foodList >= 20:
      df = -2
    if foodList <20 and foodList >=10:
      df = -3
    if foodList < 10:
      df = -4
    weights['distanceToFood'] = df
    weights['successorScore'] = 150
    weights['capsure_num'] = -200
    weights['cap_distance'] = 10
    weights['enemy_dis'] = -1000
    weights['place_score'] = 1
    weights['stop'] = -1000
    weights['reverse'] = -1
    weights['run_in_right_way'] = 1
    return weights

  def getDefenseFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0
    ## if two ghosts chase one target. TALK and Change target
    ## Need code
    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    features['bonus'] = 0
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
      if dists == 0:
        features['bonus'] = 1
      ##print "Found! ENEMY",features['invaderDistance']

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    ##defense success go straight to eat, no need to follow the start position.
    return features


  def getDefenseWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10,'bonus':100, 'stop': -10, 'reverse': 0}

