terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "GeekBrain"
      Environment = "dev"
      ManagedBy   = "Terraform"
    }
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}

locals {
  current_user_name = element(split("/", data.aws_caller_identity.current.arn), 1)
}

# Create S3 bucket for KB documents
resource "aws_s3_bucket" "kb_documents" {
  bucket = "geekbrain-kb-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "GeekBrain KB Documents"
  }
}

# Block public access to S3 bucket
resource "aws_s3_bucket_public_access_block" "kb_documents" {
  bucket = aws_s3_bucket.kb_documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload all markdown files from local directory to S3
resource "aws_s3_object" "kb_files" {
  for_each = fileset("${path.module}/../data_package/knowledge_base", "*.md")

  bucket = aws_s3_bucket.kb_documents.id
  key    = "docs/${each.value}"
  source = "${path.module}/../data_package/knowledge_base/${each.value}"

  etag = filemd5("${path.module}/../data_package/knowledge_base/${each.value}")

  content_type = "text/markdown"

  tags = {
    File = each.value
  }
}

# Required encryption policy for OpenSearch Serverless collection
resource "aws_opensearchserverless_security_policy" "kb_encryption" {
  name = "geekbrain-kb-encryption"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource = [
          "collection/geekbrain-kb-collection"
        ]
      }
    ]
    AWSOwnedKey = true
  })
}

# Required network policy for OpenSearch Serverless collection
resource "aws_opensearchserverless_security_policy" "kb_network" {
  name = "geekbrain-kb-network"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = [
            "collection/geekbrain-kb-collection"
          ]
        },
        {
          ResourceType = "dashboard"
          Resource = [
            "collection/geekbrain-kb-collection"
          ]
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# Create OpenSearch Serverless collection for vector store
resource "aws_opensearchserverless_collection" "kb_collection" {
  name = "geekbrain-kb-collection"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.kb_encryption,
    aws_opensearchserverless_security_policy.kb_network
  ]

  tags = {
    Name = "GeekBrain KB Vector Store"
  }
}

# Create data access policy for OpenSearch collection
resource "aws_opensearchserverless_access_policy" "kb_collection" {
  name        = "geekbrain-kb-access"
  type        = "data"
  description = "Allow Bedrock to access OpenSearch collection"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${aws_opensearchserverless_collection.kb_collection.name}"]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index"
          Resource     = ["index/${aws_opensearchserverless_collection.kb_collection.name}/*"]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ]
      Principal = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/bedrock-kb-execution-role",
        data.aws_caller_identity.current.arn,
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  ])
}

# Create IAM role for Bedrock to access S3 and OpenSearch
resource "aws_iam_role" "bedrock_kb_role" {
  name = "bedrock-kb-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "Bedrock KB Execution Role"
  }
}

# Policy for S3 access
resource "aws_iam_role_policy" "bedrock_s3_policy" {
  name = "bedrock-s3-access"
  role = aws_iam_role.bedrock_kb_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.kb_documents.arn,
          "${aws_s3_bucket.kb_documents.arn}/*"
        ]
      }
    ]
  })
}

# Policy for OpenSearch access
resource "aws_iam_role_policy" "bedrock_opensearch_policy" {
  name = "bedrock-opensearch-access"
  role = aws_iam_role.bedrock_kb_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = [
          aws_opensearchserverless_collection.kb_collection.arn
        ]
      }
    ]
  })
}

# Policy for Bedrock model access
resource "aws_iam_role_policy" "bedrock_model_policy" {
  name = "bedrock-model-access"
  role = aws_iam_role.bedrock_kb_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      }
    ]
  })
}

# Allow the current CLI user to create/update OpenSearch Serverless indexes
resource "aws_iam_user_policy" "current_user_aoss_access" {
  name = "geekbrain-aoss-access"
  user = local.current_user_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create Bedrock Knowledge Base
# Note: Using Python boto3 for KB creation since Terraform provider has limited support
# See d:\Xbrain\RAG\W4\src\setup_kb.py for implementation

# For now, just provision the supporting infrastructure:
# - S3 bucket (already created above)
# - OpenSearch Serverless collection (above)
# - IAM roles (above)
# Then run: python src/setup_kb.py

# Output infrastructure ready for Python KB setup
resource "local_file" "infrastructure_config" {
  filename = "${path.module}/../src/tf_outputs.json"
  content = jsonencode({
    s3_bucket_name              = aws_s3_bucket.kb_documents.id
    s3_bucket_arn               = aws_s3_bucket.kb_documents.arn
    opensearch_collection_name  = aws_opensearchserverless_collection.kb_collection.name
    opensearch_collection_arn   = aws_opensearchserverless_collection.kb_collection.arn
    bedrock_role_arn            = aws_iam_role.bedrock_kb_role.arn
    aws_account_id              = data.aws_caller_identity.current.account_id
    aws_region                  = data.aws_region.current.name
  })
}
