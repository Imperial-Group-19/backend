#!/usr/bin/env python3.8
# https://github.com/crossbario/autobahn-python/blob/master/examples/asyncio/websocket/echo/client.py

import asyncio

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

from message_protocol import Subscription, MessageBase, DBType, ErrorMessage, ErrorType, ResponseMessage, ParamsMessage, WSMsgType, Update
from message_conversion import MessageConverter

from db_objects import Product, Store


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
            new_store = Store(
                id="0x02b7433ea4f93554856aa657da1494b2bf645ef0",
                title="Super Algorithms Inc.",
                description="We help you prepare for Tech Interviews.",
                storeOwner="0x599410057bc933fd2f7319a5a835c88a9300bfb0"
            )

            response = Update(id=10, jsonrpc="2.0", method=WSMsgType.updateValue.value,
                              params=[DBType.stores.value, new_store.__dict__])
            bytes_msg = message_converter.serialise_message(response)
            print(bytes_msg)
            self.sendMessage(payload=bytes_msg, isBinary=True)

            new_product = Product(
                productName="C++",
                storeAddress="0x02b7433ea4f93554856aa657da1494b2bf645ef0",
                title="C++ course",
                description="Try out our newest course in C++ and impress your interviewers.",
                price=10000,
                features=[
                    "Full algorithms course in C++"
                ],
                productType=1
            )
            response = Update(id=10, jsonrpc="2.0", method=WSMsgType.updateValue.value,
                              params=[DBType.products.value, new_product.__dict__])
            bytes_msg = message_converter.serialise_message(response)
            print(bytes_msg)
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
