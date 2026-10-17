# Writes the Power BI project (PBIP, text format) into powerbi/project. Run: powershell -File make_project.ps1
# Opened and refreshed in Power BI Desktop (Oct 2026): tables, relationships and measures load.
$root = Join-Path $PSScriptRoot 'project'
$data = (Join-Path $PSScriptRoot 'data') + '\'
$sm = Join-Path $root 'Redispatch.SemanticModel'
$rp = Join-Path $root 'Redispatch.Report'
New-Item -ItemType Directory -Force "$sm\definition\tables", $rp | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
function W($path, $text) {
  # lines start with ~ for each tab of indentation
  $t = ($text -split "`r?`n" | ForEach-Object { if ($_ -match '^(~+)(.*)$') { ("`t" * $Matches[1].Length) + $Matches[2] } else { $_ } }) -join "`n"
  [IO.File]::WriteAllText($path, $t + "`n", $utf8)
}
W "$root\Redispatch.pbip" '{"version":"1.0","artifacts":[{"report":{"path":"Redispatch.Report"}}],"settings":{"enableAutoRecovery":true}}'
W "$rp\definition.pbir" '{"version":"1.0","datasetReference":{"byPath":{"path":"../Redispatch.SemanticModel"}}}'
W "$rp\report.json" '{"config":"{\"version\":\"5.55\",\"themeCollection\":{\"baseTheme\":{\"name\":\"CY24SU10\"}}}","layoutOptimization":0,"resourcePackages":[],"sections":[{"config":"{}","displayName":"Overview","displayOption":1,"filters":"[]","height":720,"name":"ReportSection1","visualContainers":[],"width":1280}]}'
W "$sm\definition.pbism" '{"version":"4.0","settings":{}}'
W "$sm\definition\database.tmdl" @'
database Redispatch
~compatibilityLevel: 1600
'@
W "$sm\definition\model.tmdl" @'
model Model
~culture: en-US
~defaultPowerBIDataSourceVersion: powerBI_V3
~discourageImplicitMeasures

ref table dim_month
ref table fact_monthly
ref table fact_operator_monthly
ref expression DataPath
'@
$dp = $data.Replace('"', '""')
W "$sm\definition\expressions.tmdl" @"
expression DataPath = "$dp" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
~lineageTag: 11111111-1111-1111-1111-111111111111
"@
W "$sm\definition\relationships.tmdl" @'
relationship rel_fact_monthly_month
~fromColumn: fact_monthly.month
~toColumn: dim_month.month

relationship rel_fact_operator_month
~fromColumn: fact_operator_monthly.month
~toColumn: dim_month.month
'@
function Part($name, $file, $types) {
@"
~partition $name = m
~~mode: import
~~source =
~~~~let
~~~~~~Source = Csv.Document(File.Contents(DataPath & "$file"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
~~~~~~Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
~~~~~~Typed = Table.TransformColumnTypes(Promoted, $types, "en-US")
~~~~in
~~~~~~Typed
"@
}
W "$sm\definition\tables\dim_month.tmdl" (@'
table dim_month
~lineageTag: 22222222-2222-2222-2222-222222222201
~dataCategory: Time

~column month
~~dataType: dateTime
~~isKey
~~formatString: yyyy-mm
~~lineageTag: 22222222-2222-2222-2222-222222222202
~~summarizeBy: none
~~sourceColumn: month

~column year
~~dataType: int64
~~formatString: 0
~~lineageTag: 22222222-2222-2222-2222-222222222203
~~summarizeBy: none
~~sourceColumn: year

~column month_number
~~dataType: int64
~~formatString: 0
~~lineageTag: 22222222-2222-2222-2222-222222222204
~~summarizeBy: none
~~sourceColumn: month_number

~column month_name
~~dataType: string
~~lineageTag: 22222222-2222-2222-2222-222222222205
~~summarizeBy: none
~~sourceColumn: month_name
~~sortByColumn: month_number

~column year_month
~~dataType: string
~~lineageTag: 22222222-2222-2222-2222-222222222206
~~summarizeBy: none
~~sourceColumn: year_month

'@ + (Part 'dim_month' 'dim_month.csv' '{{"month", type date}, {"year", Int64.Type}, {"month_number", Int64.Type}, {"month_name", type text}, {"year_month", type text}}'))

$m = @'
~measure 'Total Cost (m EUR)' = SUM ( fact_monthly[cost_million_eur] )
~~formatString: #,0.00
~~lineageTag: 33333333-3333-3333-3333-333333333301

~measure 'Total Volume (GWh)' = SUM ( fact_monthly[volume_gwh] )
~~formatString: #,0.00
~~lineageTag: 33333333-3333-3333-3333-333333333302

~measure 'Cost per MWh (EUR)' = DIVIDE ( [Total Cost (m EUR)] * 1000000, [Total Volume (GWh)] * 1000 )
~~formatString: #,0.00
~~lineageTag: 33333333-3333-3333-3333-333333333303

~measure 'Cost 12M Average (m EUR)' =
~~~~AVERAGEX (
~~~~~~DATESINPERIOD ( dim_month[month], MAX ( dim_month[month] ), -12, MONTH ),
~~~~~~CALCULATE ( SUM ( fact_monthly[cost_million_eur] ) )
~~~~)
~~formatString: #,0.00
~~lineageTag: 33333333-3333-3333-3333-333333333304

~measure 'Peak Month Cost (m EUR)' = MAXX ( ALL ( dim_month ), CALCULATE ( SUM ( fact_monthly[cost_million_eur] ) ) )
~~formatString: #,0.00
~~lineageTag: 33333333-3333-3333-3333-333333333305

~measure 'Latest Month Cost (m EUR)' = CALCULATE ( SUM ( fact_monthly[cost_million_eur] ), LASTDATE ( ALL ( dim_month[month] ) ) )
~~formatString: #,0.00
~~lineageTag: 33333333-3333-3333-3333-333333333306

~measure 'Decline From Peak %' = 1 - DIVIDE ( [Latest Month Cost (m EUR)], [Peak Month Cost (m EUR)] )
~~formatString: 0.0%
~~lineageTag: 33333333-3333-3333-3333-333333333307

~measure 'Reductions Share %' = DIVIDE ( SUM ( fact_monthly[reductions_gwh] ), SUM ( fact_monthly[reductions_gwh] ) + SUM ( fact_monthly[increases_gwh] ) )
~~formatString: 0.0%
~~lineageTag: 33333333-3333-3333-3333-333333333308

'@
$cols = @(@('volume_gwh','double'),@('cost_million_eur','double'),@('reductions_gwh','double'),@('increases_gwh','double'),@('conventional_gwh','double'),@('renewable_gwh','double'))
$c = "~column month`n~~dataType: dateTime`n~~formatString: yyyy-mm`n~~lineageTag: 44444444-4444-4444-4444-444444444400`n~~summarizeBy: none`n~~sourceColumn: month`n`n"
$i = 1; foreach ($x in $cols) { $c += "~column $($x[0])`n~~dataType: double`n~~lineageTag: 44444444-4444-4444-4444-44444444440$i`n~~summarizeBy: sum`n~~sourceColumn: $($x[0])`n`n"; $i++ }
W "$sm\definition\tables\fact_monthly.tmdl" ("table fact_monthly`n~lineageTag: 44444444-4444-4444-4444-444444444499`n`n" + $m + $c + (Part 'fact_monthly' 'fact_monthly.csv' '{{"month", type date}, {"volume_gwh", type number}, {"cost_million_eur", type number}, {"reductions_gwh", type number}, {"increases_gwh", type number}, {"conventional_gwh", type number}, {"renewable_gwh", type number}}'))

$o = @'
table fact_operator_monthly
~lineageTag: 55555555-5555-5555-5555-555555555599

~measure 'Operator Energy (GWh)' = DIVIDE ( SUM ( fact_operator_monthly[energy_mwh] ), 1000 )
~~formatString: #,0.00
~~lineageTag: 55555555-5555-5555-5555-555555555501

~measure 'Operator Share %' =
~~~~DIVIDE ( [Operator Energy (GWh)], CALCULATE ( [Operator Energy (GWh)], ALL ( fact_operator_monthly[operator] ) ) )
~~formatString: 0.0%
~~lineageTag: 55555555-5555-5555-5555-555555555502

~column month
~~dataType: dateTime
~~formatString: yyyy-mm
~~lineageTag: 55555555-5555-5555-5555-555555555510
~~summarizeBy: none
~~sourceColumn: month

~column operator
~~dataType: string
~~lineageTag: 55555555-5555-5555-5555-555555555511
~~summarizeBy: none
~~sourceColumn: operator

~column direction
~~dataType: string
~~lineageTag: 55555555-5555-5555-5555-555555555512
~~summarizeBy: none
~~sourceColumn: direction

~column energy_type
~~dataType: string
~~lineageTag: 55555555-5555-5555-5555-555555555513
~~summarizeBy: none
~~sourceColumn: energy_type

~column energy_mwh
~~dataType: double
~~lineageTag: 55555555-5555-5555-5555-555555555514
~~summarizeBy: sum
~~sourceColumn: energy_mwh

'@
W "$sm\definition\tables\fact_operator_monthly.tmdl" ($o + (Part 'fact_operator_monthly' 'fact_operator_monthly.csv' '{{"month", type date}, {"operator", type text}, {"direction", type text}, {"energy_type", type text}, {"energy_mwh", type number}}'))
Write-Host "Project written to $root. Open Redispatch.pbip in Power BI Desktop."
