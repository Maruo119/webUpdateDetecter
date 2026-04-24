variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
  default     = "fsa-news-checker"
}

variable "state_bucket_name" {
  description = "S3 bucket name for storing article state (must be globally unique)"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack Incoming Webhook URL for notifications"
  type        = string
  sensitive   = true
}

variable "schedule_expression" {
  description = "EventBridge schedule expression (default: every hour at :00)"
  type        = string
  default     = "cron(0 * * * ? *)"
}
