terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# S3 バケット（状態管理用）
resource "aws_s3_bucket" "j_platpat_state" {
  bucket        = var.state_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "j_platpat_state" {
  bucket = aws_s3_bucket.j_platpat_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "j-platpat-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Lambda 基本実行ポリシー
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda S3 アクセスポリシー
resource "aws_iam_role_policy" "lambda_s3" {
  name = "j-platpat-lambda-s3"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.j_platpat_state.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.j_platpat_state.arn
      }
    ]
  })
}

# Lambda 関数
resource "aws_lambda_function" "j_platpat_checker" {
  function_name = "j-platpat-checker"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler_sync"
  runtime       = "python3.12"
  timeout       = 600
  memory_size   = 1024

  # ファイルロード
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      STATE_BUCKET_NAME  = aws_s3_bucket.j_platpat_state.id
      STATE_KEY          = "j_platpat/state.json"
      SLACK_WEBHOOK_URL  = var.slack_webhook_url
    }
  }

  layers = var.lambda_layers

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }
}

# Lambda パッケージ（ZIP）
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = "${path.module}/.terraform/lambda.zip"
}

# EventBridge ルール
resource "aws_cloudwatch_event_rule" "j_platpat_schedule" {
  name                = "j-platpat-checker-schedule"
  description         = "Trigger j-platpat checker every hour"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "j_platpat_lambda" {
  rule      = aws_cloudwatch_event_rule.j_platpat_schedule.name
  target_id = "j-platpat-checker"
  arn       = aws_lambda_function.j_platpat_checker.arn
}

# Lambda 実行許可（EventBridge）
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.j_platpat_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.j_platpat_schedule.arn
}

# CloudWatch ログ グループ
resource "aws_cloudwatch_log_group" "j_platpat_logs" {
  name              = "/aws/lambda/j-platpat-checker"
  retention_in_days = 7
}

# 出力
output "lambda_function_arn" {
  value       = aws_lambda_function.j_platpat_checker.arn
  description = "ARN of the j-platpat Lambda function"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.j_platpat_state.id
  description = "Name of the S3 bucket for state"
}

output "eventbridge_rule_arn" {
  value       = aws_cloudwatch_event_rule.j_platpat_schedule.arn
  description = "ARN of the EventBridge rule"
}
