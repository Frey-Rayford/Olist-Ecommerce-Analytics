let
    Source = Csv.Document(File.Contents(DataFolder & "/customer_cohorts.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {
        {"customer_unique_id", type text}, {"first_purchase_at", type datetime},
        {"purchase_month", type text}, {"customer_state", type text},
        {"primary_category", type text}, {"first_delivery_status", type text},
        {"eligible", type logical}, {"repeat_within_window", type logical}
    }, "en-US")
in
    Types
