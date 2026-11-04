let
    Source = Csv.Document(File.Contents(DataFolder & "/fact_orders.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {
        {"order_id", type text}, {"customer_unique_id", type text},
        {"order_purchase_timestamp", type datetime}, {"purchase_month", type text},
        {"customer_state", type text}, {"primary_category", type text},
        {"delivery_status", type text}, {"delivery_days", type number},
        {"delay_days", type number}, {"review_score", type number}, {"gmv", type number}
    }, "en-US")
in
    Types
