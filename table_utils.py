from enum import Enum
from typing import Sequence


def preprocess_table(data: Sequence[Sequence[str]], remove_empty_columns: bool = False) -> list[list[str]]:
    num_columns = len(data[0])

    # remove all columns from data what are empty
    if remove_empty_columns:
        columns_to_keep = {idx for idx in range(num_columns) if any(data[row][idx] for row in range(1, len(data)))}
        data = [[row[idx] for idx in columns_to_keep] for row in data]

    # make sure every element is a string
    data = [[str(elt) for elt in line] for line in data]
    return data


# Fandom wiki cell=row formatting
def data_to_wiki_table(data: Sequence[Sequence[str]], remove_empty_columns=False) -> list[str]:
    if not data:
        return []

    ltable = preprocess_table(data, remove_empty_columns)

    wiki: list[str] = ['{| class="sortable fandom-table"', '|+']
    for header_cell in ltable[0]:
        wiki.append(f"!'''{header_cell}'''")
    wiki.append("|-")

    count = len(ltable) - 1
    for row in ltable[1:]:
        for cell in row:
            wiki.append(f'|{cell}')
        count -= 1
        if count != 0:
            wiki.append("|-")
    wiki.append('|}')
    return wiki
