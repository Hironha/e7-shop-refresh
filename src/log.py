import datetime as dt
import sys
from enum import Enum


class Ansi(Enum):
    RESET = "\x1b[0m"
    CYAN = "\x1b[36m"
    RED = "\x1b[31m"
    YELLOW = "\x1b[33m"
    BOLD = "\x1b[1m"

    @staticmethod
    def cyan(msg: str) -> str:
        return f"{Ansi.CYAN.value}{msg}{Ansi.RESET.value}"

    @staticmethod
    def red(msg: str) -> str:
        return f"{Ansi.RED.value}{msg}{Ansi.RESET.value}"

    @staticmethod
    def yellow(msg: str) -> str:
        return f"{Ansi.YELLOW.value}{msg}{Ansi.RESET.value}"

    @staticmethod
    def bold(msg: str) -> str:
        return f"{Ansi.BOLD.value}{msg}{Ansi.RESET.value}"


class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class LogEntry:
    def __init__(self, level: LogLevel, time: dt.datetime, msg: str):
        self.time = time
        self.msg = msg
        self.level = level


class Logger:
    def __init__(self):
        self.__entries: list[LogEntry] = []

    def __del__(self):
        self.flush()

    def debug(self, msg: str) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        entry = LogEntry(level=LogLevel.DEBUG, time=now, msg=msg)
        self.__entries.append(entry)

    def info(self, msg: str) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        entry = LogEntry(level=LogLevel.INFO, time=now, msg=msg)
        self.__entries.append(entry)

    def warn(self, msg: str) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        entry = LogEntry(level=LogLevel.WARN, time=now, msg=msg)
        self.__entries.append(entry)

    def error(self, msg: str) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        entry = LogEntry(level=LogLevel.ERROR, time=now, msg=msg)
        self.__entries.append(entry)

    def flush(self) -> None:
        messages: list[str] = []
        for entry in self.__entries:
            time = entry.time.isoformat(timespec="milliseconds")
            level = self.__fmt_level(entry.level, entry.level.name.rjust(5, " "))
            messages.append(f"[{time}] {level} {entry.msg}")
        self.__entries = []

        msg = "\n".join(messages)
        print(msg, file=sys.stderr)

    def __fmt_level(self, level: LogLevel, msg: str) -> str:
        match level:
            case LogLevel.DEBUG:
                return Ansi.bold(msg)
            case LogLevel.INFO:
                return Ansi.bold(Ansi.cyan(msg))
            case LogLevel.WARN:
                return Ansi.bold(Ansi.yellow(msg))
            case LogLevel.ERROR:
                return Ansi.bold(Ansi.red(msg))
