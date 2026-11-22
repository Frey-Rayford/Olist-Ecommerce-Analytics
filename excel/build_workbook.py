"""Build the report, then let desktop Excel load Power Query and create pivots."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
import xlsxwriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.delivery_analysis import build_facts

INK = "#183849"
TEAL = "#147D80"
PALE = "#EAF4F2"
AMBER = "#AA5B17"
BG = "#F3F6F8"
MUTED = "#526777"
MONEY = '"R$ "#,##0.00;[Red]("R$ "#,##0.00);"R$ 0.00"'
SOURCE_COLS = ["order_id", "purchase_date", "delivered_date", "promised_date", "state", "category", "gmv", "review_score"]


def get_data(processed: Path):
    fact, _ = build_facts(processed)
    source = fact.rename(columns={"order_purchase_timestamp": "purchase_date", "order_delivered_customer_date": "delivered_date",
                                 "order_estimated_delivery_date": "promised_date", "customer_state": "state", "primary_category": "category"})[SOURCE_COLS].copy()
    for col in SOURCE_COLS[1:4]:
        source[col] = source[col].dt.normalize()
    source = source.sort_values(["purchase_date", "order_id"]).reset_index(drop=True)
    return fact, source


def criteria(month=True, state=True, category=True):
    parts = []
    for enabled, field, cell in [(month, "month", "$C$6"), (state, "state", "$G$6"), (category, "category", "$K$6")]:
        if enabled:
            parts.extend([f"tblOrders[{field}]", f'IF(Dashboard!{cell}="All","*",Dashboard!{cell})'])
    return ",".join(parts)


def sums(column, crit):
    return f'SUMIFS(tblOrders[{column}],{crit})' if crit else f'SUM(tblOrders[{column}])'


def counts(crit):
    return f'COUNTIFS({crit})'


def add_layout(wb, name, title, subtitle, formats, cols=14):
    ws = wb.add_worksheet(name)
    ws.hide_gridlines(2)
    ws.set_default_row(21)
    ws.set_column(0, 0, 3)
    ws.set_column(1, cols - 1, 11)
    ws.merge_range(1, 1, 2, cols - 1, title, formats["title"])
    ws.merge_range(3, 1, 3, cols - 1, subtitle, formats["sub"])
    ws.freeze_panes(6, 1)
    ws.set_tab_color(TEAL)
    ws.set_landscape()
    ws.set_paper(8)
    ws.fit_to_pages(1, 1)
    ws.set_margins(0.25, 0.25, 0.3, 0.3)
    ws.set_footer('&LOlist · Historical data&C&P / &N&RVu Thanh Phong')
    return ws


def build_base(output, source):
    wb = xlsxwriter.Workbook(output)
    wb.set_properties({"title": "Olist | Sales & Delivery", "author": "Vu Thanh Phong", "comments": "Historical snapshot through 31 Aug 2018. Data: Olist / Kaggle."})
    wb.formats[0].set_font_name("Calibri")
    wb.formats[0].set_font_size(11)
    fmt = {
        "title": wb.add_format({"font_size": 27, "bold": True, "font_color": INK, "valign": "vcenter"}),
        "sub": wb.add_format({"font_size": 11, "font_color": MUTED}),
        "section": wb.add_format({"bold": True, "font_size": 13, "font_color": INK, "bottom": 1, "bottom_color": "#D7E1E7"}),
        "body": wb.add_format({"text_wrap": True, "valign": "top", "font_color": INK, "font_size": 12}),
        "header": wb.add_format({"bold": True, "font_color": "white", "bg_color": INK, "text_wrap": True, "valign": "vcenter"}),
        "input": wb.add_format({"bg_color": PALE, "font_color": TEAL, "bold": True, "border": 1, "border_color": "#91BEB7", "valign": "vcenter"}),
        "label": wb.add_format({"font_color": MUTED, "bold": True}),
        "num": wb.add_format({"num_format": "#,##0", "font_color": INK}),
        "money": wb.add_format({"num_format": MONEY, "font_color": INK}),
        "pct": wb.add_format({"num_format": "0.00%", "font_color": INK}),
        "dec": wb.add_format({"num_format": "0.00", "font_color": INK}),
        "date": wb.add_format({"num_format": "yyyy-mm-dd"}),
        "link": wb.add_format({"font_color": TEAL, "underline": 1}),
    }
    start = add_layout(wb, "Start", "Olist / Excel operations report", "Vu Thanh Phong · Sales and delivery · Snapshot: 31 Aug 2018", fmt)
    dash = add_layout(wb, "Dashboard", "Sales & delivery, in one view", "Olist / 96,411 delivered orders in the original snapshot · BRL · through 31 Aug 2018", fmt)
    monthly = add_layout(wb, "Monthly", "Monthly performance", "Follows Dashboard state and category; the month selector is deliberately ignored for the trend.", fmt)
    states = add_layout(wb, "States", "Where are deliveries falling behind?", "Follows Dashboard month and category; compares all states regardless of the Dashboard state selector.", fmt)
    pivot = add_layout(wb, "Explore", "Explore with PivotTables", "Month and state slicers control BOTH PivotTables here. Dashboard selectors are separate.", fmt, 17)
    checks = add_layout(wb, "Checks", "Reconcile before reporting", "Whole-workbook checks, independent of filters. Baselines describe the original snapshot only.", fmt)
    orders = wb.add_worksheet("Orders")
    raw = wb.add_worksheet("Source_Orders")
    lists = wb.add_worksheet("Lists")

    for ws in (orders, raw):
        ws.hide_gridlines(2)
        ws.freeze_panes(1, 1)
        ws.set_column("A:A", 35)
        ws.set_column("B:D", 13, fmt["date"])
        ws.set_column("E:E", 9)
        ws.set_column("F:F", 30)
        ws.set_column("G:G", 16, fmt["money"])
        ws.set_column("H:H", 12, fmt["dec"])
        ws.set_column("I:Q", 15)
        ws.set_tab_color("#8095A0")
    rows = []
    for record in source.itertuples(index=False, name=None):
        rows.append([None if pd.isna(v) else v.to_pydatetime() if isinstance(v, pd.Timestamp) else v for v in record])
    raw.add_table(0, 0, len(rows), 7, {"name": "tblSource", "style": "Table Style Medium 2", "data": rows,
        "columns": [{"header": name, **({"format": fmt["date"]} if name.endswith("date") else {})} for name in SOURCE_COLS]})
    raw.write_comment("A1", "One row per delivered order, exported from the existing Python pipeline. Do not paste item-level rows here.")
    # Desktop Excel adds the query-backed tblOrders after this file is closed.
    orders.write("A1", "Power Query output is created by native_excel.py")

    months = pd.period_range("2016-09", "2018-08", freq="M").astype(str).tolist()
    state_codes = sorted(source.state.unique())
    categories = sorted(source.category.unique())
    for col, values, name in [(0, ["All"] + months, "MonthChoices"), (1, ["All"] + state_codes, "StateChoices"), (2, ["All"] + categories, "CategoryChoices")]:
        lists.write_column(0, col, values)
        letter = chr(65 + col)
        wb.define_name(name, f"=Lists!${letter}$1:${letter}${len(values)}")
    region_map = {"AC":"North", "AL":"Northeast", "AP":"North", "AM":"North", "BA":"Northeast", "CE":"Northeast", "DF":"Central-West", "ES":"Southeast", "GO":"Central-West", "MA":"Northeast", "MT":"Central-West", "MS":"Central-West", "MG":"Southeast", "PA":"North", "PB":"Northeast", "PR":"South", "PE":"Northeast", "PI":"Northeast", "RJ":"Southeast", "RN":"Northeast", "RS":"South", "RO":"North", "RR":"North", "SC":"South", "SP":"Southeast", "SE":"Northeast", "TO":"North"}
    lists.add_table(0, 4, len(region_map), 5, {"name": "tblRegions", "style": "Table Style Medium 2", "columns": [{"header":"state"},{"header":"region"}], "data": list(sorted(region_map.items()))})
    lists.set_column("A:F", 24)
    lists.hide_gridlines(2)

    sections = [
        (6, "01 / Open and use", "Open Dashboard and choose a month, state or primary category in the green cells. Cached data is included: no API, Python or SQL Server is needed to explore this file."),
        (11, "02 / Explore the detail", "Monthly and States contain visible SUMIFS / COUNTIFS formulas. Explore has two native PivotTables with shared slicers. Orders contains the clean, query-backed table; Source_Orders contains the editable input."),
        (16, "03 / Refresh safely", "In Source_Orders, replace the rows inside tblSource (keep its eight headers). Data > Queries & Connections > OrdersQuery > Refresh. Wait for completion, then right-click a PivotTable on Explore > Refresh. Check the Checks sheet before reporting. Refresh is manual; the file contains no macros."),
        (22, "04 / Read the numbers correctly", "GMV is payment value including freight, not profit. Late means delivery calendar date after the promised date. Missing reviews are excluded from averages. Category is the largest product-value category in each order: this allocates the WHOLE order GMV to one primary category."),
        (28, "05 / Scope and limitations", "Only delivered orders observed by 31 Aug 2018 are included. This is a historical snapshot, not current Olist performance. Partial months and small samples can distort comparisons. Review differences are associations, not proof of causality. This workbook does not estimate repeat purchase."),
        (34, "06 / Source and permissions", "Brazilian E-Commerce Public Dataset by Olist, published on Kaggle by Olist and collaborators. Source data and this derived data workbook: CC BY-NC-SA 4.0. Reusable build code: MIT. See the repository documentation for definitions and validation evidence."),
    ]
    for row, title, body in sections:
        start.merge_range(row, 1, row, 13, title, fmt["section"])
        start.merge_range(row+1, 1, row+3, 13, body, fmt["body"])
    start.write_url("B40", "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce", fmt["link"], "Olist dataset / Kaggle")
    start.write_url("H40", "https://creativecommons.org/licenses/by-nc-sa/4.0/", fmt["link"], "Data license / CC BY-NC-SA 4.0")
    start.print_area("B2:N42")

    for label, cell, span, choices in [("MONTH", "B5", "C6:E6", "MonthChoices"), ("STATE", "F5", "G6:I6", "StateChoices"), ("PRIMARY CATEGORY", "J5", "K6:N6", "CategoryChoices")]:
        dash.write(cell, label, fmt["label"])
        dash.merge_range(span, "All", fmt["input"])
        dash.data_validation(span.split(":")[0], {"validate": "list", "source": f"={choices}", "error_type":"stop", "error_title":"Choose a listed value", "error_message":"Use the dropdown, or choose All."})
    dash.set_row(5, 28)
    crit = criteria()
    n = counts(crit)
    known = sums("known_dates", crit)
    late = sums("late", crit)
    reviewed = sums("reviewed", crit)
    dash.merge_range("B8:N8", '=IF(COUNTIF(Checks!D8:D13,"FAIL")>0,"CHECK SOURCE / Refresh or data validation needs attention",IF('+n+'=0,"NO ORDERS / Choose another filter combination","FILTERED VIEW / Month, state and primary category"))', fmt["sub"])
    kpis = [("B10:D10", "B11:D12", "DELIVERED GMV", '=IF(AND('+n+'>0,'+sums("gmv_known",crit)+'=0),"—",'+sums("gmv",crit)+')', '"R$ "#,##0', TEAL),
            ("E10:G10", "E11:G12", "DELIVERED ORDERS", "="+n, '#,##0', INK),
            ("H10:J10", "H11:J12", "LATE DELIVERY RATE", '=IFERROR('+late+'/'+known+',"—")', '0.00%', AMBER),
            ("K10:N10", "K11:N12", "MEAN REVIEW / 5", '=IFERROR('+sums("review_sum",crit)+'/'+reviewed+',"—")', '0.00', INK)]
    for labelarea, valuearea, label, formula, numformat, color in kpis:
        dash.merge_range(labelarea, label, wb.add_format({"bold":True,"font_color":MUTED,"bg_color":BG,"indent":1}))
        dash.merge_range(valuearea, formula, wb.add_format({"font_size":27,"bold":True,"font_color":color,"bg_color":BG,"valign":"vcenter","num_format":numformat,"indent":1}))
    dash.merge_range("B14:G14", '="Late orders: "&TEXT('+late+',"#,##0")&" / "&TEXT('+known+',"#,##0")&" known-date orders"', fmt["sub"])
    dash.merge_range("H14:N14", '="Reviewed orders: "&TEXT('+reviewed+',"#,##0")&" / "&TEXT('+n+',"#,##0")', fmt["sub"])
    dash.merge_range("B15:N15", '="GMV coverage: "&TEXT('+sums("gmv_known",crit)+',"#,##0")&" orders with payments; "&TEXT('+n+'-'+sums("gmv_known",crit)+',"#,##0")&" missing payment value(s), excluded from GMV."', fmt["sub"])
    for status, area in [("late","B16:G16"),("on_time","H16:N16")]:
        c = crit + f',tblOrders[delivery_status],"{status}"'
        label = "Late-order review" if status == "late" else "On-time review"
        dash.merge_range(area, f'="{label}: "&IFERROR(TEXT({sums("review_sum",c)}/{sums("reviewed",c)},"0.00"),"—")&" / 5  ·  n="&TEXT({sums("reviewed",c)},"#,##0")', fmt["label"])
    dash.merge_range("B18:N18", "DELIVERED GMV / monthly trend for the selected state and category; month selection does not restrict this chart", fmt["sub"])
    dash.merge_range("B33:N33", "LATE ORDERS / ten states with the largest counts; selected month and category, all states", fmt["sub"])
    dash.merge_range("B48:N49", "Read rates with their denominators. Category means primary category of the order, not item-level category sales.\nData ends in 2018. The report describes associations, not causes; no profit or savings estimate is included.", fmt["body"])
    dash.set_zoom(85)
    dash.set_portrait()
    dash.print_area("B2:N49")

    headers = ["Month", "Orders", "GMV (BRL)", "Late orders", "Known dates", "Late rate", "Reviewed", "Mean review", "GMV MoM", "Sample note"]
    monthly.write_row("B7", headers, fmt["header"])
    monthly.set_row(6, 32)
    monthly.set_column("B:B", 12)
    monthly.set_column("D:D", 20)
    monthly.set_column("E:J", 14)
    monthly.set_column("K:K",24)
    for idx, month in enumerate(months, 8):
        monthly.write(f"B{idx}", month)
        c = criteria(month=False)+f',tblOrders[month],B{idx}'
        formulas = ["="+counts(c), '=IF(AND('+counts(c)+'>0,'+sums("gmv_known",c)+'=0),"—",'+sums("gmv",c)+')', "="+sums("late", c), "="+sums("known_dates",c),
                    f'=IFERROR(E{idx}/F{idx},"—")', "="+sums("reviewed",c), f'=IFERROR({sums("review_sum",c)}/H{idx},"—")',
                    '="—"' if idx == 8 else f'=IF(OR(C{idx}<200,C{idx-1}<200),"—",IFERROR(D{idx}/D{idx-1}-1,"—"))']
        for col, formula in enumerate(formulas, 2):
            monthly.write_formula(idx-1, col, formula, fmt["money" if col==3 else "pct" if col in (6,9) else "dec" if col==8 else "num"])
        monthly.write_formula(f"K{idx}",f'=IF(C{idx}=0,"No orders",IF(C{idx}<200,"Small sample (<200)",""))')
    monthly.conditional_format("G8:G31", {"type":"3_color_scale", "min_color":"#EAF4F2", "mid_color":"#FFFFFF", "max_color":"#F3D1B5"})
    monthly.merge_range("B34:N35", "MoM is shown only when both months have at least 200 orders and prior GMV is positive; this is a reporting guard, not a significance test. Zero-order months remain visible. The cutoff includes only deliveries observed by 31 Aug 2018.", fmt["body"])
    monthly.print_area("B2:N35")

    states.write_row("B7", ["State", "Region", "Orders", "GMV (BRL)", "Late orders", "Known dates", "Late rate", "Reviewed", "Mean review", "Sample note", "Rank"], fmt["header"])
    states.set_row(6, 32)
    states.set_column("C:C", 17)
    states.set_column("E:E", 20)
    states.set_column("K:K", 24)
    for idx, state in enumerate(state_codes, 8):
        states.write(f"B{idx}", state)
        states.write_formula(f"C{idx}", f'=IFERROR(INDEX(tblRegions[region],MATCH(B{idx},tblRegions[state],0)),"Unknown")')
        c = criteria(state=False)+f',tblOrders[state],B{idx}'
        for col, formula in [(3, "="+counts(c)), (4, '=IF(AND('+counts(c)+'>0,'+sums("gmv_known",c)+'=0),"—",'+sums("gmv",c)+')'), (5, "="+sums("late",c)), (6,"="+sums("known_dates",c)),
                             (7,f'=IFERROR(F{idx}/G{idx},"—")'),(8,"="+sums("reviewed",c)),(9,f'=IFERROR({sums("review_sum",c)}/I{idx},"—")'),
                             (10,f'=IF(G{idx}=0,"No known dates",IF(G{idx}<200,"Small sample (<200)",""))'),
                             (11,f'=RANK(F{idx},$F$8:$F${7+len(state_codes)},0)+COUNTIF($F$8:F{idx},F{idx})-1')]:
            states.write_formula(idx-1,col,formula,fmt["money" if col==4 else "pct" if col==7 else "dec" if col==9 else "num"])
    states.conditional_format(f"F8:F{7+len(state_codes)}", {"type":"data_bar", "bar_color":TEAL})
    states.merge_range("B37:N38", "The 200-order note is a descriptive caution, not a statistical significance test. Rank is by late-order count; ties follow state code. Region is a lookup from Lists using INDEX/MATCH.", fmt["body"])
    states.print_area("B2:N38")

    # Chart sources stay visible on their own sheet rather than hiding calculations.
    states.write_row("P7", ["Top state", "Late orders"], fmt["header"])
    for idx in range(8,18):
        states.write_formula(f"P{idx}", f'=INDEX($B$8:$B$34,MATCH({idx-7},$L$8:$L$34,0))')
        states.write_formula(f"Q{idx}", f'=INDEX($F$8:$F$34,MATCH({idx-7},$L$8:$L$34,0))',fmt["num"])
    trend=wb.add_chart({"type":"column"})
    trend.add_series({"name":"Delivered GMV", "categories":"=Monthly!$B$8:$B$31", "values":"=Monthly!$D$8:$D$31", "fill":{"color":TEAL},"border":{"none":True}})
    trend.set_y_axis({"name":"BRL", "num_format":'0.0,,"M"', "major_gridlines":{"visible":True,"line":{"color":"#E3EAEE"}},"min":0})
    trend.set_x_axis({"num_font":{"rotation":-45,"size":9}})
    bar=wb.add_chart({"type":"bar"})
    bar.add_series({"name":"Late orders", "categories":"=States!$P$8:$P$17", "values":"=States!$Q$8:$Q$17", "fill":{"color":AMBER},"border":{"none":True},"data_labels":{"value":True,"position":"outside_end","num_font":{"size":10}}})
    bar.set_y_axis({"reverse":True})
    bar.set_x_axis({"min":0,"major_gridlines":{"visible":True,"line":{"color":"#E3EAEE"}}})
    for chart in (trend,bar):
        chart.set_legend({"none":True})
        chart.set_chartarea({"border":{"none":True},"fill":{"color":"white"}})
        chart.set_plotarea({"border":{"none":True}})
        chart.set_size({"width":1030,"height":290})
        chart.set_style(10)
    dash.insert_chart("B19",trend)
    dash.insert_chart("B34",bar)

    checks.write_row("B7", ["Check", "Actual", "Status", "Meaning"], fmt["header"])
    checks.set_column("B:B", 40)
    checks.set_column("C:C", 20)
    checks.set_column("D:D", 16)
    checks.set_column("E:E", 65)
    quality = [
        ("Source / query row difference", '=ROWS(tblSource[order_id])-ROWS(tblOrders[order_id])', '=IF(C8=0,"PASS","FAIL")', "Refresh OrdersQuery after replacing source rows."),
        ("Missing GMV", '=ROWS(tblOrders[order_id])-SUM(tblOrders[gmv_known])', '=IF(C9=0,"PASS","REVIEW")', "One missing payment in the original snapshot; excluded from GMV, retained in order counts."),
        ("Missing promised dates", '=ROWS(tblOrders[order_id])-SUM(tblOrders[known_dates])', '=IF(C10=0,"PASS","REVIEW")', "Excluded from the late-rate denominator."),
        ("Source / query GMV difference", '=SUM(tblSource[gmv])-SUM(tblOrders[gmv])', '=IF(ABS(C11)<0.005,"PASS","FAIL")', "Catches an unrefreshed GMV edit; other edits still require manual refresh."),
        ("Query rows / pivot orders", '=ROWS(tblOrders[order_id])-GETPIVOTDATA("Orders",Explore!B22)', '=IF(C12=0,"PASS","REVIEW")', "Clear Explore slicers and refresh pivots before comparing totals."),
        ("Late orders exceeding known dates", '=MAX(0,SUM(tblOrders[late])-SUM(tblOrders[known_dates]))', '=IF(C13=0,"PASS","FAIL")', "Late orders cannot exceed known-date orders."),
    ]
    for row, values in enumerate(quality,8):
        checks.write(f"B{row}", values[0])
        checks.write_formula(f"C{row}",values[1],fmt["dec"])
        checks.write_formula(f"D{row}",values[2])
        checks.write(f"E{row}",values[3],fmt["body"])
        checks.set_row(row-1,34)
    checks.merge_range("B16:E16", "Original snapshot / these baselines should change if you intentionally replace the source",fmt["section"])
    checks.write_row("B18",["Metric", "Workbook", "Python baseline", "Difference"],fmt["header"])
    metricrows=[("Delivered orders",'=ROWS(tblOrders[order_id])',len(source)),
                ("Delivered GMV",'=SUM(tblOrders[gmv])',float(source.gmv.sum())),
                ("Late orders",'=SUM(tblOrders[late])',int((source.delivered_date>source.promised_date).sum())),
                ("Known-date orders",'=SUM(tblOrders[known_dates])',int(source.promised_date.notna().sum())),
                ("Reviewed orders",'=SUM(tblOrders[reviewed])',int(source.review_score.notna().sum()))]
    for row,(label,formula,baseline) in enumerate(metricrows,19):
        checks.write(f"B{row}",label)
        checks.write_formula(f"C{row}",formula,fmt["dec"])
        checks.write_number(f"D{row}",baseline,fmt["dec"])
        checks.write_formula(f"E{row}",f'=C{row}-D{row}',fmt["dec"])
    checks.merge_range("B26:E28", "Power Query rejects duplicate IDs and invalid source values rather than dropping them. A refresh error leaves the last successful output in place: resolve it before using the report. Missing reviews are allowed. Averages use reviewed orders only.", fmt["body"])
    checks.conditional_format("D8:D13", {"type":"text","criteria":"containing","value":"FAIL","format":wb.add_format({"bg_color":"#FBE6E2","font_color":"#9A3324"})})
    checks.print_area("B2:E28")
    pivot.freeze_panes(21,1)
    dash.activate()
    dash.set_first_sheet()
    wb.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--processed",type=Path,default=ROOT/"data/processed")
    parser.add_argument("--output",type=Path,default=ROOT/"excel/Olist_Operations.xlsx")
    args=parser.parse_args()
    fact,source=get_data(args.processed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    build_base(args.output,source)
    print(f"BASE_WORKBOOK_OK|orders={len(source)}",flush=True)
    from native_excel import finish_workbook
    finish_workbook(args.output.resolve(), fact)


if __name__ == "__main__":
    main()
