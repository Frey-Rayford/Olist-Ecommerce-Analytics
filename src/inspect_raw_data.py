"""Inspect raw Olist CSV files without modifying them."""

from pathlib import Path

import pandas as pd


RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

    for csv_file in csv_files:
        data = pd.read_csv(csv_file, low_memory=False)
        print(f"FILE|{csv_file.name}|{len(data)}|{len(data.columns)}")

        for column in data.columns:
            missing = int(data[column].isna().sum())
            print(f"COLUMN|{column}|{data[column].dtype}|{missing}")


if __name__ == "__main__":
    main()
