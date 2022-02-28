from dataclasses import dataclass
from enum import Enum
from typing import Any, List


class DBType(Enum):
    stores   = "stores"
    products = "products"


class WSMsgType(Enum):
    subscribe    = "subscribe"
    snapshot     = "snapshot"
    update       = "update"
    insert       = "insert"


@dataclass(init=True, repr=True, frozen=True)
class ErrorType:
    code: int
    message: str


@dataclass(init=True, repr=True)
class MessageBase:
    id: int
    jsonrpc: str

    def get_as_dict(self):
        return self.__dict__


@dataclass(init=True, repr=True)
class ParamsMessage(MessageBase):
    method: str
    params: List[Any]


@dataclass(init=True, repr=True)
class ResponseMessage(MessageBase):
    result: Any


@dataclass(init=True, repr=True)
class ErrorMessage(MessageBase):
    error: ErrorType

    def __post_init__(self):
        if isinstance(self.error, dict):
            self.error = ErrorType(**self.error)

    def get_as_dict(self):
        return {
            "id": self.id,
            "jsonrpc": self.jsonrpc,
            "error": self.error.__dict__
        }


@dataclass(init=True, repr=True)
class ParamsResponse(ResponseMessage):
    result: bool


@dataclass(init=True, repr=True)
class Subscription(ParamsMessage):
    params: List[str]
    method = "subscribe"


@dataclass(init=True, repr=True)
class Update(ParamsMessage):
    params: List[str]
    method = "update"
