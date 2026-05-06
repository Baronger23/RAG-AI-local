import json

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def sign_and_send(method: str, url: str, region: str, body: dict | None = None):
    session = boto3.Session(region_name=region)
    credentials = session.get_credentials().get_frozen_credentials()

    data = json.dumps(body) if body is not None else None
    headers = {"Content-Type": "application/json"}

    request = AWSRequest(method=method, url=url, data=data, headers=headers)
    SigV4Auth(credentials, "aoss", region).add_auth(request)

    prepared_headers = dict(request.headers.items())
    response = requests.request(method=method, url=url, headers=prepared_headers, data=data, timeout=30)
    return response


def main():
    region = "us-east-1"
    endpoint = "https://n0ovdv62srj6gh3hvqj7.us-east-1.aoss.amazonaws.com"
    index_name = "bedrock-knowledge-base-index"

    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "text": {
                    "type": "text"
                },
                "metadata": {
                    "type": "text",
                    "index": False
                }
            }
        }
    }

    existing_url = f"{endpoint}/_cat/indices/{index_name}?format=json"
    existing_resp = sign_and_send("GET", existing_url, region)
    if existing_resp.status_code == 200 and existing_resp.text.strip() not in ("[]", ""):
        print(f"Existing index found: {index_name}. Deleting so it can be recreated with FAISS...")
        delete_url = f"{endpoint}/{index_name}"
        delete_resp = sign_and_send("DELETE", delete_url, region)
        print(f"Delete index status: {delete_resp.status_code}")
        print(delete_resp.text)

    create_url = f"{endpoint}/{index_name}"
    resp = sign_and_send("PUT", create_url, region, index_body)
    print(f"Create index status: {resp.status_code}")
    print(resp.text)

    if resp.status_code == 403:
        print("\n403 means the caller does not yet have data-plane permission to write to AOSS.")
        print("You need a principal with aoss:APIAccessAll plus data access policy access to this collection.")

    # Verify index exists
    verify_url = f"{endpoint}/_cat/indices/{index_name}?format=json"
    verify_resp = sign_and_send("GET", verify_url, region)
    print(f"Verify index status: {verify_resp.status_code}")
    print(verify_resp.text)


if __name__ == "__main__":
    main()
