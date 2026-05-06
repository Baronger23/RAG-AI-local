"""
Test suite for GeekBrain W4 AI System
L1, L2, L3, L4 tests
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent import agent
from rag_pipeline import L1Retriever, L2Retriever


class TestResult:
    """Store test result"""

    def __init__(self, name: str, question: str, level: str):
        self.name = name
        self.question = question
        self.level = level
        self.result = None
        self.passed = False
        self.error = None

    def run(self):
        """Execute test"""
        try:
            self.result = agent.process_query(self.question, level=self.level)
            self.error = None
        except Exception as e:
            self.error = str(e)
            self.result = None

    def print_result(self):
        """Print test result"""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        print(f"\n{status} [{self.level}] {self.name}")
        print(f"  Question: {self.question}")
        if self.error:
            print(f"  Error: {self.error}")
        elif self.result:
            print(f"  Answer: {self.result.get('answer', 'N/A')[:100]}...")
            if self.result.get("sources"):
                print(f"  Sources: {', '.join(self.result['sources'][:2])}")


# L1 Tests: Simple retrieval
L1_TESTS = [
    (
        "Team Lead Query",
        "Who is the Team Platform lead?",
        "Alex Chen",
    ),
    (
        "SLA Query",
        "What is GeekBrain's SLA for latency?",
        "200ms p99",
    ),
    (
        "Service Architecture",
        "Describe the PaymentGW service",
        "payment gateway",
    ),
    (
        "Team Members",
        "List members of Team Platform",
        "Alex Chen",
    ),
    (
        "Company Overview",
        "What is GeekBrain's mission?",
        "accessible",
    ),
]

# L2 Tests: Multi-source and conflicts
L2_TESTS = [
    (
        "API Rate Limit Conflict",
        "What is the API rate limit for PaymentGW?",
        "1000",
    ),
    (
        "Deployment Policy",
        "Can Team Commerce deploy a fix on Friday night?",
        "deploy",
    ),
    (
        "Service Ownership",
        "Which services are in the critical tier?",
        "critical",
    ),
    (
        "Incident Response",
        "What is GeekBrain's incident response policy?",
        "incident",
    ),
    (
        "Security Policy",
        "What authentication method does PaymentGW use?",
        "Auth",
    ),
]

# L3 Tests: Tools and data
L3_TESTS = [
    (
        "Q1 Cost Query",
        "What was PaymentGW's total infrastructure cost in Q1 2026?",
        "database_query",
    ),
    (
        "Current Latency",
        "What is PaymentGW's current p99 latency?",
        "get_metrics",
    ),
    (
        "Incidents Count",
        "How many incidents did PaymentGW have in Q1 2026?",
        "incidents",
    ),
    (
        "SLA Comparison",
        "Is PaymentGW's current latency within its SLA?",
        "comparison",
    ),
    (
        "Service Status",
        "What is the current status of OrderSvc?",
        "get_status",
    ),
]

# L4 Tests: Multi-turn conversation
L4_TESTS = [
    (
        "Turn 1: Highest Cost Service",
        "Which service had the highest infrastructure cost in March 2026?",
    ),
    (
        "Turn 2: Cause of Cost Spike",
        "What was the main cause of the cost spike that month?",
    ),
    (
        "Turn 3: Responsible Team",
        "Which team is responsible for that service?",
    ),
    (
        "Turn 4: Recent Status",
        "What is the current status of that service?",
    ),
]


def run_l1_tests():
    """Run L1 tests"""
    print("\n" + "=" * 80)
    print("L1 TESTS: Simple Retrieval")
    print("=" * 80)

    results = []
    for name, question, expected_keywords in L1_TESTS:
        test = TestResult(name, question, "l1")
        test.run()

        # Check if answer contains expected keywords
        if test.result and test.error is None:
            answer = test.result.get("answer", "").lower()
            expected_keywords_lower = expected_keywords.lower()
            test.passed = expected_keywords_lower in answer
        else:
            test.passed = False

        test.print_result()
        results.append(test)

    # Summary
    passed = sum(1 for t in results if t.passed)
    print(f"\n📊 L1 Summary: {passed}/{len(results)} passed")
    return results


def run_l2_tests():
    """Run L2 tests"""
    print("\n" + "=" * 80)
    print("L2 TESTS: Multi-Source Retrieval")
    print("=" * 80)

    results = []
    for name, question, expected_keywords in L2_TESTS:
        test = TestResult(name, question, "l2")
        test.run()

        # Check if answer contains expected keywords
        if test.result and test.error is None:
            answer = test.result.get("answer", "").lower()
            expected_keywords_lower = expected_keywords.lower()
            test.passed = expected_keywords_lower in answer
        else:
            test.passed = False

        test.print_result()
        results.append(test)

    # Summary
    passed = sum(1 for t in results if t.passed)
    print(f"\n📊 L2 Summary: {passed}/{len(results)} passed")
    return results


def run_l3_tests():
    """Run L3 tests"""
    print("\n" + "=" * 80)
    print("L3 TESTS: Tool-Augmented Retrieval")
    print("=" * 80)

    results = []
    for name, question, expected_tool in L3_TESTS:
        test = TestResult(name, question, "l3")
        test.run()

        # Check if tools were called
        if test.result and test.error is None:
            tools_called = test.result.get("tools_called", [])
            test.passed = len(tools_called) > 0 or expected_tool in str(tools_called)
        else:
            test.passed = False

        test.print_result()
        results.append(test)

    # Summary
    passed = sum(1 for t in results if t.passed)
    print(f"\n📊 L3 Summary: {passed}/{len(results)} passed")
    return results


def run_l4_tests():
    """Run L4 tests (multi-turn with memory)"""
    print("\n" + "=" * 80)
    print("L4 TESTS: Multi-Turn Conversation with Memory")
    print("=" * 80)

    # Clear memory first
    agent.memory.clear()

    results = []
    for name, question in L4_TESTS:
        test = TestResult(name, question, "auto")
        test.run()

        if test.result and test.error is None:
            test.passed = True
        else:
            test.passed = False

        test.print_result()
        results.append(test)

    # Check memory
    entities = agent.memory.get_entities()
    print(f"\n📝 Extracted Entities: {entities}")
    print(f"📜 Conversation Turns: {len(agent.memory.turns)}")

    # Summary
    passed = sum(1 for t in results if t.passed)
    print(f"\n📊 L4 Summary: {passed}/{len(results)} passed")
    return results


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 GeekBrain W4 AI System — Full Test Suite")
    print("=" * 80)

    all_results = []

    all_results.extend(run_l1_tests())
    all_results.extend(run_l2_tests())
    all_results.extend(run_l3_tests())

    # Reset memory before L4
    agent.memory.clear()
    all_results.extend(run_l4_tests())

    # Final summary
    total = len(all_results)
    passed = sum(1 for t in all_results if t.passed)
    failed = total - passed

    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {100 * passed / total:.1f}%")

    if failed > 0:
        print("\n❌ Failed Tests:")
        for test in all_results:
            if not test.passed:
                print(f"  • {test.name} ({test.level})")

    print("=" * 80 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
