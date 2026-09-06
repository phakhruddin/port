terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "= 6.51.0" }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = var.aws_access_key_id
  secret_key                  = var.aws_secret_access_key
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  s3_use_path_style           = true
  endpoints {
    apigateway     = var.aws_endpoint_url
    cloudwatchlogs = var.aws_endpoint_url
    cognitoidp     = var.aws_endpoint_url
    dynamodb       = var.aws_endpoint_url
    ec2            = var.aws_endpoint_url
    ecs            = var.aws_endpoint_url
    elbv2          = var.aws_endpoint_url
    iam            = var.aws_endpoint_url
    kms            = var.aws_endpoint_url
    s3             = var.aws_endpoint_url
    s3control      = var.aws_endpoint_url
    sts            = var.aws_endpoint_url
  }
}
