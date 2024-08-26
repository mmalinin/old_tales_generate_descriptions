from enum import Enum
from typing import Sequence

from table_utils import preprocess_table


class Alignment(Enum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'


def calculate_column_widths(table: Sequence[Sequence[str]]) -> list[int]:
    num_cols = len(table[0])
    col_widths = [0] * num_cols
    for row in table:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(cell))
    return col_widths


def get_alignment_separator(alignment: Alignment, width: int) -> str:
    if alignment == Alignment.LEFT:
        return ':' + '-' * (width + 1)
    elif alignment == Alignment.CENTER:
        return ':' + '-' * width + ':'
    elif alignment == Alignment.RIGHT:
        return '-' * (width + 1) + ':'
    else:
        raise ValueError(f"Unsupported alignment: {alignment}")


def create_separator_row(col_widths: list[int], alignment: Sequence[Alignment]) -> str:
    separators = [get_alignment_separator(alignment[idx], col_widths[idx]) for idx in range(len(col_widths))]
    return "|" + "|".join(separators) + "|"


def align_cell(cell, width, alignment) -> str:
    if alignment == Alignment.LEFT:
        return cell.ljust(width)
    elif alignment == Alignment.CENTER:
        return cell.center(width)
    elif alignment == Alignment.RIGHT:
        return cell.rjust(width)


def align_and_format_row(row, col_widths, align) -> str:
    aligned_row = [align_cell(cell, col_widths[idx], align[idx]) for idx, cell in enumerate(row)]
    return "| " + " | ".join(aligned_row) + " |"


def data_to_markdown_table(table: Sequence[Sequence[str]], alignment: Sequence[Alignment] = None,
                           remove_empty_cols=False) -> list[str]:
    if not table:
        return []

    processed_table = preprocess_table(table, remove_empty_cols)
    num_cols = len(processed_table[0])

    if alignment is None:
        alignment = [Alignment.LEFT] * num_cols  # Default alignment is left

    col_widths = calculate_column_widths(processed_table)

    header_row = align_and_format_row(processed_table[0], col_widths, alignment)
    separator_row = create_separator_row(col_widths, alignment)

    data_rows = [align_and_format_row(row, col_widths, alignment) for row in processed_table[1:]]

    return [header_row, separator_row] + data_rows


if __name__ == '__main__':
    test_data: list[list[str]] = [
        ["Header1", "Header2", "Header3"],
        ["Row1Col1", "Row1Col2", "Long Row1Col3"],
        ["Long Row2Col1", "Row2Col2", "Row2Col3"],
        ["Row3Col1", "LongerValue", "Row3Col3"]
    ]
    test_align: list[Alignment] = [Alignment.LEFT, Alignment.CENTER, Alignment.RIGHT]  

    markdown_table = '\n'.join(data_to_markdown_table(test_data, test_align))
    print(markdown_table)
