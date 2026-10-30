output "service_url" {
  description = "Loopback URL of the Terraform-managed Nginx container."
  value       = "http://127.0.0.1:${docker_container.nginx.ports[0].external}"
}