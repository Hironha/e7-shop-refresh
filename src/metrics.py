import csv
import datetime as dt
import os
from dataclasses import dataclass

from log import Logger
from result import Error, Ok, Result


@dataclass
class RefreshMetric:
    created_at: dt.datetime
    iterations: int
    covenant_count: int
    mystic_count: int


class MetricsStorage:
    def __init__(self, filepath: str, logger: Logger):
        self.__filepath = filepath
        self.__logger = logger
        self.__headers = ["created_at", "iterations", "covenant_count", "mystic_count"]

    def store(self, metric: RefreshMetric) -> Result[None, str]:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            with open(filepath, mode="w+", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.__headers)
                writer.writerow(self.__serialize_metric(metric))
                return Ok(None)

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return Error(f"Detected invalid headers in metrics file: {filepath}")

        with open(filepath, mode="a+", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.__serialize_metric(metric))
            self.__logger.info("Successfully Wrote content into CSV file")
            return Ok(None)

    def get_all_metrics(self) -> Result[list[RefreshMetric], str]:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            self.__logger.error(
                f"Failed getting all metrics from {filepath}. File empty or not found."
            )
            return Ok([])

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return Error("Missing or invalid headers from CSV file")

            metrics: list[RefreshMetric] = []
            for row in reader:
                created_at = dt.datetime.fromisoformat(row[0])
                iterations = int(row[1])
                covenant_count = int(row[2])
                mystic_count = int(row[3])

                metrics.append(
                    RefreshMetric(created_at, iterations, covenant_count, mystic_count)
                )

            return Ok(metrics)

    def __serialize_metric(self, metric: RefreshMetric) -> list[str]:
        created_at = metric.created_at.isoformat(timespec="milliseconds")
        iterations = str(metric.iterations)
        covenant_count = str(metric.covenant_count)
        mystic_count = str(metric.mystic_count)
        # order matters and it must be the same order defined in headers
        return [created_at, iterations, covenant_count, mystic_count]


@dataclass(frozen=True)
class MetricsSummary:
    total_iterations: int
    total_covenants: int
    total_covenants_medals: int
    total_covenants_gold: int
    covenant_rating: float
    total_mystics: int
    total_mystics_medals: int
    total_mystics_gold: int
    mystic_rating: float
    total_skystones: int
    total_gold: int


class MetricsProcessor:
    def __init__(self):
        pass

    def get_metrics_summary(self, metrics: list[RefreshMetric]) -> MetricsSummary:
        skystone_per_iteration = 3
        medals_per_unit = 5
        gold_per_covenant = 184_000
        gold_per_mystic = 280_000

        total_iterations = 0
        total_covenants = 0
        total_mystics = 0
        for metric in metrics:
            total_iterations += metric.iterations
            total_covenants += metric.covenant_count
            total_mystics += metric.mystic_count

        total_skystones = skystone_per_iteration * total_iterations
        total_covenants_medals = medals_per_unit * total_covenants
        total_covenants_gold = gold_per_covenant * total_covenants
        covenant_rating = total_covenants / total_iterations

        total_mystics_medals = medals_per_unit * total_mystics
        total_mystics_gold = gold_per_mystic * total_mystics
        mystic_rating = total_mystics / total_iterations

        total_gold = total_covenants_gold + total_mystics_gold

        return MetricsSummary(
            total_iterations=total_iterations,
            total_covenants=total_covenants,
            total_covenants_medals=total_covenants_medals,
            total_covenants_gold=total_covenants_gold,
            covenant_rating=covenant_rating,
            total_mystics=total_mystics,
            total_mystics_medals=total_mystics_medals,
            total_mystics_gold=total_mystics_gold,
            mystic_rating=mystic_rating,
            total_gold=total_gold,
            total_skystones=total_skystones,
        )
