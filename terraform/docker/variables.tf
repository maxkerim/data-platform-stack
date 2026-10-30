variable "name_prefix" {
  description = "Prefix for resources created by this local Terraform module."
  type        = string
  default     = "data-platform-iac"
}

variable "nginx_image" {
  description = "Nginx image used for the local provider smoke test."
  type        = string
  default     = "nginx:1.27-alpine"
}

variable "host_port" {
  description = "Loopback-only host port published by the Nginx container."
  type        = number
  default     = 18089

  validation {
    condition     = var.host_port > 0 && var.host_port < 65536
    error_message = "host_port must be between 1 and 65535."
  }
}