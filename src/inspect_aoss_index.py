import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def signed_get(url: str, region: str = "us-east-1"):
    session = boto3.Session(region_name=region)
    cred = session.get_credentials().get_frozen_credentials()
    req = AWSRequest(method="GET", url=url, headers={})
    SigV4Auth(cred, "aoss", region).add_auth(req)
    return requests.get(url, headers=dict(req.headers.items()), timeout=30)


def main():
    region = "us-east-1"
    endpoint = "https://n0ovdv62srj6gh3hvqj7.us-east-1.aoss.amazonaws.com"
    index = "bedrock-knowledge-base-index"

    for suffix in ["_settings", "_mapping"]:
        url = f"{endpoint}/{index}/{suffix}"
        resp = signed_get(url, region)
        print(f"PATH {suffix} STATUS {resp.status_code}")
        print(resp.text)
        print("---")


if __name__ == "__main__":
    main()
