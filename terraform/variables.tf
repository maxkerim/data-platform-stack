variable "cloud_id" {
  description = "Yandex Cloud ID."
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID."
  type        = string
}

variable "zone" {
  description = "Availability zone containing the subnet."
  type        = string
  default     = "ru-central1-a"
}

variable "subnet_id" {
  description = "Existing subnet ID for the VM. The subnet must have internet egress."
  type        = string
}

variable "ssh_allowed_cidrs" {
  description = "CIDR ranges allowed to connect to SSH. Use your trusted public IP with /32."
  type        = list(string)

  validation {
    condition     = length(var.ssh_allowed_cidrs) > 0
    error_message = "At least one trusted CIDR must be allowed for SSH."
  }
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key installed for the ubuntu user."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "vm_name" {
  description = "Name of the data platform VM."
  type        = string
  default     = "data-platform"
}

variable "image_family" {
  description = "Yandex Compute image family for the VM OS."
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "platform_id" {
  description = "Yandex Compute platform ID."
  type        = string
  default     = "standard-v3"
}

variable "vm_cores" {
  description = "Number of vCPUs."
  type        = number
  default     = 2
}

variable "vm_memory_gb" {
  description = "RAM in GiB."
  type        = number
  default     = 4
}

variable "vm_core_fraction" {
  description = "Guaranteed vCPU performance share."
  type        = number
  default     = 20
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GiB."
  type        = number
  default     = 40
}