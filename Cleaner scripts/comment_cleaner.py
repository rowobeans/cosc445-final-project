import csv
import os
import tempfile
from pathlib import Path

from combine_csvs import main as combine_source_csvs


DATA_FILE = Path(__file__).resolve().parent / "data" / "data.csv"


def main():
    combine_source_csvs()

    temporary_path = None
    try:
        with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source)
            headers = next(reader, None)
            if headers is None:
                raise ValueError(f"{DATA_FILE} is empty and has no header row")

            comment_indices = [
                index
                for index, name in enumerate(headers)
                if "comment" in name.lower()
            ]
            if not comment_indices:
                raise ValueError(f"No comment columns found in {DATA_FILE}")
            if len(comment_indices) == 1:
                print(f"{DATA_FILE} has no duplicate comment columns to merge")
                return

            first_comment_index = comment_indices[0]
            comment_index_set = set(comment_indices)
            output_headers = [
                "Comment" if index == first_comment_index else name
                for index, name in enumerate(headers)
                if index == first_comment_index or index not in comment_index_set
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

                    row[first_comment_index] = "\n\n".join(
                        row[index]
                        for index in comment_indices
                        if row[index].strip()
                    )
                    writer.writerow(
                        value
                        for index, value in enumerate(row)
                        if index == first_comment_index
                        or index not in comment_index_set
                    )

        os.replace(temporary_path, DATA_FILE)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    print(
        f"Appended {len(comment_indices) - 1} comment columns into the first; "
        f"removed the extra columns in {DATA_FILE}"
    )


if __name__ == "__main__":
    main()
