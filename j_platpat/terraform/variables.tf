variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "state_bucket_name" {
  description = "S3 bucket name for state management"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack Webhook URL for notifications"
  type        = string
  sensitive   = true
}

variable "lambda_source_dir" {
  description = "Source directory for Lambda function"
  type        = string
  default     = "./src"
}

variable "lambda_layers" {
  description = "Lambda layer ARNs (for Playwright/Chromium)"
  type        = list(string)
  default     = []
}

variable "subnet_ids" {
  description = "Subnet IDs for Lambda VPC"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for Lambda VPC"
  type        = list(string)
  default     = []
}
