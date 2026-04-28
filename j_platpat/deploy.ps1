#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Deploy j-platpat monitoring Lambda function to AWS (using container image)

.PARAMETER StateBucketName
    S3 bucket name for state management

.PARAMETER SlackWebhookUrl
    Slack Webhook URL for notifications

.PARAMETER AwsRegion
    AWS region (default: ap-northeast-1)

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
    [string]$AwsRegion = "ap-northeast-1"
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
    @{Name = "Docker"; Command = "docker --version"; Required = $true },
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

# Get AWS Account ID
Write-Header "Getting AWS account information..."
try {
    $awsAccountId = aws sts get-caller-identity --query Account --output text
    Write-Host "✓ AWS Account ID: $awsAccountId" -ForegroundColor Green
}
catch {
    Write-Error-Exit "✗ Failed to get AWS account ID: $_"
}

# Terraform setup
Write-Header "Setting up Terraform..."

if (-not (Test-Path "terraform")) {
    New-Item -ItemType Directory -Path "terraform" | Out-Null
}

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

# Terraform apply (creates ECR repo)
Write-Header "Applying Terraform deployment (creating ECR repository)..."
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

# Get ECR repository URL
Write-Header "Building and pushing Docker image..."
Push-Location "terraform"
$ecrRepoUrl = terraform output -raw ecr_repository_url
Pop-Location
Write-Host "ECR Repository URL: $ecrRepoUrl" -ForegroundColor Cyan

# AWS ECR login
Write-Host "Logging in to Amazon ECR..."
$ecrLoginCmd = aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $ecrRepoUrl
if ($LASTEXITCODE -ne 0) {
    Write-Error-Exit "✗ Failed to login to ECR"
}
Write-Host "✓ Successfully logged in to ECR" -ForegroundColor Green

# Build Docker image
Write-Host "Building Docker image..."
docker build -t j-platpat-checker:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Error-Exit "✗ Docker build failed"
}
Write-Host "✓ Docker image built successfully" -ForegroundColor Green

# Tag image for ECR
Write-Host "Tagging image for ECR..."
docker tag j-platpat-checker:latest "$ecrRepoUrl`:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Error-Exit "✗ Failed to tag image"
}
Write-Host "✓ Image tagged successfully" -ForegroundColor Green

# Push image to ECR
Write-Host "Pushing image to ECR..."
docker push "$ecrRepoUrl`:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Error-Exit "✗ Failed to push image to ECR"
}
Write-Host "✓ Image pushed to ECR successfully" -ForegroundColor Green

# Update Lambda function with new image
Write-Header "Updating Lambda function..."
try {
    aws lambda update-function-code `
        --function-name j-platpat-checker `
        --image-uri "$ecrRepoUrl`:latest" `
        --region $AwsRegion | Out-Null
    Write-Host "✓ Lambda function updated with new image" -ForegroundColor Green
}
catch {
    Write-Error-Exit "✗ Failed to update Lambda function: $_"
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
Write-Host "  1. View logs: aws logs tail /aws/lambda/j-platpat-checker --follow --region $AwsRegion"
Write-Host "  2. Manual test: aws lambda invoke --function-name j-platpat-checker --region $AwsRegion response.json"
Write-Host "  3. Monitor: aws events describe-rule --name j-platpat-checker-schedule --region $AwsRegion"
