# Terraform: GeekBrain Bedrock Knowledge Base

Tự động deploy toàn bộ infrastructure cho GeekBrain Knowledge Base:
- S3 bucket (lưu 36 markdown files)
- OpenSearch Serverless collection (vector store)
- Bedrock Knowledge Base
- IAM roles và permissions
- Automatic document ingestion

## Prerequisites

1. **AWS CLI configured** với credentials (đã setup từ trước)
   ```bash
   aws sts get-caller-identity
   # Should return your Account ID
   ```

2. **Terraform installed**
   ```bash
   terraform version
   # Phải >= 1.0
   ```

3. **Knowledge base documents** phải có ở:
   ```
   d:\Xbrain\RAG\W4\data_package\knowledge_base\
   # Phải có ~36 file *.md
   ```

## Quick Start

### Step 1: Initialize Terraform

```bash
cd d:\Xbrain\RAG\W4\terraform
terraform init
```

### Step 2: Plan deployment

```bash
terraform plan
# Review what will be created
# Should show: 1 S3 bucket, 1 KB, 1 OpenSearch collection, 36 file uploads, etc.
```

### Step 3: Apply deployment

```bash
terraform apply
# Type 'yes' when prompted
# Wait for completion (~5-10 minutes)
```

**Output sẽ hiển thị:**
```
kb_id_file = "d:\Xbrain\RAG\W4\src\kb_id.txt"
knowledge_base_id = "kb-XXXXX"
s3_bucket_name = "geekbrain-kb-341515954788"
opensearch_collection_arn = "arn:aws:aoss:us-east-1:..."
```

### Step 4: Verify setup

```bash
# Check KB ID was saved
cat d:\Xbrain\RAG\W4\src\kb_id.txt

# Check S3 bucket
aws s3 ls s3://geekbrain-kb-341515954788/docs/ | wc -l
# Should show ~36 files

# Check OpenSearch collection
aws opensearchserverless list-collections
```

### Step 5: Proceed with Python code

File `src/kb_id.txt` sẽ được tạo tự động. Python code bạn có thể đọc nó:
```python
with open('src/kb_id.txt') as f:
    kb_id = f.read().strip()
```

## What Gets Created

| Resource | Type | Details |
|----------|------|---------|
| S3 Bucket | Storage | `geekbrain-kb-{account-id}` |
| OpenSearch Collection | Vector Store | `geekbrain-kb-collection` |
| Bedrock KB | Knowledge Base | `geekbrain-kb` |
| IAM Role | Role | `bedrock-kb-execution-role` |
| Data Source | KB Data | Syncs from S3 |
| Ingestion Job | Automation | Chunks + embeds docs |

## Troubleshooting

### "Access Denied" error
- Verify AWS credentials: `aws sts get-caller-identity`
- Verify Bedrock access: `aws bedrock list-foundation-models --region us-east-1`

### "No markdown files found"
- Check path: `ls d:\Xbrain\RAG\W4\data_package\knowledge_base\`
- Should show ~36 *.md files

### "Collection already exists"
- If you run apply twice, OpenSearch collection name might conflict
- Edit `terraform.tfvars` to change `opensearch_collection_name`

### "Ingestion failed"
- OpenSearch collection takes time to become available (~1 minute)
- If error persists, manually trigger: `aws bedrock-agent start-ingestion-job ...`

## Cleanup

**To destroy all resources and start over:**

```bash
terraform destroy
# Type 'yes' when prompted
# Wait for cleanup (~2-3 minutes)
```

**This will delete:**
- S3 bucket + all files
- OpenSearch collection
- Bedrock KB
- IAM role

## Advanced: Manual Ingestion Check

If KB isn't syncing, manually check ingestion status:

```bash
# Get KB ID from state
KB_ID=$(terraform output -raw knowledge_base_id)
DS_ID=$(terraform output -raw data_source_id)

# List ingestion jobs
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region us-east-1

# Check specific job
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --ingestion-job-id <JOB_ID> \
  --region us-east-1
```

Expected statuses: `STARTING` → `IN_PROGRESS` → `COMPLETE`

---

**Next:** Once Terraform completes, proceed with Python implementation in `src/rag_pipeline.py`
