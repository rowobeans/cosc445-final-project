import csv
import os
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "data.csv"


def group_columns(headers):
    indices_by_name = defaultdict(list)
    for index, name in enumerate(headers):
        indices_by_name[name].append(index)
    return indices_by_name


def main():
    temporary_path = None
    try:
        with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source)
            headers = next(reader, None)
            if headers is None:
                raise ValueError(f"{DATA_FILE} is empty and has no header row")

            columns_by_name = group_columns(headers)
            duplicate_groups = {
                name: indices
                for name, indices in columns_by_name.items()
                if len(indices) > 1
            }
            if not duplicate_groups:
                print(f"{DATA_FILE} has no duplicate column names to merge")
                return

            merged_indices = {
                index
                for indices in duplicate_groups.values()
                for index in indices[1:]
            }
            first_indices = {
                indices[0]: indices for indices in duplicate_groups.values()
            }
            output_headers = [
                name for index, name in enumerate(headers) if index not in merged_indices
            ]

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8-sig",
                newline="",
                dir=DATA_FILE.parent,
                suffix=".tmp",
                delete=False,
            ) as output:
                temporary_path = Path(output.name)
                writer = csv.writer(output)
                writer.writerow(output_headers)

                for line_number, row in enumerate(reader, start=2):
                    if len(row) != len(headers):
                        raise ValueError(
                            f"{DATA_FILE}, line {line_number}: expected "
                            f"{len(headers)} fields, found {len(row)}"
                        )

                    output_row = []
                    for index, value in enumerate(row):
                        if index in merged_indices:
                            continue
                        if index in first_indices:
                            value = "\n\n".join(
                                row[column_index]
                                for column_index in first_indices[index]
                                if row[column_index].strip()
                            )
                        output_row.append(value)
                    writer.writerow(output_row)

        try:
            os.replace(temporary_path, DATA_FILE)
        except PermissionError:
            with temporary_path.open("rb") as completed, DATA_FILE.open(
                "wb"
            ) as destination:
                shutil.copyfileobj(completed, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    print(
        f"Merged {sum(len(indices) - 1 for indices in duplicate_groups.values())} "
        f"duplicate columns across {len(duplicate_groups)} column names in "
        f"{DATA_FILE}"
    )


if __name__ == "__main__":
    main()