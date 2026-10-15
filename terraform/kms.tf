data "aws_caller_identity" "current" {}

resource "aws_kms_key" "rag_key" {
  description             = "KMS Key for Zero-Trust RAG OpenSearch and ECS Secrets"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableIAMUserPermissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam://${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowOpenSearchServerless"
        Effect = "Allow"
        Principal = {
          Service = "opensearchserverless.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "rag_key_alias" {
  name          = "alias/zero-trust-rag-key"
  target_key_id = aws_kms_key.rag_key.key_id
}
