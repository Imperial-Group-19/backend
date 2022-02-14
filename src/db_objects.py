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
        return f"{self.wallet_address}, {self.store_address}, {self.product}, {self.timestamp}"


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
