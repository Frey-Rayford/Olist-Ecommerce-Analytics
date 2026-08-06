"""Run the complete local Python pipeline in a single command."""

from build_processed_data import main as build_processed_data
from export_dashboard_data import main as export_dashboard_data
from validate_processed_data import main as validate_processed_data


def main() -> None:
    build_processed_data()
    validate_processed_data()
    export_dashboard_data()
    print("PIPELINE_OK")


if __name__ == "__main__":
    main()
