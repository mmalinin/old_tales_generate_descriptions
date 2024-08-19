from enum import Enum
from typing import Sequence
from table_utils import preprocess_table


class Alignment(Enum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'


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


def data_to_markdown_table(table: Sequence[Sequence[str]], align: Sequence[Alignment] = None,
                           remove_empty_columns=False) -> list[str]:
    if not table:
        return []

    ltable = preprocess_table(table, remove_empty_columns)

    num_columns = len(ltable[0])

    if align is None:
        align = [Alignment.LEFT] * len(ltable[0])  # Default alignment is left

    # Calculate the maximum width of each column
    col_widths = [0] * num_columns

    for row in ltable:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(cell))

    # Build the header row
    header_row = align_and_format_row(ltable[0], col_widths, align)

    # Build the separator row with alignment
    alignment_mapper = {
        Alignment.LEFT: lambda width: ':' + '-' * (width + 1),
        Alignment.CENTER: lambda width: ':' + '-' * (width + 0) + ':',
        Alignment.RIGHT: lambda width: '-' * (width + 1) + ':'
    }

    separators = [alignment_mapper[align[idx]](col_widths[idx]) for idx in range(num_columns)]
    separator_row = "|" + "|".join(separators) + "|"

    # Build each data row
    data_rows = [align_and_format_row(row, col_widths, align) for row in ltable[1:]]

    # Combine all parts into the final Markdown table
    # markdown_table = "\n".join([header_row, separator_row] + data_rows)
    return [header_row, separator_row] + data_rows


# Example usage
data = [
    ["Header1", "Header2", "Header3"],
    ["Row1Col1", "Row1Col2", "Long row Row1Col3"],
    ["Row2Col1", "Row2Col2", "Row2Col3"],
    ["Row3Col1", "LongerValue", "Row3Col3"]
]
align = [Alignment.LEFT, Alignment.CENTER, Alignment.RIGHT]  # Alignment settings for each column

if __name__ == '__main__':
    markdown_table = '\n'.join(data_to_markdown_table(data, align))
    print(markdown_table)
