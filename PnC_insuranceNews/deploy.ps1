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
