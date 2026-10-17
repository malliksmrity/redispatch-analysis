# Copies powerbi/project to powerbi/project_with_report and writes a report page with cards and two charts.
# Run: powershell -File make_report_visuals.ps1   (after make_project.ps1)
$src = Join-Path $PSScriptRoot 'project'
$dst = Join-Path $PSScriptRoot 'project_with_report'
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Copy-Item $src $dst -Recurse
$utf8 = New-Object System.Text.UTF8Encoding($false)

function SelMeasure($entity, $prop) { @{ Measure = @{ Expression = @{ SourceRef = @{ Source = $entity } }; Property = $prop }; Name = "$entity.$prop" } }
function SelColumn($entity, $prop) { @{ Column = @{ Expression = @{ SourceRef = @{ Source = $entity } }; Property = $prop }; Name = "$entity.$prop" } }
function Container($name, $type, $x, $y, $w, $h, $entities, $select, $projections) {
  $from = @($entities | Select-Object -Unique | ForEach-Object { @{ Name = $_; Entity = $_; Type = 0 } })
  $single = [ordered]@{ visualType = $type; projections = $projections; prototypeQuery = @{ Version = 2; From = $from; Select = $select } }
  $cfg = [ordered]@{ name = $name; layouts = @(@{ id = 0; position = @{ x = $x; y = $y; z = 0; width = $w; height = $h } }); singleVisual = $single }
  [ordered]@{ config = ($cfg | ConvertTo-Json -Depth 20 -Compress); filters = '[]'; height = $h; width = $w; x = $x; y = $y; z = 0 }
}
function Card($name, $x, $y, $entity, $measure) {
  Container $name 'card' $x $y 230 90 @($entity) @(SelMeasure $entity $measure) @{ Values = @(@{ queryRef = "$entity.$measure" }) }
}
$vcs = @()
$vcs += Card 'c1' 20 20 'fact_monthly' 'Total Cost (m EUR)'
$vcs += Card 'c2' 270 20 'fact_monthly' 'Total Volume (GWh)'
$vcs += Card 'c3' 520 20 'fact_monthly' 'Cost per MWh (EUR)'
$vcs += Card 'c4' 770 20 'fact_monthly' 'Decline From Peak %'
$vcs += Card 'c5' 1020 20 'fact_operator_monthly' 'Operator Energy (GWh)'
# line chart: total cost by month
$line = Container 'l1' 'lineChart' 20 130 620 290 @('fact_monthly','dim_month') @((SelColumn 'dim_month' 'year_month'), (SelMeasure 'fact_monthly' 'Total Cost (m EUR)')) @{ Category = @(@{ queryRef = 'dim_month.year_month'; active = $true }); Y = @(@{ queryRef = 'fact_monthly.Total Cost (m EUR)' }) }
$vcs += $line
# column chart: operator share
$col = Container 'b1' 'clusteredColumnChart' 660 130 600 290 @('fact_operator_monthly') @((SelColumn 'fact_operator_monthly' 'operator'), (SelMeasure 'fact_operator_monthly' 'Operator Share %')) @{ Category = @(@{ queryRef = 'fact_operator_monthly.operator'; active = $true }); Y = @(@{ queryRef = 'fact_operator_monthly.Operator Share %' }) }
$vcs += $col
$report = [ordered]@{
  config = '{"version":"5.55","themeCollection":{"baseTheme":{"name":"CY24SU10"}}}'
  layoutOptimization = 0; resourcePackages = @()
  sections = @([ordered]@{ config = '{}'; displayName = 'Overview'; displayOption = 1; filters = '[]'; height = 440; name = 'ReportSection1'; visualContainers = $vcs; width = 1280 })
}
[IO.File]::WriteAllText((Join-Path $dst 'Redispatch.Report\report.json'), ($report | ConvertTo-Json -Depth 30), $utf8)
Write-Host "Written. Open $dst\Redispatch.pbip in Power BI Desktop."
