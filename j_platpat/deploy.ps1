#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Deploy j-platpat monitoring Lambda function to AWS

.PARAMETER StateBucketName
    S3 bucket name for state management

.PARAMETER SlackWebhookUrl
    Slack Webhook URL for notifications

.PARAMETER AwsRegion
    AWS region (default: ap-northeast-1)

.PARAMETER TfVarsFile
    Path to Terraform variables file (optional)

.EXAMPLE
    .\deploy.ps1 `
      -StateBucketName "my-j-platpat-state" `
      -SlackWebhookUrl "https://hooks.slack.com/services/..."
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$StateBucketName,

    [Parameter(Mandatory = $true)]
    [string]$SlackWebhookUrl,

    [Parameter(Mandatory = $false)]
    [string]$AwsRegion = "ap-northeast-1",

    [Parameter(Mandatory = $false)]
    [string]$TfVarsFile
)

# Error handling
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Error-Exit {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
    exit 1
}

# Check prerequisites
Write-Header "Checking prerequisites..."

$checks = @(
    @{Name = "Python"; Command = "python --version"; Required = $true },
    @{Name = "Terraform"; Command = "terraform version"; Required = $true },
    @{Name = "AWS CLI"; Command = "aws --version"; Required = $true }
)

foreach ($check in $checks) {
    try {
        $null = Invoke-Expression $check.Command 2>&1
        Write-Host "✓ $($check.Name) is installed" -ForegroundColor Green
    }
    catch {
        if ($check.Required) {
            Write-Error-Exit "✗ $($check.Name) is required but not found"
        }
        else {
            Write-Host "⚠ $($check.Name) is not found (optional)" -ForegroundColor Yellow
        }
    }
}

# Install Python dependencies
Write-Header "Installing Python dependencies..."

$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python version: $pythonVersion"

# Create virtual environment (optional, but recommended)
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# Activate virtual environment
if ($PSVersionTable.Platform -eq "Win32NT" -or $PSVersionTable.OS -like "*Windows*" -or -not $PSVersionTable.Platform) {
    & ".\venv\Scripts\Activate.ps1"
}
else {
    & "source ./venv/bin/activate"
}

# Install dependencies
Write-Host "Installing requirements..."
pip install -r requirements.txt

# Playwright browsers
Write-Host "Installing Playwright browsers..."
python -m playwright install chromium

# Prepare Lambda package
Write-Header "Preparing Lambda deployment package..."

$lambdaDir = ".\src"
$packageDir = ".\.terraform\lambda_package"

if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}

New-Item -ItemType Directory -Path $packageDir | Out-Null

# Copy source files
Copy-Item "$lambdaDir\*" $packageDir -Recurse -Exclude @("__pycache__", "*.pyc")

# Install dependencies into package
pip install -r requirements.txt -t "$packageDir" --platform manylinux2014_x86_64 --python-version 312 --only-binary=:all: --force-reinstall

# Verify package
if (-not (Test-Path "$packageDir\lambda_function.py")) {
    Write-Error-Exit "✗ Lambda function file not found in package"
}
Write-Host "✓ Lambda package prepared" -ForegroundColor Green

# Terraform setup
Write-Header "Setting up Terraform..."

if (-not (Test-Path "terraform")) {
    New-Item -ItemType Directory -Path "terraform" | Out-Null
}

# Copy Terraform files
if (Test-Path "main.tf") {
    Copy-Item "main.tf" "terraform\" -Force
} else {
    Write-Host "⚠ main.tf not found (will be created)" -ForegroundColor Yellow
}

if (Test-Path "variables.tf") {
    Copy-Item "variables.tf" "terraform\" -Force
} else {
    Write-Host "⚠ variables.tf not found (will be created)" -ForegroundColor Yellow
}

# Prepare terraform.tfvars
$tfvarsPath = "terraform\terraform.tfvars"
$tfvarsContent = @"
region              = "$AwsRegion"
state_bucket_name   = "$StateBucketName"
slack_webhook_url   = "$SlackWebhookUrl"
lambda_source_dir   = "../.terraform/lambda_package"
"@

Set-Content -Path $tfvarsPath -Value $tfvarsContent -Encoding UTF8
Write-Host "✓ terraform.tfvars created" -ForegroundColor Green

# Terraform init
Write-Header "Initializing Terraform..."
Push-Location "terraform"
try {
    terraform init
}
catch {
    Write-Error-Exit "✗ Terraform initialization failed: $_"
}
finally {
    Pop-Location
}

# Terraform plan
Write-Header "Planning Terraform deployment..."
Push-Location "terraform"
try {
    terraform plan -out=tfplan
}
catch {
    Write-Error-Exit "✗ Terraform plan failed: $_"
}
finally {
    Pop-Location
}

# Terraform apply
Write-Header "Applying Terraform deployment..."
$confirmation = Read-Host "Do you want to apply this Terraform plan? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

Push-Location "terraform"
try {
    terraform apply tfplan
    Write-Host "✓ Terraform deployment successful" -ForegroundColor Green
}
catch {
    Write-Error-Exit "✗ Terraform apply failed: $_"
}
finally {
    Pop-Location
}

# Verify Lambda function
Write-Header "Verifying Lambda function..."
try {
    $lambdaInfo = aws lambda get-function --function-name "j-platpat-checker" --region $AwsRegion 2>&1
    Write-Host "✓ Lambda function is deployed" -ForegroundColor Green
    Write-Host "  Function ARN: $($lambdaInfo.Configuration.FunctionArn)" -ForegroundColor Cyan
}
catch {
    Write-Error-Exit "✗ Failed to verify Lambda function: $_"
}

Write-Header "Deployment complete!"
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. View logs: aws logs tail /aws/lambda/j-platpat-checker --follow"
Write-Host "  2. Manual test: aws lambda invoke --function-name j-platpat-checker response.json"
Write-Host "  3. Monitor: aws events describe-rule --name j-platpat-checker-schedule"
