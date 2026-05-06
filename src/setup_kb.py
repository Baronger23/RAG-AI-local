"""
Setup Bedrock Knowledge Base using infrastructure provisioned by Terraform.

This script reads the Terraform outputs and creates the Bedrock KB.
"""

import json
import time
import boto3
from pathlib import Path

def load_terraform_outputs():
    """Load Terraform outputs from JSON file."""
    tf_outputs_path = Path(__file__).parent / "tf_outputs.json"
    
    if not tf_outputs_path.exists():
        raise FileNotFoundError(f"Terraform outputs not found at {tf_outputs_path}")
    
    with open(tf_outputs_path) as f:
        return json.load(f)

def create_bedrock_kb(config):
    """Create Bedrock Knowledge Base."""
    bedrock_client = boto3.client('bedrock-agent', region_name=config['aws_region'])
    
    kb_name = "geekbrain-kb"
    print(f"Creating Bedrock Knowledge Base: {kb_name}")
    
    try:
        # Create the knowledge base
        response = bedrock_client.create_knowledge_base(
            name=kb_name,
            description="Knowledge base for GeekBrain infrastructure Q&A",
            roleArn=config['bedrock_role_arn'],
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f"arn:aws:bedrock:{config['aws_region']}::foundation-model/amazon.titan-embed-text-v2:0"
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': config['opensearch_collection_arn'],
                    'vectorIndexName': 'bedrock-knowledge-base-index',
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✓ Knowledge Base created: {kb_id}")
        return kb_id
        
    except Exception as e:
        if 'already exists' in str(e):
            print(f"⚠️  Knowledge Base already exists, retrieving existing...")
            # Try to find existing KB
            kbs = bedrock_client.list_knowledge_bases()
            for kb in kbs.get('knowledgeBaseSummaries', []):
                if kb['name'] == kb_name:
                    kb_id = kb['knowledgeBaseId']
                    print(f"✓ Found existing Knowledge Base: {kb_id}")
                    return kb_id
        print(f"❌ Error creating Knowledge Base: {e}")
        raise

def create_data_source(kb_id, config):
    """Create S3 data source for the knowledge base."""
    bedrock_client = boto3.client('bedrock-agent', region_name=config['aws_region'])
    
    ds_name = "geekbrain-docs"
    print(f"\nCreating Data Source: {ds_name}")
    
    try:
        response = bedrock_client.create_data_source(
            knowledgeBaseId=kb_id,
            name=ds_name,
            description="Markdown documents from GeekBrain data package",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': config['s3_bucket_arn'],
                    'inclusionPrefixes': ['docs/']
                }
            }
        )
        
        ds_id = response['dataSource']['dataSourceId']
        print(f"✓ Data Source created: {ds_id}")
        return ds_id
        
    except Exception as e:
        if 'already exists' in str(e) or 'ConflictException' in str(type(e)):
            print(f"⚠️  Data Source already exists, retrieving existing...")
            # Try to find existing data source
            dss = bedrock_client.list_data_sources(knowledgeBaseId=kb_id)
            for ds in dss.get('dataSourceSummaries', []):
                if ds['name'] == ds_name:
                    ds_id = ds['dataSourceId']
                    print(f"✓ Found existing Data Source: {ds_id}")
                    return ds_id
        print(f"❌ Error creating Data Source: {e}")
        raise

def start_ingestion(kb_id, ds_id, config):
    """Start ingestion job to sync documents."""
    bedrock_client = boto3.client('bedrock-agent', region_name=config['aws_region'])
    
    print(f"\nStarting ingestion job...")
    
    try:
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"✓ Ingestion job started: {job_id}")
        print(f"  Status: {response['ingestionJob']['status']}")
        
        # Wait for ingestion to complete (or give up after 5 minutes)
        print("\nWaiting for ingestion to complete...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            time.sleep(5)
            job_response = bedrock_client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )
            
            status = job_response['ingestionJob']['status']
            print(f"  Status: {status}")
            
            if status in ['COMPLETE', 'FAILED']:
                if status == 'COMPLETE':
                    print(f"✓ Ingestion complete!")
                else:
                    print(f"❌ Ingestion failed")
                return status
        
        print(f"⚠️  Ingestion still running (timeout after {max_wait}s)")
        print(f"  You can check status later with: aws bedrock-agent get-ingestion-job --knowledge-base-id {kb_id} --data-source-id {ds_id} --ingestion-job-id {job_id}")
        return status
        
    except Exception as e:
        print(f"❌ Error starting ingestion: {e}")
        raise

def save_kb_id(kb_id):
    """Save KB ID to file for Python code to read."""
    kb_id_file = Path(__file__).parent / "kb_id.txt"
    with open(kb_id_file, 'w') as f:
        f.write(kb_id)
    print(f"✓ KB ID saved to: {kb_id_file}")

def main():
    """Main setup function."""
    print("="*60)
    print("GeekBrain Bedrock Knowledge Base Setup")
    print("="*60)
    
    # Load terraform outputs
    print("\nLoading infrastructure configuration...")
    config = load_terraform_outputs()
    print(f"✓ Loaded config from: tf_outputs.json")
    print(f"  AWS Account: {config['aws_account_id']}")
    print(f"  AWS Region: {config['aws_region']}")
    print(f"  S3 Bucket: {config['s3_bucket_name']}")
    print(f"  OpenSearch Collection: {config['opensearch_collection_name']}")
    
    # Create KB
    kb_id = create_bedrock_kb(config)
    
    # Create data source
    ds_id = create_data_source(kb_id, config)
    
    # Start ingestion
    start_ingestion(kb_id, ds_id, config)
    
    # Save KB ID
    save_kb_id(kb_id)
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print(f"\nKnowledge Base ID: {kb_id}")
    print(f"Saved to: src/kb_id.txt")
    print(f"\nYou can now:")
    print(f"1. Test the KB with: python tests/test_all.py")
    print(f"2. Run interactive demo: python src/main.py")
    print(f"3. Batch process questions: python src/main.py --batch questions.txt")

if __name__ == "__main__":
    main()
