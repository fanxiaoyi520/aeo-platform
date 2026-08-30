"""Orchestrator CLI — MS3 end-to-end listing generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import click

from aeo_orchestrator.hitl import is_waiting_hitl
from aeo_orchestrator.runner import build_runner_graph, run_listing_task, serialize_run_result
from aeo_orchestrator.state import TaskStatus


def _print_human_summary(payload: dict[str, Any]) -> None:
    click.echo(f"Task: {payload['task_id']}")
    click.echo(f"Status: {payload['status']}")
    if payload.get("waiting_hitl"):
        click.echo("Paused at human review — approve via API or re-run with --auto-approve")
    if payload.get("degraded_mode"):
        click.echo("Degraded mode: research used fallback keywords")

    final_output = payload.get("final_output")
    if isinstance(final_output, dict):
        click.echo(f"Title: {final_output.get('title', '')}")
        bullets = final_output.get("bullets")
        if isinstance(bullets, list):
            click.echo("Bullets:")
            for bullet in bullets:
                click.echo(f"  - {bullet}")
        metrics = final_output.get("metrics")
        if isinstance(metrics, dict):
            click.echo(
                f"Metrics: retries={metrics.get('retry_count')} "
                f"compliance={metrics.get('compliance_passed')}"
            )
    elif payload.get("generated"):
        generated = payload["generated"]
        if isinstance(generated, dict):
            click.echo(f"Draft title: {generated.get('title', '')}")

    trace = payload.get("trace")
    if isinstance(trace, list) and trace:
        agents = ", ".join(event.get("agent", "?") for event in trace if isinstance(event, dict))
        click.echo(f"Trace ({len(trace)} events): {agents}")


@click.group()
def main() -> None:
    """Launch AEO orchestrator CLI."""


@main.command("run")
@click.option("--sku", required=True, help="Product SKU")
@click.option("--platform", type=click.Choice(["amazon", "tiktok"]), default="amazon")
@click.option("--market", default="US", show_default=True)
@click.option(
    "--competitor",
    "competitors",
    multiple=True,
    help="Competitor ASIN (repeatable)",
)
@click.option(
    "--keyword",
    "keywords",
    multiple=True,
    help="Seed keyword (repeatable)",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    help="Auto-approve HITL for non-interactive runs",
)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON")
def run(
    sku: str,
    platform: str,
    market: str,
    competitors: tuple[str, ...],
    keywords: tuple[str, ...],
    auto_approve: bool,
    as_json: bool,
) -> None:
    """Run listing generation end-to-end (pauses at HITL unless --auto-approve)."""
    product_info: dict[str, object] = {}
    if competitors:
        product_info["competitor_asins"] = list(competitors)
    if keywords:
        product_info["keywords"] = list(keywords)

    graph = build_runner_graph()
    state = asyncio.run(
        run_listing_task(
            sku=sku,
            platform=platform,  # type: ignore[arg-type]
            market=market,
            product_info=product_info,
            auto_approve=auto_approve,
            graph=graph,
        )
    )
    waiting = is_waiting_hitl(graph, state["task_id"])
    if auto_approve and state.get("status") == TaskStatus.COMPLETED:
        waiting = False

    payload = serialize_run_result(state, waiting_hitl=waiting)
    if as_json:
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_human_summary(payload)


if __name__ == "__main__":
    main()
