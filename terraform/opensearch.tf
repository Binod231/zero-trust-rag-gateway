resource "aws_opensearchserverless_security_policy" "encryption_policy" {
  name        = "rag-encryption-policy"
  type        = "encryption"
  description = "Encryption at rest using KMS Customer Managed Key"
  policy = jsonencode({
    Rules = [{ ResourceType = "collection", Resource = ["collection/enterprise-rag-vectors"] }]
    AWSOwnedKey = false
    KmsARN      = aws_kms_key.rag_key.arn
  })
}

resource "aws_opensearchserverless_vpc_endpoint" "aoss_vpce" {
  name               = "rag-aoss-vpc-endpoint"
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids = [aws_security_group.aoss_sg.id]
}

resource "aws_security_group" "aoss_sg" {
  name        = "rag-aoss-sg"
  description = "Allow inbound HTTPS from ECS Fargate tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_opensearchserverless_security_policy" "network_policy" {
  name        = "rag-network-policy"
  type        = "network"
  description = "Restrict access strictly to VPC Endpoint"
  policy = jsonencode([{
    Rules = [
      { ResourceType = "collection", Resource = ["collection/enterprise-rag-vectors"] },
      { ResourceType = "dashboard", Resource = ["collection/enterprise-rag-vectors"] }
    ]
    AllowFromPublic = false
    SourceVPCEs     = [aws_opensearchserverless_vpc_endpoint.aoss_vpce.id]
  }])
}

resource "aws_opensearchserverless_collection" "vector_collection" {
  name        = "enterprise-rag-vectors"
  type        = "VECTORSEARCH"
  description = "Zero-Trust Multi-Tenant Vector Store"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption_policy,
    aws_opensearchserverless_security_policy.network_policy
  ]
}

resource "aws_opensearchserverless_access_policy" "data_policy" {
  name        = "rag-data-access-policy"
  type        = "data"
  description = "Grant ECS task role read/write access to vector indexes"
  policy = jsonencode([{
    Rules = [
      {
        ResourceType = "index"
        Resource     = ["index/enterprise-rag-vectors/*"]
        Permission   = [
          "aoss:CreateIndex",
          "aoss:DescribeIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument"
        ]
      },
      {
        ResourceType = "collection"
        Resource     = ["collection/enterprise-rag-vectors"]
        Permission   = ["aoss:DescribeCollectionItems"]
      }
    ]
    Principal = [
      aws_iam_role.ecs_task_role.arn,
      data.aws_caller_identity.current.arn
    ]
  }])
}
