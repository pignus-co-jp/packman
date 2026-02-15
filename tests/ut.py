from abc import ABC, abstractmethod


class Tester(ABC):
    @abstractmethod
    def _on_start(self) -> bool:
        pass

    def test(self) -> bool:
        return self._on_start()
