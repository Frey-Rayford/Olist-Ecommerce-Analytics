let
    Source = Excel.CurrentWorkbook(){[Name="tblSource"]}[Content],
    Typed = Table.TransformColumnTypes(Source, {
        {"order_id", type text}, {"purchase_date", type date},
        {"delivered_date", type date}, {"promised_date", type date},
        {"state", type text}, {"category", type text},
        {"gmv", type number}, {"review_score", type number}
    }, "en-US"),
    Clean = Table.TransformColumns(Typed, {
        {"order_id", each if _ = null then "" else Text.Trim(_), type text},
        {"state", each if _ = null or Text.Trim(_) = "" then "unknown" else Text.Upper(Text.Trim(_)), type text},
        {"category", each if _ = null or Text.Trim(_) = "" then "unknown" else Text.Trim(_), type text}
    }),
    BadRows = Table.SelectRows(Clean, each [order_id] = "" or [purchase_date] = null
        or [delivered_date] = null or [delivered_date] < [purchase_date]
        or [delivered_date] > #date(2018, 8, 31)
        or ([gmv] <> null and [gmv] < 0)
        or ([review_score] <> null and ([review_score] < 1 or [review_score] > 5))),
    Checked = if Table.RowCount(BadRows) > 0 then error "Invalid source rows: check IDs, dates, GMV and review scores."
        else if Table.RowCount(Table.Distinct(Clean, {"order_id"})) <> Table.RowCount(Clean)
            then error "Duplicate order_id: each source row must represent one order."
        else Clean,
    Month = Table.AddColumn(Checked, "month", each Date.ToText([purchase_date], "yyyy-MM"), type text),
    Status = Table.AddColumn(Month, "delivery_status", each if [promised_date] = null then "unknown"
        else if [delivered_date] > [promised_date] then "late" else "on_time", type text),
    Known = Table.AddColumn(Status, "known_dates", each if [delivery_status] = "unknown" then 0 else 1, Int64.Type),
    Late = Table.AddColumn(Known, "late", each if [delivery_status] = "late" then 1 else 0, Int64.Type),
    Reviewed = Table.AddColumn(Late, "reviewed", each if [review_score] = null then 0 else 1, Int64.Type),
    ReviewSum = Table.AddColumn(Reviewed, "review_sum", each if [review_score] = null then 0 else [review_score], type number),
    GMVKnown = Table.AddColumn(ReviewSum, "gmv_known", each if [gmv] = null then 0 else 1, Int64.Type)
in
    GMVKnown
