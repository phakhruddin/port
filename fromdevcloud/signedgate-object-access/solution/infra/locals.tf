locals {
  tags          = { SignedGateDeployment = var.prefix }
  endpoint_host = regex("^https?://([^:/]+)", var.aws_endpoint_url)[0]
  azs           = ["${var.aws_region}a", "${var.aws_region}b"]
  api_family    = "${var.prefix}-api"
}
