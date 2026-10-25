"""Command Line Interface (CLI) for IncuBrix Pipeline Orchestration.

Usage:
    python -m app.pipeline.cli complete [OPTIONS]
    python -m app.pipeline.cli refresh [OPTIONS]

Commands:
    complete    Execute an end-to-end run across ingestion, collection, scoring, audit, content, and reporting.
    refresh     Execute a refresh run to collect fresh measurements and update scores and reports.

Options:
    --market TEXT            Target search/AEO market (e.g. US, UK)
    --provider TEXT          Filter to specific provider (e.g. google_search, perplexity)
    --input-file TEXT        Path to CSV file containing creator questions for ingestion
    --sample-input           Use small new input set (data/live_review_sample.csv) for live review
    --target-audit-url TEXT  Target URL for technical SEO/AEO audit (default: https://incubrix.com)
    --max-retries INT        Maximum bounded retries for transient provider errors (default: 2)
    --content-limit INT      Maximum content drafts to generate (default: 10)
    --use-llm                Attempt LLM generation for content drafts (default: deterministic fallback)
    --skip-audit             Skip the technical SEO audit stage
    --skip-content           Skip the content draft generation stage
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from app.database.session import SessionLocal, init_db
from app.pipeline.cost_tracker import CostTracker
from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.pipeline import PipelineExecutionRequest, PipelineExecutionResponse


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m app.pipeline.cli",
        description="IncuBrix AEO, SEO & GEO Pipeline Orchestrator CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Pipeline execution command")

    # Complete command
    complete_parser = subparsers.add_parser(
        "complete",
        help="Complete end-to-end run (ingestion, collection, scoring, audit, content, reporting)",
    )
    _add_shared_options(complete_parser)
    complete_parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to CSV file with creator questions to ingest",
    )
    complete_parser.add_argument(
        "--sample-input",
        action="store_true",
        help="Use small new input set (data/live_review_sample.csv) for live review",
    )
    complete_parser.add_argument(
        "--target-audit-url",
        type=str,
        default="https://incubrix.com",
        help="Target public page URL to audit (default: https://incubrix.com)",
    )
    complete_parser.add_argument(
        "--content-limit",
        type=int,
        default=10,
        help="Maximum content drafts to generate (default: 10)",
    )
    complete_parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable configurable LLM provider for content draft generation",
    )
    complete_parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip technical SEO/AEO audit stage",
    )
    complete_parser.add_argument(
        "--skip-content",
        action="store_true",
        help="Skip content and citation generation stage",
    )

    # Refresh command
    refresh_parser = subparsers.add_parser(
        "refresh",
        help="Refresh measurements and update visibility scores and weekly reports",
    )
    _add_shared_options(refresh_parser)

    return parser


def _add_shared_options(parser: argparse.ArgumentParser) -> None:
    """Add options shared across both complete and refresh subcommands."""
    parser.add_argument(
        "--market",
        type=str,
        default=None,
        help="Target market filter (e.g. US, UK)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Filter to specific provider (e.g. google_search, perplexity)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum bounded retries for transient provider errors (default: 2)",
    )


def print_execution_summary(response: PipelineExecutionResponse) -> None:
    """Format and display structured execution telemetry to stdout."""
    status_icon = "OK" if response.status == "completed" else ("WARN" if response.status == "partial" else "FAIL")

    print("\n" + "=" * 70)
    print(f" IncuBrix Pipeline Run: {response.run_id}")
    print(f" Status:   [{status_icon}] {response.status.upper()}")
    print(f" Mode:     {response.pipeline_type}")
    print(f" Duration: {response.total_duration_seconds:.2f}s")
    print(f" Items:    Total: {response.total_items} | Success: {response.successful_items} | Failed: {response.failed_items}")
    print(f" API Cost: ${response.cost_summary.total_cost_usd:.4f} USD ({response.cost_summary.total_calls} calls)")
    print("=" * 70)

    print("\n[Stage Breakdown]")
    print(f" {'Stage':<14} | {'Status':<10} | {'Duration':<10} | {'Items (S/F)':<12} | {'Cost'}")
    print("-" * 65)
    for s in response.stages:
        status_str = s.status.value.upper()
        items_str = f"{s.items_succeeded}/{s.items_failed}"
        cost_str = f"${s.cost_usd:.4f}"
        print(f" {s.stage_name:<14} | {status_str:<10} | {s.duration_ms:>7.1f}ms | {items_str:<12} | {cost_str}")

    if response.cost_summary.items:
        print("\n[Cost Breakdown by Provider]")
        for c in response.cost_summary.items:
            est_flag = "(ESTIMATED)" if c.is_estimated else "(ACTUAL)"
            print(f" - {c.provider:<18} ({c.operation:<16}): {c.call_count} calls -> ${c.estimated_cost_usd:.4f} USD {est_flag}")

    if response.report_paths:
        print("\n[Generated Reports & Exports]")
        for name, path in response.report_paths.items():
            print(f" - {name}: {path}")

    if response.error_summary:
        print(f"\n[Errors / Warnings]: {response.error_summary}")
    print("=" * 70 + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    # Ensure local database schema is ready
    init_db()

    # Build execution request
    mode = "complete" if args.subcommand == "complete" else "refresh"
    request = PipelineExecutionRequest(
        mode=mode,
        market=getattr(args, "market", None),
        provider=getattr(args, "provider", None),
        input_file=getattr(args, "input_file", None),
        sample_input=getattr(args, "sample_input", False),
        target_audit_url=getattr(args, "target_audit_url", "https://incubrix.com"),
        max_retries=getattr(args, "max_retries", 2),
        content_limit=getattr(args, "content_limit", 10),
        use_llm=getattr(args, "use_llm", False),
        skip_audit=getattr(args, "skip_audit", False),
        skip_content=getattr(args, "skip_content", False),
    )

    db = SessionLocal()
    try:
        orchestrator = PipelineOrchestrator(
            db=db,
            cost_tracker=CostTracker(),
            max_retries=request.max_retries,
        )
        response = orchestrator.run(request)
        print_execution_summary(response)

        # Do not report success if run failed
        if response.status == "failed":
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
