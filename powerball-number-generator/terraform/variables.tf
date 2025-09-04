variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "example.com"
}

variable "subdomain" {
  description = "Subdomain for the application"
  type        = string
  default     = "app"
}

variable "container_cpu" {
  description = "CPU units for the container"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory for the container"
  type        = number
  default     = 512
}
