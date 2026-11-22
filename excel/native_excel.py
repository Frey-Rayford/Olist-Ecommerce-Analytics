"""Native Excel features and checks that cannot be verified by writing XML alone."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
from zipfile import ZipFile
import openpyxl
import pythoncom
import win32com.client


def make_portable(path: Path):
    """Remove Excel's informational last-save folder; the query uses embedded data."""
    temp=path.with_suffix(".portable.xlsx")
    with ZipFile(path) as source, ZipFile(temp,"w") as output:
        for info in source.infolist():
            data=source.read(info.filename)
            if info.filename=="xl/workbook.xml":
                data=re.sub(rb'<mc:AlternateContent\b[^>]*>.*?</mc:AlternateContent>',
                    lambda match: b'' if b'absPath' in match.group() else match.group(),data,flags=re.DOTALL)
            output.writestr(info,data)
    temp.replace(path)


def expected_metrics(fact, month="All", state="All", category="All"):
    selected=fact.copy()
    for column,value in [("purchase_month",month),("customer_state",state),("primary_category",category)]:
        if value != "All":
            selected=selected.loc[selected[column].eq(value)]
    known=int(selected.delivery_status.ne("unknown").sum())
    return {"orders":len(selected),"gmv":float(selected.gmv.sum()) if selected.empty or selected.gmv.notna().any() else None,
            "late_rate":float(selected.delivery_status.eq("late").sum()/known) if known else None,
            "review":float(selected.review_score.mean()) if selected.review_score.notna().any() else None}


def assert_close(actual,expected,label):
    if expected is None:
        assert actual == "—", (label,actual,expected)
    else:
        assert isinstance(actual,(int,float)) and abs(actual-expected) < 0.005, (label,actual,expected)


def finish_workbook(path: Path, fact):
    template=openpyxl.load_workbook(path,read_only=True,data_only=False)
    formulas=[(sheet.title,cell.coordinate,cell.value)
              for sheet in template if sheet.title not in ("Source_Orders","Orders","Lists")
              for row in sheet for cell in row if cell.data_type == "f"]
    template.close()
    excel=win32com.client.DispatchEx("Excel.Application")
    excel.Visible=False
    excel.DisplayAlerts=False
    excel.AskToUpdateLinks=False
    excel.EnableEvents=False
    wb=None
    evidence={"snapshot":"2018-08-31","checks":[],"excel_version":str(excel.Version)}
    try:
        wb=excel.Workbooks.Open(str(path),0,False)
        excel.Calculation=-4135
        ws=wb.Worksheets("Orders")
        ws.Cells.ClearContents()
        wb.Queries.Add("OrdersQuery",path.with_name("orders.pq").read_text(encoding="utf-8"))
        connection='OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location=OrdersQuery;Extended Properties=""'
        lo=ws.ListObjects.Add(0,connection,True,1,ws.Range("A1"))
        lo.Name="tblOrders"
        query=lo.QueryTable
        query.CommandType=2
        query.CommandText="SELECT * FROM [OrdersQuery]"
        query.BackgroundQuery=False
        query.RefreshOnFileOpen=False
        query.AdjustColumnWidth=False
        query.Refresh(False)
        excel.CalculateUntilAsyncQueriesDone()
        assert lo.ListRows.Count == len(fact),lo.ListRows.Count
        lo.TableStyle="TableStyleMedium2"
        ws.Range("B:D").NumberFormat="yyyy-mm-dd"
        ws.Range("G:G").NumberFormat='"R$ "#,##0.00'
        ws.Range("H:H").NumberFormat="0.00"
        evidence["checks"].append({"name":"Power Query refresh", "orders":lo.ListRows.Count,"status":"pass"})
        print("POWER_QUERY_OK",flush=True)

        explore=wb.Worksheets("Explore")
        pc=wb.PivotCaches().Create(1,"tblOrders",6)
        pc.RefreshOnFileOpen=False
        pivots=[]
        for field,cell,name in [("state","B22","pvtStates"),("category","K22","pvtCategories")]:
            p=pc.CreatePivotTable(explore.Range(cell),name)
            p.PivotFields(field).Orientation=1
            p.PivotFields(field).Position=1
            p.AddDataField(p.PivotFields("order_id"),"Orders",-4112).NumberFormat="#,##0"
            p.AddDataField(p.PivotFields("gmv"),"GMV (BRL)",-4157).NumberFormat='"R$ "#,##0'
            p.AddDataField(p.PivotFields("late"),"Late orders",-4157).NumberFormat="#,##0"
            p.AddDataField(p.PivotFields("known_dates"),"Known dates",-4157).NumberFormat="#,##0"
            p.AddDataField(p.PivotFields("review_score"),"Mean review",-4106).NumberFormat="0.00"
            p.AddDataField(p.PivotFields("reviewed"),"Reviewed orders",-4157).NumberFormat="#,##0"
            p.RowAxisLayout(1)
            p.TableStyle2="PivotStyleMedium9"
            p.ShowTableStyleRowStripes=True
            p.PreserveFormatting=True
            p.HasAutoFormat=False
            p.PivotFields(field).AutoSort(2,"Orders")
            pivots.append(p)
        explore.Columns("B:B").ColumnWidth=12
        explore.Columns("C:H").ColumnWidth=16
        explore.Columns("K:K").ColumnWidth=36
        explore.Columns("L:Q").ColumnWidth=16
        explore.PageSetup.PrintArea="B2:Q99"
        explore.PageSetup.FitToPagesWide=1
        explore.PageSetup.FitToPagesTall=2
        slicers={}
        for field,title,top,left,width,columns in [("month","Purchase month",105,18,480,4),("state","Customer state",105,600,430,5)]:
            cache=wb.SlicerCaches.Add(pivots[0],field)
            cache.PivotTables.AddPivotTable(pivots[1])
            slicer=cache.Slicers.Add(explore,pythoncom.Missing,field+"Selector",title,top,left,width,265)
            slicer.Left=explore.Range("B6" if field=="month" else "K6").Left
            slicer.Top=explore.Range("B6").Top
            slicer.Width=width
            slicer.Height=265
            slicer.NumberOfColumns=columns
            slicer.Caption=title
            slicer.Style="SlicerStyleLight1"
            slicer.Shape.Placement=3
            slicers[field]=cache
        explore.Range("B20:Q20").Merge()
        explore.Range("B20").Value="Counts and sums share the same slicers. Late rate = Late orders / Known dates; compare sample sizes before interpreting reviews."
        explore.Range("B20").Font.Color=0x776752
        explore.Range("B20").Font.Size=11
        evidence["checks"].append({"name":"Native PivotTables and shared slicers","pivots":2,"slicers":2,"status":"pass"})
        print("PIVOTS_OK",flush=True)

        dash=wb.Worksheets("Dashboard")
        # tblOrders did not exist when Excel first opened the layout file.
        for sheet,cell,formula in formulas:
            wb.Worksheets(sheet).Range(cell).Formula=formula
        excel.Calculation=-4105
        excel.CalculateFullRebuild()
        scenarios=[("All","All","All"),("All","RJ","All"),("2018-01","SP","All"),
                   ("All","All","health_beauty"),("2016-11","All","All")]
        for month,state,category in scenarios:
            for cell,value in [("C6",month),("G6",state),("K6",category)]:
                dash.Range(cell).Value=value
            excel.CalculateFull()
            expected=expected_metrics(fact,month,state,category)
            actual={metric:dash.Range(cell).Value for metric,cell in [("gmv","B11"),("orders","E11"),("late_rate","H11"),("review","K11")]}
            for metric in expected:
                assert_close(actual[metric],expected[metric],f"{month}/{state}/{category}/{metric}")
            trend_expected=expected_metrics(fact,"All",state,category)
            states_expected=expected_metrics(fact,month,"All",category)
            assert_close(excel.Evaluate("SUM(Monthly!C8:C31)"),trend_expected["orders"],"trend orders")
            assert_close(excel.Evaluate("SUM(Monthly!D8:D31)"),trend_expected["gmv"],"trend GMV")
            assert_close(excel.Evaluate("SUM(States!D8:D34)"),states_expected["orders"],"state orders")
            assert_close(excel.Evaluate("SUM(States!E8:E34)"),states_expected["gmv"],"state GMV")
            evidence["checks"].append({"name":"Dashboard filters and chart scopes","month":month,"state":state,"category":category,"actual":actual,"status":"pass"})
        for cell in ["C6","G6","K6"]:
            dash.Range(cell).Value="All"
        print("FILTERS_OK",flush=True)

        cache=slicers["state"]
        for item in cache.SlicerItems:
            if item.Name != "RJ":
                item.Selected=False
        for p in pivots:
            assert int(p.GetPivotData("Orders").Value)==int(fact.customer_state.eq("RJ").sum())
        evidence["checks"].append({"name":"RJ slicer filters both pivots","orders":int(fact.customer_state.eq("RJ").sum()),"status":"pass"})
        cache.ClearManualFilter()

        # Change a real source value, refresh, then restore it before saving.
        src=wb.Worksheets("Source_Orders")
        initial=float(src.Range("G3").Value)
        original_gmv=float(fact.gmv.sum())
        src.Range("G3").Value=initial+1
        query.Refresh(False)
        pc.Refresh()
        excel.CalculateFull()
        assert_close(dash.Range("B11").Value,original_gmv+1,"refreshed GMV")
        src.Range("G3").Value=initial
        query.Refresh(False)
        pc.Refresh()
        excel.CalculateFullRebuild()
        assert_close(dash.Range("B11").Value,original_gmv,"restored GMV")
        evidence["checks"].append({"name":"Edited source > Power Query > formulas > pivots; source restored","status":"pass"})
        print("REFRESH_ROUNDTRIP_OK",flush=True)

        check=wb.Worksheets("Checks")
        for row in range(8,14):
            expected_status="REVIEW" if row==9 and fact.gmv.isna().any() else "PASS"
            assert check.Range(f"D{row}").Value==expected_status,(row,check.Range(f"D{row}").Value)
        assert check.Range("C9").Value==int(fact.gmv.isna().sum())
        evidence["checks"].append({"name":"Missing payments retained as missing","orders":int(fact.gmv.isna().sum()),"status":"pass"})
        for row in range(19,24):
            assert abs(check.Range(f"E{row}").Value)<0.005,(row,check.Range(f"E{row}").Value)
        for sheet in wb.Worksheets:
            for kind in (2,-4123):
                try:
                    errors=sheet.UsedRange.SpecialCells(kind,16)
                except Exception:
                    continue
                raise AssertionError(f"Excel error cells on {sheet.Name}: {errors.Address}")
        evidence["checks"].append({"name":"Quality checks, Python parity, no Excel error cells","status":"pass"})
        dash.Activate()
        excel.ActiveWindow.DisplayGridlines=False
        excel.ActiveWindow.Zoom=85
        dash.Range("C6").Select()
        wb.CheckCompatibility=False
        wb.Save()
        preview=path.parent/"preview.pdf"
        dash.ExportAsFixedFormat(0,str(preview))
        wb.Close(False)
        wb=None
        make_portable(path)
        # Read-only reopen verifies that query, slicers and formula results persist.
        wb=excel.Workbooks.Open(str(path),0,True)
        assert wb.Queries.Count==1
        assert wb.SlicerCaches.Count==2
        assert int(wb.Worksheets("Dashboard").Range("E11").Value)==len(fact)
        evidence["checks"].append({"name":"Saved .xlsx reopens with cached results, query and slicers","status":"pass"})
        evidence["workbook_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_name("validation.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(f"EXCEL_VALIDATED|{len(evidence['checks'])} checks|{path.stat().st_size} bytes",flush=True)
    finally:
        if wb is not None:
            wb.Close(False)
        excel.Quit()
