data "aws_iam_policy_document" "ecs_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.prefix}-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json
  tags               = local.tags
}
resource "aws_iam_role" "api" {
  name               = "${var.prefix}-api"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json
  tags               = local.tags
}

resource "aws_iam_role_policy" "execution" {
  name   = "${var.prefix}-execution"
  role   = aws_iam_role.execution.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.api.arn}:*" }] })
}

resource "aws_iam_role_policy" "api" {
  name = "${var.prefix}-api"
  role = aws_iam_role.api.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["s3:ListBucket"], Resource = aws_s3_bucket.objects.arn },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = "${aws_s3_bucket.objects.arn}/tenants/*" },
    { Effect = "Allow", Action = ["dynamodb:DescribeTable", "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Scan"], Resource = aws_dynamodb_table.metadata.arn },
    { Effect = "Allow", Action = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"], Resource = [aws_kms_key.objects.arn, aws_kms_key.metadata.arn] }
  ] })
}

resource "aws_cognito_user_pool" "main" {
  name = "${var.prefix}-users"
  tags = local.tags
}

resource "aws_cognito_resource_server" "main" {
  identifier   = "signedgate"
  name         = "signedgate"
  user_pool_id = aws_cognito_user_pool.main.id
  scope {
    scope_name        = "viewer"
    scope_description = "Read shared files"
  }
  scope {
    scope_name        = "contributor"
    scope_description = "Manage owned files"
  }
  scope {
    scope_name        = "admin"
    scope_description = "Manage all files"
  }
}

locals {
  client_scopes = {
    viewer        = "viewer"
    contributor_a = "contributor"
    contributor_b = "contributor"
    admin         = "admin"
  }
}

resource "aws_cognito_user_pool_client" "role" {
  for_each                             = local.client_scopes
  name                                 = "${var.prefix}-${each.key}"
  user_pool_id                         = aws_cognito_user_pool.main.id
  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = ["signedgate/${each.value}"]
  depends_on                           = [aws_cognito_resource_server.main]
}
