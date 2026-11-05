import json
from pathlib import Path
import re
import unittest


PROJECT = Path(__file__).resolve().parents[1] / 'powerbi/Olist'


class PowerBiProjectTests(unittest.TestCase):
    def test_report_fields_bind_to_model_and_visuals_fit_pages(self):
        tables = {path.stem: path.read_text(encoding='utf-8-sig') for path in (PROJECT / 'Olist.SemanticModel/definition/tables').glob('*.tmdl')}
        def names(source, kind):
            return {next(value for value in match if value) for match in re.findall(r'^\t' + kind + r" (?:'([^']+)'|([^\s=]+))", source, re.MULTILINE)}
        columns = {name: names(source, 'column') for name, source in tables.items()}
        measures = {name: names(source, 'measure') for name, source in tables.items()}
        report = PROJECT / 'Olist.Report'
        binding = json.loads((report / 'definition.pbir').read_text(encoding='utf-8-sig'))
        self.assertTrue((report / binding['datasetReference']['byPath']['path'] / 'definition/model.tmdl').is_file())
        pages = json.loads((report / 'definition/pages/pages.json').read_text(encoding='utf-8-sig'))['pageOrder']
        self.assertEqual(len(pages), 2)
        for page_id in pages:
            folder = report / 'definition/pages' / page_id
            page = json.loads((folder / 'page.json').read_text(encoding='utf-8-sig'))
            for path in folder.glob('visuals/*/visual.json'):
                visual = json.loads(path.read_text(encoding='utf-8-sig'))
                pos = visual['position']
                self.assertGreaterEqual(pos['x'], 0)
                self.assertGreaterEqual(pos['y'], 0)
                self.assertLessEqual(pos['x'] + pos['width'], page['width'])
                self.assertLessEqual(pos['y'] + pos['height'], page['height'])
                for role in visual['visual'].get('query', {}).get('queryState', {}).values():
                    for projection in role['projections']:
                        for kind, field in projection['field'].items():
                            table = field['Expression']['SourceRef']['Entity']
                            self.assertIn(field['Property'], measures[table] if kind == 'Measure' else columns[table])

    def test_shared_dimensions_filter_both_facts_without_fact_to_fact_join(self):
        source = (PROJECT / 'Olist.SemanticModel/definition/relationships.tmdl').read_text(encoding='utf-8-sig')
        facts = {'fact_orders', 'customer_cohorts'}
        relationships = []
        for block in source.split('relationship ')[1:]:
            self.assertNotIn('crossFilteringBehavior: bothDirections', block)
            from_table = re.search(r'fromColumn: ([^.]+)\.', block).group(1)
            to_table = re.search(r'toColumn: ([^.]+)\.', block).group(1)
            self.assertFalse({from_table, to_table}.issubset(facts))
            relationships.append((from_table, to_table))
        for dimension in ['DimMonth', 'DimState', 'DimCategory']:
            self.assertEqual({start for start, end in relationships if end == dimension}, facts)


if __name__ == '__main__':
    unittest.main()
