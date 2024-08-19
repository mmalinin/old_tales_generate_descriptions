from typing import Sequence


def preprocess_table(data: Sequence[Sequence[str]], remove_empty_columns):
    num_columns = len(data[0])

    # remove all columns from data what are empty
    if remove_empty_columns:
        columns_to_keep = {idx for idx in range(num_columns) if any(data[row][idx] for row in range(1, len(data)))}
        data = [[row[idx] for idx in columns_to_keep] for row in data]

    # make sure every element is a strings
    data = [[str(elt) for elt in line] for line in data]
    return data
