param(
    [Parameter(Mandatory = $true)]
    [string]$StateBucketName
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Install dependencies into src/
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install -r "$ScriptDir\requirements.txt" -t "$ScriptDir\src\" --upgrade --quiet

# 2. Create build dir (Terraform archive_file writes here)
New-Item -ItemType Directory -Force -Path "$ScriptDir\build" | Out-Null

# 3. Terraform deploy
Set-Location "$ScriptDir\terraform"
terraform init -upgrade
terraform apply -auto-approve -var="state_bucket_name=$StateBucketName"

Write-Host "Deploy complete." -ForegroundColor Green
