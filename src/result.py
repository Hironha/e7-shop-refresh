from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Ok[T]:
    value: T

    def is_ok(self) -> Literal[True]:
        return True


@dataclass(frozen=True)
class Error[E]:
    error: E

    def is_ok(self) -> Literal[False]:
        return False


type Result[T, E] = Ok[T] | Error[E]
