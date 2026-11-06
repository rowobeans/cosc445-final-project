import csv
import os
import tempfile
from collections import defaultdict
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = DATA_DIR / "data.csv"


def identify_columns(headers):
    occurrences = defaultdict(int)
    columns = []
    for name in headers:
        occurrence = occurrences[name]
        occurrences[name] += 1
        columns.append((name, occurrence))
    return columns


def main():
    sources = sorted(
        path
        for path in DATA_DIR.glob("*.csv")
        if path.resolve() != OUTPUT_FILE.resolve()
    )
    if not sources:
        raise FileNotFoundError(f"No source CSV files found in {DATA_DIR}")

    source_columns = {}
    output_columns = []
    output_positions = {}
    for path in sources:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            headers = next(csv.reader(source), None)
        if headers is None:
            raise ValueError(f"{path} is empty and has no header row")

        columns = identify_columns(headers)
        source_columns[path] = columns
        for column in columns:
            if column not in output_positions:
                output_positions[column] = len(output_columns)
                output_columns.append(column)

    temporary_path = None
    total_rows = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=DATA_DIR,
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = csv.writer(output)
            writer.writerow([name for name, _ in output_columns])

            for path in sources:
                columns = source_columns[path]
                with path.open("r", encoding="utf-8-sig", newline="") as source:
                    reader = csv.reader(source)
                    next(reader)
                    for line_number, row in enumerate(reader, start=2):
                        if len(row) != len(columns):
                            raise ValueError(
                                f"{path}, line {line_number}: expected "
                                f"{len(columns)} fields, found {len(row)}"
                            )

                        combined_row = [""] * len(output_columns)
                        for column, value in zip(columns, row):
                            combined_row[output_positions[column]] = value
                        writer.writerow(combined_row)
                        total_rows += 1

        os.replace(temporary_path, OUTPUT_FILE)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    print(
        f"Combined {total_rows} rows from {len(sources)} CSV files "
        f"into {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
