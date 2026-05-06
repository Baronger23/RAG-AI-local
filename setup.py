"""
Setup guide: Configure AWS credentials and run tests
Execute this after getting AWS credentials from team
"""

import os
import sys
import subprocess
from pathlib import Path


def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("\n🔐 Checking AWS Credentials...")
    
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if access_key and secret_key:
        print("✅ AWS credentials found in environment")
        return True
    else:
        print("⚠️  AWS credentials NOT found in environment")
        print("\nTo configure credentials, choose one method:")
        print("\n1️⃣  Environment Variables (Temporary - per session):")
        print("""
   $env:AWS_ACCESS_KEY_ID = "your-access-key"
   $env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
   $env:AWS_DEFAULT_REGION = "us-east-1"
        """)
        print("\n2️⃣  .env File (Persistent - in project root):")
        print("""
   Create d:\\Xbrain\\RAG\\W4\\.env with:
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_DEFAULT_REGION=us-east-1
        """)
        print("\n3️⃣  AWS CLI Config (System-wide):")
        print("   aws configure")
        return False


def check_database():
    """Check if database is seeded"""
    print("\n🗄️  Checking Database...")
    
    db_path = Path("data_package/geekbrain.db")
    
    if db_path.exists():
        print(f"✅ Database found at {db_path}")
        return True
    else:
        print(f"⚠️  Database not found at {db_path}")
        print("\nTo seed the database:")
        print("""
   cd data_package/scripts
   python seed_data.py --db-type sqlite
        """)
        return False


def check_monitoring_api():
    """Check if monitoring API is running"""
    print("\n📡 Checking Monitoring API...")
    
    import requests
    
    try:
        response = requests.get("http://localhost:8000/services", timeout=2)
        if response.status_code == 200:
            print("✅ Monitoring API is running at http://localhost:8000")
            return True
    except:
        pass
    
    print("⚠️  Monitoring API not running at http://localhost:8000")
    print("\nTo start the monitoring API:")
    print("""
   cd data_package/scripts
   uvicorn monitoring_api:app --reload --port 8000
    """)
    return False


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Dependencies...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ Dependencies installed")
            return True
        else:
            print(f"❌ Failed to install dependencies:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                GeekBrain W4 AI System — Setup Guide                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print("📋 Checking prerequisites...")

    checks = {
        "Dependencies": install_dependencies,
        "Database": check_database,
        "Monitoring API": check_monitoring_api,
        "AWS Credentials": check_aws_credentials,
    }

    results = {}
    for name, check_func in checks.items():
        results[name] = check_func()

    # Summary
    print("\n" + "=" * 80)
    print("📊 SETUP STATUS")
    print("=" * 80)

    for name, passed in results.items():
        status = "✅" if passed else "⚠️ "
        print(f"{status} {name}")

    print("\n" + "=" * 80)
    print("🚀 NEXT STEPS")
    print("=" * 80)

    if not results["Dependencies"]:
        print("1. Install dependencies: pip install -r requirements.txt")

    if not results["Database"]:
        print("2. Seed database: cd data_package/scripts && python seed_data.py")

    if not results["Monitoring API"]:
        print("3. Start API: cd data_package/scripts && uvicorn monitoring_api:app --port 8000")

    if not results["AWS Credentials"]:
        print("4. Configure AWS credentials (see above)")

    print("""
5. Run tests: python tests/test_all.py
6. Run interactive mode: python src/main.py
7. Ask a single question: python src/main.py "Your question?"

💡 For full help, see docs/README.md
    """)

    print("=" * 80 + "\n")

    all_ok = all(results.values())

    if all_ok:
        print("✅ All prerequisites met! You can start using the system.")
    else:
        print("⚠️  Some prerequisites are missing. See above for setup instructions.")

    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
