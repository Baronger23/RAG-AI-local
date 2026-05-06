"""
Deep Test Script for GeekBrain AI RAG System
Focuses on complex L3 (Tool-use) and L4 (Multi-turn Memory) scenarios
"""

import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agent import agent
from logger import logger

def print_banner(text):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def run_test_case(name, question, level="auto"):
    print(f"\n[TEST] {name}")
    print(f"Q: {question}")
    
    start_time = time.time()
    result = agent.process_query(question, level=level)
    duration = time.time() - start_time
    
    print(f"\nA: {result.get('answer', 'NO ANSWER')}")
    print(f"\nTools called: {result.get('tools_called', [])}")
    print(f"Duration: {duration:.2f}s")
    print("-" * 40)
    return result

def main():
    print_banner("DEEP TEST SUITE: L3 & L4 VERIFICATION")

    # --- L3 SCENARIOS ---
    print_banner("L3 SCENARIOS: TOOL ORCHESTRATION")
    
    # 1. Cost Aggregation (requires DB)
    run_test_case(
        "Q1 Cost Aggregation",
        "What was PaymentGW's total cost in Q1 2026?"
    )

    # 2. Current Metrics (requires Monitoring API)
    run_test_case(
        "Current Metrics",
        "What is PaymentGW's current p99 latency?"
    )

    # 3. SLA Compliance (requires BOTH DB and API)
    run_test_case(
        "SLA Compliance Check",
        "Is PaymentGW within its latency SLA? Compare its current metrics with the target in the database."
    )

    # --- L4 SCENARIOS ---
    print_banner("L4 SCENARIOS: MULTI-TURN MEMORY")
    agent.memory.clear()

    # Turn 1
    run_test_case(
        "L4 Turn 1: Entity Identification",
        "Which service had the highest infrastructure cost in March 2026?"
    )

    # Turn 2
    run_test_case(
        "L4 Turn 2: Reasoning & Retrieval",
        "What was the main cause of the cost increase that month?"
    )

    # Turn 3
    run_test_case(
        "L4 Turn 3: Pronoun Resolution",
        "Which team is responsible for that service?"
    )

    # Turn 4
    run_test_case(
        "L4 Turn 4: Deep Retrieval",
        "The postmortem mentioned a review deadline. Is it overdue?"
    )

    print_banner("TEST SUITE COMPLETED")

if __name__ == "__main__":
    main()
