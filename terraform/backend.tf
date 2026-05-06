# Optional: Store Terraform state in S3 (commented out for local dev)
# Uncomment after running terraform init once
# 
# terraform {
#   backend "s3" {
#     bucket         = "geekbrain-terraform-state"
#     key            = "w4/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "geekbrain-terraform-locks"
#   }
# }

# For now, state stored locally (.terraform/terraform.tfstate)
# This is fine for dev/testing
