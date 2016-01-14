# Pingpong Python Client

This project contains a client for the Hackapong events

NOTICE: The test server enforces a threshold of 20 messages per client in a second. At the moment the bot answers each message from the server with up direction message. This exceeds the threshold defined by the server and kicks the bot out of the game.

## Usage

to build:
`./build.sh`

This sets up a virtualenv, and runs `pip install -r requirements.txt` in the virtualenv
to install dependencies.

to run:
`./start.sh <bot-name> <host> <port>`

to stop
`./stop.sh`

## License

Copyright (C) 2016 Janne Härkönen

Distributed under the Apache-2.0 license http://www.apache.org/licenses/LICENSE-2.0.html
