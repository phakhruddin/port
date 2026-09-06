resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.api_family}"
  retention_in_days = 7
  tags              = local.tags
}

resource "aws_lb" "main" {
  name               = substr("${var.prefix}-alb", 0, 32)
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  tags               = local.tags
}

resource "aws_lb_target_group" "api" {
  name        = substr("${var.prefix}-api", 0, 32)
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id
  health_check {
    path     = "/health/ready"
    protocol = "HTTP"
    port     = "traffic-port"
  }
  tags = local.tags
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_cluster" "main" {
  name = "${var.prefix}-cluster"
  tags = local.tags
}

resource "aws_ecs_task_definition" "api" {
  family                   = local.api_family
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.api.arn
  container_definitions = jsonencode([{
    name         = "api", image = var.api_image, essential = true,
    portMappings = [{ containerPort = 8080, hostPort = 8080, protocol = "tcp" }],
    environment = [
      { name = "AWS_ENDPOINT_URL", value = var.aws_endpoint_url },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "AWS_ACCESS_KEY_ID", value = var.aws_access_key_id },
      { name = "AWS_SECRET_ACCESS_KEY", value = var.aws_secret_access_key },
      { name = "OBJECT_BUCKET", value = aws_s3_bucket.objects.id },
      { name = "METADATA_TABLE", value = aws_dynamodb_table.metadata.name },
      { name = "PRESIGN_TTL_SECONDS", value = tostring(var.presign_ttl_seconds) },
      { name = "COGNITO_ISSUER", value = "http://localhost:4566/${aws_cognito_user_pool.main.id}" },
      { name = "COGNITO_JWKS_URL", value = "${var.aws_endpoint_url}/${aws_cognito_user_pool.main.id}/.well-known/jwks.json" },
      { name = "COGNITO_AUDIENCES", value = join(",", [for role in ["viewer", "contributor_a", "contributor_b", "admin"] : aws_cognito_user_pool_client.role[role].id]) },
      { name = "BIND_ADDR", value = "0.0.0.0:8080" }
    ],
    logConfiguration = { logDriver = "awslogs", options = { "awslogs-group" = aws_cloudwatch_log_group.api.name, "awslogs-region" = var.aws_region, "awslogs-stream-prefix" = "api" } }
  }])
  tags = local.tags
}

resource "aws_ecs_service" "api" {
  name            = "${var.prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }
  depends_on = [aws_lb_listener.http, aws_vpc_endpoint.s3]
  tags       = local.tags
}
