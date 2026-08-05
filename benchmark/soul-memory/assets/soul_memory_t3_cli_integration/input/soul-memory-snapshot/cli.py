#!/usr/bin/env python3
"""
Soul Memory CLI Interface for OpenClaw Plugin v3.6.0

Provides a simple command-line interface for searching memories.
Output is JSON formatted for easy parsing by TypeScript/JavaScript.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core import SoulMemorySystem, SearchResult
except ImportError:
    print("Error: Could not import SoulMemorySystem", file=sys.stderr)
    sys.exit(1)


def format_results_for_json(results: List[SearchResult]) -> List[Dict[str, Any]]:
    """Format search results for JSON output.

    Supports both legacy SearchResult objects and v3.4+ dict-style results.
    """
    formatted = []
    for result in results:
        if isinstance(result, dict):
            formatted.append({
                "path": result.get("source", result.get("path", "UNKNOWN")),
                "content": str(result.get("content", "")).strip(),
                "score": float(result.get("score", 0.0)),
                "priority": result.get("priority", "N")
            })
        else:
            formatted.append({
                "path": result.source if hasattr(result, 'source') else "UNKNOWN",
                "content": result.content.strip() if hasattr(result, 'content') else "",
                "score": float(result.score) if hasattr(result, 'score') else 0.0,
                "priority": result.priority if hasattr(result, 'priority') else "N"
            })
    return formatted


def search_command(args: argparse.Namespace) -> None:
    """Execute search command and output JSON results"""
    try:
        # Suppress all internal stdout chatter so plugin gets pure JSON only
        import io
        from contextlib import redirect_stdout

        silent_buf = io.StringIO()
        with redirect_stdout(silent_buf):
            memory_system = SoulMemorySystem()
            memory_system.initialize()
            results = memory_system.search(
                args.query,
                top_k=args.top_k,
                min_score=args.min_score
            )

        # v3.4.0: 結果已是 dict 格式，無需再次過濾
        # results 現在是 [{'content': str, 'score': float, 'source': str, 'priority': str}, ...]

        # Format and output (pure JSON only)
        formatted = format_results_for_json(results)
        print(json.dumps(formatted, ensure_ascii=False, indent=2))

    except Exception as e:
        import traceback
        error_result = [{
            "error": str(e),
            "path": "ERROR",
            "content": f"Search failed: {e}",
            "score": 0.0
        }]
        print(json.dumps(error_result, ensure_ascii=False), file=sys.stdout)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Soul Memory CLI for OpenClaw",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "SSH VPS problem" --top_k 3
  %(prog)s search "QST physics" --min_score 2.0
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search memory')
    search_parser.add_argument('query', help='Search query text')
    search_parser.add_argument('--top_k', type=int, default=5,
                               help='Number of results to return (default: 5)')
    search_parser.add_argument('--min_score', type=float, default=3.0,
                               help='Minimum similarity score (default: 0.0)')
    search_parser.set_defaults(func=search_command)

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if args.command == 'search':
        search_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
