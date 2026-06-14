variable "api_image" {
  description = "The Docker image for api"
  type        = string
  default     = "alexkot257/api:latest"
}

variable "api_port" {
  description = "Port for api"
  type        = number
  default     = 5000
}

variable "network_name" {
  description = "Docker network name"
  type        = string
  default     = "tf_app_network"
}

variable "redis_host" {
  description = "Host for Redis"
  type        = string
  default     = "localhost"
}

variable "web_image" {
  description = "The Docker image for web"
  type        = string
  default     = "alexkot257/web:latest"
}

variable "web_port" {
  description = "Port for web"
  type        = number
  default     = 5050
}

variable "redis_image" {
  description = "The Docker image for Redis"
  type        = string
  default     = "redis:latest"
}

variable "redis_port" {
  description = "Port for Redis"
  type        = number
  default     = 6379
}