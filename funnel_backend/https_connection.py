import asyncio
import socket
import ssl
from concurrent import futures as concurrent_futures
from logging import Logger

import urllib.parse as _urlencode
import aiohttp
import ujson as json
import yarl
from aiohttp import client_exceptions as aiotthp_cl_except


class HTTPSConnection:

    def __init__(self, base_url: str, connection_timeout: float = 10, is_ssl_required=True,
                 origin=None, logger: Logger = None, *args, **kwargs):

        # Connection Settings
        self.base_url = base_url
        self.logging = logger
        self.is_ssl_required = is_ssl_required
        self.origin = origin
        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.connection_timeout = connection_timeout if connection_timeout else 10
        self.session: aiohttp.ClientSession = None
        self.context = None
        self.tcp_connector = None

    def open_session(self):
        if self.session is None:
            self.logging.debug("opening up session")
            context = ssl.create_default_context() if self.is_ssl_required else None
            self.tcp_connector = aiohttp.TCPConnector(ssl=context, loop=self.event_loop)
            self.session = aiohttp.ClientSession(loop=self.event_loop, connector=self.tcp_connector,
                                                 timeout=self.connection_timeout)
            self.logging.debug("opened up session")

    async def close_session(self):
        if self.session is not None:
            await self.session.close()

    async def fetch(self, path: str, method: str, headers: dict = None, body=None):
        headers = headers or {}
        headers.update({"Accept-Encoding": "gzip, deflate"})
        if self.origin:
            headers.update({"Origin": self.origin})

        self.open_session()
        url = self.base_url + path
        self.logging.warning("%s %s, Request: %s %s", method, url, headers, body)

        encoded_body = body.encode() if body else None
        session_method = getattr(self.session, method.lower())

        try:
            async with session_method(yarl.URL(url, encoded=True),
                                      data=encoded_body,
                                      headers=headers,
                                      timeout=self.connection_timeout) as response:

                http_response = await response.text()
                http_status_code = response.status
                try:
                    json_response = json.loads(http_response)
                except Exception as e:
                    self.logging.warning(f"not valid json: {e}")
                    json_response = None

                # response_headers = response.headers
                self.logging.debug("%s %s, Response: %s %s %s", method, url, http_status_code, headers, http_response)

        except socket.gaierror as e:
            raise Exception(f"Method {method} for {url} not available: {e}")

        except concurrent_futures._base.TimeoutError as e:
            raise Exception(f"Timeout for method {method} for {url} not available: {e}")

        except aiotthp_cl_except.ClientConnectionError as e:
            raise Exception(f"Client connection error for {method} for {url} not available: {e}")

        except aiotthp_cl_except.ClientError as e:
            raise Exception(f"Client error for method {method} for {url} not available: {e}")

        if json_response is not None:
            return json_response

        return response.content

    @staticmethod
    def url_encode(params={}, doseq=False):
        for key, value in params.items():
            if isinstance(value, bool):
                params[key] = 'true' if value else 'false'
        return _urlencode.urlencode(params, doseq)
