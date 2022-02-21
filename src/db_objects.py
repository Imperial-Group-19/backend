from dataclasses import dataclass
from typing import List


@dataclass(init=True, repr=True, frozen=True)
class User:
    name: str 
    email_address: str 
    wallet_address: str

    def __str__(self):
        return f"{self.name}, {self.email_address}, {self.wallet_address}"


@dataclass(init=True, repr=True, frozen=True)
class Transaction:
    wallet_address: str 
    store_address: str 
    product_id: str 
    timestamp: int

    def __str__(self):
        return f"{self.wallet_address}, {self.store_address}, {self.product_id}, {self.timestamp}"


@dataclass(init=True, repr=True, frozen=True)
class Store:
    id: str
    title: str
    description: str
    store_address: str

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Store):
            if self.id == __o.id:
                return True
        return False

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(init=True, repr=True, frozen=True)
class Product:
    product_id: str
    store_id: str
    title: str
    description: str
    price: int 
    features: List[str]

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Store):
            if self.store_id == __o.store_id and self.product_id == __o.product_id:
                return True
        return False

    def __hash__(self) -> int:
        return hash(self.product_id) ^ hash(self.store_id)


@dataclass(init=True, repr=True)
class FunnelEvent:
    block_hash: str
    transaction_hash: str
    block_number: int
    address: str
    data: str
    transaction_idx: int


@dataclass(init=True, repr=True)
class FunnelContractEvent(FunnelEvent):
    event: str
    event_data: dict


@dataclass(init=True, repr=True)
class StoreCreated(FunnelEvent):
    storeAddress: str
    storeOwner: str


@dataclass(init=True, repr=True)
class PaymentMade(FunnelEvent):
    customer: str
    storeAddress: str
    productNames: List[str]

    def __post_init__(self):
        if isinstance(self.productNames, tuple):
            self.product_names = list(self.productNames)


@dataclass(init=True, repr=True)
class ProductCreated(FunnelEvent):
    storeAddress: str
    productName: str
    price: int


@dataclass(init=True, repr=True)
class ProductRemoved(FunnelEvent):
    storeAddress: str
    productName: str


@dataclass(init=True, repr=True)
class ProductUpdated(FunnelEvent):
    storeAddress: str
    productName: str
    newPrice: int


@dataclass(init=True, repr=True)
class RefundMade(FunnelEvent):
    customer: str
    storeAddress: str
    productNames: List[str]

    def __post_init__(self):
        if isinstance(self.productNames, tuple):
            self.product_names = list(self.productNames)


@dataclass(init=True, repr=True)
class StoreRemoved(FunnelEvent):
    storeAddress: str


@dataclass(init=True, repr=True)
class StoreUpdated(FunnelEvent):
    storeAddress: str
    newStoreAddress: str


ALLOWED_EVENTS = {
    "StoreCreated"  : StoreCreated,
    "PaymentMade"   : PaymentMade,
    "ProductCreated": ProductCreated,
    "ProductRemoved": ProductRemoved,
    "ProductUpdated": ProductUpdated,
    "RefundMade"    : RefundMade,
    "StoreRemoved"  : StoreRemoved,
    "StoreUpdated"  : StoreUpdated
}
