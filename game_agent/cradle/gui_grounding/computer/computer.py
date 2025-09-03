from abc import ABC, abstractmethod
from typing import List, Dict, Literal

class Computer(ABC):
    @property
    @abstractmethod
    def environment(self) -> Literal["windows", "mac", "linux"]:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def screenshot(self) -> str:
        pass

    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> None:
        pass

    @abstractmethod
    def double_click(self, x: int, y: int) -> None:
        pass

    @abstractmethod
    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        pass

    @abstractmethod
    def type(self, text: str) -> None:
        pass

    @abstractmethod
    def wait(self, ms: int = 1000) -> None:
        pass

    @abstractmethod
    def move(self, x: int, y: int) -> None:
        pass

    @abstractmethod
    def keypress(self, keys: List[str]) -> None:
        pass

    @abstractmethod
    def drag(self, path: List[Dict[str, int]]) -> None:
        pass

    @abstractmethod
    def get_current_url(self) -> str:
        pass