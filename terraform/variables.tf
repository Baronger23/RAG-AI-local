variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "geekbrain"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "knowledge_base_name" {
  description = "Bedrock Knowledge Base name"
  type        = string
  default     = "geekbrain-kb"
}

variable "kb_documents_path" {
  description = "Path to knowledge base documents"
  type        = string
  default     = "../data_package/knowledge_base"
}

variable "opensearch_collection_name" {
  description = "OpenSearch Serverless collection name"
  type        = string
  default     = "geekbrain-kb-collection"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "GeekBrain"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
