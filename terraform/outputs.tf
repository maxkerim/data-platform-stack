output "vm_public_ip" {
  description = "Public IP address of the VM."
  value       = yandex_compute_instance.platform.network_interface[0].nat_ip_address
}

output "ansible_inventory" {
  description = "Inline Ansible inventory for the provisioned VM."
  value       = "${yandex_compute_instance.platform.network_interface[0].nat_ip_address},"
}