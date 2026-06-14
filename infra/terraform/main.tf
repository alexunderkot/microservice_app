terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

resource "docker_network" "app_net" {
  name = var.network_name
}

resource "docker_container" "api" {
  name  = "tf_api"
  image = var.api_image

  networks_advanced {
    name = docker_network.app_net.name
  }

  ports {
    internal = var.api_port
    external = var.api_port
  }

  env = [
    "REDIS_HOST=${docker_container.redis.name}"
  ]
}

resource "docker_container" "web" {
  name = "tf_web"
  image = var.web_image

  networks_advanced {
    name = docker_network.app_net.name
  }

  ports {
    internal = var.web_port
    external = var.web_port
  }

  env = [
    "API_URL=http://${docker_container.api.name}:${var.api_port}"
  ]
}

resource "docker_container" "redis" {
  name = "tf_redis"
  image = var.redis_image

  networks_advanced {
    name = docker_network.app_net.name
  }

  ports {
    internal = var.redis_port
    external = var.redis_port
  }
}