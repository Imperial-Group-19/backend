from dataclasses import dataclass


@dataclass(init=True, repr=True, frozen=True)
class Message:
    pass


@dataclass(init=True, repr=True, frozen=True)
class Subscription(Message):
    type: str

    def __hash__(self):
        return hash(self.type)

    def __eq__(self, other):
        return self.type == other.type
