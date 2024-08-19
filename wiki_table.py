from typing import Sequence
from table_utils import preprocess_table


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
