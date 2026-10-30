terraform {
  required_version = ">= 1.6.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "platform" {
  name       = "${var.name_prefix}-network"
  driver     = "bridge"
  attachable = true
}

resource "docker_volume" "nginx_html" {
  name = "${var.name_prefix}-nginx-html"
}

resource "docker_image" "nginx" {
  name         = var.nginx_image
  keep_locally = true
}

resource "docker_container" "nginx" {
  name    = "${var.name_prefix}-nginx"
  image   = docker_image.nginx.image_id
  restart = "unless-stopped"

  networks_advanced {
    name = docker_network.platform.name
  }

  ports {
    internal = 80
    external = var.host_port
    ip       = "127.0.0.1"
  }

  volumes {
    volume_name    = docker_volume.nginx_html.name
    container_path = "/usr/share/nginx/html"
  }
}
