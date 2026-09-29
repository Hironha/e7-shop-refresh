from dataclasses import dataclass
from typing import Literal, TypeGuard


@dataclass(frozen=True)
class Ok[T]:
    value: T

    @staticmethod
    def is_ok[U, E](result: Result[U, E]) -> TypeGuard[Ok[U]]:
        return result.__is_ok()

    @staticmethod
    def get[U, E](result: Result[U, E]) -> U | None:
        if Ok.is_ok(result):
            return result.value
        return None

    def __is_ok(self) -> Literal[True]:
        return True


@dataclass(frozen=True)
class Error[E]:
    error: E

    @staticmethod
    def is_error[T, U](result: Result[T, U]) -> TypeGuard[Error[U]]:
        return not result.__is_ok()

    @staticmethod
    def get[T, U](result: Result[T, U]) -> U | None:
        if Error.is_error(result):
            return result.error
        return None

    def __is_ok(self) -> Literal[False]:
        return False


type Result[T, E] = Ok[T] | Error[E]
