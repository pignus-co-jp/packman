from abc import ABC
import uuid

class Entity(ABC):
    def __init__(self, id: str):
        self._id = id

    @property
    def id(self) -> str:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id!r})"


    @classmethod
    def next_id(cls) -> str:
        return str(uuid.uuid4())
