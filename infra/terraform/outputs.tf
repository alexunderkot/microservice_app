output "container_name" {
    description = "Name of the Docker container"
    value       = docker_container.api.name
}

output "network_name" {
    description = "Name of the Docker network"
    value       = docker_network.app_net.name
}