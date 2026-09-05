resource "aws_kms_key" "objects" {
  description             = "${var.prefix} object encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 7
  tags                    = local.tags
}
resource "aws_kms_alias" "objects" {
  name          = "alias/${var.prefix}-objects"
  target_key_id = aws_kms_key.objects.key_id
}

resource "aws_kms_key" "metadata" {
  description             = "${var.prefix} metadata encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 7
  tags                    = local.tags
}
resource "aws_kms_alias" "metadata" {
  name          = "alias/${var.prefix}-metadata"
  target_key_id = aws_kms_key.metadata.key_id
}

resource "aws_s3_bucket" "objects" {
  bucket        = "${var.prefix}-objects"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_versioning" "objects" {
  bucket = aws_s3_bucket.objects.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "objects" {
  bucket = aws_s3_bucket.objects.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.objects.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "objects" {
  bucket                  = aws_s3_bucket.objects.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "objects" {
  bucket = aws_s3_bucket.objects.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Sid = "DenyInsecureTransport", Effect = "Deny", Principal = "*", Action = "s3:*", Resource = [aws_s3_bucket.objects.arn, "${aws_s3_bucket.objects.arn}/*"], Condition = { Bool = { "aws:SecureTransport" = "false" } } }] })
}

resource "aws_dynamodb_table" "metadata" {
  name         = "${var.prefix}-metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_id"
  attribute {
    name = "file_id"
    type = "S"
  }
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.metadata.arn
  }
  tags = local.tags
}
