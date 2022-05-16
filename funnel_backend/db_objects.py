from dataclasses import dataclass
from typing import List


@dataclass(init=True, repr=True, frozen=True)
class User:
    name: str 
    email_address: str 
    wallet_address: str

    def __str__(self):
        return f"{self.name}, {self.email_add}, {self.wallet_add}"


@dataclass(init=True, repr=True, frozen=True)
class Transaction:
    wallet_address: str 
    store_address: str 
    product: List[str] 
    time_stamp: int

    def __str__(self):
        return f"{self.wallet_address}, {self.store_address}, {self.product}, {self.time_stamp}"


@dataclass(init=True, repr=True, frozen=True)
class Store:
    id: str
    title: str
    description: str
    storeOwner: str

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Store):
            if self.id == __o.id:
                return True
        return False

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(init=True, repr=True)
class Product:
    productName: str
    storeAddress: str
    title: str
    description: str
    price: int
    features: List[str]
    productType: int

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Product):
            if self.storeAddress == __o.storeAddress and self.productName == __o.productName and self.productType == __o.productType:
                return True
        return False

    def __hash__(self) -> int:
        return hash(self.productName) ^ hash(self.storeAddress) ^ hash(self.productType)


@dataclass(init=True, repr=True)
class Affiliate:
    affiliateAddress: str
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Affiliate):
            if self.affiliateAddress == __o.affiliateAddress:
                return True
        return False
    def __hash__(self) -> str:
        return hash(self.affiliateAddress)

@dataclass(init=True, repr=True)
class FunnelEvent:
    blockHash: str
    transactionHash: str
    blockNumber: int
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
    productType: int
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
    newStoreOwner: str


@dataclass(init=True, repr = True)
class AffiliateRegistered(FunnelEvent):
    storeAddress: str
    affiliateAddress: str


@dataclass(init=True, repr = True)
class OwnershipTransferred(FunnelEvent):
    previousOwner: str
    newOwner: str


ALLOWED_EVENTS = {
    "StoreCreated"  : StoreCreated,
    "PaymentMade"   : PaymentMade,
    "ProductCreated": ProductCreated,
    "ProductRemoved": ProductRemoved,
    "ProductUpdated": ProductUpdated,
    "RefundMade"    : RefundMade,
    "StoreRemoved"  : StoreRemoved,
    "StoreUpdated"  : StoreUpdated,
    "AffiliateRegistered": AffiliateRegistered,
    "OwnershipTransferred": OwnershipTransferred
}
