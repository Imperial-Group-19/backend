from dataclasses import dataclass


@dataclass(init=True, repr=True, frozen=True)
class User:
    name: str 
    email_add: str 
    wallet_id: str

@dataclass(init=True, repr=True, frozen=True)
class Transaction:
    payer_id: str 
    payee_id: str 
    coin: str 
    amount: float 
    gas_spend: float