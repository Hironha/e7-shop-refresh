import csv
import datetime as dt
import os
from dataclasses import dataclass

from log import Logger


@dataclass
class RefreshMetric:
    created_at: dt.datetime
    iterations: int
    covenant_count: int
    mystic_count: int


class MetricStorage:
    def __init__(self, filepath: str, logger: Logger):
        self.__filepath = filepath
        self.__logger = logger
        self.__headers = ["created_at", "iterations", "covenant_count", "mystic_count"]

    def store(self, metric: RefreshMetric) -> str | None:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            with open(filepath, mode="w+", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.__headers)
                writer.writerow(self.__serialize_metric(metric))
                return

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return f"Detected invalid headers in metrics file: {filepath}"

        with open(filepath, mode="a+", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.__serialize_metric(metric))
            self.__logger.info("Successfully Wrote content into CSV file")

    def __serialize_metric(self, metric: RefreshMetric) -> list[str]:
        created_at = metric.created_at.isoformat(timespec="milliseconds")
        iterations = str(metric.iterations)
        covenant_count = str(metric.covenant_count)
        mystic_count = str(metric.mystic_count)
        # order matters and it must be the same order defined in headers
        return [created_at, iterations, covenant_count, mystic_count]
