"""Check the published XLSX without needing Excel on the CI runner."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
NS={"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def validate(path=ROOT/"excel/Olist_Operations.xlsx"):
    desktop=json.loads((ROOT/"excel/validation.json").read_text(encoding="utf-8"))
    reference=json.loads((ROOT/"reports/delivery_findings.json").read_text(encoding="utf-8"))
    assert all(check["status"]=="pass" for check in desktop["checks"])
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==desktop["workbook_sha256"]
    with ZipFile(path) as z:
        assert z.testzip() is None
        names=z.namelist()
        assert "xl/vbaProject.bin" not in names
        assert not any(name.startswith("xl/externalLinks/") for name in names)
        tables={}
        for name in names:
            if name.startswith("xl/tables/table") and name.endswith(".xml"):
                table=ET.fromstring(z.read(name))
                tables[table.attrib["name"]]=table.attrib["ref"]
        assert {"tblSource","tblOrders","tblRegions"}.issubset(tables)
        for table in ("tblSource","tblOrders"):
            last=int(''.join(c for c in tables[table].split(':')[-1] if c.isdigit()))
            assert last-1==reference["orders"],(table,last)
        pivots=[n for n in names if n.startswith("xl/pivotTables/pivotTable") and n.endswith(".xml")]
        assert len(pivots)==2
        slicers=[n for n in names if n.startswith("xl/slicerCaches/slicerCache") and n.endswith(".xml")]
        assert len(slicers)==2
        connections=z.read("xl/connections.xml")
        assert b"OrdersQuery" in connections and b"Microsoft.Mashup.OleDb.1" in connections
        assert b"absPath" not in z.read("xl/workbook.xml")
        workbook=ET.fromstring(z.read("xl/workbook.xml"))
        rels={r.attrib["Id"]:posixpath.normpath("xl/"+r.attrib["Target"]) for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheets={s.attrib["name"]:rels[s.attrib[REL]] for s in workbook.find("s:sheets",NS)}
        def cells(sheet):
            return {c.attrib["r"]:c for c in ET.fromstring(z.read(sheets[sheet])).findall(".//s:c",NS)}
        dashboard=cells("Dashboard")
        checks=cells("Checks")
        def number(cells,ref):
            return float(cells[ref].find("s:v",NS).text)
        assert number(dashboard,"E11")==reference["orders"]
        assert abs(number(dashboard,"H11")-reference["late_rate"])<1e-12
        assert number(checks,"C21")==reference["late_orders"]
        assert number(checks,"C23")==reference["late_reviewed_orders"]+reference["on_time_reviewed_orders"]
        assert all(abs(number(checks,f"E{row}"))<0.005 for row in range(19,24))
        for cell in ("B11","E11","H11","K11"):
            assert dashboard[cell].find("s:f",NS) is not None
        for sheet,filename in sheets.items():
            with z.open(filename) as stream:
                for _,element in ET.iterparse(stream,events=("end",)):
                    if element.tag==f"{{{NS['s']}}}c":
                        assert element.attrib.get("t")!="e",(sheet,element.attrib.get("r"))
                    element.clear()
    print(f"EXCEL_PACKAGE_OK|orders={reference['orders']}|pivots=2|slicers=2|no_formula_errors")


if __name__=="__main__":
    validate()
