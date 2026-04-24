param(
    [Parameter(Mandatory = $true)]
    [string]$StateBucketName,

    [Parameter(Mandatory = $true)]
    [string]$SlackWebhookUrl
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Install dependencies into src/
#    lxml has C extensions → must download Linux wheel (Lambda runs on Amazon Linux x86_64)
#    boto3 is pre-installed in the Lambda runtime → skip bundling
Write-Host "Installing Python dependencies (Linux-compatible wheels)..." -ForegroundColor Cyan
python -m pip install lxml `
    --platform manylinux2014_x86_64 `
    --target "$ScriptDir\src\" `
    --only-binary=:all: `
    --python-version 312 `
    --implementation cp `
    --upgrade --quiet

python -m pip install requests `
    --target "$ScriptDir\src\" `
    --upgrade --quiet

# 2. Create build dir (Terraform archive_file writes here)
New-Item -ItemType Directory -Force -Path "$ScriptDir\build" | Out-Null

# 3. Terraform deploy
Set-Location "$ScriptDir\terraform"
terraform init -upgrade
terraform apply -auto-approve `
    -var="state_bucket_name=$StateBucketName" `
    -var="slack_webhook_url=$SlackWebhookUrl"

Write-Host "Deploy complete." -ForegroundColor Green

# ── Smoke test ──────────────────────────────────────────────────────────────
$FunctionName = "fsa-news-checker"
$S3Key        = "FSA/state.json"
$TmpResponse  = "$env:TEMP\lambda_response.json"

Write-Host "`nInvoking Lambda..." -ForegroundColor Cyan
$logResult = aws lambda invoke --function-name $FunctionName --log-type Tail $TmpResponse --query 'LogResult' --output text
if ($logResult) {
    try {
        [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($logResult)) | Write-Host
    } catch {
        Write-Host "[Warning] Could not decode log result" -ForegroundColor Yellow
    }
}
$response = Get-Content $TmpResponse | ConvertFrom-Json
if ($response.statusCode -ne 200) {
    Write-Host "[FAIL] Lambda returned unexpected response:" -ForegroundColor Red
    Get-Content $TmpResponse
    exit 1
}
Write-Host "[OK] Lambda response: statusCode=$($response.statusCode)" -ForegroundColor Green

Write-Host "`nChecking S3 state ($S3Key)..." -ForegroundColor Cyan
$stateJson = aws s3 cp "s3://$StateBucketName/$S3Key" - 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Could not read S3 state: $stateJson" -ForegroundColor Red
    exit 1
}
$state = $stateJson | ConvertFrom-Json
foreach ($site_name in ($state | Get-Member -MemberType NoteProperty).Name) {
    $count = $state.$site_name.Count
    Write-Host "  $site_name : $count 件" -ForegroundColor White
}
Write-Host "[OK] S3 state verified." -ForegroundColor Green
