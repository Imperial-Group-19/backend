#!/usr/bin/env python3

# server
# https://github.com/crossbario/autobahn-python/blob/master/examples/asyncio/websocket/echo/server.py
import argparse
import asyncio
import dataclasses
from logging import Logger
from typing import Union, Dict

import ujson
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.websocket.protocol import ConnectionRequest, WebSocketProtocol

from message_protocol import Subscription, MessageBase, SubscriptionType, ErrorMessage, ErrorType, ResponseMessage
from message_conversion import MessageConverter


class WebSocketServer(WebSocketServerFactory):

    class ServerProtocol(WebSocketServerProtocol):
        def onConnect(self, request: ConnectionRequest):
            self.__request = request
            self.factory.logging.warning(f"Client connecting: {self.__request.peer}")
            self.factory.add_remote_client(self)

        def onOpen(self):
            self.factory.logging.warning(f"WebsocketConnection open for: {self.__request.peer}")

        def onMessage(self, payload: Union[bytes, str], is_binary: bool):
            if is_binary:
                self.factory.logging.warning(f"Binary message received from: {self.__request.peer}: msg: {payload}")
            else:
                self.factory.logging.warning(f"Binary message received from: {self.__request.peer}: msg: {payload.decode('utf8')}")

            # handle msgs here - read json/binaries + give callbacks

        def onClose(self, was_clean: bool, code: int, reason: str):
            self.factory.logging.warning(f"Client disconnecting: {self.__request.peer}: {was_clean=}, {code=}, {reason=}")
            self.factory.remove_remote_client(self.remote_address)

        def send_msg(self, data: bytes):
            self.factory.logging.warning(f"Sending bytes: {data}")
            self.sendMessage(data, True)

        def close_connection(self, code: WebSocketProtocol.CLOSE_STATUS_CODES_ALLOWED, reason: str):
            self._fail_connection(code=code, reason=reason)

        def get_peer_name(self) -> str:
            if self.__request:
                return f"{self.__request.peer}"
            return ""

    def __init__(self, port: int, logging: Logger):
        self.port = port
        self.logging = logging
        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        ws_address = f"ws://127.0.0.1:{self.port}"
        super(WebSocketServer, self).__init__(ws_address)
        # this is dodgy - but works :eyes: python....
        self.ServerProtocol.factory = self
        self.protocol = self.ServerProtocol

        self.__message_converter = MessageConverter()
        self.__allowed_subscriptions = [enum_pos.value for enum_pos in list(SubscriptionType)]

        # sets of clients and subscribers here
        self.__connected_clients = set()
        self.__subscribed_clients: Dict[SubscriptionType, set] = {}
        for enum_pos in list(SubscriptionType):
            self.__subscribed_clients[enum_pos] = set()

        # add server to asyncio + run until complete
        self.server = self.event_loop.create_server(protocol_factory=self,
                                                    host="", port=self.port)
        self.__async_server_future = self.event_loop.run_until_complete(self.server)

    def add_remote_client(self, server_protocol):
        peer_name = server_protocol.get_peer_name()
        self.logging.debug(f"Added remote client: {peer_name}")
        self.__connected_clients.add(server_protocol)

    def remove_remote_client(self, server_protocol):
        peer_name = server_protocol.get_peer_name()
        self.logging.debug(f"Removing remote client: {peer_name}")
        if server_protocol in self.__connected_clients:
            self.__connected_clients.remove(server_protocol)

        self.__remove_subscriber(server_protocol)

    def process_msg(self, payload: Union[str, bytes], subscriber):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        msg_received = self.__message_converter.deserialise_message(payload)

        if isinstance(msg_received, Subscription):
            for subscription in msg_received.params:
                if subscription not in self.__allowed_subscriptions:
                    # send error message + disconnect client
                    error_msg = f"Following subscription param not supported: {subscription}"
                    response = ErrorMessage(id=msg_received.id, jsonrpc=msg_received.jsonrpc, error=ErrorType(code=1, message=error_msg))
                    bytes_msg = self.__message_converter.serialise_message(response)
                    subscriber.send_msg(bytes_msg)

                    subscriber.close_connection(
                        WebSocketServerProtocol.CLOSE_STATUS_CODE_INVALID_PAYLOAD,
                        error_msg
                    )
                    return

            for subscription in msg_received.params:
                enum_sub = SubscriptionType[subscription]
                self.__add_subscriber(enum_sub, subscriber)

            response = ResponseMessage(id=msg_received.id, jsonrpc=msg_received.jsonrpc, result=True)
            bytes_msg = self.__message_converter.serialise_message(response)
            subscriber.send_msg(bytes_msg)

        else:
            error_msg = f"What you sent is not yet supported..."
            response = ErrorMessage(id=msg_received.id, jsonrpc=msg_received.jsonrpc,
                                    error=ErrorType(code=1, message=error_msg))
            bytes_msg = self.__message_converter.serialise_message(response)
            subscriber.send_msg(bytes_msg)

            subscriber.close_connection(
                WebSocketServerProtocol.CLOSE_STATUS_CODE_INVALID_PAYLOAD,
                error_msg
            )

    def send_msg(self, msg: MessageBase):
        try:
            msg_dict = dataclasses.asdict(msg)
            bytes_msg = ujson.dumps(msg_dict).encode('utf-8')
            for server_protocol in self.__connected_clients:
                server_protocol.send_msg(bytes_msg)
        except Exception as e:
            self.logging.exception(e)

    def close_server(self):
        if self.__async_server_future:
            self.__async_server_future.close()

    def __add_subscriber(self, sub_type: SubscriptionType, server_protocol):
        self.__subscribed_clients[sub_type].add(server_protocol)

    def __remove_subscriber(self, server_protocol):
        for subscriber_set in self.__subscribed_clients.values():
            if server_protocol in subscriber_set:
                subscriber_set.remove(server_protocol)


if __name__ == '__main__':
    import logging
    import os

    parser = argparse.ArgumentParser(prog='Middle tier service between frontend, db, nodes.')
    parser.add_argument("--port", help="port on which ws server should run", type=int, action='store', dest='port', required=True)
    parser.add_argument("--log", help="log folder destination", type=str, action='store', dest='log_dir', required=True)
    parser.add_argument("--log-level", help="logging level", type=str,
                        choices=["DEBUG", "INFO", "WARNING", "CRITICAL"], action='store', dest='log_level', required=True)
    args = parser.parse_args()

    log_file = os.path.join(args.log_dir, "middle-tier-service.log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    ws_server = WebSocketServer(port=args.port, logging=logging)

    async def dummy_function():
        while True:
            subscription = Subscription(id=1, jsonrpc="2.0", method="subscribe", params=["one", "two", "three"])
            ws_server.send_msg(subscription)
            await asyncio.sleep(1)

    loop.create_task(dummy_function())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ws_server.close_server()
        loop.close()
