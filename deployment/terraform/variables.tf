variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "monitoring"
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "desired_count" {
  description = "Desired count of ECS tasks"
  type        = number
  default     = 1
}

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
}

variable "django_debug" {
  description = "Django DEBUG setting"
  type        = string
  default     = "False"
}

variable "django_allowed_hosts" {
  description = "Django ALLOWED_HOSTS"
  type        = string
  default     = "*"
}

variable "api_token" {
  description = "API Token for authentication"
  type        = string
}