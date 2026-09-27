import io
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class _BorderCharConfig:
    is_first_column: bool
    is_last_column: bool
    is_first_char: bool
    is_last_char: bool


_BorderCharStrategy = Callable[[_BorderCharConfig], str]


class GridBuilder:
    def __init__(
        self, padding_left: int | None = None, padding_right: int | None = None
    ):
        self.__padding_left = padding_left or 1
        self.__padding_right = padding_right or 1

    def build(self, data: list[list[str]]) -> str:
        if len(data) == 0:
            return ""

        col_spacing = self.__calculate_columns_length(data)
        buffer = io.StringIO()

        first_row = data[0]
        self.__write_border(
            buffer, col_spacing, first_row, self.__first_border_strategy
        )
        buffer.write("\n")

        for r, row in enumerate(data):
            for c, col in enumerate(row):
                # write left border
                buffer.write("│")
                col_len = col_spacing[c]
                col_aligned = self.__pad_column(col).ljust(col_len, " ")
                buffer.write(col_aligned)
            # write right border
            buffer.write("│")
            buffer.write("\n")

            is_last_row = r == len(data) - 1
            if is_last_row:
                strategy = self.__last_border_strategy
                self.__write_border(buffer, col_spacing, row, strategy)
            else:
                strategy = self.__middle_border_strategy
                self.__write_border(buffer, col_spacing, row, strategy)
            buffer.write("\n")

        return buffer.getvalue()

    def __pad_column(self, col: str) -> str:
        buffer = io.StringIO()
        buffer.write(" " * self.__padding_left)
        buffer.write(col)
        buffer.write(" " * self.__padding_right)
        return buffer.getvalue()

    def __write_border(
        self,
        buffer: io.StringIO,
        col_spacing: list[int],
        row: list[str],
        strategy: _BorderCharStrategy,
    ) -> None:
        for i, _ in enumerate(row):
            is_first_column = i == 0
            is_last_column = i == len(row) - 1

            # +1 because of the left border char
            col_len = col_spacing[i] + 1
            # last column needs another +1 because of the right border char
            col_full_len = col_len + 1 if is_last_column else col_len
            for j in range(col_full_len):
                is_first_char = j == 0
                is_last_char = j == col_full_len - 1
                parameters = _BorderCharConfig(
                    is_first_column=is_first_column,
                    is_last_column=is_last_column,
                    is_first_char=is_first_char,
                    is_last_char=is_last_char,
                )
                buffer.write(strategy(parameters))

    def __first_border_strategy(self, cfg: _BorderCharConfig) -> str:
        if cfg.is_first_column and cfg.is_first_char:
            return "┌"
        elif not cfg.is_first_column and cfg.is_first_char:
            return "┬"
        elif cfg.is_last_column and cfg.is_last_char:
            return "┐"
        else:
            return "─"

    def __middle_border_strategy(self, cfg: _BorderCharConfig) -> str:
        if cfg.is_first_column and cfg.is_first_char:
            return "├"
        elif not cfg.is_first_column and cfg.is_first_char:
            return "┼"
        elif cfg.is_last_column and cfg.is_last_char:
            return "┤"
        else:
            return "─"

    def __last_border_strategy(self, cfg: _BorderCharConfig) -> str:
        if cfg.is_first_column and cfg.is_first_char:
            return "└"
        elif not cfg.is_first_column and cfg.is_first_char:
            return "┴"
        elif cfg.is_last_column and cfg.is_last_char:
            return "┘"
        else:
            return "─"

    # TODO: rename to __calculate_cells_length
    def __calculate_columns_length(self, data: list[list[str]]) -> list[int]:
        col_spacing: list[int] = []
        for row in data:
            for j, col in enumerate(row):
                col_len = len(col) + self.__padding_left + self.__padding_right
                if j > len(col_spacing) - 1:
                    col_spacing.append(col_len)
                else:
                    col_spacing[j] = max(col_spacing[j], col_len)
        return col_spacing
