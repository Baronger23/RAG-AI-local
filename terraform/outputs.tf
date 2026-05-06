output "s3_bucket_name" {
  description = "S3 bucket name for KB documents"
  value       = aws_s3_bucket.kb_documents.id
}

output "opensearch_collection_name" {
  description = "OpenSearch Serverless collection name"
  value       = aws_opensearchserverless_collection.kb_collection.name
}

output "opensearch_collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  value       = aws_opensearchserverless_collection.kb_collection.arn
}

output "bedrock_role_arn" {
  description = "IAM role ARN for Bedrock"
  value       = aws_iam_role.bedrock_kb_role.arn
}

output "infrastructure_config_file" {
  description = "File containing all infrastructure configuration for Python setup"
  value       = local_file.infrastructure_config.filename
}

output "next_steps" {
  description = "Instructions for next steps"
  value = <<-EOT
    Infrastructure provisioned! Next steps:
    1. Verify S3 bucket: aws s3 ls s3://${aws_s3_bucket.kb_documents.id}/docs/
    2. Run Python setup script: python src/setup_kb.py
    3. This will create the Bedrock Knowledge Base and return the KB ID
    4. The KB ID will be saved to src/kb_id.txt
  EOT
}
