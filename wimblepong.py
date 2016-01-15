"""Usage: wimblepong.py teamname host port """

import json
import logging
import socket
import sys
import Pong
import math
import random

class JsonOverTcp(object):
    """Send and receive newline delimited JSON messages over TCP."""
    def __init__(self, host, port):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, int(port)))

    def send(self, data):
        self._socket.sendall(json.dumps(data) + '\n')

    def receive(self):
        data = ''
        while '\n' not in data:
            data += self._socket.recv(1)
        return json.loads(data)


class PingPongBot(object):
    counter = 0
    def __init__(self, connection, log):
        self._connection = connection
        self._log = log
        self.time = 0
        self.killshot = False
        self.nextTurn = None

    def run(self, teamname, oppname=None):
        self.name = teamname
        self._log.info("Starting game!")
        self.lastMove = 0
        self.myDirection = 0
        self.lastY = 0
        self.turnCounter = 0
        self.mode = "KILLSHOT"
        self.postChange=False
        if oppname is None:
            self.game = Pong.PongGame(self._log, teamname)
            self.nextTurn = self.game.turn
            self._connection.send({'msgType': 'join', 'data': teamname})
        else:
            self.game = Pong.PongGame(self._log, teamname, oppname)
            self._connection.send({'msgType': 'requestDuel', 'data': [teamname, oppname]})

        self._response_loop()

    def _response_loop(self):
        response_handlers = {
                u'joined': self._game_joined,
                u'gameStarted': self._game_started,
                u'gameIsOn': self._make_move,
                u'gameIsOver': self._game_over
                }
        while True:
            response = self._connection.receive()
            msg_type, data = response['msgType'], response['data']
            try:
                response_handlers[msg_type](data)
            except KeyError:
                self._log.error('Unkown response: %s' % msg_type)

    def _game_joined(self, data):
        self._log.info('Game visualization url: %s' % data)

    def _game_started(self, data):
        self._log.info('Game started: %s vs. %s' % (data[0], data[1]))

    def _make_move(self, data):
        self.update(data)

        if self.game.turn != self.nextTurn:
            self.turn_change()
        if self.postChange:
            self.post_change()
            self.postChange=False

        dir = self.calculate_move()

        if (dir != self.lastMove) or (self.game.me.dir != self.lastMove):
            self._connection.send({'msgType': 'changeDir', 'data': dir})
            self.lastMove = dir
    def turn_change(self):
        self.game.turn = self.nextTurn
        self.turnCounter += 1
        self.mode_change()
        self.postChange = True

    def post_change(self):
        if abs(self.game.ball.k()) < 0.3:
            self.mode == "POWERBALL"
        elif abs(self.game.ball.k()) > 0.7:
            self.mode == "KILLSHOT"


    def mode_change(self, force=False):
        if force or self.turnCounter > 5:
            self.turnCounter = 0
            if self.mode == "POWERBALL":
                self.mode = "KILLSHOT"
            if self.mode == "KILLSHOT":
                self.mode = "RANDOM"
            if self.mode == "RANDOM":
                self.mode = "POWERBALL"

    def _game_over(self, data):
        self._log.info('Game ended. Winner: %s' % data)

    def calculate_move(self):

        expected_y, dy = self.projected_y()

        paddle_top = self.game.me.y
        paddle_height = self.game.conf.paddleHeight
        paddle_mid = paddle_top + paddle_height / 2
        paddle_bottom = paddle_top + paddle_height

        top_region = (paddle_top, paddle_top+5)
        bottom_region = (paddle_bottom-5, paddle_bottom)

        dir = 0

        region = self._select_region(dy, paddle_top, paddle_height)
        return self._in_region(expected_y, region)

        h = self.game.conf.height
        ballD = self.game.conf.ballRadius * 1.8

        if (abs(expected_y - paddle_mid) < (paddle_height / 2)) or \
            (self.lastMove == -1 and paddle_top < ball) or \
            (self.lastMove == 1 and abs(paddle_top+paddle_height-h) < ball):
            return 0
        elif expected_y > (paddle_bottom):
            return 1.0
        elif expected_y < (paddle_top):
            return -1.0

    def _select_region(self, dy, paddle_top, paddle_height):
        top_region = [paddle_top, paddle_top+paddle_height*0.2]
        mid_region = [paddle_top+paddle_height*0.2, paddle_top+paddle_height*0.8]
        bottom_region = [paddle_top+paddle_height*0.8, paddle_top+paddle_height]
        #self._log.info('dy=%f' % dy)


        KILLSHOT = 0.4
        if self.game.ball.velocity > KILLSHOT:
            dy *= -1 # invert direction
        if dy == 0:
            return random.choice([top_region, bottom_region])
        elif dy > 0:
            return top_region
        else:
            return bottom_region

    def _in_region(self, value, region):
        if region[0] <= value <= region[1]:
            return 0
        elif value < region[0]:
            return -1
        else:
            return 1

    def update(self, data):
        self.game.update(data)


    def projected_y(self, side=None):
        if side is None:
            side = self.game.me.side

        ball = self.game.ball
        ballR = self.game.conf.ballRadius
        paddleW = self.game.conf.paddleWidth

        # Conversion to actual playable area
        x1 = ball.x - ballR
        y1 = ball.y - ballR
        dx = ball.heading[0]
        dy = ball.heading[1]
        width = self.game.conf.width - (ballR*2) - (paddleW*2)
        height = self.game.conf.height - (ballR*2)

        new_t = self.game.time
        dt = new_t - self.time
        self.time = new_t

        if dx == 0:
            return y1, 0

        # Convert back to actual y values
        ret = self.project_y(x1, y1, dy, dx, height, width, side, ballR)


        k = dy/dx

        return ret

    def project_y(self, x1, y1, dy=0, dx=0, height=480, width=640, side="left", offset=5):
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
        y2 = k * (x_goal-5 - x1) + y1


        if (y // height) % 2 == 0:
            ret1 = (y - height * (y // height) + offset)
            ret2 = ret1 - (y2 - height * (y2 // height) + offset)
            return (ret1, ret2)
        else:
            ret1 = height * ((y // height) + 1) - y + offset
            ret2 = ret1 - (height * ((y2 // height) + 1) - y2 + offset)
        return  (ret1, ret2)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        level=logging.INFO)
    log = logging.getLogger(__name__)

    if len(sys.argv) == 4:
        try:
            teamname, hostname, port = sys.argv[1:]
            PingPongBot(JsonOverTcp(hostname, port), log).run(teamname)
        except TypeError:
            raise
            sys.exit(__doc__)
    else:
        try:
            teamname, oppname, hostname, port = sys.argv[1:]
            PingPongBot(JsonOverTcp(hostname, port), log).run(teamname, oppname)
        except TypeError:
            raise
            sys.exit(__doc__)
