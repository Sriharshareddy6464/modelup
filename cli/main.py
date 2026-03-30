import typer
import httpx
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

BACKEND_URL = "http://18.61.156.165:9000"
EC2_IP = "18.61.156.165"


@app.command()
def deploy(
    model: str = typer.Option(..., help="HuggingFace model ID e.g. facebook/bart-large-cnn"),
    task: str = typer.Option(..., help="Task type e.g. summarization, text-generation")
):
    """Deploy a HuggingFace model as a live API endpoint."""
    console.print(f"[bold cyan]Deploying {model}...[/bold cyan]")

    with httpx.Client(timeout=600) as client:
        response = client.post(f"{BACKEND_URL}/deploy", json={"model_id": model, "task": task})

    if response.status_code == 200:
        data = response.json()
        console.print(f"[bold green]✓ Endpoint ready:[/bold green] http://{EC2_IP}{data['endpoint']}")
    else:
        console.print(f"[bold red]✗ Failed:[/bold red] status={response.status_code} body={response.text}")


@app.command()
def destroy(
    model: str = typer.Option(..., help="HuggingFace model ID to destroy")
):
    """Stop and remove a deployed model."""
    model_slug = model.replace("/", "-")

    with httpx.Client(timeout=30) as client:
        response = client.delete(f"{BACKEND_URL}/deploy/{model_slug}")

    if response.status_code == 200:
        console.print(f"[bold green]✓ Destroyed:[/bold green] {model_slug}")
    else:
        console.print(f"[bold red]✗ Failed:[/bold red] {response.json()['detail']}")


@app.command(name="list")
def list_models():
    """List all deployed models."""
    with httpx.Client(timeout=10) as client:
        response = client.get(f"{BACKEND_URL}/list")

    data = response.json()

    if not data:
        console.print("[yellow]No models currently deployed.[/yellow]")
        return

    table = Table(title="Deployed Models")
    table.add_column("Model", style="cyan")
    table.add_column("Task", style="magenta")
    table.add_column("Port", style="green")
    table.add_column("Status", style="bold")

    for slug, info in data.items():
        table.add_row(info["model_id"], info["task"], str(info["port"]), info["status"])

    console.print(table)


@app.command()
def info(
    model: str = typer.Option(..., help="HuggingFace model ID")
):
    """Get info about a deployed model."""
    model_slug = model.replace("/", "-")

    with httpx.Client(timeout=10) as client:
        response = client.get(f"{BACKEND_URL}/info/{model_slug}")

    if response.status_code == 200:
        console.print(response.json())
    else:
        console.print(f"[bold red]✗ Not found:[/bold red] {model_slug}")


@app.command()
def status():
    """Check if the modelup backend is running."""
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(f"{BACKEND_URL}/status")
        console.print("[bold green]✓ Backend is online[/bold green]")
    except Exception:
        console.print("[bold red]✗ Backend is offline[/bold red]")


if __name__ == "__main__":
    app()