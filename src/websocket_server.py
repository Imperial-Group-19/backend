#!/usr/bin/env python3

# server
# https://github.com/crossbario/autobahn-python/blob/master/examples/asyncio/websocket/echo/server.py
import argparse
import asyncio
import dataclasses
from getpass import getpass
from logging import Logger
from typing import Union, Dict, List

import ujson
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.websocket.protocol import ConnectionRequest, WebSocketProtocol
from sshtunnel import SSHTunnelForwarder

from db_connection import postgresDBClient
from db_objects import Store, Product, ALLOWED_EVENTS, FunnelContractEvent, StoreCreated, StoreRemoved, StoreUpdated, \
    PaymentMade, RefundMade, ProductCreated, ProductRemoved, ProductUpdated
from message_conversion import MessageConverter
from message_protocol import Subscription, MessageBase, DBType, ErrorMessage, ErrorType, ResponseMessage, ParamsMessage, \
    WSMsgType, Update
from polygon_node_connection import PolygonNodeClient


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
            self.factory.process_msg(payload, self)

        def onClose(self, was_clean: bool, code: int, reason: str):
            self.factory.logging.warning(f"Client disconnecting: {self.__request.peer}: {was_clean}, {code}, {reason}")
            self.factory.remove_remote_client(self)

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
        self.__allowed_subscriptions = [enum_pos.value for enum_pos in list(DBType)]

        # sets of clients and subscribers here
        self.__connected_clients = set()
        self.__subscribed_clients: Dict[DBType, set] = {}
        for enum_pos in list(DBType):
            self.__subscribed_clients[enum_pos] = set()

        self.__products_counter = 0
        self.__stores_counter = 0

        # add db client
        self.db_connect = postgresDBClient(self.logging)

        # add server to asyncio + run until complete
        self.server = self.event_loop.create_server(protocol_factory=self,
                                                    host="", port=self.port)
        self.__async_server_future = self.event_loop.run_until_complete(self.server)
        self.__polygon_node_connection = PolygonNodeClient(event_loop=self.event_loop, logger=self.logging,
                                                           https_url="https://rpc-mumbai.maticvigil.com",
                                                           contract_address="0xBAdA7AAF69f5ba7930FE756c7703bcA4A297Fd0e",
                                                           contract_abi_file="funnel_abi.json",
                                                           start_block=25460649)

        self.__polygon_node_connection.register_event_callback("ws_server", self.process_contract_events)

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

        try:
            msg_received = self.__message_converter.deserialise_message(payload)
        except Exception as e:
            error_msg = f"Received unsupported message: {payload}: Exception: {e}"
            self.logging.warning(error_msg)
            self.send_error_msg(server_protocol=subscriber, msg_id=-1,
                                error_type=ErrorType(code=99, message="Invalid json."))
            return

        if isinstance(msg_received, Subscription):
            for subscription in msg_received.params:
                if subscription not in self.__allowed_subscriptions:
                    # send error message + disconnect client
                    error_msg = f"Following subscription param not supported: {subscription}"
                    self.send_error_msg(server_protocol=subscriber, msg_id=-1,
                                        error_type=ErrorType(code=99, message=error_msg))
                    subscriber.close_connection(
                        WebSocketServerProtocol.CLOSE_STATUS_CODE_INVALID_PAYLOAD,
                        error_msg
                    )
                    return

            self.send_response_msg(server_protocol=subscriber, msg_id=msg_received.id, result=True)

            for subscription in msg_received.params:
                enum_sub = DBType[subscription]
                self.__add_subscriber(enum_sub, subscriber)

        elif isinstance(msg_received, Update):
            error_msg = ""
            if len(msg_received.params) == 2:
                if isinstance(msg_received.params[1], dict):
                    if msg_received.params[0] == DBType.products.value:
                        try:
                            product = Product(**msg_received.params[1])
                            inserted = self.update_product(product)
                            self.send_response_msg(server_protocol=subscriber, msg_id=msg_received.id, result=inserted)
                            if inserted:
                                self.send_product_update(product)
                            return
                        except Exception as e:
                            error_msg = f"Wrong keys/value types for product item: {msg_received}"
                            self.logging.exception(e)

                    elif msg_received.params[0] == DBType.stores.value:
                        try:
                            store = Store(**msg_received.params[1])
                            inserted = self.update_store(store)
                            self.send_response_msg(server_protocol=subscriber, msg_id=msg_received.id, result=inserted)
                            if inserted:
                                self.send_store_update(store)
                            return
                        except Exception as e:
                            error_msg = "Wrong keys/value types for store item"
                            self.logging.exception(e)

                    else:
                        error_msg = "No such db object!"

            else:
                error_msg = "Insert params have wrong format. Expecting [str, dict]"

            self.send_error_msg(server_protocol=subscriber, msg_id=msg_received.id,
                                error_type=ErrorType(code=2, message=error_msg))

        else:
            error_msg = f"What you sent is not yet supported..."
            self.send_error_msg(server_protocol=subscriber, msg_id=msg_received.id,
                                error_type=ErrorType(code=1, message=error_msg))
            subscriber.close_connection(
                WebSocketServerProtocol.CLOSE_STATUS_CODE_INVALID_PAYLOAD,
                error_msg
            )

    def send_error_msg(self, server_protocol, msg_id: int, error_type: ErrorType):
        response = ErrorMessage(id=msg_id, jsonrpc="2.0", error=error_type)
        bytes_msg = self.__message_converter.serialise_message(response)
        server_protocol.send_msg(bytes_msg)

    def send_response_msg(self, server_protocol, msg_id: int, result: bool):
        response = ResponseMessage(id=msg_id, jsonrpc="2.0", result=result)
        bytes_msg = self.__message_converter.serialise_message(response)
        server_protocol.send_msg(bytes_msg)

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

    def send_product_update(self, product: Product):
        self.__products_counter += 1
        snapshot_msg = ParamsMessage(id=self.__products_counter, jsonrpc="2.0", method=WSMsgType.update.value,
                                     params=[DBType.products.value, [product.__dict__]])
        bytes_msg = self.__message_converter.serialise_message(snapshot_msg)
        for subscriber in self.__subscribed_clients[DBType.products]:
            subscriber.send_msg(bytes_msg)

    def send_store_update(self, store: Store):
        self.__stores_counter += 1
        snapshot_msg = ParamsMessage(id=self.__stores_counter, jsonrpc="2.0", method=WSMsgType.update.value,
                                     params=[DBType.stores.value, [store.__dict__]])
        bytes_msg = self.__message_converter.serialise_message(snapshot_msg)
        for subscriber in self.__subscribed_clients[DBType.stores]:
            subscriber.send_msg(bytes_msg)

    def __add_subscriber(self, sub_type: DBType, server_protocol):
        self.__subscribed_clients[sub_type].add(server_protocol)
        if sub_type == DBType.stores:
            msg_counter = self.__stores_counter
            params = [DBType.stores.value, [item.__dict__ for item in self.db_connect.get_stores()]]
        elif sub_type == DBType.products:
            msg_counter = self.__products_counter
            params = [DBType.products.value, [item.__dict__ for item in self.db_connect.get_products()]]
        else:
            raise Exception("Unrecognised sub snapshot")

        snapshot_msg = ParamsMessage(id=msg_counter, jsonrpc="2.0", method=WSMsgType.snapshot.value, params=params)
        bytes_msg = self.__message_converter.serialise_message(snapshot_msg)
        server_protocol.send_msg(bytes_msg)

    def __remove_subscriber(self, server_protocol):
        for subscriber_set in self.__subscribed_clients.values():
            if server_protocol in subscriber_set:
                subscriber_set.remove(server_protocol)

    def process_contract_events(self, list_events: List[FunnelContractEvent]):
        for event in list_events:
            if event.event in ALLOWED_EVENTS:
                cls_obj = ALLOWED_EVENTS[event.event]
                cls_obj_data = event.__dict__
                cls_obj_data.pop("event")
                extra_data = cls_obj_data.pop("event_data")
                cls_obj_data.update(extra_data)
                init_obj = cls_obj(**cls_obj_data)
                self.logging.warning(init_obj)
                # add write feature to DB
                self.write_db(init_obj)

    def write_db(self, init_obj):
        if isinstance(init_obj, StoreCreated):
            self.db_connect.write_store_created(init_obj)
        elif isinstance(init_obj, StoreRemoved):
            self.db_connect.write_store_removed(init_obj)
        elif isinstance(init_obj, StoreUpdated):
            self.db_connect.write_store_updated(init_obj)
        elif isinstance(init_obj, ProductCreated):
            self.db_connect.write_product_created(init_obj)
        elif isinstance(init_obj, ProductRemoved):
            self.db_connect.write_product_removed(init_obj)
        elif isinstance(init_obj, ProductUpdated):
            self.db_connect.write_product_updated(init_obj)
        elif isinstance(init_obj, PaymentMade):
            self.db_connect.write_payment_made(init_obj)
        elif isinstance(init_obj, RefundMade):
            self.db_connect.write_refund_made(init_obj)

    def update_product(self, product: Product):
        self.db_connect.update_product(product)
        # self.db_connect.products[product] = product
        return True

    def update_store(self, store: Store):
        self.db_connect.update_store(store)
        # self.db_connect.stores[store] = store
        return True


if __name__ == '__main__':
    import logging
    import os

    parser = argparse.ArgumentParser(prog='Middle tier service between frontend, db, nodes.')
    parser.add_argument("--port", help="port on which ws server should run", type=int, action='store', dest='port', required=True)
    parser.add_argument("--log", help="log folder destination", type=str, action='store', dest='log_dir', required=True)
    parser.add_argument("--log-level", help="logging level", type=str,
                        choices=["DEBUG", "INFO", "WARNING", "CRITICAL"], action='store', dest='log_level', required=True)
    parser.add_argument("--is-prod", help="is production server", type = str,
                        choices=['True', 'False'], action='store', dest='is_prod')
    args = parser.parse_args()

    if args.is_prod == 'False':
        username = input("Enter SSH username: ")
        pkey = input("Enter SSH private key: ")
        pw = getpass(prompt = 'Enter SSH private key password: ')

        PORT = 5432
        server = SSHTunnelForwarder(
            ('35.195.58.180', 22),
            ssh_username=username,
            ssh_pkey = pkey,
            ssh_private_key_password= pw,
            remote_bind_address=('localhost', PORT),
            local_bind_address=('localhost', PORT),
            allow_agent=False
        )
        server.start()

    log_file = os.path.join(args.log_dir, "middle-tier-service.log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    ws_server = WebSocketServer(port=args.port, logging=logging)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ws_server.close_server()
        loop.close()
