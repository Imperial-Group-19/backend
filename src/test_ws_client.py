#!/usr/bin/env python3.8
# https://github.com/crossbario/autobahn-python/blob/master/examples/asyncio/websocket/echo/client.py

import asyncio

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory


class MyClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onConnecting(self, transport_details):
        print("Connecting; transport details: {}".format(transport_details))
        return None  # ask for defaults

    def onOpen(self):
        print("WebSocket connection open.")

        def hello():
            self.sendMessage("Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.loop.call_later(1, hello)

        # start sending messages every second ..
        hello()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print(f"Binary message received: {payload}")
        else:
            print(f"Text message received: {payload}")

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='Test websocket client.')
    parser.add_argument("--port", help="port on which ws server should run", type=int, action='store', dest='port', required=True)
    args = parser.parse_args()

    factory = WebSocketClientFactory(f"ws://127.0.0.1:{args.port}")
    factory.protocol = MyClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, '127.0.0.1', args.port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
