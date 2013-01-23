class Position( object ):
    
    def __init__(self, y, x):
        self.y = y # integer
        self.x = x # integer
    
    def __str__(self):
        return "(%d, %d)" % (self.y, self.x)
    
    def __eq__(self, other):
        return self.y == other.y and self.x == other.x

class Mine( object ):
    
    def __init__(self, position, playerId):
        self.position = position # Position object
        self.playerId = playerId # id of player, who planted that mine

class Countdown( object ):
    
    def __init__(self, number, mapSize, playerId):
        self.number = number # integer
        self.mapSize = mapSize # Position object
        self.playerId = playerId # integer

class Map( object ):
    
    def __init__(self, mines, playersPositions):
        self.mines = mines # list of Mine objects
        self.playersPositions = playersPositions # list of Position objects, in order of players ids

class PlayerAction( object ):
    
    def __init__(self, action):
        self.action = action # 1-char string indicating player's action

class Result( object ):
    
    def __init__(self, winners, scores):
        self.winners = winners # list of ids of players who win the game
        self.scores = scores # list of how many tiles was assigned to each player, in playerId order. Might be empty in case when every player except one was blown up.