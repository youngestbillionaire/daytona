import asyncio
import json
import sys
import time
from typing import Optional
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import typer
import websockets
from orchestrator.config import settings

app = typer.Typer(
    name="founder0",
    help="FOUNDER-0 Autonomous Multi-Agent Startup Engine CLI",
    add_completion=False
)
console = Console()

SERVER_URL = f"http://localhost:{settings.PORT}"
WS_URL = f"ws://localhost:{settings.PORT}"

@app.command()
def run(idea: str = typer.Argument(..., help="The one-sentence startup idea to build")):
    """Trigger an autonomous run end-to-end, stream stage logs, and output live links."""
    console.print(Panel(
        f"[bold cyan]FOUNDER-0 Autonomous Startup Engine[/bold cyan]\n[italic white]Input Idea:[/italic white] \"{idea}\"",
        border_style="cyan"
    ))

    # 1. Create run
    try:
        with console.status("[bold green]Contacting orchestrator...[/bold green]"):
            res = httpx.post(f"{SERVER_URL}/api/runs", json={"idea": idea}, timeout=10.0)
            if res.status_code != 200:
                console.print(f"[bold red]Failed to create run: {res.text}[/bold red]")
                raise typer.Exit(code=1)
            run_data = res.json()
            run_id = run_data["id"]

        console.print(f"[bold green]✓[/bold green] Run initiated: [bold yellow]{run_id}[/bold yellow]\n")

        # 2. Connect WebSocket to stream logs
        async def stream_run():
            ws_endpoint = f"{WS_URL}/ws/runs/{run_id}"
            async with websockets.connect(ws_endpoint) as ws:
                current_stage = ""
                while True:
                    msg = await ws.recv()
                    payload = json.loads(msg)
                    event_type = payload.get("event")
                    data = payload.get("data", {})

                    if event_type == "stage_transition":
                        stage = data.get("stage")
                        status = data.get("status")
                        if status == "running" and stage != current_stage:
                            current_stage = stage
                            console.print(f"\n[bold blue]━━━ STAGE: {stage} ━━━[/bold blue]")
                        elif status == "succeeded":
                            console.print(f"[bold green]✓ {stage} succeeded[/bold green]")
                        elif status == "failed":
                            console.print(f"[bold red]✗ {stage} failed: {data.get('error')}[/bold red]")

                    elif event_type == "log":
                        log_line = data.get("log", "")
                        console.print(f"  [dim]{log_line}[/dim]")

                    elif event_type == "run_completed":
                        console.print("\n" + "="*60)
                        console.print(Panel(
                            f"[bold green]🏆 FOUNDER-0 EXECUTION COMPLETE[/bold green]\n\n"
                            f"[bold white]Product Name:[/bold white] {data.get('product_name')}\n"
                            f"[bold cyan]Live MVP Preview:[/bold cyan] {data.get('preview_url')}\n"
                            f"[bold magenta]Pitch Deck URL:[/bold magenta] {SERVER_URL}{data.get('deck_url')}",
                            title="🚀 Venture Shipped",
                            border_style="green"
                        ))
                        break

                    elif event_type == "run_failed":
                        console.print(f"\n[bold red]❌ Run failed: {data.get('error')}[/bold red]")
                        break

        asyncio.run(stream_run())

    except Exception as e:
        console.print(f"[bold red]Connection error: {e}[/bold red]")
        console.print("[dim]Make sure the orchestrator server is running via `python -m orchestrator.main`[/dim]")
        raise typer.Exit(code=1)

@app.command("list")
def list_runs():
    """List all previous and ongoing runs."""
    try:
        res = httpx.get(f"{SERVER_URL}/api/runs", timeout=5.0)
        if res.status_code != 200:
            console.print(f"[bold red]Error: {res.text}[/bold red]")
            return
        runs = res.json()

        table = Table(title="FOUNDER-0 Runs History", border_style="cyan")
        table.add_column("Run ID", style="yellow")
        table.add_column("Product Name", style="bold white")
        table.add_column("Status", style="green")
        table.add_column("Current Stage", style="cyan")
        table.add_column("Idea", style="dim")

        for r in runs:
            table.add_row(
                r["id"],
                r.get("product_name") or "Pending",
                r["status"],
                r["current_stage"],
                (r["idea"][:40] + "...") if len(r["idea"]) > 40 else r["idea"]
            )

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Failed to connect to server: {e}[/bold red]")

@app.command()
def status(run_id: str = typer.Argument(..., help="The Run ID to inspect")):
    """Inspect timeline and artifacts of a specific run."""
    try:
        res = httpx.get(f"{SERVER_URL}/api/runs/{run_id}/timeline", timeout=5.0)
        if res.status_code != 200:
            console.print(f"[bold red]Error: {res.text}[/bold red]")
            return
        data = res.json()

        table = Table(title=f"Timeline for Run {run_id}", border_style="magenta")
        table.add_column("Stage", style="bold")
        table.add_column("Status", style="cyan")
        table.add_column("Logs Count", justify="right")

        for s in data["stages"]:
            status_color = "green" if s["status"] == "succeeded" else ("red" if s["status"] == "failed" else "yellow")
            table.add_row(
                s["stage"],
                f"[{status_color}]{s['status']}[/{status_color}]",
                str(len(s.get("logs", [])))
            )

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Failed to fetch status: {e}[/bold red]")

@app.command()
def replay(run_id: str = typer.Argument(..., help="The Run ID to replay")):
    """Replay an existing run from scratch with the same prompt."""
    try:
        res = httpx.post(f"{SERVER_URL}/api/runs/{run_id}/replay", timeout=5.0)
        if res.status_code != 200:
            console.print(f"[bold red]Error: {res.text}[/bold red]")
            return
        new_run = res.json()
        console.print(f"[bold green]Replay started with new Run ID: {new_run['id']}[/bold green]")
        console.print(f"Run `founder0 status {new_run['id']}` to monitor.")
    except Exception as e:
        console.print(f"[bold red]Replay error: {e}[/bold red]")

@app.command("seed-graph")
def seed_graph():
    """Run baseline Neo4j opportunity graph pre-seeding."""
    from orchestrator.seed_graph import seed_baseline_graph
    with console.status("[bold green]Seeding Neo4j Opportunity Knowledge Graph...[/bold green]"):
        asyncio.run(seed_baseline_graph())
    console.print("[bold green]✓ Baseline opportunity graph seeded successfully![/bold green]")

if __name__ == "__main__":
    app()
