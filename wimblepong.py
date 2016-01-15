"""Usage: wimblepong.py teamname host port """

import json
import logging
import socket
import sys
import Pong

X_LEFT = 0
X_RIGHT = 640
Y_MIN = 0
Y_MAX = 480

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

    def run(self, teamname, oppname=None):
        self.name = teamname
        self._log.info("Starting game!")
        if oppname is None:
            self.game = Pong.PongGame(self._log, teamname)
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
        ball_y = 0
        plyr_y = 0
        paddle_mid = 25

        try:
            self.game.update(data)
            ball_y = self.game.ball.projected_y(self.game.me.side)
            plyr_y = self.game.me.y
            paddle_mid = self.game.conf.paddleHeight / 2
        except KeyError:
            self._log.error('Object not found in json')

        dir = 0
        if abs(ball_y - plyr_y - paddle_mid) < 1:
            dir = 0
        elif ball_y > (plyr_y + paddle_mid):
            dir = 1.0
        elif ball_y < (plyr_y + paddle_mid):
            dir = -1.0
        self._connection.send({'msgType': 'changeDir', 'data': dir})

    def _game_over(self, data):
        self._log.info('Game ended. Winner: %s' % data)

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
