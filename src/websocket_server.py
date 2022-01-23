#!/usr/bin/env python3.8

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

from messaging_protocol import Subscription, Message


class WebSocketServer(WebSocketServerFactory):

    class ServerProtocol(WebSocketServerProtocol):
        def __init__(self, web_socket_server):
            self.__websocket_server = web_socket_server
            self.__logging = self.__websocket_server.logging
            self.__request: ConnectionRequest = None
            super().__init__()

        def onConnect(self, request: ConnectionRequest):
            self.__request = request
            self.__logging.info(f"Client connecting: {self.__request.peer}")
            self.__websocket_server.add_remote_client(self)

        def onOpen(self):
            self.__logging.info(f"WebsocketConnection open for: {self.__request.peer}")

        def onMessage(self, payload: Union[bytes, str], is_binary: bool):
            if is_binary:
                self.__logging.debug(f"Binary message received from: {self.__request.peer}: msg: {payload}")
            else:
                self.__logging.debug(f"Binary message received from: {self.__request.peer}: msg: {payload.decode('utf8')}")

            # handle msgs here - read json/binaries + give callbacks

        def onClose(self, was_clean: bool, code: int, reason: str):
            self.__logging.info(f"Client disconnecting: {self.__request.peer}: {was_clean=}, {code=}, {reason=}")
            self.__websocket_server.remove_remote_client(self.remote_address)

        def send_msg(self, data: bytes):
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
        super().__init__(ws_address)

        # sets of clients and subscribers here
        self.__connected_clients = set()
        self.__subscribed_clients: Dict[Subscription, set] = {}

        # add server to asyncio + run until complete
        self.server = self.event_loop.create_server(protocol_factory=lambda: self.ServerProtocol(self),
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

        for sub_clients in self.__subscribed_clients.values():
            if server_protocol in sub_clients:
                sub_clients.remove(server_protocol)

    def send_msg(self, msg: Message):
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
    logging.basicConfig(filename=log_file, level=args.log_level)

    loop = asyncio.get_event_loop()
    ws_server = WebSocketServer(port=args.port, logging=logging)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ws_server.close_server()
        loop.close()
