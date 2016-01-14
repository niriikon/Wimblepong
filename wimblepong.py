"""Usage: pongbot.py teamname host port """

import json
import logging
import socket
import sys

X_LEFT = 0
X_RIGHT = 640
Y_MIN = 0
Y_MAX = 320

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
    def __init__(self, connection, log):
        self._connection = connection
        self._log = log

    def run(self, teamname):
        self._connection.send({'msgType': 'join', 'data': teamname})
        self._response_loop()

    def _response_loop(self):
        response_handlers = {
                'joined': self._game_joined,
                'gameStarted': self._game_started,
                'gameIsOn': self._make_move,
                'gameIsOver': self._game_over
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
        self._connection.send({'msgType': 'changeDir', 'data': -1.0})

    def _game_over(self, data):
        self._log.info('Game ended. Winner: %s' % data)

class PongPlayer(object):
    pass

class PongBall(object):
    heading = (0, 0)
    DIR_RIGHT = 1
    DIR_STATIONARY = 0
    DIR_LEFT = -1
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, x, y):
        self.heading = (x-self.x, y-self.y)
        self.x = x
        self.y = y

    def direction(self):
        ''' Returns 1 if ball is heading away from player, -1 if towards and 0 if direction is unknown
        '''
        if self.heading[0] < 0:
            return DIR_LEFT
        elif self.heading[0] == 0:
            return DIR_STATIONARY
        else:
            return DIR_RIGHT

    def projected_y(self):
        p_x = self.x
        p_y = self.y
        p_dirx = self.heading[0]
        p_diry = self.heading[1]
        while p_x < X_RIGHT:
            p_x += p_dirx
            p_y += p_diry

            # Change y direction
            if p_y > Y_MAX or p_y < Y_MIN:
                p_diry *= -1
            if p_x >= X_RIGHT:
                p_dirx == DIR_LEFT

class PongState(object):

    def __init__(self, data):
        pass

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        level=logging.INFO)
    log = logging.getLogger(__name__)
    try:
        teamname, hostname, port = sys.argv[1:]
        PingPongBot(JsonOverTcp(hostname, port), log).run(teamname)
    except TypeError:
        sys.exit(__doc__)
