"""Run the complete local Python pipeline in a single command."""

from build_processed_data import main as build_processed_data
from export_dashboard_data import main as export_dashboard_data
from validate_processed_data import main as validate_processed_data
from delivery_analysis import export as export_delivery_analysis
from write_delivery_report import write_report


def main() -> None:
    build_processed_data()
    validate_processed_data()
    export_dashboard_data()
    export_delivery_analysis()
    write_report()
    print("PIPELINE_OK")


if __name__ == "__main__":
    main()
