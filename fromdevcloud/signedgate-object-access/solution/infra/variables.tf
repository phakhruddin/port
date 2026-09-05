variable "prefix" { type = string }
variable "aws_region" { type = string }
variable "aws_endpoint_url" { type = string }
variable "api_image" { type = string }
variable "api_image_id" { type = string }
variable "presign_ttl_seconds" { type = number }
variable "aws_access_key_id" {
  type      = string
  sensitive = true
}
variable "aws_secret_access_key" {
  type      = string
  sensitive = true
}
