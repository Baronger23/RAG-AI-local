"""
Bonus C: Knowledge Base Sync Utility
Triggers an ingestion job to sync documents from S3 to Bedrock Knowledge Base.
"""

import boto3
import time
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(__file__))
from config import BEDROCK_KB_ID, AWS_REGION
from logger import logger

def sync_kb():
    if not BEDROCK_KB_ID:
        print("Error: BEDROCK_KB_ID not found in environment or src/kb_id.txt")
        return False

    client = boto3.client("bedrock-agent", region_name=AWS_REGION)
    
    try:
        # 1. Get data source ID
        print(f"Finding data sources for KB: {BEDROCK_KB_ID}...")
        response = client.list_data_sources(knowledgeBaseId=BEDROCK_KB_ID)
        data_sources = response.get("dataSourceSummaries", [])
        
        if not data_sources:
            print(f"No data sources found for KB {BEDROCK_KB_ID}")
            return False
            
        data_source_id = data_sources[0]["dataSourceId"]
        name = data_sources[0]["name"]
        print(f"Found data source: {name} ({data_source_id})")
        
        # 2. Start ingestion job
        print(f"Starting ingestion job for {name}...")
        sync_response = client.start_ingestion_job(
            knowledgeBaseId=BEDROCK_KB_ID,
            dataSourceId=data_source_id
        )
        
        job_id = sync_response["ingestionJob"]["ingestionJobId"]
        print(f"Sync started. Job ID: {job_id}")
        
        # 3. Poll for status
        while True:
            status_response = client.get_ingestion_job(
                knowledgeBaseId=BEDROCK_KB_ID,
                dataSourceId=data_source_id,
                ingestionJobId=job_id
            )
            status = status_response["ingestionJob"]["status"]
            print(f"Status: {status}")
            
            if status in ["COMPLETE", "FAILED", "STOPPED"]:
                break
            time.sleep(5)
            
        if status == "COMPLETE":
            print("\n✅ Knowledge Base successfully synchronized!")
            return True
        else:
            print(f"\n❌ Sync failed with status: {status}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GeekBrain Knowledge Base Sync Tool")
    print("=" * 60)
    sync_kb()
