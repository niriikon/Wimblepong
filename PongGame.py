class PongGame(object):
    def __init__(self, log, playerName, oppName="opponent"):
        self.playerName = playerName
        self.oppName = oppName
        self.me = PongPlayer(log, playerName)
        self.opponent = PongPlayer(log, oppName)
        self.ball = PongBall(log)
        self.conf = PongConfig(log)

    def update(self, data):
        try:
            _find_side()
            self.me.update(data[self.me.side])
            self.opponent.update(data[self.opponent.update])
            self.ball.update(data['ball'])
            self.conf.update(data['conf'])
        except KeyError:
            self._log.error('Error parsing json')

    def _find_side(self, data):
        if self.me.side == None:
            if data['left']['playerName'] == self.playerName:
                self.me.side = 'left'
                self.opponent.side = 'right'
            else:
                self.me.side = 'right'
                self.opponent.side = 'left'

class PongPlayer(object):
    def __init__(self, log, name):
        self.name = name
        self._log = log
        self.side = None
        self.y = 0

    def update(self, data):
        try:
            self.y = data['y']
            self.name = data['playerName']
        except KeyError:
            self._log.error('Error parsing player data')

class PongBall(object):
    heading = (0, 0)
    DIR_RIGHT = 1
    DIR_STATIONARY = 0
    DIR_LEFT = -1
    def __init__(self, log):
        self._log = log
        self.x = 0
        self.y = 0
        self.heading = (0, 0)

    def update(self, data):
        try:
            newx = data['pos']['x']
            newy = data['pos']['y']
            if self.x != 0 and self.y != 0:
                self.heading = (newx-self.x, newy-self.y)
            self.x = newy
            self.y = newx
        except KeyError:
            self._log.error('Error parsing Ball data')

    def direction(self):
        ''' Returns 1 if ball is heading away from player, -1 if towards and 0 if direction is unknown
        '''
        if self.heading[0] < 0:
            return DIR_LEFT
        elif self.heading[0] == 0:
            return DIR_STATIONARY
        else:
            return DIR_RIGHT

    def projected_y(self, side):
        x1 = self.x
        y1 = self.y
        dx = self.heading[0]
        dy = self.heading[1]
        width = 640
        height = 480
        if dx == 0:
            return 0

        if side == "right":
            if dx > 0:
                x_goal = width
            else:
                x_goal = -width
        else:
            if dx < 0:
                x_goal = 0
            else:
                x_goal = width*2

        k = dy / dx
        y = k * (x_goal - x1) + y1

        if (y // height) % 2 == 0:
            return y - height * (y // height)
        else:
            return height * ((y // height) + 1) - y

class PongConfig(object):
    def __init__(self, log):
        self._log = log
        self.width = 480
        self.height = 640
        self.paddleHeight = 50
        self.paddleWidth = 5
        self.ballRadius = 5
        self.tickInt = 20

    def update(self, data):
        try:
            self.width = data['maxWidth']
            self.height = data['maxHeight']
            self.paddleHeight = data['paddleHeight']
            self.paddleWidth = data['paddleWidth']
            self.ballRadius = data['ballRadius']
            self.tickInt = data['tickInterval']
        except KeyError:
            self._log.error('Error parsing config')