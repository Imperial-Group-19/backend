from dataclasses import dataclass, field
from typing import Any, List
from enum import Enum


class SubscriptionType(Enum):
    stores   = "stores"
    products = "products"


class SnapshotType(Enum):
    stores   = "storesSnapshot"
    products = "productsSnapshot"


class UpdateType(Enum):
    stores   = "storesUpdate"
    products = "productsUpdate"


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
class Subscription(ParamsMessage):
    params: List[str]
    method = "subscribe"


@dataclass(init=True, repr=True)
class SubscriptionResponse(ResponseMessage):
    result: bool
