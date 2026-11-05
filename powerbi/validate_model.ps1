param(
    [Parameter(Mandatory=$true)][int]$Port,
    [string]$PowerBiBin = 'C:\Program Files\Microsoft Power BI Desktop\bin',
    [string]$Output = (Join-Path $PSScriptRoot '..\reports\powerbi_validation.json')
)
$ErrorActionPreference = 'Stop'
Add-Type -Path (Join-Path $PowerBiBin 'Microsoft.AnalysisServices.Server.Core.dll')
Add-Type -Path (Join-Path $PowerBiBin 'Microsoft.AnalysisServices.Server.Tabular.dll')
Add-Type -Path (Join-Path $PowerBiBin 'Microsoft.PowerBI.AdomdClient.dll')
$olistExpected = Get-Content (Join-Path $PSScriptRoot '..\reports\delivery_findings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$olistServer = New-Object Microsoft.AnalysisServices.Tabular.Server
function Read-OlistQuery([string]$Query) {
    $olistCommand = $olistConnection.CreateCommand()
    $olistCommand.CommandText = $Query
    $olistReader = $olistCommand.ExecuteReader()
    try {
        while ($olistReader.Read()) {
            $olistRow = [ordered]@{}
            for ($olistColumn=0; $olistColumn -lt $olistReader.FieldCount; $olistColumn++) {
                $olistRow[$olistReader.GetName($olistColumn)] = if ($olistReader.IsDBNull($olistColumn)) { $null } else { $olistReader.GetValue($olistColumn) }
            }
            [pscustomobject]$olistRow
        }
    } finally { $olistReader.Close() }
}
function Assert-OlistNear($Actual,$Expected,[string]$Label) {
    if ($null -eq $Actual -or [Math]::Abs([double]$Actual-[double]$Expected) -gt 0.00000001) { throw "Mismatch for $Label : $Actual versus $Expected" }
}
try {
    $olistServer.Connect("Data Source=localhost:$Port")
    if ($olistServer.Databases.Count -ne 1) { throw 'Expected the engine for one open Olist report.' }
    $olistDatabase = $olistServer.Databases[0]
    if (-not $olistDatabase.Model.Tables.Contains('fact_orders')) { throw 'This port is not the Olist model.' }
    $olistConnection = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Port;Initial Catalog=$($olistDatabase.Name)")
    $olistConnection.Open()
    try {
        $olistTotals = Read-OlistQuery 'EVALUATE ROW("orders", [Delivered Orders], "known_delivery_dates", [Orders With Known Dates], "late_orders", [Late Orders], "late_rate", [Late Delivery Rate], "late_review", [Late Review], "on_time_review", [On Time Review], "late_reviewed_orders", [Late Reviewed Orders], "on_time_reviewed_orders", [On Time Reviewed Orders], "newer_customers_excluded", [Newer Customers Excluded])'
        foreach ($olistMetric in $olistTotals.PSObject.Properties) { Assert-OlistNear $olistMetric.Value $olistExpected.($olistMetric.Name.Trim('[',']')) $olistMetric.Name }
        $olistCohorts = @(Read-OlistQuery 'EVALUATE SUMMARIZECOLUMNS(customer_cohorts[first_delivery_status], "eligible", [Eligible Customers], "repeated", [Repeat Customers 90d], "rate", [Repeat Rate 90d], "lower", [Repeat CI Lower], "upper", [Repeat CI Upper])')
        foreach ($olistRow in $olistCohorts) {
            $olistGroup = $olistExpected.cohorts.($olistRow.'customer_cohorts[first_delivery_status]')
            Assert-OlistNear $olistRow.'[eligible]' $olistGroup.eligible 'eligible customers'
            Assert-OlistNear $olistRow.'[repeated]' $olistGroup.repeated 'repeat customers'
            Assert-OlistNear $olistRow.'[rate]' $olistGroup.repeat_rate 'repeat rate'
            Assert-OlistNear $olistRow.'[lower]' $olistGroup.wilson_95[0] 'Wilson lower'
            Assert-OlistNear $olistRow.'[upper]' $olistGroup.wilson_95[1] 'Wilson upper'
        }
        $olistRj = Read-OlistQuery 'EVALUATE CALCULATETABLE(ROW("orders", [Delivered Orders], "late", [Late Orders], "rate", [Late Delivery Rate]), TREATAS({"RJ"}, DimState[state]))'
        Assert-OlistNear $olistRj.'[orders]' 12338 'RJ orders'
        Assert-OlistNear $olistRj.'[late]' 1483 'RJ late orders'
        Assert-OlistNear $olistRj.'[rate]' (1483.0/12338) 'RJ late rate'
        $olistTiny = Read-OlistQuery 'EVALUATE CALCULATETABLE(ROW("late_trend", [Late Rate Trend], "repeat_trend", [Repeat Rate Trend]), TREATAS({"2016-09"}, DimMonth[month]))'
        if ($null -ne $olistTiny.'[late_trend]' -or $null -ne $olistTiny.'[repeat_trend]') { throw 'Trend threshold should suppress the tiny September 2016 sample.' }
        [ordered]@{verified_date='2026-11-05'; engine='Power BI Desktop local Analysis Services'; snapshot=$olistExpected.snapshot; result='passed'; totals=$olistTotals; cohorts=$olistCohorts; rj_filter=$olistRj; trend_threshold=$olistTiny} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding UTF8
        Write-Output 'POWERBI_DAX_PARITY_OK'
    } finally { $olistConnection.Close() }
} finally { $olistServer.Disconnect() }
