# ⚡ Quick Start Guide (5 minutes)

## Prerequisites

- Python 3.9+
- Windows/Mac/Linux
- Internet connection (to start monitoring API)

## Step 1: Install Dependencies (1 min)

```powershell
cd d:\Xbrain\RAG\W4
pip install -r requirements.txt
```

## Step 2: Seed Database (1 min)

```powershell
cd data_package/scripts
python seed_data.py --db-type sqlite
```

✅ This creates `geekbrain.db` with all structured data (costs, incidents, SLA, metrics)

## Step 3: Start Monitoring API (1 min)

**Keep this terminal open:**

```powershell
cd data_package/scripts
uvicorn monitoring_api:app --reload --port 8000
```

✅ API running at http://localhost:8000

## Step 4: Run Tests (1 min)

**In a new terminal:**

```powershell
cd d:\Xbrain\RAG\W4
python tests/test_all.py
```

📊 Output shows test results for L1, L2, L3, L4 levels

## Step 5: Try It Out! (1 min)

**Interactive mode:**

```powershell
cd d:\Xbrain\RAG\W4
python src/main.py
```

Then ask:
```
💬 You: Who is the Team Platform lead?
💬 You: What was PaymentGW's Q1 cost?
💬 You: exit
```

**Or single question:**

```powershell
python src/main.py "Who leads Team Platform?"
```

---

## 🎯 Expected Output

### Test Output

```
L1 TESTS: Simple Retrieval
========================================

✅ PASS [l1] Team Lead Query
  Question: Who is the Team Platform lead?
  Answer: Alex Chen is the Team Platform lead...

...

📊 L1 Summary: 5/5 passed
📊 L2 Summary: 5/5 passed
📊 L3 Summary: 5/5 passed
📊 L4 Summary: 4/4 passed

📊 FINAL SUMMARY
Total Tests: 19
✅ Passed: 19
Success Rate: 100.0%
```

### Interactive Mode

```
🤖 GeekBrain AI Assistant
================================================================================
Ask me questions about GeekBrain infrastructure.
Type 'exit' to quit, 'clear' to clear memory, 'help' for commands.

💬 You: Who is the Team Platform lead?

================================================================================
[L1] ANSWER
================================================================================
Alex Chen is the Team Platform lead (from team_platform.md).

--------------------------------------------------------------------------------
SOURCES:
  • team_platform.md
================================================================================

💬 You: exit
👋 Goodbye!
```

---

## 🔐 Adding AWS Credentials (Optional - for real LLM)

When you have AWS access keys, create `.env`:

```
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
MODE=local
```

Then restart the system to use real Claude LLM (currently uses mock LLM).

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `No such file or directory: requirements.txt` | Run from `d:\Xbrain\RAG\W4` directory |
| `ModuleNotFoundError: No module named 'requests'` | Run `pip install -r requirements.txt` |
| `Address already in use: 8000` | Port 8000 is taken. Use `--port 8001` instead |
| `ModuleNotFoundError: No module named 'src'` | Add `src` to PYTHONPATH or run from `W4` directory |
| Tests show `❌ FAIL` | Check logs in `logs/geekbrain.log` |

---

## 📚 After Quick Start

- Read [docs/README.md](docs/README.md) for full documentation
- Check [plan/W4_IMPLEMENTATION_PLAN.md](plan/W4_IMPLEMENTATION_PLAN.md) for architecture details
- Explore code in `src/` directory
- Read test cases in `tests/test_all.py`

---

## 🚀 Ready for Production?

1. Setup AWS credentials properly
2. Create S3 bucket and upload knowledge base docs
3. Create Bedrock Knowledge Base
4. Set `MODE=cloud` in config
5. Run tests again with real LLM

See [docs/README.md](docs/README.md) for full setup instructions.

---

**That's it!** You now have a working RAG + Tool-Augmented AI system. 🎉

Questions? Check the logs: `logs/geekbrain.log`
