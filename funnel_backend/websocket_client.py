# https://github.com/tpodlaski/copra/blob/master/copra/websocket/client.pyimport logging
import asyncio
from logging import Logger
from time import time
from urllib.parse import urlparse

from autobahn.asyncio.websocket import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol
from autobahn.websocket.protocol import WebSocketProtocol


class Timer:
    def __init__(self, event_loop: asyncio.AbstractEventLoop, timeout: float, callback: asyncio.coroutine):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job(), loop=event_loop)

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()


class WsClientProtocol(WebSocketClientProtocol):
    """should not be accessed or overwritten"""

    def __init__(self, logger: Logger):
        self.client_logger = logger
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self

    def onConnect(self, response):
        self.client_logger.debug(f"onConnect: response: {response}")

    def onConnecting(self, transport_details):
        pass

    def onOpen(self):
        self.client_logger.warning(f"onOpen")
        self.factory.on_open()

    def onClose(self, wasClean, code, reason):
        self.client_logger.warning(f"onClose: wasClean: {wasClean}: code: {code}: reason: {reason}")
        self.factory.on_close(wasClean, code, reason)

    def onMessage(self, payload, isBinary):
        # here can create use https://facebook.github.io/zstd/ to compress and store data efficiently and just
        # write parsers for them later
        self.client_logger.debug(f"onMessage: isBinary: {isBinary}: payload: {payload}")
        self.factory.on_message(payload)


class WebSocketConnection(WebSocketClientFactory):

    def __init__(self, url: str, connection_timeout: float = 10, reconnect_interval: float = 5.0, max_reconnects=10,
                 ping_interval: float = 0, ping_timeout: float = None, auto_connect: bool = True, ws_header=None,
                 origin=None, logger: Logger = None, *args, **kwargs):

        # Connection Settings
        self.logging = logger
        self.url = url
        self.ws_header = ws_header
        self.origin = origin
        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.connection_timeout = connection_timeout if connection_timeout else 10
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        # Connection Handling Attributes - specifically reconnects
        self.reconnect_interval = reconnect_interval
        self.max_reconnects = max_reconnects

        self.last_connected_time = time()
        self.current_reconnect_time = reconnect_interval
        self.current_reconnect_no = 0

        self.coroutine = None

        # states for the websocket
        self.connected = asyncio.Event()
        self.disonnected = asyncio.Event()
        self.disonnected.set()
        self.closing = False
        self.running_timer = None

        # check when the last message was received and if connection should time out
        self.last_msg_recv = time()
        self.msg_timeout_timer = None

        super().__init__(url=self.url,
                         headers=ws_header,
                         origin=origin)

        # can set more options like logOctets, logFrames
        # docs: https://readthedocs.org/projects/autobahn/downloads/pdf/latest/
        self.setProtocolOptions(autoPingInterval=self.ping_interval,
                                autoPingTimeout=self.ping_timeout,
                                echoCloseCodeReason=True)

        if auto_connect:
            self.run()

    # Place holder method
    async def create_connection(self):
        self.logging.warning(f"_connect(): Initialising connection to {self.url}.")
        self.protocol = WsClientProtocol(self.logging)
        url = urlparse(self.url)
        self.coroutine = await self.event_loop.create_connection(self, url.hostname, url.port,
                                                                 ssl=(url.scheme == "wss"))
        self.loop.create_task(self.coroutine)

    def run(self):
        self.running_timer = Timer(self.event_loop, 0., self.create_connection)

    def on_open(self):
        self.connected.set()
        self.disonnected.clear()
        self.closing = False
        self.last_connected_time = time()
        self.logging.info(f"connected to: {self.url}")
        self._on_open()
        self.last_msg_recv = time()
        self.start_timers()

    def on_close(self, was_clean, code, reason):
        self.connected.clear()
        self.disonnected.set()
        self.logging.warning(f"on_close: is_expected: {self.closing}: was_clean: {was_clean}: code: {code}: "
                             f"reason: {reason}")
        self.stop_timers()
        self._on_close()
        if not self.closing:
            current_time = time()
            if (current_time - self.last_connected_time) > self.current_reconnect_time:
                self.current_reconnect_no = 0

            # reconnect
            self.current_reconnect_no = self.current_reconnect_no + 1
            self.current_reconnect_time = self.current_reconnect_no * self.reconnect_interval
            if self.current_reconnect_no < self.max_reconnects:
                self.logging.warning(f"_connect(): Reconnecting to {self.url} after {self.current_reconnect_time}.")
                Timer(self.event_loop, self.current_reconnect_time, self.create_connection)

    def on_error(self, message, reason=""):
        self.logging.error(f"on_error: message: {message}: reason: {reason}")

    def on_message(self, message):
        self.last_msg_recv = time()
        self.stop_timers()
        try:
            self._on_message(message)
            self.start_timers()
        except Exception as e:
            self.logging.exception(e)
            self.logging.error(f"_on_message: failed to parse: {message}. Reconnecting.")
            Timer(self.event_loop, 0., self.reconnect)

    async def close(self):
        self.closing = True
        self.protocol.sendClose()
        await self.disconnected.wait()
        if self.running_timer is not None:
            self.running_timer.cancel()

    async def reconnect(self):
        self._on_close()
        self.protocol.sendClose()
        await self.disonnected.wait()

    def send_message(self, message: str):
        if self.protocol.state == WebSocketProtocol.STATE_OPEN:
            self.protocol.sendMessage(message.encode('utf8'))
        else:
            self.logging.warning(f"Failed to send msg: {message}: as ws connection closed!")

    def _on_open(self, *args) -> None:
        raise NotImplementedError("The 'on_message' method is implemented in the derived class.")

    def _on_message(self, data: bytes, *args) -> None:
        raise NotImplementedError("The 'on_message' method is implemented in the derived class.")

    def _on_close(self, *args) -> None:
        raise NotImplementedError("The 'on_message' method is implemented in the derived class.")

    async def has_connection_timed_out(self):
        current_time = time()
        if (current_time - self.last_msg_recv) > self.connection_timeout:
            self.logging.warning(f"reconnecting due to: connection timeout.")
            Timer(self.event_loop, 0., self.reconnect)

    def start_timers(self):
        self.msg_timeout_timer = Timer(self.event_loop, self.connection_timeout, self.has_connection_timed_out)

    def stop_timers(self):
        if self.msg_timeout_timer is not None:
            self.msg_timeout_timer.cancel()
