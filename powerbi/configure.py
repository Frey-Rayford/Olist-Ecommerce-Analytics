"""Point the Power BI project's DataFolder parameter at the exported CSVs."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def configure(folder):
    folder = folder.resolve()
    for filename in ['fact_orders.csv', 'customer_cohorts.csv']:
        if not (folder / filename).is_file():
            raise FileNotFoundError(f'{filename} is missing. Run python src/run_pipeline.py first.')
    path = ROOT / 'Olist/Olist.SemanticModel/definition/expressions.tmdl'
    source = path.read_text(encoding='utf-8-sig')
    value = folder.as_posix().replace('"', '""')
    updated, count = re.subn(r'^expression DataFolder = .*$', lambda _: f'expression DataFolder = "{value}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]', source, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError('DataFolder parameter was not found in the model.')
    path.write_text(updated, encoding='utf-8')
    print(f'POWERBI_DATA_FOLDER_OK|{folder}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-folder', type=Path, default=ROOT / 'data')
    configure(parser.parse_args().data_folder)
