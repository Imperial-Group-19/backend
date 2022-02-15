#!/usr/bin/env python3.8
# https://github.com/crossbario/autobahn-python/blob/master/examples/asyncio/websocket/echo/client.py

import asyncio

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

from message_protocol import Subscription, MessageBase, DBType, ErrorMessage, ErrorType, ResponseMessage, ParamsMessage, WSMsgType, Insert
from message_conversion import MessageConverter

from db_objects import Product


class MyClientProtocol(WebSocketClientProtocol):
    first_time = True

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onConnecting(self, transport_details):
        print("Connecting; transport details: {}".format(transport_details))
        return None  # ask for defaults

    def onOpen(self):
        print("WebSocket connection open.")
        sub_msg = Subscription(id=0, jsonrpc="2.0", method=Subscription.method, params=[DBType.products.value, DBType.stores.value])
        bytes_msg = MessageConverter.serialise_message(sub_msg)
        self.sendMessage(payload=bytes_msg, isBinary=True)

    def onMessage(self, payload, isBinary):
        if isBinary:
            print(f"Binary message received: {payload}")
        else:
            print(f"Text message received: {payload}")

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        try:
            message_converter = MessageConverter()
            msg_received = message_converter.deserialise_message(payload)
        except Exception as e:
            print(f"Received unsupported message: {payload}: Exception: {e}")
            return

        if isinstance(msg_received, ResponseMessage) and self.first_time:
            self.first_time = False
            new_product = Product(
                product_id="C#",
                store_id="hey",
                title="C# course",
                description="Try out our newest course in C# and impress your interviewers.",
                price=45000,
                features=[
                    "Full algorithms course in C#"
                ]
            )
            response = Insert(id=10, jsonrpc="2.0", method=WSMsgType.insert.value,
                              params=[DBType.products.value, new_product.__dict__])
            bytes_msg = message_converter.serialise_message(response)
            self.sendMessage(payload=bytes_msg, isBinary=True)

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
