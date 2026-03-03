from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .client import DexScreenerClient
from .config import DEFAULT_CHAINS, ScanFilters
from .models import HotTokenCandidate
from .scanner import HotScanner
from .state import ScanPreset, StateStore
from .ui import (
    build_header,
    render_chain_heat_table,
    render_distribution_panel,
    render_flow_panel,
    render_hot_table,
    render_pair_detail,
    render_search_table,
)

app = typer.Typer(
    add_completion=False,
    help="Visual Dexscreener scanner CLI. Spot hot runners and inspect pair flow from the terminal.",
)
preset_app = typer.Typer(help="Save and reuse named scan filter presets.")
task_app = typer.Typer(help="Manage repeatable scan tasks.")
app.add_typer(preset_app, name="preset")
app.add_typer(task_app, name="task")
console = Console()


def _parse_chains(raw: str) -> tuple[str, ...]:
    values = tuple(c.strip().lower() for c in raw.split(",") if c.strip())
    return values or DEFAULT_CHAINS


def _candidate_json(c: HotTokenCandidate) -> dict[str, object]:
    p = c.pair
    return {
        "chainId": p.chain_id,
        "tokenAddress": p.base_address,
        "tokenSymbol": p.base_symbol,
        "tokenName": p.base_name,
        "dexId": p.dex_id,
        "pairAddress": p.pair_address,
        "pairUrl": p.pair_url,
        "priceUsd": p.price_usd,
        "priceChangeH1": p.price_change_h1,
        "priceChangeH24": p.price_change_h24,
        "volumeH24": p.volume_h24,
        "txnsH1": p.txns_h1,
        "liquidityUsd": p.liquidity_usd,
        "marketCap": p.market_cap,
        "fdv": p.fdv,
        "boostTotal": c.boost_total,
        "boostCount": c.boost_count,
        "hasProfile": c.has_profile,
        "score": c.score,
        "tags": c.tags,
    }


def _resolved_filters(
    *,
    chains: str | None,
    limit: int | None,
    min_liquidity_usd: float | None,
    min_volume_h24_usd: float | None,
    min_txns_h1: int | None,
    min_price_change_h1: float | None,
    preset_name: str | None,
) -> ScanFilters:
    default_filters = ScanFilters(chains=DEFAULT_CHAINS)
    resolved = default_filters

    if preset_name:
        store = StateStore()
        preset = store.get_preset(preset_name)
        if not preset:
            console.print(f"[red]Preset '{preset_name}' not found.[/red]")
            raise typer.Exit(code=1)
        resolved = preset.to_filters()

    if chains:
        resolved.chains = _parse_chains(chains)
    if limit is not None:
        resolved.limit = limit
    if min_liquidity_usd is not None:
        resolved.min_liquidity_usd = min_liquidity_usd
    if min_volume_h24_usd is not None:
        resolved.min_volume_h24_usd = min_volume_h24_usd
    if min_txns_h1 is not None:
        resolved.min_txns_h1 = min_txns_h1
    if min_price_change_h1 is not None:
        resolved.min_price_change_h1 = min_price_change_h1
    return resolved


def _task_filters(task_name_or_id: str) -> tuple[ScanFilters, str]:
    store = StateStore()
    task = store.get_task(task_name_or_id)
    if not task:
        console.print(f"[red]Task '{task_name_or_id}' not found.[/red]")
        raise typer.Exit(code=1)

    filters = ScanFilters(chains=DEFAULT_CHAINS)
    source = "defaults"
    if task.preset:
        preset = store.get_preset(task.preset)
        if not preset:
            console.print(f"[red]Task preset '{task.preset}' not found.[/red]")
            raise typer.Exit(code=1)
        filters = preset.to_filters()
        source = f"preset:{preset.name}"

    if task.filters:
        payload = task.filters
        if payload.get("chains"):
            filters.chains = tuple(payload["chains"])
        if payload.get("limit") is not None:
            filters.limit = int(payload["limit"])
        if payload.get("min_liquidity_usd") is not None:
            filters.min_liquidity_usd = float(payload["min_liquidity_usd"])
        if payload.get("min_volume_h24_usd") is not None:
            filters.min_volume_h24_usd = float(payload["min_volume_h24_usd"])
        if payload.get("min_txns_h1") is not None:
            filters.min_txns_h1 = int(payload["min_txns_h1"])
        if payload.get("min_price_change_h1") is not None:
            filters.min_price_change_h1 = float(payload["min_price_change_h1"])
        source += "+overrides"

    return filters, task.id


async def _scan(filters: ScanFilters) -> list[HotTokenCandidate]:
    async with DexScreenerClient() as client:
        scanner = HotScanner(client)
        return await scanner.scan(filters)


@app.command("hot")
def hot(
    chains: Annotated[str | None, typer.Option(help="Comma-separated chain IDs")] = None,
    limit: Annotated[int | None, typer.Option(help="Number of rows")] = None,
    min_liquidity_usd: Annotated[float | None, typer.Option(help="Minimum pair liquidity in USD")] = None,
    min_volume_h24_usd: Annotated[float | None, typer.Option(help="Minimum 24h volume in USD")] = None,
    min_txns_h1: Annotated[int | None, typer.Option(help="Minimum 1h transactions")] = None,
    min_price_change_h1: Annotated[float | None, typer.Option(help="Minimum 1h price change percent")] = None,
    preset: Annotated[str | None, typer.Option(help="Named preset to load before overrides")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output machine-readable JSON")] = False,
) -> None:
    """One-shot hot runner scan."""
    filters = _resolved_filters(
        chains=chains,
        limit=limit,
        min_liquidity_usd=min_liquidity_usd,
        min_volume_h24_usd=min_volume_h24_usd,
        min_txns_h1=min_txns_h1,
        min_price_change_h1=min_price_change_h1,
        preset_name=preset,
    )
    candidates = asyncio.run(_scan(filters))
    if as_json:
        typer.echo(json.dumps([_candidate_json(c) for c in candidates], indent=2, ensure_ascii=True))
        return

    console.print(build_header())
    console.print(
        render_hot_table(
            candidates,
            chains=filters.chains,
            limit=filters.limit,
            min_liquidity_usd=filters.min_liquidity_usd,
            min_volume_h24_usd=filters.min_volume_h24_usd,
            min_txns_h1=filters.min_txns_h1,
        )
    )
    console.print(Columns([render_chain_heat_table(candidates), render_flow_panel(candidates)]))


@app.command("watch")
def watch(
    chains: Annotated[str | None, typer.Option(help="Comma-separated chain IDs")] = None,
    limit: Annotated[int | None, typer.Option(help="Number of rows")] = None,
    interval: Annotated[float, typer.Option(help="Refresh interval seconds")] = 7.0,
    min_liquidity_usd: Annotated[float | None, typer.Option(help="Minimum pair liquidity in USD")] = None,
    min_volume_h24_usd: Annotated[float | None, typer.Option(help="Minimum 24h volume in USD")] = None,
    min_txns_h1: Annotated[int | None, typer.Option(help="Minimum 1h transactions")] = None,
    min_price_change_h1: Annotated[float | None, typer.Option(help="Minimum 1h price change percent")] = None,
    preset: Annotated[str | None, typer.Option(help="Named preset to load before overrides")] = None,
) -> None:
    """Live visual hot runner board for terminal workflows."""
    filters = _resolved_filters(
        chains=chains,
        limit=limit if limit is not None else 16,
        min_liquidity_usd=min_liquidity_usd,
        min_volume_h24_usd=min_volume_h24_usd,
        min_txns_h1=min_txns_h1,
        min_price_change_h1=min_price_change_h1,
        preset_name=preset,
    )

    async def loop() -> None:
        async with DexScreenerClient() as client:
            scanner = HotScanner(client)
            with Live(console=console, screen=True, refresh_per_second=6) as live:
                while True:
                    candidates = await scanner.scan(filters)
                    view = Group(
                        build_header(),
                        render_hot_table(
                            candidates,
                            chains=filters.chains,
                            limit=filters.limit,
                            min_liquidity_usd=filters.min_liquidity_usd,
                            min_volume_h24_usd=filters.min_volume_h24_usd,
                            min_txns_h1=filters.min_txns_h1,
                        ),
                        Columns([render_chain_heat_table(candidates), render_flow_panel(candidates)]),
                        Panel(
                            f"Refreshing every {interval:.1f}s. Press Ctrl+C to exit.",
                            border_style="dim",
                        ),
                    )
                    live.update(view)
                    await asyncio.sleep(interval)

    try:
        asyncio.run(loop())
    except KeyboardInterrupt:
        console.print("[dim]Stopped watch mode.[/dim]")


@app.command("inspect")
def inspect(
    address: Annotated[str, typer.Argument(help="Token address or pair address")],
    chain: Annotated[str, typer.Option("--chain", "-c", help="Chain ID, e.g. solana/base/ethereum")] = "solana",
    pair: Annotated[bool, typer.Option("--pair", help="Treat address as pair address")] = False,
) -> None:
    """Inspect a token or specific pair with concentration proxies."""

    async def run_inspect() -> None:
        async with DexScreenerClient() as client:
            scanner = HotScanner(client)
            if pair:
                p = await scanner.inspect_pair(chain, address)
                if not p:
                    console.print("[red]Pair not found.[/red]")
                    raise typer.Exit(code=1)
                console.print(build_header())
                console.print(render_pair_detail(p))
                return

            pairs = await scanner.inspect_token(chain, address)
            if not pairs:
                console.print("[red]Token not found or no pairs available.[/red]")
                raise typer.Exit(code=1)

            primary = pairs[0]
            orders = await client.get_orders(chain, address)
            boosts = orders.get("boosts", [])
            boost_total = float(sum(float(b.get("amount", 0) or 0) for b in boosts))
            candidate = HotTokenCandidate(
                pair=primary,
                score=0.0,
                boost_total=boost_total,
                boost_count=len(boosts),
                has_profile=any(o.get("type") == "tokenProfile" for o in orders.get("orders", [])),
                discovery="inspect",
                tags=[],
            )

            console.print(build_header())
            console.print(render_pair_detail(primary, boost_total=boost_total, boost_count=len(boosts)))
            console.print(render_distribution_panel(candidate))
            if len(pairs) > 1:
                console.print(f"[dim]Additional pairs found: {len(pairs) - 1}[/dim]")

    asyncio.run(run_inspect())


@app.command("search")
def search(
    query: Annotated[str, typer.Argument(help="Search query (symbol, token, pair) ")],
    limit: Annotated[int, typer.Option(help="Max result rows")] = 20,
) -> None:
    """Search across Dexscreener pairs."""

    async def run_search() -> None:
        async with DexScreenerClient() as client:
            scanner = HotScanner(client)
            pairs = await scanner.search(query=query, limit=limit)
            console.print(build_header())
            console.print(render_search_table(pairs))

    asyncio.run(run_search())


@app.command("god-prompt")
def god_prompt() -> None:
    """Print the God prompt for extending this tool."""
    path = Path(__file__).resolve().parents[1] / "GOD_PROMPT.md"
    if not path.exists():
        console.print("[red]GOD_PROMPT.md not found.[/red]")
        raise typer.Exit(code=1)
    console.print(path.read_text(encoding="utf-8"))


@app.command("why")
def why() -> None:
    """Explain why Dexscreener is used and what this CLI optimizes."""
    payload = {
        "top_use_cases": [
            "Fast discovery of active pools and cross-chain momentum.",
            "Liquidity/volume/transaction context for early signal validation.",
            "Trend-aware ranking and boost/profile visibility.",
        ],
        "dexscreener_api_constraints": {
            "60_rpm": [
                "/token-profiles/latest/v1",
                "/token-boosts/latest/v1",
                "/token-boosts/top/v1",
                "/orders/v1/{chainId}/{tokenAddress}",
            ],
            "300_rpm": [
                "/latest/dex/search",
                "/latest/dex/pairs/{chainId}/{pairId}",
                "/token-pairs/v1/{chainId}/{tokenAddress}",
            ],
            "holder_distribution": "Not exposed by public Dexscreener API endpoints.",
        },
    }
    console.print(json.dumps(payload, indent=2))


@preset_app.command("save")
def preset_save(
    name: Annotated[str, typer.Argument(help="Preset name")],
    chains: Annotated[str | None, typer.Option(help="Comma-separated chain IDs")] = None,
    limit: Annotated[int | None, typer.Option(help="Number of rows")] = None,
    min_liquidity_usd: Annotated[float | None, typer.Option(help="Minimum pair liquidity in USD")] = None,
    min_volume_h24_usd: Annotated[float | None, typer.Option(help="Minimum 24h volume in USD")] = None,
    min_txns_h1: Annotated[int | None, typer.Option(help="Minimum 1h transactions")] = None,
    min_price_change_h1: Annotated[float | None, typer.Option(help="Minimum 1h price change percent")] = None,
    from_preset: Annotated[str | None, typer.Option(help="Use this preset as a base")] = None,
) -> None:
    """Save a named preset from filters."""
    filters = _resolved_filters(
        chains=chains,
        limit=limit,
        min_liquidity_usd=min_liquidity_usd,
        min_volume_h24_usd=min_volume_h24_usd,
        min_txns_h1=min_txns_h1,
        min_price_change_h1=min_price_change_h1,
        preset_name=from_preset,
    )
    store = StateStore()
    preset = ScanPreset.from_filters(name=name, filters=filters)
    store.save_preset(preset)
    console.print(f"[green]Saved preset '{name}'.[/green]")


@preset_app.command("list")
def preset_list() -> None:
    """List saved presets."""
    store = StateStore()
    presets = store.list_presets()
    if not presets:
        console.print("[yellow]No presets found.[/yellow]")
        return
    table = Table(title="Presets")
    table.add_column("Name", style="bold cyan")
    table.add_column("Chains")
    table.add_column("Limit", justify="right")
    table.add_column("MinLiq", justify="right")
    table.add_column("MinVol24", justify="right")
    table.add_column("MinTx1h", justify="right")
    table.add_column("Updated", style="dim")
    for p in presets:
        table.add_row(
            p.name,
            ",".join(p.chains),
            str(p.limit),
            f"{p.min_liquidity_usd:.0f}",
            f"{p.min_volume_h24_usd:.0f}",
            str(p.min_txns_h1),
            p.updated_at,
        )
    console.print(table)


@preset_app.command("show")
def preset_show(name: Annotated[str, typer.Argument(help="Preset name")]) -> None:
    """Show a preset as JSON."""
    store = StateStore()
    preset = store.get_preset(name)
    if not preset:
        console.print(f"[red]Preset '{name}' not found.[/red]")
        raise typer.Exit(code=1)
    typer.echo(json.dumps(preset.to_dict(), indent=2, ensure_ascii=True))


@preset_app.command("delete")
def preset_delete(name: Annotated[str, typer.Argument(help="Preset name")]) -> None:
    """Delete a preset."""
    store = StateStore()
    deleted = store.delete_preset(name)
    if not deleted:
        console.print(f"[red]Preset '{name}' not found.[/red]")
        raise typer.Exit(code=1)
    console.print(f"[green]Deleted preset '{name}'.[/green]")


@task_app.command("create")
def task_create(
    name: Annotated[str, typer.Argument(help="Task name")],
    preset: Annotated[str | None, typer.Option(help="Preset name to base this task on")] = None,
    chains: Annotated[str | None, typer.Option(help="Inline chain override")] = None,
    limit: Annotated[int | None, typer.Option(help="Inline limit override")] = None,
    min_liquidity_usd: Annotated[float | None, typer.Option(help="Inline min liquidity override")] = None,
    min_volume_h24_usd: Annotated[float | None, typer.Option(help="Inline min volume override")] = None,
    min_txns_h1: Annotated[int | None, typer.Option(help="Inline min txns override")] = None,
    min_price_change_h1: Annotated[float | None, typer.Option(help="Inline min 1h % override")] = None,
    notes: Annotated[str, typer.Option(help="Task notes")] = "",
) -> None:
    """Create a new scan task."""
    store = StateStore()
    if preset and not store.get_preset(preset):
        console.print(f"[red]Preset '{preset}' not found.[/red]")
        raise typer.Exit(code=1)

    overrides: dict[str, object] = {}
    if chains:
        overrides["chains"] = list(_parse_chains(chains))
    if limit is not None:
        overrides["limit"] = limit
    if min_liquidity_usd is not None:
        overrides["min_liquidity_usd"] = min_liquidity_usd
    if min_volume_h24_usd is not None:
        overrides["min_volume_h24_usd"] = min_volume_h24_usd
    if min_txns_h1 is not None:
        overrides["min_txns_h1"] = min_txns_h1
    if min_price_change_h1 is not None:
        overrides["min_price_change_h1"] = min_price_change_h1

    try:
        task = store.create_task(
            name=name,
            preset=preset,
            filters=overrides or None,
            notes=notes,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Created task '{task.name}' ({task.id}).[/green]")


@task_app.command("list")
def task_list(
    status: Annotated[str | None, typer.Option(help="Filter by status: todo/running/done/blocked")] = None,
) -> None:
    """List tasks."""
    store = StateStore()
    if status and status not in {"todo", "running", "done", "blocked"}:
        console.print("[red]Invalid status. Use todo/running/done/blocked.[/red]")
        raise typer.Exit(code=1)
    tasks = store.list_tasks(status=status)  # type: ignore[arg-type]
    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return
    table = Table(title="Scan Tasks")
    table.add_column("ID", style="bold cyan")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Preset")
    table.add_column("Last Run")
    table.add_column("Updated", style="dim")
    for task in tasks:
        table.add_row(
            task.id,
            task.name,
            task.status,
            task.preset or "-",
            task.last_run_at or "-",
            task.updated_at,
        )
    console.print(table)


@task_app.command("show")
def task_show(task: Annotated[str, typer.Argument(help="Task id or name")]) -> None:
    """Show task JSON."""
    store = StateStore()
    row = store.get_task(task)
    if not row:
        console.print(f"[red]Task '{task}' not found.[/red]")
        raise typer.Exit(code=1)
    typer.echo(json.dumps(row.to_dict(), indent=2, ensure_ascii=True))


@task_app.command("status")
def task_status(
    task: Annotated[str, typer.Argument(help="Task id or name")],
    status: Annotated[str, typer.Argument(help="todo/running/done/blocked")],
) -> None:
    """Update task status."""
    if status not in {"todo", "running", "done", "blocked"}:
        console.print("[red]Invalid status. Use todo/running/done/blocked.[/red]")
        raise typer.Exit(code=1)
    store = StateStore()
    try:
        row = store.update_task_status(task, status=status)  # type: ignore[arg-type]
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Task '{row.name}' status -> {row.status}.[/green]")


@task_app.command("delete")
def task_delete(task: Annotated[str, typer.Argument(help="Task id or name")]) -> None:
    """Delete a task."""
    store = StateStore()
    deleted = store.delete_task(task)
    if not deleted:
        console.print(f"[red]Task '{task}' not found.[/red]")
        raise typer.Exit(code=1)
    console.print(f"[green]Deleted task '{task}'.[/green]")


@task_app.command("run")
def task_run(
    task: Annotated[str, typer.Argument(help="Task id or name")],
    as_json: Annotated[bool, typer.Option("--json", help="Output machine-readable JSON")] = False,
) -> None:
    """Execute a task scan now."""
    filters, task_id = _task_filters(task)
    candidates = asyncio.run(_scan(filters))
    store = StateStore()
    store.touch_task_run(task_id)

    if as_json:
        typer.echo(json.dumps([_candidate_json(c) for c in candidates], indent=2, ensure_ascii=True))
        return
    console.print(build_header())
    console.print(
        render_hot_table(
            candidates,
            chains=filters.chains,
            limit=filters.limit,
            min_liquidity_usd=filters.min_liquidity_usd,
            min_volume_h24_usd=filters.min_volume_h24_usd,
            min_txns_h1=filters.min_txns_h1,
        )
    )
    console.print(Columns([render_chain_heat_table(candidates), render_flow_panel(candidates)]))


if __name__ == "__main__":
    app()
