"""
GeekBrain W4 AI System — Main Entry Point
Command-line interface for asking questions
"""

import sys
import argparse
from typing import Optional

from agent import agent
from rag_pipeline import L1Retriever, L2Retriever
from logger import logger


def format_result(result: dict, verbose: bool = False) -> str:
    """Format agent result for console output"""
    output = []

    # Answer
    output.append("\n" + "=" * 80)
    output.append(f"[{result.get('level', 'UNKNOWN')}] ANSWER")
    output.append("=" * 80)
    output.append(result.get("answer", "No answer"))

    # Sources
    if result.get("sources"):
        output.append("\n" + "-" * 80)
        output.append("SOURCES:")
        for source in result["sources"]:
            output.append(f"  • {source}")

    # Verbose: show tool results
    if verbose and result.get("tool_results"):
        output.append("\n" + "-" * 80)
        output.append("TOOL RESULTS:")
        for tool_name, tool_result in result["tool_results"].items():
            output.append(f"\n{tool_name}:")
            if isinstance(tool_result, dict):
                for key, value in tool_result.items():
                    if key != "data":  # Skip large data arrays
                        output.append(f"  {key}: {value}")

    # Metadata
    if verbose:
        output.append("\n" + "-" * 80)
        output.append("METADATA:")
        output.append(f"  Duration: {result.get('duration_seconds', 0):.2f}s")
        output.append(f"  Level: {result.get('level', 'unknown')}")
        if result.get("chunks_retrieved"):
            output.append(f"  Chunks retrieved: {result.get('chunks_retrieved')}")

    output.append("=" * 80 + "\n")

    return "\n".join(output)


def interactive_mode(verbose: bool = False):
    """Interactive conversation mode"""
    print("\n🤖 GeekBrain AI Assistant")
    print("=" * 80)
    print("Ask me questions about GeekBrain infrastructure.")
    print("Type 'exit' to quit, 'clear' to clear memory, 'help' for commands.")
    print("=" * 80)

    while True:
        try:
            question = input("\n💬 You: ").strip()

            if not question:
                continue

            if question.lower() == "exit":
                print("👋 Goodbye!")
                break

            if question.lower() == "clear":
                agent.memory.clear()
                print("🧹 Memory cleared")
                continue

            if question.lower() == "help":
                print("""
Commands:
  exit        - Quit the program
  clear       - Clear conversation memory
  help        - Show this help
  entities    - Show extracted entities from memory
  memory      - Show conversation history
  
Use natural language questions:
  - "Who is the Team Platform lead?"
  - "What was PaymentGW's Q1 cost?"
  - "Is PaymentGW within its SLA?"
  - "What caused the PaymentGW outage?"
                """)
                continue

            if question.lower() == "entities":
                entities = agent.memory.get_entities()
                print(f"Extracted entities: {entities}")
                continue

            if question.lower() == "memory":
                context = agent.memory.get_context()
                print(f"Conversation history:\n{context}")
                continue

            # Process question
            logger.info(f"User question: {question}")
            result = agent.process_query(question)
            print(format_result(result, verbose=verbose))

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            print(f"\n❌ Error: {e}")


def batch_mode(questions_file: str, verbose: bool = False):
    """Process questions from a file"""
    try:
        with open(questions_file, "r") as f:
            questions = [line.strip() for line in f if line.strip()]

        print(f"\n📋 Processing {len(questions)} questions from {questions_file}")
        print("=" * 80)

        results = []
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {question}")

            try:
                result = agent.process_query(question)
                results.append(result)
                print(format_result(result, verbose=verbose))
            except Exception as e:
                logger.error(f"Error processing question {i}: {e}")
                print(f"❌ Error: {e}")

        # Summary
        print("\n" + "=" * 80)
        print(f"BATCH SUMMARY: Processed {len(results)}/{len(questions)} questions")
        success_count = sum(1 for r in results if r.get("success", True))
        print(f"Success rate: {success_count}/{len(results)}")

    except FileNotFoundError:
        print(f"❌ File not found: {questions_file}")
        sys.exit(1)


def single_question_mode(question: str, level: str = "auto", verbose: bool = False):
    """Answer a single question"""
    print(f"\n❓ Question: {question}")
    print("=" * 80)

    try:
        result = agent.process_query(question, level=level)
        print(format_result(result, verbose=verbose))
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="GeekBrain W4 AI System — Ask questions about infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main.py
  
  # Single question
  python main.py "Who is the Team Platform lead?"
  
  # Specific level
  python main.py "What was PaymentGW cost?" --level l3
  
  # Batch from file
  python main.py --batch questions.txt
  
  # Verbose output
  python main.py "Question?" --verbose
        """,
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Single question to ask (or leave blank for interactive mode)",
    )
    parser.add_argument(
        "--level",
        choices=["l1", "l2", "l3", "auto"],
        default="auto",
        help="Processing level (default: auto)",
    )
    parser.add_argument(
        "--batch",
        help="Batch file with questions (one per line)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (show tool results, metadata)",
    )

    args = parser.parse_args()

    # Determine mode
    if args.batch:
        batch_mode(args.batch, verbose=args.verbose)
    elif args.question:
        single_question_mode(args.question, level=args.level, verbose=args.verbose)
    else:
        interactive_mode(verbose=args.verbose)


if __name__ == "__main__":
    main()
