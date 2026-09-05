output "manifest" {
  sensitive = true
  value = {
    deployment = var.prefix
    network = {
      vpc_id                  = aws_vpc.main.id
      public_subnet_ids       = aws_subnet.public[*].id
      private_subnet_ids      = aws_subnet.private[*].id
      private_route_table_ids = aws_route_table.private[*].id
      s3_endpoint_id          = aws_vpc_endpoint.s3.id
      alb_sg_id               = aws_security_group.alb.id
      api_sg_id               = aws_security_group.api.id
    }
    alb = {
      arn              = aws_lb.main.arn
      listener_arn     = aws_lb_listener.http.arn
      target_group_arn = aws_lb_target_group.api.arn
      dns_name         = aws_lb.main.dns_name
      advertised_url   = "http://${aws_lb.main.dns_name}"
      url              = "http://${local.endpoint_host}:80"
      connect_url      = "http://${local.endpoint_host}:80"
    }
    compute = { cluster_arn = aws_ecs_cluster.main.arn, service_arn = aws_ecs_service.api.id, task_definition_arn = aws_ecs_task_definition.api.arn, desired_count = 2 }
    storage = { bucket = aws_s3_bucket.objects.id, metadata_table = aws_dynamodb_table.metadata.name }
    auth = {
      user_pool_id                = aws_cognito_user_pool.main.id
      issuer                      = "http://localhost:4566/${aws_cognito_user_pool.main.id}"
      token_url                   = "${var.aws_endpoint_url}/cognito-idp/oauth2/token"
      viewer_client_id            = aws_cognito_user_pool_client.role["viewer"].id
      viewer_client_secret        = aws_cognito_user_pool_client.role["viewer"].client_secret
      contributor_a_client_id     = aws_cognito_user_pool_client.role["contributor_a"].id
      contributor_a_client_secret = aws_cognito_user_pool_client.role["contributor_a"].client_secret
      contributor_b_client_id     = aws_cognito_user_pool_client.role["contributor_b"].id
      contributor_b_client_secret = aws_cognito_user_pool_client.role["contributor_b"].client_secret
      admin_client_id             = aws_cognito_user_pool_client.role["admin"].id
      admin_client_secret         = aws_cognito_user_pool_client.role["admin"].client_secret
    }
    kms   = { object_arn = aws_kms_key.objects.arn, metadata_arn = aws_kms_key.metadata.arn }
    logs  = { api = aws_cloudwatch_log_group.api.name }
    image = { reference = var.api_image, id = var.api_image_id }
  }
}
